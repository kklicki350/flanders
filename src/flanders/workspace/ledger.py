"""Ledger transitions. The only code that writes run and task state.

Only the scheduler's parent process calls these (single writer), each transition in
one short transaction.
"""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from flanders.workspace.models import Run, RunStatus, Task, TaskStatus


def create_run(run_id: str, *, name: str, kind: str = "run", source: str | None = None,
               search_mode: str = "", key_params: dict | None = None) -> Run:
    return Run.objects.create(
        run_id=run_id, name=name, kind=kind, source_id=source, search_mode=search_mode,
        key_params=key_params or {}, created_at=timezone.now(),
    )


def run_started(run_id: str, pid: int) -> None:
    now = timezone.now()
    Run.objects.filter(pk=run_id).update(status=RunStatus.RUNNING, pid=pid, started_at=now,
                                         heartbeat_at=now, message="")


def heartbeat(run_id: str, stage: str | None = None) -> None:
    fields = {"heartbeat_at": timezone.now()}
    if stage is not None:
        fields["stage"] = stage
    Run.objects.filter(pk=run_id).update(**fields)


def run_finished(run_id: str, status: str, message: str = "") -> None:
    run = Run.objects.get(pk=run_id)
    failed = run.tasks.filter(status=TaskStatus.FAILED).values("tag").distinct().count()
    Run.objects.filter(pk=run_id).update(status=status, finished_at=timezone.now(),
                                         message=message, failed_count=failed, pid=None)


def set_genome_count(run_id: str, n: int) -> None:
    Run.objects.filter(pk=run_id).update(genome_count=n)


def ensure_tasks(run_id: str, stage: str, tags: list[str]) -> None:
    with transaction.atomic():
        existing = set(Task.objects.filter(run_id=run_id, stage=stage).values_list("tag", flat=True))
        Task.objects.bulk_create(
            [Task(run_id=run_id, stage=stage, tag=t) for t in tags if t not in existing]
        )


def start_task(run_id: str, stage: str, tag: str) -> None:
    Task.objects.filter(run_id=run_id, stage=stage, tag=tag).update(
        status=TaskStatus.RUNNING, started_at=timezone.now(), reason="", detail="")


def complete_task(run_id: str, stage: str, tag: str, duration_s: float) -> None:
    """Call only after the task's outputs are fsynced and atomically renamed (NFR8)."""
    Task.objects.filter(run_id=run_id, stage=stage, tag=tag).update(
        status=TaskStatus.COMPLETE, finished_at=timezone.now(), duration_s=duration_s)


def fail_task(run_id: str, stage: str, tag: str, reason: str, detail: str, duration_s: float) -> None:
    Task.objects.filter(run_id=run_id, stage=stage, tag=tag).update(
        status=TaskStatus.FAILED, finished_at=timezone.now(), reason=reason[:80],
        detail=detail[:4000], duration_s=duration_s)


def reset_in_flight(run_id: str) -> int:
    """On resume: tasks left `running` by a dead process go back to pending (NFR7)."""
    return Task.objects.filter(run_id=run_id, status=TaskStatus.RUNNING).update(
        status=TaskStatus.PENDING, started_at=None)


def task_status(run_id: str, stage: str) -> dict[str, str]:
    return dict(Task.objects.filter(run_id=run_id, stage=stage).values_list("tag", "status"))


def failed_tags(run_id: str) -> dict[str, tuple[str, str, str]]:
    """tag -> (stage, reason, detail) for the first failure of each tag."""
    out: dict[str, tuple[str, str, str]] = {}
    for t in Task.objects.filter(run_id=run_id, status=TaskStatus.FAILED).order_by("finished_at"):
        out.setdefault(t.tag, (t.stage, t.reason, t.detail))
    return out
