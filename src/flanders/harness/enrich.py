"""Per-genome enrichment: one result set per (genome x location). Django-free.

Population (the null): every ORF in the genome's background set plus every
neighborhood ORF. With `paralog_collapsed`, the background set is one representative
per mmseqs2 cluster; neighborhood ORFs are always counted individually. A location's
neighborhood ORFs are tested against that population: is the feature more frequent
among them than among ORFs drawn at random from the genome?
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from flanders.config.models import StatisticsConfig
from flanders.genomics.models import LOCATIONS, EnrichInput, Location
from flanders.harness import rng as rng_mod
from flanders.harness import stats

BACKGROUND_DEFINITIONS = {
    "paralog_collapsed": (
        "Population = one representative ORF per mmseqs2 cluster (min identity {identity}, "
        "coverage {coverage}) across the genome, plus every neighborhood ORF counted individually."
    ),
    "raw": "Population = every annotated ORF in the genome.",
}


@dataclass
class LocationResult:
    location: Location
    tests: list[dict]
    covariates: dict


def _population(inp: EnrichInput, background: str):
    if background == "raw":
        return list(inp.orfs)
    return [o for o in inp.orfs if o.in_background or o.location is not None]


def predictor_for(feature: str, predictors: dict[str, str]) -> str | None:
    role = feature.split(":", 1)[0]
    return predictors.get(role)


def analyze(inp: EnrichInput, cfg: StatisticsConfig, seed: int) -> list[LocationResult]:
    population = _population(inp, cfg.background)
    pop_features = [set(o.features) for o in population]
    results = []
    for loc in LOCATIONS:
        hood = [o for o in inp.orfs if o.location == loc]
        if not hood:
            continue
        hood_features = [set(o.features) for o in hood]
        rows: list[dict] = []
        for feature in inp.features_tested:
            k = sum(feature in f for f in hood_features)
            flags = np.fromiter((feature in f for f in pop_features), dtype=bool, count=len(population))
            b = int(flags.sum())
            effect = stats.log2_enrichment(k, len(hood), b, len(population))
            for test in cfg.tests:
                if test == "binomial":
                    res = stats.binomial_enrichment(k, len(hood), b, len(population))
                else:
                    gen = rng_mod.child(seed, f"permutation:{inp.tag}:{loc}:{feature}")
                    res = stats.permutation_enrichment(k, len(hood), flags, cfg.permutations, gen)
                rows.append(
                    {
                        "feature": feature,
                        "test": test,
                        "predictor": predictor_for(feature, inp.predictors_used),
                        "k": k,
                        "n": len(hood),
                        "background_hits": b,
                        "background_n": len(population),
                        "effect_log2": effect,
                        "p_value": res.p_value,
                        "reason": res.reason or ("no_neighborhood_hits" if k == 0 else None),
                    }
                )
        # Correct across features, separately for each test, within this location.
        for test in cfg.tests:
            group = [r for r in rows if r["test"] == test]
            qs = stats.correct([r["p_value"] for r in group], cfg.correction)
            for r, q in zip(group, qs, strict=True):
                r["q_value"] = q
                r["significant"] = None if q is None else bool(q < cfg.threshold)
        rows.sort(key=lambda r: (r["test"], r["feature"]))
        covariates = {
            "gc": stats.covariate_shift([o.gc for o in hood], [o.gc for o in population]),
            "length_aa": stats.covariate_shift(
                [float(o.length_aa) for o in hood], [float(o.length_aa) for o in population]
            ),
        }
        results.append(LocationResult(loc, rows, covariates))
    return results


def background_definition(cfg: StatisticsConfig) -> str:
    return BACKGROUND_DEFINITIONS[cfg.background].format(
        identity=cfg.paralog_identity, coverage=cfg.paralog_coverage
    )
