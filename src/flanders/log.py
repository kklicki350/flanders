"""Run logs: JSON Lines per task plus run.jsonl; a plain-text renderer on stderr."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

from flanders.workspace.ids import utcnow_iso

_lock = threading.Lock()
QUIET = False


def event(logs: Path, run_id: str, stage: str, tag: str, level: str, name: str, **fields) -> None:
    entry = {"ts": utcnow_iso(), "level": level, "run_id": run_id, "stage": stage, "tag": tag,
             "event": name, **fields}
    line = json.dumps(entry, default=str) + "\n"
    target = logs / stage / f"{tag}.jsonl" if tag != "run" else logs / "run.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        with open(target, "a") as fh:
            fh.write(line)
        if tag != "run":
            with open(logs / "run.jsonl", "a") as fh:
                fh.write(line)
        if not QUIET and level in ("info", "warning", "error"):
            detail = fields.get("message") or fields.get("reason") or ""
            where = stage if tag == "run" else f"{stage} {tag}"
            print(f"[{entry['ts'][11:19]}] {level:7} {where}: {name.replace('_', ' ')}"
                  f"{' - ' + str(detail) if detail else ''}", file=sys.stderr, flush=True)


def stderr(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)
