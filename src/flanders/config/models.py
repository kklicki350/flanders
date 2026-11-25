"""Run configuration. FLANDERS-owned keys are validated; dependency sections pass through."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from flanders.genomics.accessions import require_assembly

FeatureName = Literal["signal_peptide", "transmembrane", "pfam", "antismash"]
TestName = Literal["binomial", "permutation"]
Correction = Literal["bh", "bonferroni", "none"]
Background = Literal["paralog_collapsed", "raw"]
SearchMode = Literal["snapshot", "remote"]
OrganismGroup = Literal["gram-negative", "gram-positive", "eukaryote"]

DEPENDENCY_SECTIONS = ("cblaster", "antismash")


class StatisticsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tests: list[TestName] = Field(default_factory=lambda: ["binomial", "permutation"])
    correction: Correction = "bh"
    threshold: float = Field(0.05, gt=0, lt=1)
    background: Background = "paralog_collapsed"
    permutations: int = Field(10_000, ge=100)
    paralog_identity: float = Field(0.5, gt=0, le=1)
    paralog_coverage: float = Field(0.8, gt=0, le=1)


class RunConfig(BaseModel):
    """The run-config file as a validated model. `extra="forbid"` catches typos."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    query: str  # protein FASTA path
    genomes: str | None = None  # file listing assembly accession.version, one per line
    search: SearchMode = "snapshot"
    flank_orfs: int = Field(4, ge=1, le=50)
    features: list[FeatureName] = Field(
        default_factory=lambda: ["signal_peptide", "transmembrane", "pfam", "antismash"]
    )
    organism_group: OrganismGroup = "gram-negative"
    statistics: StatisticsConfig = Field(default_factory=StatisticsConfig)
    seed: int = 20260101
    jobs: int | None = Field(None, ge=1)
    tree: str | None = None
    ncbi: dict[str, Any] = Field(default_factory=dict)  # {api_key: ...}
    cblaster: dict[str, Any] = Field(default_factory=dict)
    antismash: dict[str, Any] = Field(default_factory=dict)

    @field_validator("features")
    @classmethod
    def _unique(cls, v: list[str]) -> list[str]:
        if len(set(v)) != len(v):
            raise ValueError("features listed more than once")
        return v

    def model_post_init(self, _ctx: Any) -> None:
        if self.search == "snapshot" and not self.genomes:
            raise ValueError("search: snapshot needs `genomes:` (a file of assembly accessions)")
        if self.search == "remote" and not self.ncbi.get("email"):
            raise ValueError("search: remote needs `ncbi: {email: you@institution.edu}` (NCBI requires a contact)")


def read_genome_list(text: str) -> list[str]:
    accs = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            accs.append(require_assembly(line.split()[0]))
    if len(set(accs)) != len(accs):
        raise ValueError("genome list contains duplicates")
    return accs
