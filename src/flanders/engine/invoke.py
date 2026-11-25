"""The invocation recorder: every external program runs through `run_tool()` (FR79).

Each heavy tool lives in its own micromamba environment under FLANDERS_ENV_ROOT
(default /opt/conda/envs in the image). Outside the image, tools are taken from PATH.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import threading
import time
from contextvars import ContextVar
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from flanders.errors import DependencyRejectedError, TaskFailure
from flanders.workspace.ids import utcnow_iso

ENV_ROOT = Path(os.environ.get("FLANDERS_ENV_ROOT", "/opt/conda/envs"))

# Where the current run records invocations; set by the scheduler.
current_record: ContextVar[Path | None] = ContextVar("current_record", default=None)
_record_lock = threading.Lock()
_children: set[subprocess.Popen] = set()
_children_lock = threading.Lock()


@dataclass
class ToolResult:
    returncode: int
    stdout_path: Path
    stderr_path: Path

    def stderr_tail(self, n: int = 2000) -> str:
        try:
            return self.stderr_path.read_text(errors="replace")[-n:]
        except OSError:
            return ""


def env_bin(env: str | None) -> Path | None:
    if env is None:
        return None
    p = ENV_ROOT / env / "bin"
    return p if p.is_dir() else None


def _environ(env: str | None, extra: dict[str, str] | None) -> dict[str, str]:
    e = dict(os.environ)
    b = env_bin(env)
    if b is not None:
        e["PATH"] = f"{b}{os.pathsep}{e.get('PATH', '')}"
        e["CONDA_PREFIX"] = str(b.parent)
    if extra:
        e.update(extra)
    return e


@lru_cache(maxsize=64)
def tool_version(env: str | None, argv: tuple[str, ...]) -> str:
    """Run a version command once per process (e.g. ('cblaster', '--version'))."""
    try:
        out = subprocess.run(list(argv), env=_environ(env, None), capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    text = (out.stdout or out.stderr).strip().splitlines()
    return text[0].strip() if text else "unknown"


@lru_cache(maxsize=64)
def tool_output(env: str | None, argv: tuple[str, ...]) -> str:
    """Full stdout of a read-only probe command (help or version text)."""
    try:
        out = subprocess.run(list(argv), env=_environ(env, None), capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.stdout


def which(env: str | None, program: str) -> str | None:
    import shutil

    return shutil.which(program, path=_environ(env, None)["PATH"])


def run_tool(
    *,
    tool: str,
    argv: list[str],
    cwd: Path,
    env: str | None = None,
    timeout: float | None = None,
    version: str = "unknown",
    log_prefix: str | None = None,
    passthrough_section: str | None = None,
    extra_env: dict[str, str] | None = None,
    check: bool = True,
) -> ToolResult:
    """Run an external program, capture stdout/stderr to files, record it verbatim.

    A non-zero exit raises DependencyRejectedError when the tool rejected arguments that
    came from a pass-through config section (argparse convention: exit code 2), and a
    TaskFailure otherwise.
    """
    cwd.mkdir(parents=True, exist_ok=True)
    prefix = log_prefix or tool
    out_path, err_path = cwd / f"{prefix}.stdout", cwd / f"{prefix}.stderr"
    started = time.monotonic()
    with open(out_path, "wb") as out, open(err_path, "wb") as err:
        try:
            proc = subprocess.Popen(argv, cwd=cwd, stdout=out, stderr=err, env=_environ(env, extra_env))
        except FileNotFoundError as exc:
            raise TaskFailure("tool_not_found", f"{tool}: {argv[0]} is not installed") from exc
        with _children_lock:
            _children.add(proc)
        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            rc = proc.wait()
            _record(tool, env, version, argv, cwd, started, rc, out_path, err_path, note="timeout")
            raise TaskFailure("tool_timeout", f"{tool} exceeded {timeout}s") from None
        finally:
            with _children_lock:
                _children.discard(proc)
    _record(tool, env, version, argv, cwd, started, rc, out_path, err_path)
    result = ToolResult(rc, out_path, err_path)
    if check and rc != 0:
        tail = result.stderr_tail(600).strip()
        if passthrough_section and rc == 2:
            raise DependencyRejectedError(tool, passthrough_section, tail or f"exit status {rc}")
        raise TaskFailure(f"{tool}_failed", f"exit status {rc}; {tail[-400:]} (log: {err_path})")
    return result


def terminate_children() -> None:
    with _children_lock:
        procs = list(_children)
    for p in procs:
        try:
            p.terminate()
        except OSError:
            pass


def _record(tool, env, version, argv, cwd, started, rc, out_path, err_path, note=None) -> None:
    path = current_record.get()
    if path is None:
        return
    entry = {
        "ts": utcnow_iso(),
        "tool": tool,
        "version": version,
        "env": env,
        "argv": argv,
        "command": shlex.join(argv),
        "cwd": str(cwd),
        "duration_s": round(time.monotonic() - started, 3),
        "exit_status": rc,
        "stdout": str(out_path),
        "stderr": str(err_path),
    }
    if note:
        entry["note"] = note
    line = json.dumps(entry) + "\n"
    with _record_lock, open(path, "a") as fh:
        fh.write(line)


def passthrough_args(section: dict) -> list[str]:
    """Render a dependency config section as CLI flags, keys verbatim (`key` -> `--key`).

    true -> bare flag; false/null -> omitted; list -> flag followed by each value.
    """
    args: list[str] = []
    for key, value in section.items():
        flag = key if key.startswith("-") else f"--{key}"
        if value is True:
            args.append(flag)
        elif value is False or value is None:
            continue
        elif isinstance(value, list):
            args.append(flag)
            args.extend(str(v) for v in value)
        else:
            args.extend([flag, str(value)])
    return args
