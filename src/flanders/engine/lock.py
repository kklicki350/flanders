"""Single-run lock: an OS file lock plus the ledger's pid/heartbeat."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path

from flanders.errors import RunLockedError


class RunLock:
    def __init__(self, path: Path):
        self.path = path
        self._fh = None

    def acquire(self, run_id: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self.path, "a+")
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fh.seek(0)
            holder = fh.read().strip() or "another run"
            fh.close()
            raise RunLockedError(f"another run is active ({holder}); one run at a time") from None
        fh.seek(0)
        fh.truncate()
        fh.write(f"{run_id} pid={os.getpid()}")
        fh.flush()
        self._fh = fh

    def release(self) -> None:
        if self._fh is not None:
            fcntl.flock(self._fh, fcntl.LOCK_UN)
            self._fh.close()
            self._fh = None


def lock_is_free(path: Path) -> bool:
    if not path.exists():
        return True
    with open(path, "a+") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        fcntl.flock(fh, fcntl.LOCK_UN)
        return True


def mark_stale_runs_interrupted(lock_path: Path) -> list[str]:
    """If nobody holds the lock, any run still marked running died: mark it interrupted."""
    from flanders.workspace.models import Run, RunStatus

    if not lock_is_free(lock_path):
        return []
    stale = list(Run.objects.filter(status=RunStatus.RUNNING).values_list("run_id", flat=True))
    Run.objects.filter(run_id__in=stale).update(status=RunStatus.INTERRUPTED, pid=None)
    return stale
