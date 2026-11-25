"""Statistical tests and multiple-testing corrections. Django-free, numpy/scipy only."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats

PSEUDOCOUNT = 0.5


@dataclass(frozen=True)
class TestResult:
    p_value: float | None
    reason: str | None = None


def binomial_enrichment(k: int, n: int, background_hits: int, background_n: int) -> TestResult:
    """One-sided binomial test: is the flank rate k/n greater than the background rate?"""
    if n == 0:
        return TestResult(None, "empty_neighborhood")
    if background_n == 0:
        return TestResult(None, "zero_background")
    p0 = background_hits / background_n
    if p0 == 0.0:
        # The population includes the neighborhood, so p0 == 0 implies k == 0.
        return TestResult(1.0)
    if p0 == 1.0:
        return TestResult(1.0)
    return TestResult(float(stats.binomtest(k, n, p0, alternative="greater").pvalue))


def permutation_enrichment(
    k: int, n: int, background_flags: np.ndarray, permutations: int, rng: np.random.Generator
) -> TestResult:
    """Label-shuffling test: draw n ORFs without replacement from the background.

    p = (1 + #{draws with count >= k}) / (1 + permutations), the standard unbiased form.
    """
    if n == 0:
        return TestResult(None, "empty_neighborhood")
    m = background_flags.size
    if m == 0:
        return TestResult(None, "zero_background")
    if n > m:
        return TestResult(None, "background_smaller_than_neighborhood")
    flags = background_flags.astype(np.int64)
    # Sampling without replacement of n from m, `permutations` times. For a 0/1 vector
    # the count is hypergeometric, so draw it directly: exact and fast.
    successes = int(flags.sum())
    counts = rng.hypergeometric(successes, m - successes, n, size=permutations)
    return TestResult(float((1 + int((counts >= k).sum())) / (1 + permutations)))


def log2_enrichment(k: int, n: int, background_hits: int, background_n: int) -> float | None:
    """log2((k/n) / (b/B)) with a 0.5 pseudocount on both counts."""
    if n == 0 or background_n == 0:
        return None
    flank = (k + PSEUDOCOUNT) / (n + 2 * PSEUDOCOUNT)
    back = (background_hits + PSEUDOCOUNT) / (background_n + 2 * PSEUDOCOUNT)
    return math.log2(flank / back)


def bonferroni(pvalues: list[float | None]) -> list[float | None]:
    m = sum(p is not None for p in pvalues)
    return [None if p is None else min(1.0, p * m) for p in pvalues]


def benjamini_hochberg(pvalues: list[float | None]) -> list[float | None]:
    idx = [i for i, p in enumerate(pvalues) if p is not None]
    out: list[float | None] = [None] * len(pvalues)
    if not idx:
        return out
    adjusted = stats.false_discovery_control([pvalues[i] for i in idx], method="bh")
    for i, q in zip(idx, adjusted, strict=True):
        out[i] = float(q)
    return out


def correct(pvalues: list[float | None], method: str) -> list[float | None]:
    if method == "bh":
        return benjamini_hochberg(pvalues)
    if method == "bonferroni":
        return bonferroni(pvalues)
    if method == "none":
        return list(pvalues)
    raise ValueError(f"unknown correction {method!r}")


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "mean": None, "median": None, "sd": None}
    arr = np.asarray(values, dtype=float)
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "sd": float(arr.std(ddof=1)) if arr.size > 1 else None,
    }


def covariate_shift(flank: list[float], background: list[float]) -> dict:
    """Flank vs background distribution summary plus a two-sided Mann-Whitney U test."""
    out = {"flank": summarize(flank), "background": summarize(background)}
    if len(flank) >= 1 and len(background) >= 1:
        res = stats.mannwhitneyu(flank, background, alternative="two-sided")
        out["mann_whitney_p"] = float(res.pvalue)
        out["reason"] = None
    else:
        out["mann_whitney_p"] = None
        out["reason"] = "insufficient_data"
    return out
