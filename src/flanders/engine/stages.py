"""Pipeline stages. Each per-tag task writes into `<tag>.tmp/`, then renames (NFR8).

    fetch_genomes -> discover -> extract_flanks -> annotate_bgc -> predict_features
        -> collapse_paralogs -> enrich -> emit_fcer

In snapshot mode genomes are fetched before discovery (local search); in remote mode
discovery runs against NCBI first and only genomes with a cluster are fetched.
"""

from __future__ import annotations

import json
import os
import shutil
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from flanders import CITATION, __version__
from flanders.adapters import antismash, cblaster
from flanders.adapters import predictors as preds
from flanders.config.models import RunConfig
from flanders.errors import TaskFailure, UpstreamDriftError
from flanders.fcer import io as fcer_io
from flanders.fcer.models import Fcer
from flanders.genomics import coords, genbank
from flanders.genomics.accessions import is_versioned
from flanders.genomics.models import EnrichInput, EnrichOrf, Orf
from flanders.harness import enrich as harness
from flanders.ncbi import client as ncbi
from flanders.workspace.ids import utcnow_iso
from flanders.workspace.layout import RunPaths, Workspace


class Stage(StrEnum):
    FETCH_GENOMES = "fetch_genomes"
    DISCOVER = "discover"
    EXTRACT_FLANKS = "extract_flanks"
    ANNOTATE_BGC = "annotate_bgc"
    PREDICT_FEATURES = "predict_features"
    COLLAPSE_PARALOGS = "collapse_paralogs"
    ENRICH = "enrich"
    EMIT_FCER = "emit_fcer"


RUN_WIDE = {Stage.DISCOVER}


@dataclass
class RunContext:
    run_id: str
    name: str
    ws: Workspace
    paths: RunPaths
    cfg: RunConfig
    effective: dict
    jobs: int
    reference_checksums: dict[str, str] = field(default_factory=dict)
    input_checksums: dict[str, str] = field(default_factory=dict)
    predictors: dict[str, preds.Predictor] = field(default_factory=dict)

    @property
    def genome_cache(self) -> Path:
        return self.ws.root / "snapshots" / "genomes"

    def out(self, stage: Stage, tag: str) -> Path:
        return self.paths.task_dir(stage, tag)

    def read_json(self, stage: Stage, tag: str, name: str):
        return json.loads((self.out(stage, tag) / name).read_text())


@contextmanager
def task_output(final: Path):
    """Yield a scratch directory that becomes `final` only if the block succeeds."""
    tmp = final.with_name(final.name + ".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    yield tmp
    for p in tmp.rglob("*"):
        if p.is_file():
            with open(p, "rb") as fh:
                os.fsync(fh.fileno())
    if final.exists():
        shutil.rmtree(final)
    os.replace(tmp, final)


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=1, default=str) + "\n")


# ----------------------------------------------------------------------- genomes

def fetch_genome(ctx: RunContext, tag: str) -> None:
    """Fetch an assembly into the shared accession.version cache (immutable records)."""
    cache = ctx.genome_cache / tag
    meta_path = cache / "meta.json"
    if not meta_path.exists():
        with task_output(cache) as tmp:
            gbff = ncbi.download_assembly(tag, tmp, api_key=ctx.cfg.ncbi.get("api_key"))
            proteins, records = [], set()
            for orf, seq in genbank.iter_orfs(gbff):
                proteins.append((orf.orf_id, seq))
                records.add(orf.record)
            if not proteins:
                raise TaskFailure("no_cds_annotation",
                                  f"{tag} has no annotated CDS; use an annotated (e.g. RefSeq GCF_) assembly")
            report = {}
            if (tmp / f"{tag}.report.json").exists():
                report = json.loads((tmp / f"{tag}.report.json").read_text())
            _write_json(tmp / "meta.json", {
                "accession": tag,
                "organism": genbank.organism_name(gbff) or report.get("organism", {}).get("organismName"),
                "retrieved_at": utcnow_iso(),
                "gbff": f"{tag}.gbff",
                "gbff_sha256": _sha(gbff),
                "protein_count": len(proteins),
                "protein_content_sha256": ncbi.protein_content_checksum(proteins),
                "records": sorted(records),
                "ncbi_report": report,
            })
    with task_output(ctx.out(Stage.FETCH_GENOMES, tag)) as tmp:
        meta = json.loads(meta_path.read_text())
        _write_json(tmp / "genome.json", {**meta, "path": str(cache / meta["gbff"])})


def _sha(path: Path) -> str:
    from flanders.reference.data import sha256_file

    return sha256_file(path)


def genome_meta(ctx: RunContext, tag: str) -> dict:
    return ctx.read_json(Stage.FETCH_GENOMES, tag, "genome.json")


# ---------------------------------------------------------------------- discover

def discover(ctx: RunContext, fetched_tags: list[str]) -> dict:
    """Run cblaster; return {"clusters": {tag: cluster}, "excluded": {tag: reason}}."""
    final = ctx.out(Stage.DISCOVER, "run")
    query = ctx.paths.inputs / Path(ctx.cfg.query).name
    with task_output(final) as tmp:
        excluded: dict[str, str] = {}
        cblaster.configure(tmp, ctx.cfg.ncbi.get("email"), ctx.cfg.ncbi.get("api_key"))
        if ctx.cfg.search == "snapshot":
            gbffs, record_to_tag = [], {}
            for tag in fetched_tags:
                meta = genome_meta(ctx, tag)
                gbffs.append(Path(meta["path"]))
                for rec in meta["records"]:
                    record_to_tag[rec] = tag
                    record_to_tag[rec.split(".")[0]] = tag
            db = cblaster.makedb(gbffs, "snapshot", tmp / "db", cpus=ctx.jobs)
            session = cblaster.search(query, "local", tmp, ctx.cfg.cblaster, db, cpus=ctx.jobs)
            manifest = _snapshot_manifest(ctx, fetched_tags)
            _write_json(tmp / "manifest.json", manifest)
        else:
            session = cblaster.search(query, "remote", tmp, ctx.cfg.cblaster, None, cpus=ctx.jobs)
            record_to_tag = {}
        clusters = cblaster.parse_session(session)
        by_tag: dict[str, list] = {}
        log = ctx.paths.root / "ncbi_requests.jsonl"
        for cl in clusters:
            tag = record_to_tag.get(cl.scaffold) or record_to_tag.get(cl.scaffold.split(".")[0])
            if tag is None and ctx.cfg.search == "remote":
                if not is_versioned(cl.scaffold):
                    raise UpstreamDriftError(f"cblaster reported an unversioned scaffold {cl.scaffold!r}")
                try:
                    tag = ncbi.nucleotide_to_assembly(cl.scaffold, log, ctx.cfg.ncbi.get("api_key"))
                except TaskFailure:
                    tag = None
                record_to_tag[cl.scaffold] = tag or f"unmapped:{cl.scaffold}"
                tag = record_to_tag[cl.scaffold]
            if tag is None:
                continue
            by_tag.setdefault(tag, []).append(cl)
        chosen = {}
        for tag, cls in sorted(by_tag.items()):
            if tag.startswith("unmapped:"):
                excluded[tag] = "scaffold_not_linked_to_an_assembly"
                continue
            cls.sort(key=lambda c: (-c.score, c.scaffold, c.start))
            best = cls[0]
            organism = best.organism
            if ctx.cfg.search == "snapshot":
                # cblaster names local organisms after the input file; use the record's own name.
                organism = genome_meta(ctx, tag).get("organism") or organism
            chosen[tag] = {
                "organism": organism, "scaffold": best.scaffold, "start": best.start,
                "end": best.end, "score": best.score, "other_clusters": len(cls) - 1,
                "hits": [h.__dict__ for h in best.hits],
            }
        for tag in fetched_tags:
            if tag not in chosen:
                excluded[tag] = "no_cluster_found"
        result = {"clusters": chosen, "excluded": excluded, "cblaster_version": cblaster.version(),
                  "search_mode": ctx.cfg.search, "searched_at": utcnow_iso()}
        _write_json(tmp / "clusters.json", result)
    return result


def _snapshot_manifest(ctx: RunContext, tags: list[str]) -> dict:
    import hashlib

    entries = []
    for tag in sorted(tags):
        m = genome_meta(ctx, tag)
        entries.append({k: m[k] for k in ("accession", "organism", "retrieved_at", "gbff_sha256",
                                          "protein_count", "protein_content_sha256")})
    h = hashlib.sha256()
    for e in entries:
        h.update(f"{e['accession']}\t{e['protein_content_sha256']}\n".encode())
    return {"kind": "fresh_snapshot", "created_at": utcnow_iso(), "genomes": entries,
            "content_sha256": h.hexdigest(), "datasets_version": ncbi.datasets_version()}


def discovery(ctx: RunContext) -> dict:
    return ctx.read_json(Stage.DISCOVER, "run", "clusters.json")


# ------------------------------------------------------------------ neighborhood

def _match_seed(orfs: list[Orf], hits: list[dict], start: int, end: int) -> list[int]:
    names = {h["name"] for h in hits}
    names |= {n.split(".")[0] for n in names}
    idx = [i for i, o in enumerate(orfs)
           if o.orf_id in names or o.orf_id.split(".")[0] in names or (o.locus_tag and o.locus_tag in names)]
    if not idx:  # fall back to coordinates
        idx = [i for i, o in enumerate(orfs) if coords.overlaps(o.start, o.end, start, end)]
    return idx


def extract_flanks(ctx: RunContext, tag: str) -> None:
    cl = discovery(ctx)["clusters"][tag]
    gbff = Path(genome_meta(ctx, tag)["path"])
    with task_output(ctx.out(Stage.EXTRACT_FLANKS, tag)) as tmp:
        all_orfs: list[Orf] = []
        with open(tmp / "proteins.faa", "w") as faa:
            for orf, seq in genbank.iter_orfs(gbff):
                all_orfs.append(orf)
                faa.write(f">{orf.orf_id}\n{seq}\n")
        scaffold = cl["scaffold"]
        on_record = sorted((o for o in all_orfs if o.record == scaffold or o.record.split(".")[0] == scaffold.split(".")[0]),
                           key=lambda o: (o.start, o.end))
        if not on_record:
            raise TaskFailure("scaffold_not_in_genome", f"{scaffold} not found in {tag}")
        seed_idx = _match_seed(on_record, cl["hits"], cl["start"], cl["end"])
        if not seed_idx:
            raise TaskFailure("seed_not_located", f"no ORF on {scaffold} matches the cluster hits")
        lo, hi = min(seed_idx), max(seed_idx)
        strand = Counter(on_record[i].strand for i in seed_idx).most_common(1)[0][0]
        n = ctx.cfg.flank_orfs
        left = list(range(max(0, lo - n), lo))
        right = list(range(hi + 1, min(len(on_record), hi + 1 + n)))
        upstream, downstream = (left, right) if strand == "+" else (right, left)
        members = {on_record[i].orf_id: "seed" for i in range(lo, hi + 1)}
        members.update({on_record[i].orf_id: "upstream" for i in upstream})
        members.update({on_record[i].orf_id: "downstream" for i in downstream})
        with open(tmp / "orfs.jsonl", "w") as fh:
            for o in all_orfs:
                fh.write(o.model_dump_json() + "\n")
        notes = []
        if len(upstream) < n or len(downstream) < n:
            notes.append("flank_truncated_by_record_end")
        _write_json(tmp / "neighborhood.json", {
            "record": on_record[lo].record, "seed_start": on_record[lo].start, "seed_end": on_record[hi].end,
            "seed_strand": strand, "flank_orfs": n, "members": members, "organism": cl["organism"],
            "notes": notes, "orf_count": len(all_orfs),
        })


def _orfs(ctx: RunContext, tag: str) -> list[Orf]:
    with open(ctx.out(Stage.EXTRACT_FLANKS, tag) / "orfs.jsonl") as fh:
        return [Orf.model_validate_json(line) for line in fh]


def _proteins(ctx: RunContext, tag: str) -> Path:
    return ctx.out(Stage.EXTRACT_FLANKS, tag) / "proteins.faa"


# ---------------------------------------------------------------------- features

def annotate_bgc(ctx: RunContext, tag: str) -> None:
    with task_output(ctx.out(Stage.ANNOTATE_BGC, tag)) as tmp:
        calls: dict[str, list[str]] = {}
        regions = []
        if "antismash" in ctx.cfg.features:
            gbff = Path(genome_meta(ctx, tag)["path"])
            cpus = _cpus(ctx, 4)
            params = dict(ctx.cfg.antismash)
            taxon = str(params.pop("taxon", "bacteria"))
            result = antismash.run(gbff, tmp / "antismash", ctx.ws.reference / _ref_release() / "antismash8",
                                   params, cpus, taxon)
            regions = antismash.parse_regions(result)
            orfs = _orfs(ctx, tag)
            for r in regions:
                for o in orfs:
                    if (o.record == r.record or o.record.split(".")[0] == r.record.split(".")[0]) and \
                            coords.overlaps(o.start, o.end, r.start, r.end):
                        feats = calls.setdefault(o.orf_id, [])
                        for p in r.products:
                            feats.append(f"antismash:{p}")
                        feats.append("antismash:any")
            # Keep only the JSON result; the HTML report is large.
            keep = tmp / "antismash_result.json"
            shutil.copy(result, keep)
            shutil.rmtree(tmp / "antismash" / "out", ignore_errors=True)
        _write_json(tmp / "bgc.json", {"calls": {k: sorted(set(v)) for k, v in calls.items()},
                                       "regions": [r.__dict__ for r in regions],
                                       "tool": f"antismash {antismash.version()}" if regions or
                                       "antismash" in ctx.cfg.features else None})


def _ref_release() -> str:
    from flanders.reference.data import RELEASE

    return RELEASE


def _cpus(ctx: RunContext, per_task: int) -> int:
    return max(1, min(per_task, ctx.jobs))


def predict_features(ctx: RunContext, tag: str) -> None:
    fasta = _proteins(ctx, tag)
    with task_output(ctx.out(Stage.PREDICT_FEATURES, tag)) as tmp:
        calls: dict[str, set[str]] = {}
        used: dict[str, str] = {}
        unavailable: dict[str, str] = {}
        cpus = _cpus(ctx, 2)
        if "signal_peptide" in ctx.cfg.features:
            p = preds.choose(preds.SIGNAL_CHAIN, ctx.predictors)
            if p is None:
                unavailable["signal_peptide"] = "no signal-peptide predictor installed"
            else:
                for pid in preds.signal_peptides(p, fasta, tmp, ctx.cfg.organism_group, cpus):
                    calls.setdefault(pid, set()).add("signal_peptide")
                used["signal_peptide"] = p.label
        if "transmembrane" in ctx.cfg.features:
            p = preds.choose(preds.TM_CHAIN, ctx.predictors)
            if p is None:
                unavailable["transmembrane"] = (
                    "no transmembrane predictor installed (TMHMM 2.0c or Phobius); "
                    "see `flanders tools status`")
            else:
                for pid in preds.transmembrane(p, fasta, tmp):
                    calls.setdefault(pid, set()).add("transmembrane")
                used["transmembrane"] = p.label
        if "pfam" in ctx.cfg.features:
            ref = ctx.ws.reference / _ref_release() / "pfam" / "Pfam-A.hmm"
            for pid, doms in preds.pfam_domains(fasta, ref, tmp, cpus).items():
                calls.setdefault(pid, set()).update(f"pfam:{d}" for d in doms)
            used["pfam"] = f"hmmer {preds.hmmer_release()}"
        _write_json(tmp / "features.json", {"calls": {k: sorted(v) for k, v in calls.items()},
                                            "predictors": used, "unavailable": unavailable})


def collapse_paralogs(ctx: RunContext, tag: str) -> None:
    st = ctx.cfg.statistics
    with task_output(ctx.out(Stage.COLLAPSE_PARALOGS, tag)) as tmp:
        mapping = preds.mmseqs_clusters(_proteins(ctx, tag), tmp, st.paralog_identity,
                                        st.paralog_coverage, _cpus(ctx, 4))
        shutil.rmtree(tmp / "tmp", ignore_errors=True)
        reps = set(mapping.values())
        hood = ctx.read_json(Stage.EXTRACT_FLANKS, tag, "neighborhood.json")
        feats = ctx.read_json(Stage.PREDICT_FEATURES, tag, "features.json")
        bgc = ctx.read_json(Stage.ANNOTATE_BGC, tag, "bgc.json")
        orfs = []
        for o in _orfs(ctx, tag):
            f = set(feats["calls"].get(o.orf_id, [])) | set(bgc["calls"].get(o.orf_id, []))
            orfs.append(EnrichOrf(orf_id=o.orf_id, location=hood["members"].get(o.orf_id),
                                  in_background=o.orf_id in reps or o.orf_id not in mapping,
                                  length_aa=o.length_aa, gc=o.gc, features=sorted(f)))
        # Feature universe: per-ORF predictions always; domains and BGC classes only when
        # present in the neighborhood (absent ones cannot be enriched).
        universe = set()
        for name in ("signal_peptide", "transmembrane"):
            if name in ctx.cfg.features and name not in feats["unavailable"]:
                universe.add(name)
        for o in orfs:
            if o.location is not None:
                universe |= {f for f in o.features if f.startswith(("pfam:", "antismash:"))}
        used = dict(feats["predictors"])
        used["paralog_collapse"] = f"mmseqs {preds.mmseqs_version()}"
        if bgc.get("tool"):
            used["antismash"] = bgc["tool"]
        inp = EnrichInput(
            tag=tag, organism=hood.get("organism"), record=hood["record"], seed_start=hood["seed_start"],
            seed_end=hood["seed_end"], seed_strand=hood["seed_strand"], flank_orfs=hood["flank_orfs"],
            orfs=orfs, features_tested=sorted(universe), unavailable_features=feats["unavailable"],
            predictors_used=used, background_definition=harness.background_definition(st),
        )
        (tmp / "enrich_input.json").write_text(inp.model_dump_json() + "\n")


# --------------------------------------------------------------------- statistics

def enrich(ctx: RunContext, tag: str) -> None:
    inp = EnrichInput.model_validate_json(
        (ctx.out(Stage.COLLAPSE_PARALOGS, tag) / "enrich_input.json").read_text())
    results = harness.analyze(inp, ctx.cfg.statistics, ctx.cfg.seed)
    with task_output(ctx.out(Stage.ENRICH, tag)) as tmp:
        _write_json(tmp / "results.json", [r.__dict__ for r in results])


def emit_fcer(ctx: RunContext, tag: str) -> list[Path]:
    inp = EnrichInput.model_validate_json(
        (ctx.out(Stage.COLLAPSE_PARALOGS, tag) / "enrich_input.json").read_text())
    results = ctx.read_json(Stage.ENRICH, tag, "results.json")
    hood = ctx.read_json(Stage.EXTRACT_FLANKS, tag, "neighborhood.json")
    orf_meta = {o.orf_id: o for o in _orfs(ctx, tag) if o.orf_id in hood["members"]}
    feats_by_orf = {o.orf_id: o.features for o in inp.orfs}
    st = ctx.cfg.statistics
    disc = discovery(ctx)
    tools = _tool_records(ctx, disc, inp)
    neighborhood = {
        "record": inp.record, "seed_start": inp.seed_start, "seed_end": inp.seed_end,
        "seed_strand": inp.seed_strand, "flank_orfs": inp.flank_orfs,
        "orfs": [
            {"orf_id": oid, "location": hood["members"][oid], "start": o.start, "end": o.end,
             "strand": o.strand, "locus_tag": o.locus_tag, "product": o.product,
             "length_aa": o.length_aa, "features": feats_by_orf.get(oid, [])}
            for oid, o in sorted(orf_meta.items(), key=lambda kv: (kv[1].start, kv[1].end))
        ],
    }
    provenance = {
        "flanders_version": __version__, "created_at": utcnow_iso(), "run_id": ctx.run_id,
        "run_name": ctx.name, "search_mode": ctx.cfg.search,
        "discovery_reproducible": ctx.cfg.search != "remote",
        "search_metadata": {k: disc[k] for k in ("searched_at", "cblaster_version", "search_mode")},
        "effective_config": ctx.effective, "tools": tools,
        "reference_checksums": ctx.reference_checksums, "input_checksums": ctx.input_checksums,
        "analyzers": inp.predictors_used, "unavailable_features": inp.unavailable_features,
        "background_definition": inp.background_definition, "citation": CITATION,
    }
    written = []
    final = ctx.out(Stage.EMIT_FCER, tag)
    with task_output(final) as tmp:
        for r in results:
            fcer = Fcer.model_validate({
                "tag": tag, "organism": inp.organism, "location": r["location"],
                "neighborhood": neighborhood,
                "statistics": {**st.model_dump(), "seed": ctx.cfg.seed},
                "tests": r["tests"], "covariates": r["covariates"], "provenance": provenance,
            })
            fcer_io.write(fcer, tmp)
        written = sorted(p.name for p in tmp.glob("*.json"))
    ctx.paths.fcer.mkdir(parents=True, exist_ok=True)
    for name in written:
        for ext in (".json", ".csv"):
            src = final / name.replace(".json", ext)
            shutil.copy(src, ctx.paths.fcer / src.name)
    return [ctx.paths.fcer / n for n in written]


def _tool_records(ctx: RunContext, disc: dict, inp: EnrichInput) -> list[dict]:
    recs = [{"tool": "cblaster", "version": disc.get("cblaster_version", "unknown")}]
    for label in sorted(set(inp.predictors_used.values())):
        tool, _, ver = label.partition(" ")
        recs.append({"tool": tool, "version": ver or "unknown"})
    recs.append({"tool": "ncbi-datasets", "version": ncbi.datasets_version()})
    return recs
