"""Load and merge configuration: invocation override > config file > default (FR8)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from flanders.config.models import RunConfig
from flanders.errors import ConfigError


def _coerce(value: str) -> Any:
    """Parse a `--set key=value` value with YAML scalar rules (30 -> int, true -> bool)."""
    return yaml.safe_load(value) if value != "" else ""


def apply_overrides(data: dict[str, Any], overrides: list[str]) -> dict[str, Any]:
    """Apply dotted `key.sub=value` overrides. Dependency sections accept any key."""
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in data.items()}
    for item in overrides:
        if "=" not in item:
            raise ConfigError(f"override must look like key=value: {item!r}")
        key, raw = item.split("=", 1)
        parts = key.strip().split(".")
        node = out
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            if not isinstance(node, dict):
                raise ConfigError(f"override {key!r}: {part!r} is not a section")
        node[parts[-1]] = _coerce(raw)
    return out


def load_config(path: Path | None, overrides: list[str] | None = None) -> tuple[RunConfig, dict]:
    """Return (validated config, effective merged config as a plain dict)."""
    data: dict[str, Any] = {}
    if path is not None:
        if not path.exists():
            raise ConfigError(f"config file not found: {path}")
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"{path}: not valid YAML: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError(f"{path}: top level must be a mapping")
    data = apply_overrides(data, overrides or [])
    try:
        cfg = RunConfig.model_validate(data)
    except ValidationError as exc:
        lines = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "(config)"
            lines.append(f"  {loc}: {err['msg']}")
        raise ConfigError("invalid configuration:\n" + "\n".join(lines)) from exc
    return cfg, cfg.model_dump(mode="json")
