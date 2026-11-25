"""Reference data in the workspace: antiSMASH databases and Pfam-A, checksummed.

`flanders reference fetch` downloads and records SHA-256 for every file in a manifest;
runs refuse to start when required reference data is missing (exit 6) and record the
manifest checksums they used. `reference verify` recomputes every checksum.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from flanders import __version__
from flanders.engine.invoke import run_tool
from flanders.errors import ReferenceDataError
from flanders.workspace.ids import utcnow_iso

PFAM_URL = "https://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/"
RELEASE = ".".join(__version__.split(".")[:2])


@dataclass(frozen=True)
class Reference:
    root: Path

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    @property
    def pfam_hmm(self) -> Path:
        return self.root / "pfam" / "Pfam-A.hmm"

    @property
    def antismash_db(self) -> Path:
        return self.root / "antismash8"

    def manifest(self) -> dict:
        if not self.manifest_path.exists():
            return {"components": {}}
        return json.loads(self.manifest_path.read_text())

    def require(self, components: list[str]) -> dict[str, str]:
        """Check required components exist; return their checksums for provenance."""
        comps = self.manifest().get("components", {})
        missing = [c for c in components if c not in comps]
        if missing:
            raise ReferenceDataError(
                f"reference data missing: {', '.join(missing)}. Run `flanders reference fetch` first."
            )
        return {c: comps[c]["sha256"] for c in components}


def for_workspace(reference_dir: Path) -> Reference:
    return Reference(reference_dir / RELEASE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def tree_checksum(root: Path) -> tuple[str, dict[str, str]]:
    files = {str(p.relative_to(root)): sha256_file(p) for p in sorted(root.rglob("*")) if p.is_file()}
    h = hashlib.sha256()
    for rel, digest in sorted(files.items()):
        h.update(f"{rel}\t{digest}\n".encode())
    return h.hexdigest(), files


def _save(ref: Reference, name: str, info: dict) -> None:
    m = ref.manifest()
    m.setdefault("release", RELEASE)
    m.setdefault("components", {})[name] = info
    ref.root.mkdir(parents=True, exist_ok=True)
    ref.manifest_path.write_text(json.dumps(m, indent=2, sort_keys=True) + "\n")


def fetch_pfam(ref: Reference, log=print) -> None:
    dest = ref.pfam_hmm.parent
    dest.mkdir(parents=True, exist_ok=True)
    version = "unknown"
    try:
        with urllib.request.urlopen(PFAM_URL + "Pfam.version.gz", timeout=60) as r:
            text = gzip.decompress(r.read()).decode()
        version = next((ln.split(":", 1)[1].strip() for ln in text.splitlines()
                        if ln.lower().startswith("pfam release")), "unknown")
    except Exception:  # noqa: BLE001 - version note only
        pass
    log(f"Downloading Pfam-A {version} (~300 MB compressed) ...")
    tmp = dest / "Pfam-A.hmm.gz.part"
    with urllib.request.urlopen(PFAM_URL + "Pfam-A.hmm.gz", timeout=600) as r, open(tmp, "wb") as fh:
        shutil.copyfileobj(r, fh, 1 << 20)
    with gzip.open(tmp, "rb") as src, open(ref.pfam_hmm, "wb") as dst:
        shutil.copyfileobj(src, dst, 1 << 20)
    tmp.unlink()
    for f in dest.glob("Pfam-A.hmm.h3?"):
        f.unlink()
    log("Indexing Pfam-A with hmmpress ...")
    run_tool(tool="hmmpress", argv=["hmmpress", str(ref.pfam_hmm)], cwd=dest, env="env-hmmer-mmseqs")
    digest, files = tree_checksum(dest)
    _save(ref, "pfam", {"version": version, "source": PFAM_URL, "fetched_at": utcnow_iso(),
                        "sha256": digest, "files": files})


def fetch_antismash(ref: Reference, log=print) -> None:
    log("Downloading antiSMASH databases (several GB; this takes a while) ...")
    ref.antismash_db.mkdir(parents=True, exist_ok=True)
    run_tool(tool="antismash-download-databases",
             argv=["download-antismash-databases", "--database-dir", str(ref.antismash_db)],
             cwd=ref.antismash_db, env="env-antismash8", timeout=6 * 3600)
    log("Checksumming antiSMASH databases ...")
    digest, files = tree_checksum(ref.antismash_db)
    _save(ref, "antismash8", {"source": "download-antismash-databases", "fetched_at": utcnow_iso(),
                              "sha256": digest, "file_count": len(files)})


def verify(ref: Reference) -> list[str]:
    problems = []
    for name, info in ref.manifest().get("components", {}).items():
        root = ref.pfam_hmm.parent if name == "pfam" else ref.antismash_db
        if not root.exists():
            problems.append(f"{name}: directory missing")
            continue
        digest, _ = tree_checksum(root)
        if digest != info["sha256"]:
            problems.append(f"{name}: checksum mismatch")
    return problems
