"""antiSMASH adapter (8 primary, 7 supported): run on a genome and parse BGC regions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from flanders.engine.invoke import passthrough_args, run_tool, tool_version
from flanders.errors import UpstreamDriftError

ENV = "env-antismash8"
SUPPORTED = ("8.", "7.")
_LOC = re.compile(r"\[<?(\d+):>?(\d+)\]")


@dataclass
class Region:
    record: str
    start: int  # 1-based inclusive
    end: int
    products: list[str]


def version() -> str:
    raw = tool_version(ENV, ("antismash", "--version"))
    return raw.split()[-1] if raw != "unknown" else raw


def run(genbank: Path, outdir: Path, databases: Path, params: dict, cpus: int, taxon: str) -> Path:
    argv = ["antismash", "--output-dir", str(outdir / "out"), "--cpus", str(cpus),
            "--databases", str(databases), "--taxon", taxon]
    user = dict(params)
    user.setdefault("genefinding-tool", "none")  # use the assembly's own annotation
    user.setdefault("minimal", True)  # region detection only; pass `minimal: false` for full analysis
    argv += passthrough_args(user) + [str(genbank)]
    run_tool(tool="antismash", argv=argv, cwd=outdir, env=ENV, version=version(),
             log_prefix="antismash", passthrough_section="antismash", timeout=6 * 3600)
    found = [p for p in (outdir / "out").glob("*.json") if p.name != "regions.js"]
    if not found:
        raise UpstreamDriftError(f"antiSMASH {version()} produced no JSON result")
    return found[0]


def parse_regions(path: Path, tool_version_str: str | None = None) -> list[Region]:
    v = tool_version_str or version()
    if v != "unknown" and not v.startswith(SUPPORTED):
        raise UpstreamDriftError(f"antiSMASH {v} is not a supported version")
    try:
        data = json.loads(path.read_text())
        regions = []
        for rec in data["records"]:
            rec_id = rec["id"]
            for feat in rec["features"]:
                if feat["type"] != "region":
                    continue
                m = _LOC.search(feat["location"])
                if not m:
                    raise ValueError(f"unparseable location {feat['location']!r}")
                start0, end0 = int(m.group(1)), int(m.group(2))
                products = feat.get("qualifiers", {}).get("product", [])
                regions.append(Region(rec_id, start0 + 1, end0, sorted(set(products))))
        return regions
    except (KeyError, TypeError, ValueError) as exc:
        raise UpstreamDriftError(f"antiSMASH {v} JSON format not recognized: {exc!r}") from exc
