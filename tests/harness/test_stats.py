import numpy as np
import pytest
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import binom_test as sm_binom_test

from flanders.harness import rng as rng_mod
from flanders.harness import stats


@pytest.mark.parametrize("k,n,b,m", [(3, 4, 100, 4000), (0, 8, 50, 3000), (4, 4, 2000, 4000), (1, 9, 1, 500)])
def test_binomial_matches_statsmodels(k, n, b, m):
    ours = stats.binomial_enrichment(k, n, b, m).p_value
    ref = sm_binom_test(k, n, b / m, alternative="larger")
    assert ours == pytest.approx(ref, rel=1e-12)


def test_binomial_null_reasons():
    assert stats.binomial_enrichment(0, 0, 1, 10).reason == "empty_neighborhood"
    assert stats.binomial_enrichment(1, 2, 0, 0).reason == "zero_background"
    assert stats.binomial_enrichment(0, 4, 0, 100).p_value == 1.0


@pytest.mark.parametrize("method,sm", [("bh", "fdr_bh"), ("bonferroni", "bonferroni")])
def test_corrections_match_statsmodels(method, sm):
    p = [0.001, 0.02, 0.03, 0.2, 0.5, 0.04]
    ours = stats.correct(p, method)
    ref = multipletests(p, method=sm)[1]
    np.testing.assert_allclose(ours, ref, rtol=1e-12)


def test_correction_skips_nulls():
    out = stats.correct([0.01, None, 0.04], "bonferroni")
    assert out == [0.02, None, 0.08]


def test_permutation_is_seeded_and_calibrated():
    flags = np.zeros(1000, dtype=bool)
    flags[:100] = True  # 10% background rate
    a = stats.permutation_enrichment(3, 4, flags, 5000, rng_mod.child(7, "x")).p_value
    b = stats.permutation_enrichment(3, 4, flags, 5000, rng_mod.child(7, "x")).p_value
    assert a == b
    exact = sm_binom_test(3, 4, 0.1, alternative="larger")  # close to hypergeometric here
    assert a == pytest.approx(exact, abs=0.004)


def test_permutation_p_never_zero():
    flags = np.zeros(500, dtype=bool)
    flags[:5] = True
    p = stats.permutation_enrichment(4, 4, flags, 1000, rng_mod.child(1, "y")).p_value
    assert p == pytest.approx(1 / 1001)


def test_log2_effect_pseudocount():
    assert stats.log2_enrichment(0, 0, 1, 1) is None
    assert stats.log2_enrichment(2, 4, 100, 1000) > 0


def test_rng_child_independent_of_order():
    a = rng_mod.child(5, "a").integers(0, 1_000_000)
    rng_mod.child(5, "b").integers(0, 1_000_000)
    assert rng_mod.child(5, "a").integers(0, 1_000_000) == a
