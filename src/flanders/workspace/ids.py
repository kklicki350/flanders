"""Run identifiers: YYYYMMDDTHHMMSSZ-<6 lowercase hex>. Generated only here."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime


def new_run_id(now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(3)}"


def utcnow_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
