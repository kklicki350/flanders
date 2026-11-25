"""End-to-end engine test against stand-in tools (no network, no image)."""

import json
import os

import pytest

from tests.engine import fake_tools


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


@pytest.mark.django_db(transaction=True)
def test_full_run(env):
    from flanders.engine import pipeline
    from flanders.workspace.models import FcerEntry, Run

    ws, cfg_dir = env
    ctx = pipeline.prepare(cfg_dir / "run.yaml", [], None, 2, ws)
    code = pipeline.execute(ctx)
    report = json.loads(ctx.paths.report.read_text())
    assert code == 0, report
    assert report["status"] == "complete"
    assert report["excluded"] == [{"tag": "GCF_000000003.1", "reason": "no_cluster_found"}]
    fcers = sorted(p.name for p in ctx.paths.fcer.glob("*.json"))
    assert fcers == [f"{t}.{loc}.json" for t in ("GCF_000000001.1", "GCF_000000002.1")
                     for loc in ("downstream", "seed", "upstream")]
    up = json.loads((ctx.paths.fcer / "GCF_000000001.1.upstream.json").read_text())
    assert next(iter(up)) == "schema_version"
    sp = next(t for t in up["tests"] if t["feature"] == "signal_peptide" and t["test"] == "binomial")
    assert (sp["k"], sp["n"]) == (4, 4)
    assert sp["significant"] is True
    assert up["provenance"]["analyzers"]["signal_peptide"].startswith("deepsig")
    assert "transmembrane" in up["provenance"]["unavailable_features"]
    seed = json.loads((ctx.paths.fcer / "GCF_000000001.1.seed.json").read_text())
    feats = {t["feature"] for t in seed["tests"]}
    assert {"pfam:PF00005", "antismash:NRPS", "antismash:any"} <= feats
    assert [o["location"] for o in up["neighborhood"]["orfs"]].count("upstream") == 4
    # inputs captured, invocations recorded, index populated
    assert (ctx.paths.inputs / "query.faa").exists()
    tools = {json.loads(line)["tool"] for line in ctx.paths.invocations.read_text().splitlines()}
    assert {"cblaster", "antismash", "deepsig", "hmmsearch", "mmseqs", "datasets"} <= tools
    assert Run.objects.get(pk=ctx.run_id).status == "complete"
    assert FcerEntry.objects.filter(run_id=ctx.run_id).count() == 6
    assert (ctx.paths.fcer / "GCF_000000001.1.upstream.csv").read_text().startswith("# schema_version,1.0")


@pytest.mark.django_db(transaction=True)
def test_rejected_passthrough_halts_with_exit_3(env):
    from flanders.engine import pipeline

    ws, cfg_dir = env
    ctx = pipeline.prepare(cfg_dir / "run.yaml", ["cblaster.bogus_flag=1"], None, 2, ws)
    assert pipeline.execute(ctx) == 3
    from flanders.workspace.models import Run, Task
    assert Run.objects.get(pk=ctx.run_id).status == "halted"
    assert Task.objects.get(run_id=ctx.run_id, stage="discover").status == "failed"
    report = json.loads(ctx.paths.report.read_text())
    assert "cblaster" in report["message"]


@pytest.mark.django_db(transaction=True)
def test_resume_skips_completed(env):
    from flanders.engine import pipeline
    from flanders.workspace.models import Task

    ws, cfg_dir = env
    ctx = pipeline.prepare(cfg_dir / "run.yaml", [], None, 2, ws)
    assert pipeline.execute(ctx) == 0
    first = {(t.stage, t.tag): t.finished_at for t in Task.objects.filter(run_id=ctx.run_id)}
    # Simulate a crash during emit_fcer of one genome: in-flight task left `running`.
    Task.objects.filter(run_id=ctx.run_id, stage="emit_fcer", tag="GCF_000000002.1").update(status="running")
    ctx2 = pipeline.load_existing(ctx.run_id, ws, 2)
    assert pipeline.execute(ctx2) == 0
    after = {(t.stage, t.tag): t.finished_at for t in Task.objects.filter(run_id=ctx.run_id)}
    changed = [k for k in first if first[k] != after[k]]
    assert changed == [("emit_fcer", "GCF_000000002.1")]


def test_missing_input_is_config_error(env, tmp_path):
    from flanders.engine import pipeline
    from flanders.errors import ConfigError

    ws, cfg_dir = env
    (cfg_dir / "query.faa").unlink()
    with pytest.raises(ConfigError, match="query"):
        pipeline.prepare(cfg_dir / "run.yaml", [], None, 2, ws)


