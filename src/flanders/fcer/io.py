"""FCER serialization. JSON is canonical; CSV is derived from it by this one writer."""

from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path
from typing import Any

from flanders.fcer.models import Fcer


def _check_finite(obj: Any) -> None:
    if isinstance(obj, float) and not math.isfinite(obj):
        raise ValueError("non-finite float in FCER; use null plus a reason")
    if isinstance(obj, dict):
        for v in obj.values():
            _check_finite(v)
    elif isinstance(obj, list):
        for v in obj:
            _check_finite(v)


def dumps(fcer: Fcer) -> str:
    data = fcer.model_dump(mode="json")
    _check_finite(data)
    # schema_version first; floats at full precision (shortest round-trip repr).
    ordered = {"schema_version": data.pop("schema_version"), **data}
    return json.dumps(ordered, indent=2, allow_nan=False) + "\n"


def canonical_dumps(obj: Any) -> str:
    """Canonical form for checksums: sorted keys, no whitespace, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def load(path: Path) -> Fcer:
    return Fcer.model_validate_json(path.read_text())


CSV_COLUMNS = [
    "tag", "organism", "location", "feature", "test", "predictor", "k", "n",
    "background_hits", "background_n", "effect_log2", "p_value", "q_value", "significant", "reason",
]


def to_csv(fcer: Fcer) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["# schema_version", fcer.schema_version])
    w.writerow(CSV_COLUMNS)
    for t in fcer.tests:
        row = t.model_dump()
        w.writerow(
            [fcer.tag, fcer.organism or "", fcer.location]
            + ["" if row[c] is None else repr(row[c]) if isinstance(row[c], float) else row[c]
               for c in CSV_COLUMNS[3:]]
        )
    return buf.getvalue()


def write(fcer: Fcer, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{fcer.tag}.{fcer.location}"
    path = directory / f"{stem}.json"
    _atomic_write(path, dumps(fcer))
    _atomic_write(directory / f"{stem}.csv", to_csv(fcer))
    return path


def _atomic_write(path: Path, text: str) -> None:
    import os

    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
