"""cblaster adapter: database build, search, and a version-gated session parser."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from flanders.engine.invoke import passthrough_args, run_tool, tool_version
from flanders.errors import UpstreamDriftError

ENV = "env-cblaster"
SUPPORTED = ("1.3.", "1.4.")


def version() -> str:
    raw = tool_version(ENV, ("cblaster", "--version"))
    return raw.split()[-1] if raw != "unknown" else raw


@dataclass
class Hit:
    name: str  # subject protein name as cblaster reports it
    start: int | None
    end: int | None
    strand: str | None
    queries: list[str] = field(default_factory=list)


@dataclass
class Cluster:
    organism: str
    scaffold: str  # nucleotide accession as cblaster reports it
    start: int
    end: int
    score: float
    hits: list[Hit]


def makedb(genbank_files: list[Path], name: str, cwd: Path, cpus: int) -> Path:
    argv = ["cblaster", "makedb", "--cpus", str(cpus), "--name", name, *map(str, genbank_files)]
    run_tool(tool="cblaster", argv=argv, cwd=cwd, env=ENV, version=version(), log_prefix="cblaster.makedb")
    db = cwd / f"{name}.dmnd"
    if not db.exists():
        raise UpstreamDriftError(f"cblaster {version()} makedb did not produce {db.name}")
    return db


def search(query: Path, mode: str, cwd: Path, params: dict, database: Path | None, cpus: int) -> Path:
    session = cwd / "session.json"
    argv = ["cblaster", "search", "--query_file", str(query), "--mode", mode,
            "--session_file", str(session), "--output", str(cwd / "summary.txt")]
    if mode == "local":
        argv += ["--database", str(database), "--cpus", str(cpus)]
    argv += passthrough_args(params)
    run_tool(tool="cblaster", argv=argv, cwd=cwd, env=ENV, version=version(),
             log_prefix="cblaster.search", passthrough_section="cblaster")
    if not session.exists():
        raise UpstreamDriftError(f"cblaster {version()} search did not write a session file")
    return session


def parse_session(path: Path, tool_version_str: str | None = None) -> list[Cluster]:
    v = tool_version_str or version()
    if v != "unknown" and not v.startswith(SUPPORTED):
        raise UpstreamDriftError(f"cblaster {v} is not a supported version ({', '.join(SUPPORTED)}x)")
    try:
        data = json.loads(path.read_text())
        clusters: list[Cluster] = []
        for org in data["organisms"]:
            org_name = " ".join(x for x in (org.get("name"), org.get("strain")) if x).strip()
            for scaf in org["scaffolds"]:
                subjects = scaf["subjects"]
                for cl in scaf.get("clusters", []):
                    hits = []
                    for idx in cl["indices"]:
                        s = subjects[idx]
                        hits.append(Hit(
                            name=s["name"],
                            start=s.get("start"),
                            end=s.get("end"),
                            strand={1: "+", -1: "-"}.get(s.get("strand"), s.get("strand")),
                            queries=sorted({h["query"] for h in s.get("hits", [])}),
                        ))
                    clusters.append(Cluster(org_name, scaf["accession"], int(cl["start"]),
                                            int(cl["end"]), float(cl.get("score", 0.0)), hits))
        return clusters
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise UpstreamDriftError(f"cblaster {v} session format not recognized: {exc!r}") from exc
