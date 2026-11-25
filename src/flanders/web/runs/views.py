"""GUI views. Thin: they read the index and files, and launch runs via the supervisor."""

from __future__ import annotations

import json
import re
from collections import Counter

import yaml
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from flanders import CITATION
from flanders.config.merge import load_config
from flanders.engine import supervisor
from flanders.errors import FlandersError
from flanders.web.runs import svg
from flanders.workspace.models import FcerEntry, Run, RunStatus

WS = settings.WORKSPACE
FLANK = ("upstream", "downstream")


def _run(run_id: str) -> Run:
    try:
        return Run.objects.get(pk=run_id)
    except Run.DoesNotExist as exc:
        raise Http404("no such run") from exc


def _report(run: Run) -> dict:
    p = WS.run_dir(run.run_id) / "report.json"
    return json.loads(p.read_text()) if p.exists() else {"failed": [], "excluded": []}


def _effective(run: Run) -> dict:
    p = WS.run_dir(run.run_id) / "config.effective.yaml"
    return yaml.safe_load(p.read_text()) if p.exists() else {}


def home(request):
    latest = Run.objects.filter(status__in=[RunStatus.COMPLETE, RunStatus.COMPLETE_WITH_FAILURES]).first()
    if latest:
        return redirect("runs:genomes", run_id=latest.run_id)
    return redirect("runs:list")


def run_list(request):
    return render(request, "runs/list.html", {"runs": Run.objects.all(), "nav": "runs"})


def genomes(request, run_id: str):
    run = _run(run_id)
    report = _report(run)
    eff = _effective(run)
    entries = list(FcerEntry.objects.filter(run=run).order_by("tag", "location"))
    by_tag: dict[str, list[FcerEntry]] = {}
    for e in entries:
        by_tag.setdefault(e.tag, []).append(e)
    analyzed = len(by_tag)
    # Tallies: genomes in which a feature is significant upstream or downstream.
    tally = Counter()
    for es in by_tag.values():
        feats = {f for e in es if e.location in FLANK for f, _q in e.significant}
        tally.update(feats)
    feature = request.GET.get("feature")
    q = request.GET.get("q", "").strip().lower()
    sort = request.GET.get("sort", "sig")
    rows = []
    for e in entries:
        if feature and feature not in {f for f, _ in e.significant}:
            continue
        if q and q not in e.tag.lower() and q not in e.organism.lower():
            continue
        rows.append({"e": e, "n_sig": len(e.significant), "top": e.significant[:4]})
    if sort == "sig":
        rows.sort(key=lambda r: (-r["n_sig"], r["e"].best_q if r["e"].best_q is not None else 2, r["e"].tag))
    elif sort == "genome":
        rows.sort(key=lambda r: (r["e"].organism, r["e"].tag))
    ctx = {
        "run": run, "nav": "genomes", "rows": rows, "report": report, "stats": eff.get("statistics", {}),
        "eff": eff, "analyzed": analyzed,
        "requested": run.genome_count or analyzed + len(report.get("excluded", [])) + len(report.get("failed", [])),
        "tallies": sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))[:24],
        "feature": feature, "q": q, "sort": sort,
    }
    if request.headers.get("HX-Request"):
        return render(request, "runs/_genome_rows.html", ctx)
    return render(request, "runs/genomes.html", ctx)


def genome(request, run_id: str, tag: str):
    run = _run(run_id)
    files = sorted((WS.run_dir(run_id) / "fcer").glob(f"{tag}.*.json"))
    if not files:
        raise Http404("no FCER for this genome")
    fcers = {f.name.split(".")[-2]: json.loads(f.read_text()) for f in files}
    loc = request.GET.get("location") or ("upstream" if "upstream" in fcers else next(iter(fcers)))
    if loc not in fcers:
        raise Http404("no such location")
    fc = fcers[loc]
    selected = request.GET.get("feature")
    tests = fc["statistics"]["tests"]
    rows: dict[str, dict] = {}
    for t in fc["tests"]:
        r = rows.setdefault(t["feature"], {"feature": t["feature"], "k": t["k"], "n": t["n"],
                                           "b": t["background_hits"], "B": t["background_n"],
                                           "effect": t["effect_log2"], "predictor": t["predictor"]})
        r[t["test"]] = t
    primary = tests[0]
    table = sorted(rows.values(), key=lambda r: (
        r.get(primary, {}).get("q_value") if r.get(primary, {}).get("q_value") is not None else 2, r["feature"]))
    ctx = {
        "run": run, "nav": "genomes", "tag": tag, "fc": fc, "loc": loc, "locations": list(fcers),
        "table": table, "tests": tests, "primary": primary, "selected": selected,
        "map": svg.neighborhood(fc["neighborhood"]["orfs"], selected),
        "stats": fc["statistics"],
    }
    return render(request, "runs/genome.html", ctx)


def provenance(request, run_id: str, tag: str, location: str):
    path = WS.run_dir(run_id) / "fcer" / f"{tag}.{location}.json"
    if not path.exists():
        raise Http404()
    fc = json.loads(path.read_text())
    prov = fc["provenance"]
    return render(request, "runs/_provenance.html", {
        "prov": prov, "config_yaml": yaml.safe_dump(prov["effective_config"], sort_keys=False),
        "run_id": run_id, "tag": tag, "location": location,
    })


def export_config(request, run_id: str):
    run = _run(run_id)
    text = (WS.run_dir(run.run_id) / "config.effective.yaml").read_text()
    resp = HttpResponse(text, content_type="application/x-yaml")
    resp["Content-Disposition"] = f'attachment; filename="{run.run_id}.yaml"'
    return resp


def ledger(request, run_id: str | None = None):
    run = _run(run_id) if run_id else Run.objects.filter(status=RunStatus.RUNNING).first()
    if run is None:
        return render(request, "runs/_ledger.html", {"run": None})
    counts = Counter()
    per_tag: dict[str, dict] = {}
    for t in run.tasks.order_by("id"):
        if t.tag == "run":
            continue
        cur = per_tag.setdefault(t.tag, {"tag": t.tag, "stage": t.stage, "status": t.status, "reason": ""})
        if t.status == "failed":
            cur.update(stage=t.stage, status="failed", reason=f"{t.reason}: {t.detail[:200]}")
        elif cur["status"] != "failed":
            cur.update(stage=t.stage, status=t.status)
    for v in per_tag.values():
        if v["status"] == "complete" and v["stage"] != "emit_fcer":
            v["status"] = "in progress"
        counts[v["status"]] += 1
    show_panel = request.GET.get("panel") == "1"
    return render(request, "runs/_ledger.html", {
        "run": run, "counts": counts, "tags": sorted(per_tag.values(), key=lambda v: (v["status"] != "failed", v["tag"])),
        "panel": show_panel, "active": run.status == RunStatus.RUNNING,
    })


@require_POST
def cancel(request, run_id: str):
    run = _run(run_id)
    if run.pid and run.status == RunStatus.RUNNING:
        supervisor.cancel(run.pid)
    return redirect("runs:list")


@require_POST
def resume(request, run_id: str):
    try:
        supervisor.resume(run_id, WS)
    except FlandersError as exc:
        return render(request, "runs/list.html", {"runs": Run.objects.all(), "error": str(exc), "nav": "runs"})
    return redirect("runs:list")


# ----------------------------------------------------------------- composer

CURATED_CBLASTER = [("min_identity", "Minimum identity (%)", "--min_identity"),
                    ("min_coverage", "Minimum query coverage (%)", "--min_coverage"),
                    ("max_evalue", "Maximum e-value", "--max_evalue"),
                    ("gap", "Maximum gap between hits (bp)", "--gap"),
                    ("unique", "Minimum unique query hits", "--unique")]


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", s).strip("-")[:60] or "draft"


def _kv(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = yaml.safe_load(v.strip()) if v.strip() else True
    return out


def compose(request):
    errors, review = [], None
    form = request.POST if request.method == "POST" else {}
    if request.method == "POST":
        name = _slug(form.get("name", "") or "run")
        draft = WS.root / "drafts" / name
        draft.mkdir(parents=True, exist_ok=True)
        if "query" in request.FILES:
            (draft / "query.faa").write_bytes(request.FILES["query"].read())
        genomes_text = form.get("genomes", "").strip()
        if genomes_text:
            (draft / "genomes.txt").write_text(genomes_text + "\n")
        cfg: dict = {
            "name": form.get("name") or name, "query": "query.faa", "search": form.get("search", "snapshot"),
            "flank_orfs": int(form.get("flank_orfs") or 4), "features": request.POST.getlist("features"),
            "organism_group": form.get("organism_group", "gram-negative"),
            "statistics": {"tests": request.POST.getlist("tests") or ["binomial"],
                           "correction": form.get("correction", "bh"),
                           "threshold": float(form.get("threshold") or 0.05),
                           "background": form.get("background", "paralog_collapsed"),
                           "permutations": int(form.get("permutations") or 10000)},
            "cblaster": {}, "antismash": {},
        }
        if cfg["search"] == "snapshot":
            cfg["genomes"] = "genomes.txt"
        for key, _label, _flag in CURATED_CBLASTER:
            if form.get(f"cb_{key}"):
                cfg["cblaster"][key] = yaml.safe_load(form[f"cb_{key}"])
        cfg["cblaster"].update(_kv(form.get("cb_extra", "")))
        cfg["antismash"]["taxon"] = form.get("as_taxon", "bacteria")
        cfg["antismash"]["minimal"] = form.get("as_minimal") == "on"
        cfg["antismash"].update(_kv(form.get("as_extra", "")))
        path = draft / "run.yaml"
        path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        if not (draft / "query.faa").exists():
            errors.append("Choose a query protein FASTA file.")
        if cfg["search"] == "snapshot" and not genomes_text:
            errors.append("List at least one assembly accession (e.g. GCF_000011345.1), one per line.")
        if not errors:
            try:
                load_config(path)
            except FlandersError as exc:
                errors.append(str(exc))
        if not errors and form.get("action") == "launch":
            try:
                supervisor.launch(path, cfg["name"], WS)
            except FlandersError as exc:
                errors.append(str(exc))
            else:
                return redirect("runs:list")
        review = {"yaml": path.read_text(), "command": f"flanders run -c {path}", "path": path}
    active = Run.objects.filter(status=RunStatus.RUNNING).exists()
    return render(request, "runs/compose.html", {
        "nav": "compose", "errors": errors, "review": review, "form": form, "curated": CURATED_CBLASTER,
        "active": active, "features_checked": request.POST.getlist("features") if form else
        ["signal_peptide", "transmembrane", "pfam", "antismash"],
    })


def citation(request):
    return HttpResponse(CITATION, content_type="text/plain")

