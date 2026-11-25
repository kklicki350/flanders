"""GUI-side run supervision: launch `flanders run -c <saved config>` as a child process.

Pipeline code never runs inside the web process. The child runs in its own session so
Cancel can signal its whole process group (the run and the tools it started).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

from flanders.engine.lock import lock_is_free
from flanders.errors import RunLockedError
from flanders.workspace.layout import Workspace


def _argv() -> list[str]:
    return [sys.executable, "-m", "flanders"]


def launch(config: Path, name: str | None, ws: Workspace) -> subprocess.Popen:
    if not lock_is_free(ws.lock_path):
        raise RunLockedError("another run is active; one run at a time")
    argv = [*_argv(), "run", "-c", str(config)]
    if name:
        argv += ["--name", name]
    log = ws.root / ".flanders" / "gui-launch.log"
    with open(log, "ab") as fh:
        return subprocess.Popen(argv, cwd=config.parent, stdout=fh, stderr=fh, stdin=subprocess.DEVNULL,
                                start_new_session=True)


def resume(run_id: str, ws: Workspace) -> subprocess.Popen:
    if not lock_is_free(ws.lock_path):
        raise RunLockedError("another run is active; one run at a time")
    log = ws.root / ".flanders" / "gui-launch.log"
    with open(log, "ab") as fh:
        return subprocess.Popen([*_argv(), "resume", run_id], cwd=ws.root, stdout=fh, stderr=fh,
                                stdin=subprocess.DEVNULL, start_new_session=True)


def cancel(pid: int) -> None:
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except ProcessLookupError:
        pass
