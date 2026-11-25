"""FCER index and workspace reindex (FR78): the database is derived from files."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from flanders.workspace.layout import Workspace
from flanders.workspace.models import FcerEntry, Run, RunStatus


def _summary(data: dict) -> tuple[list[list], float | None]:
    """Significant features under the run's primary (first) test as [feature, q], best first."""
    tests = data["tests"]
    primary = data["statistics"]["tests"][0] if data["statistics"]["tests"] else None
    rows = [t for t in tests if t["test"] == primary]
    sig = sorted(([t["feature"], t["q_value"]] for t in rows if t["significant"]), key=lambda x: (x[1], x[0]))
    qs = [t["q_value"] for t in rows if t["q_value"] is not None]
    return sig, (min(qs) if qs else None)


def index_run_fcers(run_id: str, fcer_dir: Path) -> int:
    if not fcer_dir.exists():
        return 0
    rows = []
    for path in sorted(fcer_dir.glob("*.json")):
        data = json.loads(path.read_text())
        sig, best = _summary(data)
        rows.append(FcerEntry(run_id=run_id, tag=data["tag"], location=data["location"],
                              organism=data.get("organism") or "", record=data["neighborhood"]["record"],
                              path=str(path), significant=sig, best_q=best))
    with transaction.atomic():
        FcerEntry.objects.filter(run_id=run_id).delete()
        FcerEntry.objects.bulk_create(rows)
    return len(rows)


def reindex(ws: Workspace) -> int:
    """Rebuild run history and FCER index from runs/*/run.json, report.json and fcer/."""
    n = 0
    for run_dir in sorted((ws.root / "runs").iterdir()):
        meta_path = run_dir / "run.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        report = json.loads((run_dir / "report.json").read_text()) if (run_dir / "report.json").exists() else {}
        status = report.get("status", RunStatus.INTERRUPTED)
        created = datetime.fromisoformat(meta["created_at"].replace("Z", "+00:00"))
        Run.objects.update_or_create(run_id=meta["run_id"], defaults={
            "name": meta["name"], "kind": meta.get("kind", "run"), "source_id": None,
            "status": status, "created_at": created, "message": report.get("message", ""),
            "failed_count": len(report.get("failed", [])),
            "genome_count": report.get("genomes_with_cluster", 0) + len(report.get("excluded", [])),
            "finished_at": timezone.now() if report else None,
        })
        index_run_fcers(meta["run_id"], run_dir / "fcer")
        n += 1
    return n
