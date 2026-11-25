"""The workspace index: run history, run ledger, FCER index. Rebuildable from files."""

from __future__ import annotations

from django.db import models


class RunStatus(models.TextChoices):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    COMPLETE_WITH_FAILURES = "complete_with_failures"
    HALTED = "halted"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class TaskStatus(models.TextChoices):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class Run(models.Model):
    run_id = models.CharField(primary_key=True, max_length=32)
    name = models.CharField(max_length=200, blank=True)
    kind = models.CharField(max_length=20, default="run")  # run | variant | stats_replay
    source = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    origin = models.CharField(max_length=20, default="local")  # local | imported
    status = models.TextField(choices=RunStatus.choices, default=RunStatus.PENDING)
    stage = models.CharField(max_length=40, blank=True)
    message = models.TextField(blank=True)
    search_mode = models.CharField(max_length=20, blank=True)
    genome_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    key_params = models.JSONField(default=dict)
    created_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    pid = models.IntegerField(null=True)
    heartbeat_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-created_at"]


class Task(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="tasks")
    stage = models.CharField(max_length=40)
    tag = models.CharField(max_length=64)
    status = models.TextField(choices=TaskStatus.choices, default=TaskStatus.PENDING)
    reason = models.CharField(max_length=80, blank=True)
    detail = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    duration_s = models.FloatField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["run", "stage", "tag"], name="unique_task")]


class FcerEntry(models.Model):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="fcers")
    tag = models.CharField(max_length=64)
    location = models.CharField(max_length=16)
    organism = models.CharField(max_length=300, blank=True)
    record = models.CharField(max_length=64, blank=True)
    path = models.CharField(max_length=500)
    significant = models.JSONField(default=list)  # features significant under the run's primary test
    best_q = models.FloatField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["run", "tag", "location"], name="unique_fcer")]
