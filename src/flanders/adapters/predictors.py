"""Per-ORF predictors: signal peptides (fallback chain), transmembrane topology, Pfam.

Signal-peptide chain: SignalP 6 -> SignalP 5 -> DeepSig -> Phobius, whichever are
installed. Only DeepSig ships in the image; the others are user-installed under
<workspace>/tools/<name>/ (see `flanders tools status`).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from flanders.engine.invoke import run_tool, tool_output, tool_version, which
from flanders.errors import UpstreamDriftError

PRED_ENV = "env-predictors"
HMM_ENV = "env-hmmer-mmseqs"


@dataclass(frozen=True)
class Predictor:
    name: str  # signalp6 | signalp5 | deepsig | phobius | tmhmm
    program: str  # absolute path or program name
    env: str | None
    version: str

    @property
    def label(self) -> str:
        return f"{self.name} {self.version}"


def _user_tool(tools_dir: Path, name: str, program: str) -> str | None:
    for cand in (tools_dir / name / "bin" / program, tools_dir / name / program):
        if cand.is_file():
            return str(cand)
    return None


def detect(tools_dir: Path) -> dict[str, Predictor]:
    found: dict[str, Predictor] = {}
    for name, program in (("signalp6", "signalp6"), ("signalp5", "signalp"),
                          ("phobius", "phobius.pl"), ("tmhmm", "tmhmm")):
        path = _user_tool(tools_dir, name, program)
        if path:
            found[name] = Predictor(name, path, None, (tools_dir / name / "VERSION").read_text().strip()
                                    if (tools_dir / name / "VERSION").exists() else "user-installed")
    if which(PRED_ENV, "deepsig"):
        raw = tool_version(PRED_ENV, ("deepsig", "--version"))
        found["deepsig"] = Predictor("deepsig", "deepsig", PRED_ENV, raw.split()[-1] if raw != "unknown" else raw)
    return found


SIGNAL_CHAIN = ("signalp6", "signalp5", "deepsig", "phobius")
TM_CHAIN = ("tmhmm", "phobius")


def choose(chain: tuple[str, ...], available: dict[str, Predictor]) -> Predictor | None:
    for name in chain:
        if name in available:
            return available[name]
    return None


_DEEPSIG_ORG = {"gram-negative": "gramn", "gram-positive": "gramp", "eukaryote": "euk"}
_SIGNALP5_ORG = {"gram-negative": "gram-", "gram-positive": "gram+", "eukaryote": "euk"}
_SIGNALP6_ORG = {"gram-negative": "other", "gram-positive": "other", "eukaryote": "eukarya"}


def signal_peptides(pred: Predictor, fasta: Path, cwd: Path, organism_group: str, cpus: int) -> set[str]:
    """Return the IDs of proteins predicted to carry a signal peptide (any SP type)."""
    if pred.name == "deepsig":
        out = cwd / "deepsig.tsv"
        run_tool(tool="deepsig", argv=["deepsig", "-f", str(fasta), "-o", str(out), "-k",
                                       _DEEPSIG_ORG[organism_group], "-t", str(cpus)],
                 cwd=cwd, env=pred.env, version=pred.version)
        hits = set()
        for row in _rows(out):
            if len(row) >= 3 and row[2].strip().lower() == "signal peptide":
                hits.add(row[0].split()[0])
        return hits
    if pred.name == "signalp6":
        outdir = cwd / "signalp6"
        run_tool(tool="signalp6", argv=[pred.program, "--fastafile", str(fasta), "--organism",
                                        _SIGNALP6_ORG[organism_group], "--output_dir", str(outdir),
                                        "--format", "none", "--mode", "fast"],
                 cwd=cwd, version=pred.version)
        return {r[0].split()[0] for r in _rows(outdir / "prediction_results.txt")
                if len(r) > 1 and r[1] != "OTHER"}
    if pred.name == "signalp5":
        prefix = cwd / "signalp5"
        run_tool(tool="signalp5", argv=[pred.program, "-fasta", str(fasta), "-org",
                                        _SIGNALP5_ORG[organism_group], "-format", "short",
                                        "-prefix", str(prefix)], cwd=cwd, version=pred.version)
        return {r[0].split()[0] for r in _rows(Path(f"{prefix}_summary.signalp5"))
                if len(r) > 1 and r[1] != "OTHER"}
    if pred.name == "phobius":
        res = run_tool(tool="phobius", argv=[pred.program, "-short", str(fasta)], cwd=cwd, version=pred.version)
        return {k for k, (tm, sp) in _phobius(res.stdout_path).items() if sp}
    raise ValueError(pred.name)


def transmembrane(pred: Predictor, fasta: Path, cwd: Path) -> set[str]:
    """Return IDs of proteins with at least one predicted transmembrane helix."""
    if pred.name == "tmhmm":
        res = run_tool(tool="tmhmm", argv=[pred.program, "-short", str(fasta)], cwd=cwd, version=pred.version)
        hits = set()
        for line in res.stdout_path.read_text().splitlines():
            parts = line.split("\t")
            field = next((p for p in parts if p.startswith("PredHel=")), None)
            if field is None:
                if line.strip():
                    raise UpstreamDriftError(f"TMHMM output not recognized: {line[:80]!r}")
                continue
            if int(field.split("=")[1]) > 0:
                hits.add(parts[0])
        return hits
    if pred.name == "phobius":
        res = run_tool(tool="phobius", argv=[pred.program, "-short", str(fasta)], cwd=cwd, version=pred.version)
        return {k for k, (tm, sp) in _phobius(res.stdout_path).items() if tm > 0}
    raise ValueError(pred.name)


def _phobius(path: Path) -> dict[str, tuple[int, bool]]:
    out = {}
    for line in path.read_text().splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 3:
            out[parts[0]] = (int(parts[1]), parts[2] == "Y")
    return out


def pfam_domains(fasta: Path, hmm: Path, cwd: Path, cpus: int) -> dict[str, set[str]]:
    """hmmsearch Pfam-A (gathering thresholds) -> {protein_id: {PF00005, ...}}."""
    domtbl = cwd / "pfam.domtbl"
    run_tool(tool="hmmsearch", argv=["hmmsearch", "--cut_ga", "--noali", "--cpu", str(cpus),
                                     "--domtblout", str(domtbl), "-o", "/dev/null", str(hmm), str(fasta)],
             cwd=cwd, env=HMM_ENV, version=hmmer_release())
    hits: dict[str, set[str]] = {}
    for line in domtbl.read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split()
        if len(parts) < 22:
            raise UpstreamDriftError(f"hmmsearch domtblout row not recognized: {line[:80]!r}")
        hits.setdefault(parts[0], set()).add(parts[4].split(".")[0])
    return hits


def hmmer_release() -> str:
    for line in tool_output(HMM_ENV, ("hmmsearch", "-h")).splitlines():
        if line.startswith("# HMMER"):
            return line.split()[2]
    return "unknown"


def mmseqs_version() -> str:
    return tool_version(HMM_ENV, ("mmseqs", "version"))


def mmseqs_clusters(fasta: Path, cwd: Path, identity: float, coverage: float, cpus: int) -> dict[str, str]:
    """mmseqs2 easy-cluster -> {member_id: representative_id}."""
    prefix = cwd / "paralogs"
    raw = mmseqs_version()
    run_tool(tool="mmseqs", argv=["mmseqs", "easy-cluster", str(fasta), str(prefix), str(cwd / "tmp"),
                                  "--min-seq-id", str(identity), "-c", str(coverage),
                                  "--threads", str(cpus), "-v", "1"],
             cwd=cwd, env=HMM_ENV, version=raw)
    mapping = {}
    for row in _rows(Path(f"{prefix}_cluster.tsv")):
        if len(row) != 2:
            raise UpstreamDriftError("mmseqs cluster table not recognized")
        mapping[row[1]] = row[0]
    return mapping


def _rows(path: Path) -> list[list[str]]:
    if not path.exists():
        raise UpstreamDriftError(f"expected tool output missing: {path.name}")
    with open(path) as fh:
        return [r for r in csv.reader(fh, delimiter="\t") if r and not r[0].startswith("#")]
