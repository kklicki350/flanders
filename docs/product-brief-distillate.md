---
title: "Product Brief Distillate: FLANDERS"
type: llm-distillate
source: "docs/product-brief.md"
created: "2026-05-02"
purpose: "Token-efficient context for downstream PRD creation"
---

# FLANDERS Product Brief — Distillate

Detail captured during brief discovery that goes beyond the 1–2 page executive summary. Structured for downstream PRD authoring (`bmad-create-prd`).

## Identity & licensing

- Acronym: **F**unctional **L**andscape **A**nd **N**eighbor-**D**etermining g**E**nomic **R**egion **S**earch — kept from original FLANDERS (2021); fits the meta-tool reframing.
- Project codename in BMad config: `flanders` (set in `_bmad/bmm/config.yaml`).
- Target license: **MIT** (open-source, "for fun + bioRxiv" — no commercial intent).
- Original FLANDERS lives at `archive/flanders_original_repo/` (~500 LOC, broken on modern deps; reference-only). Post-processing helpers at `archive/skip_smash_original/`. Neither is a rebuild template.

## Core technical decisions (locked)

- **Dependencies as first-class:** cblaster (cluster discovery + flank extraction) + antiSMASH 7 (BGC annotation), full parameter pass-through. No fork, no shim. cblaster + antiSMASH together cover ~50% of original FLANDERS scope.
- **v1 feature panel:** SignalP + TMHMM + Pfam-A `hmmscan`. Pluggable behind `--features`.
- **Fallback chain for SignalP-class predictors:** SignalP 5 → DeepSig → Phobius. Stays as architectural insurance regardless of DTU response.
- **Statistical baseline:** binomial against paralog-collapsed per-genome ORF background. Paralog clustering via mmseqs2 at a documented identity threshold (threshold TBD, but explicit and reportable).
- **Statistical second baseline:** label-shuffling permutation test ships in v1 alongside the binomial.
- **MTC:** Benjamini–Hochberg + Bonferroni first-class outputs.
- **Per-output covariate reporting:** GC% and gene-length distributions for flank vs background, in every FCER.
- **Output artifact name:** FLANDERS Cluster Enrichment Record (**FCER**). Per-(genome × location) record + cross-genome aggregate. Versioned via `schema_version` field, JSON Schema in repo, semver-tracked.
- **Backend:** FastAPI (locked).
- **Install primary:** Docker image (cross-platform canonical). Plus `install-flanders.sh` bootstrap that detects platform, installs Docker if needed, pulls image, drops `flanders` shim on PATH (Linux/macOS/WSL).
- **Install secondary (developer-mode):** pip + bioconda with pinned env.yml.
- **GUI architecture:** `flanders gui` → localhost FastAPI + browser SPA. Pre-built static assets shipped in the wheel (no `npm` for end users). Same SPA + FastAPI become the v2 hosted webapp; deployment is the only thing that changes.

## Decisions still open / TBD

- **Frontend framework:** SvelteKit vs React+Vite — not yet picked.
- **Synteny library:** clinker vs pyGenomeViz vs GenomeView — not yet picked.
- **mmseqs2 identity threshold** for paralog collapsing — pick + document.
- **Pfam-A HMM database** — bundled in image vs fetched on first run.
- **DTU academic-use clarification** for SignalP 6 / TMHMM 2.0c — Kevin to email.

## Decisions explicitly deferred (do not re-litigate in PRD)

- **Co-maintainer / institutional GitHub org.** v1 accepts solo-author bus factor. Revisit before v2 webapp scope locks.
- **Target journal post-preprint.** Preprint-only is acceptable; no commitment.
- **Timeline / milestones.** No commitment in v1; not in brief.
- **Webapp hosting / topology / compute architecture / persistence layer.** Entire webapp question deferred to v2.

## Rejected ideas (with rationale — don't re-propose)

- **AWS free-tier real server-compute** — t2.micro OOM and Lambda 15-min cap won't fit cblaster + antiSMASH against NCBI nr.
- **Tiered-compute webapp** (server-side light analytics, local heavy compute) — superseded by Kevin's choice to shelve the entire webapp from v1.
- **Paid VPS for live cblaster runs** (e.g. Hetzner CX22) — same: webapp deferred to v2.
- **Tauri / Electron desktop wrapper** — desktop-shell layer is dead weight when the eventual target is a webapp; SPA + localhost FastAPI gets there cleaner. (Tauri remains as a v1.1 contingency if localhost GUI proves systematically unreliable on locked-down laptops.)
- **PyInstaller / AppImage single-installer** — neither handles heavy bioinformatics dep stacks (HMMER, antiSMASH, cblaster) well. Docker bootstrap script is the realistic single-install answer.
- **Pixi-based bootstrap** (newer conda-compatible package manager) — considered; Docker chosen over it for dep-heaviness reasons and reproducibility-image alignment.
- **"Demo mode" GUI against pre-computed FCERs** for non-coding biologists — superseded when v1 audience contracted to author + similar-skilled bioinformaticians; non-coders are v2-bound.
- **Second demonstration case in the v1 preprint** (e.g. lanthipeptides in *Streptomyces*, NRPS in *Pseudomonas*) — moved to v1.5 applications follow-up paper instead. v1 preprint = method paper with cyanobacterial *ebo* case study.
- **Pull cblaster/antiSMASH features into FLANDERS** — explicitly *not* the strategy. Pass-through orchestration only.

## Technical context / constraints (worth carrying forward)

- antiSMASH 7 (2023) ships stable JSON + a Python API → programmatic orchestration newly tractable post-2023.
- Reviewer caveat: antiSMASH JSON schema is *not* fully stable across point releases. CI and Renovate must catch breakage.
- **antiSMASH HMM databases re-version without git tag changes.** FCER must record HMM-DB checksums, not just antiSMASH version strings.
- HMMER is a transitive dep already (antiSMASH uses it) — Pfam-A `hmmscan` adds essentially no new install cost.
- **Both SignalP 6 *and* TMHMM 2.0c** are DTU-licensed and redistribution-restricted. Not just SignalP. Two licensing concerns, one fallback chain.
- **bioconda recipe risk:** wrapping antiSMASH (heavy recipe with biopython/python pins) and cblaster (own recipe with diamond/biopython pins) means version-solver conflicts are near-certain. Precedent: BiG-SCAPE took years to stabilize the conda solve. Mitigation: ship pinned env.yml, document conda as expert-mode, push users toward Docker.
- **cblaster remote-BLAST mode** hits live NCBI nr (changes daily) — explicitly non-reproducible. Preprint reproducibility requires local BLAST mode against a frozen DB snapshot, archived to Zenodo with the Docker image.
- **bioconda IS mandatory for community uptake** in this niche, even if Docker is the recommended path. Skipping bioconda forfeits the audience.
- **MIBiG 4 + antiSMASH-DB v4** ground enrichment statistics meaningfully (the "what counts as a known BGC" denominator finally exists).
- "Modular genetic element" framing (PADLOC, DefenseFinder, lsaBGC, recent HGT-in-BGC preprints) is hot in 2024–2026 — positioning tailwind.

## Detailed user scenarios

- **S1 — Author dogfooding (primary v1 flow):** Kevin runs the 92-genome *ebo* analysis end-to-end on his own workstation. CLI invocation with full parameter pass-through to cblaster + antiSMASH. Output: FCERs for downstream analysis and preprint figures. Local GUI used for interactive exploration during paper writing.
- **S2 — Pipeline integration:** Bioinformatician drops `flanders run …` into a Snakemake or Nextflow pipeline. Consumes JSON output programmatically. No GUI involvement.
- **S3 — Reviewer rerun:** Peer reviewer pulls Docker image from Zenodo DOI cited in preprint. Uses the harness to swap the statistical test or MTC and rerun against published FCERs. Verifies enrichment claims independently.
- **S4 — (v2) Non-coder exploration:** Hosted webapp, no install. User uploads a result or browses precomputed *ebo* demo. Shareable URLs cited in downstream papers — citation flywheel.

## Competitive intelligence (for positioning section of PRD)

- **BiG-SCAPE** (Wageningen): clusters BGCs across genomes. Different question — clustering vs neighborhood enrichment.
- **CORASON** (Medema lineage): phylogeny-anchored neighborhood analysis. **v2 hook target.** Not a v1 competitor.
- **EvoMining**: evolutionary signatures of biosynthesis. Adjacent, not overlapping. Reportedly stalled after primary author moved on (cautionary precedent for solo-author tools).
- **gecco / DeepBGC**: ML-based BGC prediction from sequence. Different layer (discovery, not characterization).
- **cblaster** (Gilchrist, Chooi lab): first-class FLANDERS dependency. *Coopetition* — risk that cblaster team absorbs the enrichment layer themselves. Mitigation: positioning + pre-publication outreach to convert "could absorb" → "endorses."
- **antiSMASH** (Wageningen, Medema/Weber): first-class FLANDERS dependency. Same outreach strategy.
- **MIBiG** (community standard for BGC entries): FCER schema should align with MIBiG identifiers (v2 vision item). FLANDERS as MIBiG on-ramp.
- **iTOL, antiSMASH-web**: precedents for citation-flywheel mechanic (shareable URLs in papers drive adoption).
- **Tools that died:** ClusterFinder, EvoMining (visible stall after primary author moved on; pattern: solo author + no institutional org + dependency-churn unaddressed).
- **Tools that survived:** BiG-SCAPE, antiSMASH, cblaster (institutional homes, multi-maintainer, active dependency-churn response, conference workshops).

## Citability & community footprint commitments (v1)

- Zenodo-GitHub release archival: every git tag → Zenodo DOI per version.
- `CITATION.cff` in repo root.
- "If you used FLANDERS, cite: …" line printed at end of every CLI run.
- Citation string embedded in FCER metadata block.
- bio.tools registration at preprint time.
- Cross-link PRs to cblaster and antiSMASH READMEs at preprint time.
- Read-the-Docs site with quickstart.
- Jupyter tutorial notebook on the 92-genome corpus shipped in `/docs`.
- (Stretch, not committed:) nf-core / Snakemake-wrappers wrapper, OMICtools entry, Microbiome Digest submission.

## v1 hooks designed in for v2

- `--tree <newick>` argument from v1 — supports v2 CORASON-style phylogeny-anchored analysis.
- Per-genome FCER results structured for tree joins (joinable by genome accession).
- `--features` plug-in interface — third-party feature analyzers in v2 (InterProScan, EffectorP, defense-finder, MIBiG-similarity scoring).
- Same SPA + same FastAPI in v1 GUI = v2 webapp without a frontend rewrite.
- Same orchestration code wrapping cblaster = v2 "live cblaster runs through the UI" without backend rewrite.

## v1.5 / v2 / beyond — scope signals for downstream planning

- **v1.5:** Applications follow-up paper. Second contrasting demonstration (lanthipeptides / NRPS / other). Same FLANDERS, different biology. Citation pair with v1 method paper.
- **v2:** Hosted webapp (deployment of v1 SPA + FastAPI), phylogeny-anchored analysis, expanded feature panel, phylogenetic-signal tests (Pagel's λ, Blomberg's K), shareable result URLs (citation flywheel), webapp hardening (CORS, port-conflict, corporate-AV friction handling for non-coder users on locked-down laptops).
- **Beyond v2:** FCER schema and enrichment harness generalize past BGCs — operon analysis, defense-system islands, CRISPR cassettes, plasmid cargo. Harness factored as importable Python sub-package — citation reach beyond natural-products community. FCER ↔ MIBiG identifier alignment.

## Out of scope (do not propose for v1 PRD)

- BGC prediction from sequence (gecco/DeepBGC territory).
- Phylogenetic tree inference (FLANDERS consumes a tree; doesn't build one).
- BGC clustering across genomes (BiG-SCAPE territory).
- Phylogenetic-signal tests (v2).
- Database hosting, auth, persistence (v2).
- A new statistical method invented for FLANDERS (uses standard tests; the contribution is harness + reproducibility, not novel statistics).
