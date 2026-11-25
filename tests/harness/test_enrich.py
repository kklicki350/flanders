from flanders.config.models import StatisticsConfig
from flanders.genomics.models import EnrichInput, EnrichOrf
from flanders.harness.enrich import analyze


def make_input():
    orfs = []
    # 4 upstream ORFs, 3 carry a signal peptide
    for i in range(4):
        orfs.append(EnrichOrf(orf_id=f"U{i}.1", location="upstream", in_background=False,
                              length_aa=300, gc=0.5, features=["signal_peptide"] if i < 3 else []))
    for i in range(3):
        orfs.append(EnrichOrf(orf_id=f"S{i}.1", location="seed", in_background=False,
                              length_aa=400, gc=0.5, features=["pfam:PF00005"]))
    # 2000 background ORFs, 5% signal peptides; 100 more that are collapsed away
    for i in range(2100):
        orfs.append(EnrichOrf(orf_id=f"B{i}.1", location=None, in_background=i < 2000,
                              length_aa=250, gc=0.45, features=["signal_peptide"] if i % 20 == 0 else []))
    return EnrichInput(tag="GCF_000000001.1", record="NC_000001.1", seed_start=1, seed_end=10,
                       seed_strand="+", flank_orfs=4, orfs=orfs,
                       features_tested=["pfam:PF00005", "signal_peptide"],
                       predictors_used={"signal_peptide": "deepsig 1.2.5"},
                       background_definition="test")


def test_analyze_locations_and_population():
    res = analyze(make_input(), StatisticsConfig(permutations=2000), seed=1)
    assert [r.location for r in res] == ["upstream", "seed"]
    up = {(t["feature"], t["test"]): t for t in res[0].tests}
    sp = up[("signal_peptide", "binomial")]
    assert sp["k"] == 3 and sp["n"] == 4
    assert sp["background_n"] == 2000 + 7  # collapsed background + neighborhood
    assert sp["predictor"] == "deepsig 1.2.5"
    assert sp["significant"] is True
    assert up[("signal_peptide", "permutation")]["q_value"] is not None


def test_raw_background_counts_everything():
    res = analyze(make_input(), StatisticsConfig(background="raw", tests=["binomial"]), seed=1)
    assert res[0].tests[0]["background_n"] == 2107
