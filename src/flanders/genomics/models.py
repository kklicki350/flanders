"""Genomic data models shared by the pipeline, harness and FCER. Django-free."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Strand = Literal["+", "-"]
Location = Literal["upstream", "seed", "downstream"]
LOCATIONS: tuple[Location, ...] = ("upstream", "seed", "downstream")


class Orf(BaseModel):
    """One annotated CDS. Coordinates are 1-based inclusive on `record`."""

    model_config = ConfigDict(frozen=True)

    orf_id: str  # protein accession.version, or record:locus_tag when no protein_id
    record: str  # nucleotide accession.version
    start: int
    end: int
    strand: Strand
    locus_tag: str | None = None
    product: str | None = None
    length_aa: int
    gc: float  # GC fraction of the CDS nucleotide sequence


class EnrichOrf(BaseModel):
    """An ORF as the enrichment harness sees it: membership plus feature calls."""

    orf_id: str
    location: Location | None  # None = not part of the neighborhood
    in_background: bool
    length_aa: int
    gc: float
    features: list[str] = Field(default_factory=list)


class EnrichInput(BaseModel):
    """Everything a stats-only replay needs for one genome. Stored per tag."""

    tag: str
    organism: str | None = None
    record: str
    seed_start: int
    seed_end: int
    seed_strand: Strand
    flank_orfs: int
    orfs: list[EnrichOrf]
    features_tested: list[str]  # feature universe for this genome
    unavailable_features: dict[str, str] = Field(default_factory=dict)  # feature -> reason
    predictors_used: dict[str, str] = Field(default_factory=dict)  # role -> tool version
    background_definition: str
