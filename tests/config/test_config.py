import pytest

from flanders.config.merge import apply_overrides, load_config
from flanders.config.models import read_genome_list
from flanders.errors import ConfigError


def test_precedence(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("query: q.faa\ngenomes: g.txt\nflank_orfs: 6\ncblaster:\n  min_identity: 30\n")
    cfg, eff = load_config(p, ["flank_orfs=8", "cblaster.max_distance=20000", "statistics.correction=bonferroni"])
    assert cfg.flank_orfs == 8
    assert eff["cblaster"] == {"min_identity": 30, "max_distance": 20000}
    assert cfg.statistics.correction == "bonferroni"
    assert eff["statistics"]["threshold"] == 0.05  # default filled in


def test_typo_is_config_error(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("query: q.faa\ngenomes: g.txt\nflank_orf: 6\n")
    with pytest.raises(ConfigError, match="flank_orf"):
        load_config(p)


def test_snapshot_needs_genomes(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("query: q.faa\n")
    with pytest.raises(ConfigError):
        load_config(p)


def test_override_requires_equals():
    with pytest.raises(ConfigError):
        apply_overrides({}, ["flank_orfs"])


def test_genome_list():
    assert read_genome_list("GCF_000011345.1  # Nostoc\n\nGCA_000017845.1\n") == [
        "GCF_000011345.1", "GCA_000017845.1"]
    with pytest.raises(ValueError):
        read_genome_list("GCF_000011345\n")
