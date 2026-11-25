"""Workspace layout. Files are the source of truth; the SQLite index is rebuildable."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT = Path(os.environ.get("FLANDERS_WORKSPACE", Path.home() / "flanders"))
SUBDIRS = ("runs", "imports", "snapshots", "drafts", "reference", "tools", ".flanders")


@dataclass(frozen=True)
class Workspace:
    root: Path

    @classmethod
    def default(cls) -> Workspace:
        return cls(Path(os.environ.get("FLANDERS_WORKSPACE", DEFAULT)).expanduser())

    @property
    def db_path(self) -> Path:
        return self.root / ".flanders" / "index.sqlite3"

    @property
    def lock_path(self) -> Path:
        return self.root / ".flanders" / "run.lock"

    def run_dir(self, run_id: str) -> Path:
        return self.root / "runs" / run_id

    @property
    def reference(self) -> Path:
        return self.root / "reference"

    @property
    def tools(self) -> Path:
        return self.root / "tools"

    def ensure(self) -> None:
        for d in SUBDIRS:
            (self.root / d).mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class RunPaths:
    root: Path

    @property
    def inputs(self) -> Path:
        return self.root / "inputs"

    @property
    def config(self) -> Path:
        return self.root / "config.effective.yaml"

    @property
    def fcer(self) -> Path:
        return self.root / "fcer"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def report(self) -> Path:
        return self.root / "report.json"

    @property
    def invocations(self) -> Path:
        return self.root / "invocations.jsonl"

    def stage(self, stage: str) -> Path:
        return self.root / "stages" / stage

    def task_dir(self, stage: str, tag: str) -> Path:
        return self.stage(stage) / tag

    def ensure(self) -> None:
        for p in (self.inputs, self.fcer, self.logs, self.root / "stages"):
            p.mkdir(parents=True, exist_ok=True)
