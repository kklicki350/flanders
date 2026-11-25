import os
import tempfile
from pathlib import Path

# The workspace (and therefore the database path) must be set before Django loads settings.
_WS = Path(tempfile.mkdtemp(prefix="flanders-test-ws-"))
os.environ.setdefault("FLANDERS_WORKSPACE", str(_WS))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flanders.web.settings")


import json  # noqa: E402

import pytest  # noqa: E402

from tests.engine import fake_tools  # noqa: E402


@pytest.fixture
def env(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    extra = fake_tools.install(bin_dir, tmp_path / "data")
    for k, v in extra.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    import flanders.engine.invoke as invoke

    monkeypatch.setattr(invoke, "ENV_ROOT", tmp_path / "no-envs")
    invoke.tool_version.cache_clear()
    invoke.tool_output.cache_clear()
    from flanders.workspace.layout import Workspace

    ws = Workspace(tmp_path / "ws")
    ws.ensure()
    from flanders.reference.data import RELEASE

    ref = ws.reference / RELEASE
    (ref / "pfam").mkdir(parents=True)
    (ref / "pfam" / "Pfam-A.hmm").write_text("fake")
    (ref / "manifest.json").write_text(json.dumps({"components": {
        "pfam": {"sha256": "a" * 64}, "antismash8": {"sha256": "b" * 64}}}))
    cfg_dir = tmp_path / "project"
    cfg_dir.mkdir()
    (cfg_dir / "query.faa").write_text(">Q1\nMKKLLAAV\n")
    (cfg_dir / "genomes.txt").write_text("\n".join(fake_tools.GENOMES) + "\n")
    (cfg_dir / "run.yaml").write_text(
        "name: fake-ebo\nquery: query.faa\ngenomes: genomes.txt\nflank_orfs: 4\n"
        "features: [signal_peptide, transmembrane, pfam, antismash]\n"
        "statistics: {permutations: 500}\ncblaster: {min_identity: 30}\n")
    return ws, cfg_dir


