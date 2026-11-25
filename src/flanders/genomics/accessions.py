"""Versioned accession checks. An unversioned accession is a validation error."""

from __future__ import annotations

import re

_VERSIONED = re.compile(r"^[A-Z]{1,6}_?[A-Z0-9]*\d+\.\d+$")
_ASSEMBLY = re.compile(r"^GC[AF]_\d{9}\.\d+$")


def is_versioned(acc: str) -> bool:
    return bool(_VERSIONED.match(acc))


def require_versioned(acc: str, what: str = "accession") -> str:
    if not is_versioned(acc):
        raise ValueError(f"{what} must be versioned (accession.version): {acc!r}")
    return acc


def is_assembly(acc: str) -> bool:
    return bool(_ASSEMBLY.match(acc))


def require_assembly(acc: str) -> str:
    if not is_assembly(acc):
        raise ValueError(
            f"genome must be an assembly accession.version like GCF_000011345.1: {acc!r}"
        )
    return acc
