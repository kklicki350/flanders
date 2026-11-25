"""FCER: FLANDERS Cluster Enrichment Record. Pydantic models are the schema source of truth."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from flanders.genomics.models import Location, Strand

SCHEMA_VERSION = "1.0"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Neighborhood(_Strict):
    record: str = Field(description="Nucleotide accession.version carrying the cluster")
    seed_start: int = Field(description="1-based inclusive")
    seed_end: int = Field(description="1-based inclusive")
    seed_strand: Strand
    flank_orfs: int
    orfs: list[NeighborhoodOrf]


class NeighborhoodOrf(_Strict):
    orf_id: str
    location: Location
    start: int
    end: int
    strand: Strand
    locus_tag: str | None
    product: str | None
    length_aa: int
    features: list[str]


class FeatureTest(_Strict):
    feature: str
    test: Literal["binomial", "permutation"]
    predictor: str | None = Field(None, description="Tool that produced the feature call")
    k: int = Field(description="Neighborhood ORFs carrying the feature")
    n: int = Field(description="Neighborhood ORFs at this location")
    background_hits: int
    background_n: int
    effect_log2: float | None = Field(description="log2 enrichment, 0.5 pseudocount")
    p_value: float | None
    q_value: float | None = Field(description="Corrected across features at this location")
    significant: bool | None
    reason: str | None = Field(None, description="Why a value is null")


class Covariates(_Strict):
    gc: dict[str, Any]
    length_aa: dict[str, Any]


class StatisticsSettings(_Strict):
    tests: list[str]
    correction: str
    threshold: float
    background: str
    permutations: int
    paralog_identity: float
    paralog_coverage: float
    seed: int


class ToolRecord(_Strict):
    tool: str
    version: str


class Provenance(_Strict):
    flanders_version: str
    created_at: str
    run_id: str
    run_name: str | None
    search_mode: str
    discovery_reproducible: bool
    search_metadata: dict[str, Any]
    effective_config: dict[str, Any]
    tools: list[ToolRecord]
    reference_checksums: dict[str, str]
    input_checksums: dict[str, str]
    analyzers: dict[str, str] = Field(description="role -> tool actually used, after fallback")
    unavailable_features: dict[str, str]
    background_definition: str
    citation: str


class Fcer(_Strict):
    schema_version: Literal["1.0"] = SCHEMA_VERSION
    tag: str = Field(description="Assembly accession.version")
    organism: str | None
    location: Location
    neighborhood: Neighborhood
    statistics: StatisticsSettings
    tests: list[FeatureTest]
    covariates: Covariates
    provenance: Provenance


Neighborhood.model_rebuild()
