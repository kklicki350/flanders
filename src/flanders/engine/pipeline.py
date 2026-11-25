"""Run orchestration: the single entry point used by both the CLI and the GUI.

The scheduler is the only ledger writer. Per-tag tasks run in a thread pool (tools do
the heavy work in subprocesses); results come back to this thread, which records them.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import threading
import time
import traceback
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path

import yaml

from flanders import log
from flanders.adapters import predictors as preds
from flanders.config.merge import load_config
from flanders.config.models import RunConfig, read_genome_list
from flanders.engine import invoke
from flanders.engine import stages as S
from flanders.engine.lock import RunLock, mark_stale_runs_interrupted
from flanders.engine.stages import RunContext, Stage
from flanders.errors import (
    ConfigError,
    DependencyRejectedError,
    FlandersError,
    ReferenceDataError,
    RunCancelled,
    TaskFailure,
    UpstreamDriftError,
)
from flanders.reference.data import for_workspace, sha256_file
from flanders.workspace import ledger
from flanders.workspace.ids import new_run_id, utcnow_iso
from flanders.workspace.layout import RunPaths, Workspace
from flanders.workspace.models import RunStatus, TaskStatus

HALTING = (DependencyRejectedError, UpstreamDriftError, ReferenceDataError)
_cancel = threading.Event()


def _concurrency(stage: Stage, jobs: int) -> int:
    return {
        Stage.FETCH_GENOMES: min(3, jobs),  # NCBI rate limits
        Stage.ANNOTATE_BGC: max(1, jobs // 4),
        Stage.PREDICT_FEATURES: max(1, jobs // 2),
        Stage.COLLAPSE_PARALOGS: max(1, jobs // 4),
    }.get(stage, jobs)


# ------------------------------------------------------------------ preparation

def _capture_inputs(cfg: RunConfig, base: Path, paths: RunPaths) -> dict[str, str]:
    """Copy every input file into the run folder and checksum it (FR86)."""
    checksums = {}
    for key in ("query", "genomes", "tree"):
        value = getattr(cfg, key)
        if not value:
            continue
        src = (base / value).expanduser() if not Path(value).is_absolute() else Path(value)
        if not src.is_file():
            raise ConfigError(
                f"{key}: input file not found: {src}. Run flanders from the folder that contains it, "
                f"or give its full path.")
        dest = paths.inputs / src.name
        shutil.copy(src, dest)
        checksums[f"{key}:{src.name}"] = sha256_file(dest)
    return checksums


def _preflight(cfg: RunConfig, ws: Workspace) -> dict[str, str]:
    ref = for_workspace(ws.reference)
    needed = [c for c, f in (("pfam", "pfam"), ("antismash8", "antismash")) if f in cfg.features]
    if invoke.which(S.cblaster.ENV, "cblaster") is None:
        raise FlandersError("cblaster is not available. Run FLANDERS through the `flanders` command "
                            "installed by install-flanders.sh (it runs inside the FLANDERS image).")
    return ref.require(needed)


def prepare(config_path: Path | None, overrides: list[str], name: str | None, jobs: int | None,
            ws: Workspace, kind: str = "run", source: str | None = None) -> RunContext:
    cfg, effective = load_config(config_path, overrides)
    reference = _preflight(cfg, ws)
    run_id = new_run_id()
    paths = RunPaths(ws.run_dir(run_id))
    paths.ensure()
    base = config_path.parent if config_path else Path.cwd()
    try:
        input_checksums = _capture_inputs(cfg, base, paths)
        if cfg.genomes:
            read_genome_list((paths.inputs / Path(cfg.genomes).name).read_text())
    except (ConfigError, ValueError) as exc:
        shutil.rmtree(paths.root, ignore_errors=True)
        raise ConfigError(str(exc)) from exc
    paths.config.write_text(yaml.safe_dump(effective, sort_keys=False))
    (paths.root / "run.json").write_text(json.dumps({
        "run_id": run_id, "name": name or cfg.name or run_id, "kind": kind, "source": source,
        "created_at": utcnow_iso(), "input_checksums": input_checksums,
        "reference_checksums": reference, "config_file": str(config_path) if config_path else None,
    }, indent=1))
    ctx = RunContext(run_id=run_id, name=name or cfg.name or run_id, ws=ws, paths=paths, cfg=cfg,
                     effective=effective, jobs=jobs or cfg.jobs or max(1, (os.cpu_count() or 2) - 1),
                     reference_checksums=reference, input_checksums=input_checksums)
    ledger.create_run(run_id, name=ctx.name, kind=kind, source=source, search_mode=cfg.search,
                      key_params=_key_params(cfg))
    return ctx


def load_existing(run_id: str, ws: Workspace, jobs: int | None = None) -> RunContext:
    paths = RunPaths(ws.run_dir(run_id))
    meta = json.loads((paths.root / "run.json").read_text())
    effective = yaml.safe_load(paths.config.read_text())
    cfg = RunConfig.model_validate(effective)
    return RunContext(run_id=run_id, name=meta["name"], ws=ws, paths=paths, cfg=cfg, effective=effective,
                      jobs=jobs or cfg.jobs or max(1, (os.cpu_count() or 2) - 1),
                      reference_checksums=meta["reference_checksums"],
                      input_checksums=meta["input_checksums"])


def _key_params(cfg: RunConfig) -> dict:
    return {"search": cfg.search, "flank_orfs": cfg.flank_orfs, "features": cfg.features,
            "tests": cfg.statistics.tests, "correction": cfg.statistics.correction,
            "threshold": cfg.statistics.threshold, "background": cfg.statistics.background}


# ------------------------------------------------------------------- execution

def execute(ctx: RunContext, out_dir: Path | None = None) -> int:
    lock = RunLock(ctx.ws.lock_path)
    lock.acquire(ctx.run_id)
    _cancel.clear()
    previous = signal.signal(signal.SIGTERM, _on_term) if threading.current_thread() is threading.main_thread() else None
    token = invoke.current_record.set(ctx.paths.invocations)
    ledger.reset_in_flight(ctx.run_id)
    ledger.run_started(ctx.run_id, os.getpid())
    ctx.predictors = preds.detect(ctx.ws.tools)
    status, message, code = RunStatus.COMPLETE, "", 0
    try:
        _run_stages(ctx)
        failed = ledger.failed_tags(ctx.run_id)
        if failed:
            status, code = RunStatus.COMPLETE_WITH_FAILURES, 1
            message = f"{len(failed)} genome(s) failed"
    except RunCancelled:
        status, message, code = RunStatus.CANCELLED, "cancelled", 130
    except HALTING as exc:
        status, message, code = RunStatus.HALTED, str(exc), exc.exit_code
        log.event(ctx.paths.logs, ctx.run_id, "run", "run", "error", "run_halted", message=str(exc))
    except FlandersError as exc:
        status, message, code = RunStatus.FAILED, str(exc), exc.exit_code
        log.event(ctx.paths.logs, ctx.run_id, "run", "run", "error", "run_failed", message=str(exc))
    except Exception as exc:  # noqa: BLE001 - record, then re-raise for the traceback
        ledger.run_finished(ctx.run_id, RunStatus.FAILED, f"internal error: {exc}")
        log.event(ctx.paths.logs, ctx.run_id, "run", "run", "error", "internal_error",
                  message=traceback.format_exc())
        raise
    finally:
        invoke.current_record.reset(token)
        if previous is not None:
            signal.signal(signal.SIGTERM, previous)
    write_report(ctx, status, message)
    _index_fcers(ctx)
    ledger.run_finished(ctx.run_id, status, message)
    lock.release()
    if out_dir is not None and status in (RunStatus.COMPLETE, RunStatus.COMPLETE_WITH_FAILURES):
        out_dir.mkdir(parents=True, exist_ok=True)
        for f in ctx.paths.fcer.iterdir():
            shutil.copy(f, out_dir / f.name)
        shutil.copy(ctx.paths.report, out_dir / "report.json")
    return code


def _on_term(signum, frame) -> None:  # noqa: ARG001
    _cancel.set()
    invoke.terminate_children()


def _plan(cfg: RunConfig) -> list[Stage]:
    middle = [Stage.EXTRACT_FLANKS, Stage.ANNOTATE_BGC, Stage.PREDICT_FEATURES, Stage.COLLAPSE_PARALOGS,
              Stage.ENRICH, Stage.EMIT_FCER]
    if cfg.search == "snapshot":
        return [Stage.FETCH_GENOMES, Stage.DISCOVER, *middle]
    return [Stage.DISCOVER, Stage.FETCH_GENOMES, *middle]


def _run_stages(ctx: RunContext) -> None:
    cfg = ctx.cfg
    active: list[str] = []
    if cfg.search == "snapshot":
        active = read_genome_list((ctx.paths.inputs / Path(cfg.genomes).name).read_text())
        ledger.set_genome_count(ctx.run_id, len(active))
    for stage in _plan(cfg):
        if _cancel.is_set():
            raise RunCancelled()
        ledger.heartbeat(ctx.run_id, stage.value)
        if stage in S.RUN_WIDE:
            active = _run_discover(ctx, active)
            continue
        active = _run_per_tag(ctx, stage, active)


def _run_discover(ctx: RunContext, fetched: list[str]) -> list[str]:
    done = ledger.task_status(ctx.run_id, Stage.DISCOVER).get("run") == TaskStatus.COMPLETE
    if not done:
        ledger.ensure_tasks(ctx.run_id, Stage.DISCOVER, ["run"])
        ledger.start_task(ctx.run_id, Stage.DISCOVER, "run")
        log.event(ctx.paths.logs, ctx.run_id, Stage.DISCOVER, "run", "info", "task_started",
                  message=f"cblaster {ctx.cfg.search} search")
        t0 = time.monotonic()
        try:
            result = S.discover(ctx, fetched)
        except TaskFailure as exc:
            # Discovery is run-wide: a failure here fails the run.
            ledger.fail_task(ctx.run_id, Stage.DISCOVER, "run", exc.reason, exc.detail, time.monotonic() - t0)
            raise FlandersError(f"discovery failed: {exc}") from exc
        except HALTING as exc:
            ledger.fail_task(ctx.run_id, Stage.DISCOVER, "run", type(exc).__name__, str(exc), time.monotonic() - t0)
            raise
        ledger.complete_task(ctx.run_id, Stage.DISCOVER, "run", time.monotonic() - t0)
        log.event(ctx.paths.logs, ctx.run_id, Stage.DISCOVER, "run", "info", "task_completed",
                  message=f"{len(result['clusters'])} genomes with a cluster, {len(result['excluded'])} without")
    result = S.discovery(ctx)
    tags = sorted(result["clusters"])
    if ctx.cfg.search == "remote":
        ledger.set_genome_count(ctx.run_id, len(tags) + len(result["excluded"]))
    return tags


def _run_per_tag(ctx: RunContext, stage: Stage, tags: list[str]) -> list[str]:
    func = {
        Stage.FETCH_GENOMES: S.fetch_genome, Stage.EXTRACT_FLANKS: S.extract_flanks,
        Stage.ANNOTATE_BGC: S.annotate_bgc, Stage.PREDICT_FEATURES: S.predict_features,
        Stage.COLLAPSE_PARALOGS: S.collapse_paralogs, Stage.ENRICH: S.enrich, Stage.EMIT_FCER: S.emit_fcer,
    }[stage]
    ledger.ensure_tasks(ctx.run_id, stage, tags)
    status = ledger.task_status(ctx.run_id, stage)
    pending = [t for t in tags if status.get(t) == TaskStatus.PENDING]
    failed_before = {t for t in tags if status.get(t) == TaskStatus.FAILED}
    if pending:
        log.event(ctx.paths.logs, ctx.run_id, stage, "run", "info", "stage_started",
                  message=f"{len(pending)} task(s), {len(tags) - len(pending) - len(failed_before)} already complete")
    halt: BaseException | None = None
    started: dict[Future, tuple[str, float]] = {}
    with ThreadPoolExecutor(max_workers=_concurrency(stage, ctx.jobs)) as pool:
        queue = list(pending)
        while queue or started:
            while queue and len(started) < pool._max_workers and halt is None and not _cancel.is_set():
                tag = queue.pop(0)
                ledger.start_task(ctx.run_id, stage, tag)
                started[pool.submit(_call, func, ctx, tag)] = (tag, time.monotonic())
            if not started:
                break
            done, _ = wait(list(started), timeout=10, return_when=FIRST_COMPLETED)
            ledger.heartbeat(ctx.run_id)
            for fut in done:
                tag, t0 = started.pop(fut)
                exc = fut.exception()
                dt = time.monotonic() - t0
                if exc is None:
                    ledger.complete_task(ctx.run_id, stage, tag, dt)
                    log.event(ctx.paths.logs, ctx.run_id, stage, tag, "debug", "task_completed", duration_s=dt)
                elif isinstance(exc, HALTING):
                    ledger.fail_task(ctx.run_id, stage, tag, type(exc).__name__, str(exc), dt)
                    halt = halt or exc
                elif isinstance(exc, TaskFailure):
                    ledger.fail_task(ctx.run_id, stage, tag, exc.reason, exc.detail, dt)
                    log.event(ctx.paths.logs, ctx.run_id, stage, tag, "warning", "task_failed",
                              reason=exc.reason, message=exc.detail[:300])
                else:
                    ledger.fail_task(ctx.run_id, stage, tag, "internal_error", repr(exc), dt)
                    log.event(ctx.paths.logs, ctx.run_id, stage, tag, "warning", "task_failed",
                              reason="internal_error", message="".join(traceback.format_exception(exc))[-1500:])
            if halt is not None or _cancel.is_set():
                queue.clear()
                invoke.terminate_children()
    if _cancel.is_set():
        ledger.reset_in_flight(ctx.run_id)
        raise RunCancelled()
    if halt is not None:
        raise halt
    status = ledger.task_status(ctx.run_id, stage)
    return [t for t in tags if status.get(t) == TaskStatus.COMPLETE]


def _call(func, ctx, tag):
    token = invoke.current_record.set(ctx.paths.invocations)
    try:
        return func(ctx, tag)
    finally:
        invoke.current_record.reset(token)


# ----------------------------------------------------------------- report/index

def write_report(ctx: RunContext, status: str, message: str) -> None:
    failed = ledger.failed_tags(ctx.run_id)
    excluded = {}
    disc_path = ctx.out(Stage.DISCOVER, "run") / "clusters.json"
    clusters = {}
    if disc_path.exists():
        disc = json.loads(disc_path.read_text())
        excluded = disc["excluded"]
        clusters = disc["clusters"]
    report = {
        "run_id": ctx.run_id, "name": ctx.name, "status": status, "message": message,
        "finished_at": utcnow_iso(),
        "genomes_with_cluster": len(clusters),
        "fcer_count": len(list(ctx.paths.fcer.glob("*.json"))) if ctx.paths.fcer.exists() else 0,
        "failed": [{"tag": t, "stage": s, "reason": r, "detail": d[:1000]} for t, (s, r, d) in sorted(failed.items())],
        "excluded": [{"tag": t, "reason": r} for t, r in sorted(excluded.items())],
        "notes": {t: {"other_clusters": c["other_clusters"]} for t, c in clusters.items() if c.get("other_clusters")},
    }
    tmp = ctx.paths.report.with_suffix(".tmp")
    tmp.write_text(json.dumps(report, indent=1) + "\n")
    os.replace(tmp, ctx.paths.report)


def _index_fcers(ctx: RunContext) -> None:
    from flanders.workspace.index import index_run_fcers

    index_run_fcers(ctx.run_id, ctx.paths.fcer)


def recover_stale(ws: Workspace) -> list[str]:
    return mark_stale_runs_interrupted(ws.lock_path)
