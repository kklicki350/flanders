"""NCBI access: Datasets CLI for assemblies, E-utilities for accession mapping.

Every request is retried with exponential backoff and jitter and recorded.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

from flanders.engine.invoke import run_tool, tool_version
from flanders.errors import TaskFailure
from flanders.workspace.ids import utcnow_iso

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ENV = "env-ncbi"
_jitter = np.random.Generator(np.random.PCG64())  # network timing only, never results


def datasets_version() -> str:
    return tool_version(ENV, ("datasets", "--version"))


def download_assembly(accession: str, dest: Path, api_key: str | None = None, attempts: int = 4) -> Path:
    """Download one assembly's GenBank flat file; returns the .gbff path."""
    dest.mkdir(parents=True, exist_ok=True)
    zpath = dest / f"{accession}.zip"
    argv = ["datasets", "download", "genome", "accession", accession, "--include", "gbff",
            "--filename", str(zpath), "--no-progressbar"]
    if api_key:
        argv += ["--api-key", api_key]
    for attempt in range(attempts):
        try:
            run_tool(tool="datasets", argv=argv, cwd=dest, env=ENV, timeout=1800,
                     version=datasets_version(), log_prefix=f"datasets.{attempt}")
            break
        except TaskFailure:
            if attempt == attempts - 1:
                raise
            time.sleep(2**attempt + float(_jitter.random()))
    out = dest / f"{accession}.gbff"
    with zipfile.ZipFile(zpath) as zf:
        members = [m for m in zf.namelist() if m.endswith(".gbff")]
        if not members:
            raise TaskFailure("no_gbff", f"{accession}: NCBI returned no GenBank file (unannotated or suppressed)")
        with zf.open(members[0]) as src, open(out, "wb") as dst:
            while chunk := src.read(1 << 20):
                dst.write(chunk)
        report = [m for m in zf.namelist() if m.endswith("assembly_data_report.jsonl")]
        if report:
            (dest / f"{accession}.report.json").write_bytes(zf.read(report[0]).splitlines()[0])
    zpath.unlink()
    return out


def eutils(endpoint: str, params: dict, log: Path | None, api_key: str | None = None,
           attempts: int = 5) -> dict:
    q = dict(params, retmode="json", tool="flanders")
    if api_key:
        q["api_key"] = api_key
    url = f"{EUTILS}/{endpoint}.fcgi?{urllib.parse.urlencode(q)}"
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = json.loads(resp.read())
            _log(log, url, "ok")
            return data
        except Exception as exc:  # noqa: BLE001 - network: retry then fail the tag
            _log(log, url, f"error: {exc}")
            if attempt == attempts - 1:
                raise TaskFailure("ncbi_unavailable", f"{endpoint}: {exc}") from exc
            time.sleep(2**attempt * 0.5 + float(_jitter.random()))
    raise AssertionError("unreachable")


def nucleotide_to_assembly(nuccore: str, log: Path | None, api_key: str | None = None) -> str | None:
    """Map a nucleotide accession.version to its assembly accession.version."""
    found = eutils("esearch", {"db": "nuccore", "term": f"{nuccore}[accn]"}, log, api_key)
    ids = found.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return None
    linked = eutils("elink", {"dbfrom": "nuccore", "db": "assembly", "id": ids[0]}, log, api_key)
    uids = []
    for ls in linked.get("linksets", []):
        for db in ls.get("linksetdbs", []):
            uids += db.get("links", [])
    if not uids:
        return None
    summ = eutils("esummary", {"db": "assembly", "id": ",".join(map(str, uids[:5]))}, log, api_key)
    result = summ.get("result", {})
    accs = [result[u].get("assemblyaccession") for u in result.get("uids", []) if u in result]
    accs = [a for a in accs if a]
    # Prefer RefSeq (GCF, annotated) over GenBank (GCA).
    accs.sort(key=lambda a: (not a.startswith("GCF_"), a))
    return accs[0] if accs else None


def protein_content_checksum(proteins: list[tuple[str, str]]) -> str:
    """SHA-256 over protein records sorted by accession.version, canonically serialized."""
    h = hashlib.sha256()
    for acc, seq in sorted(proteins):
        h.update(f"{acc}\t{seq}\n".encode())
    return h.hexdigest()


def _log(log: Path | None, url: str, status: str) -> None:
    if log is None:
        return
    with open(log, "a") as fh:
        fh.write(json.dumps({"ts": utcnow_iso(), "url": url.split("api_key=")[0], "status": status}) + "\n")
