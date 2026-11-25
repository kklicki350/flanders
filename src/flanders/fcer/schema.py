"""Generate the published JSON Schema from the Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path

from flanders.fcer.models import SCHEMA_VERSION, Fcer


def schema() -> dict:
    s = Fcer.model_json_schema()
    s["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    s["$id"] = f"https://github.com/kklicki350/flanders/schemas/fcer/{SCHEMA_VERSION}/fcer.schema.json"
    s["title"] = "FLANDERS Cluster Enrichment Record"
    return s


def schema_path(root: Path) -> Path:
    return root / "schemas" / "fcer" / SCHEMA_VERSION / "fcer.schema.json"


def write_schema(root: Path) -> Path:
    path = schema_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema(), indent=2, sort_keys=True) + "\n")
    return path
