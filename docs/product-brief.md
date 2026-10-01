---
title: "Product Brief: FLANDERS"
status: "complete"
created: "2026-05-02"
updated: "2026-05-02"
inputs:
  - _bmad-output/planning-artifacts/flanders-brief-session-state.md
  - archive/flanders_original_repo/ (reference-only)
  - archive/skip_smash_original/ (reference-only)
---

# Product Brief: FLANDERS

*Functional Landscape And Neighbor-Determining gEnomic Region Search*

## Executive Summary

FLANDERS-2026 is a **reproducibility and statistics layer** for biosynthetic-gene-cluster (BGC) discovery and characterization — a decade-later rebuild by the original author, fixing what modern dependencies broke and what the original FLANDERS got wrong about statistics. It orchestrates **cblaster** (cluster discovery + flank extraction) and **antiSMASH 7** (BGC annotation) as first-class dependencies with full parameter pass-through, then layers a **pluggable per-ORF feature panel** and a **statistical enrichment harness with corrected p-values against an explicit, reviewable null** on top. cblaster + antiSMASH 7 together cover roughly half of what the original FLANDERS did; FLANDERS-2026 contributes the layer above — disciplined orchestration, defensible enrichment statistics, and a single unified per-(genome × location) artifact (the **FLANDERS Cluster Enrichment Record**, FCER) suitable for downstream hypothesis testing.

v1 is built for the author and similar-skilled bioinformaticians: a Docker-first CLI for pipelines and a local GUI for interactive exploration of one's own results. The GUI is intentionally architected as a localhost-served SPA so the same frontend becomes a hosted webapp in v2 — at which point non-coding biologists become a first-class audience without a rewrite.

The primary deliverable is a **bioRxiv preprint** framed as a method paper with the *ebo* (extracellular-binding-ortholog) gene family across 92 cyanobacterial genomes as the demonstration case. Real adopters along the way are a bonus, not a goal.

## The Problem

A modern microbial-natural-products researcher chasing a BGC family across a clade typically writes glue. cblaster finds clusters and extracts flanking ORFs. antiSMASH annotates them. Custom Python pulls per-ORF features (signal peptides, transmembrane domains). More custom Python tests for enrichment. More custom Python joins per-tool outputs into something analyzable. The glue gets rewritten in every lab.

Each piece works in isolation. cblaster has a clean Python API. antiSMASH 7 ships stable JSON. SignalP and TMHMM run unattended. The gap is **orchestration with statistical rigor**. No tool today takes "this protein family across this clade" and returns a single defensible artifact answering: *which features are enriched on the flanks, with what effect size, with what multiple-testing-corrected significance, against what explicit background distribution?*

When that artifact doesn't exist, a peer reviewer can't easily evaluate whether enrichment claims hold up — and the researcher spends weeks building bespoke pipelines instead of asking biological questions.

## The Solution

FLANDERS-2026 is a thin orchestration layer with three concrete responsibilities:

1. **Run the dependencies, don't replace them.** cblaster handles cluster discovery and flank extraction. antiSMASH 7 handles BGC annotation. Full parameter pass-through means a user can fully reproduce a cblaster-only or antiSMASH-only run *through* FLANDERS — there is no fork, no shim, no reimplementation.
2. **Per-ORF feature panel.** SignalP, TMHMM, and **Pfam-A domain scanning (hmmscan)** in v1, behind a `--features` plug-in interface so InterProScan, EffectorP, defense-finder, and others slot in for v2 without an architecture change. Fallback chain (SignalP 5 / DeepSig / Phobius) is built in from day one as insurance against the SignalP 6 / TMHMM 2.0c license uncertainty.
3. **Enrichment harness.** Binomial against a paralog-collapsed per-genome ORF background as the baseline; pluggable for Fisher / hypergeometric / label-shuffling permutation tests. Multiple-testing correction (Benjamini–Hochberg, Bonferroni) is first-class output, not a footnote. Every output reports GC% and gene-length distributions for flank vs background so reviewers can verify the null is matched.

Output is the **FLANDERS Cluster Enrichment Record (FCER)**: a per-(genome × location) CSV+JSON record plus a cross-genome aggregate, structured for direct downstream use — phylogenetic comparison, hypothesis testing, manuscript figures — with no parsing project required.

Two interfaces share one codebase:

- **CLI** (Docker is the recommended cross-platform install; pip and bioconda available for developers) for batch jobs, pipelines, and headless reruns.
- **Local GUI** — `flanders gui` spins up a localhost FastAPI server and serves a browser SPA (SvelteKit or React+Vite). Interactive table, synteny viewer, ability to re-run *light* analytics (different background, different MTC) without re-running the heavy pipeline. The same SPA + FastAPI become the v2 webapp; only deployment changes.

**Install story.** Docker is the canonical install for cross-platform parity (Linux / macOS / WSL). A small bootstrap script (`install-flanders.sh`) detects the platform, installs Docker if absent, pulls the image, and drops a `flanders` shim on PATH — so end users run one script, then invoke `flanders` directly without juggling conda environments or per-OS installers.

## What Makes This Different

- **Built for the reviewer.** Pass-through architecture means any FLANDERS result can be verified by re-running cblaster or antiSMASH directly with the captured parameters; the enrichment harness lets reviewers swap the test, the correction, or the background distribution and rerun against the saved artifact without touching the heavy pipeline. There is no "FLANDERS magic" to take on faith.
- **Statistics as a first-class output.** Most pipelines in this space report counts. FLANDERS reports effect sizes with corrected p-values against an explicit, documented background distribution. The artifact records every statistical choice so methods sections write themselves.
- **One named, versioned artifact (FCER), not a pile.** A unified per-(genome × location) record plus a cross-genome aggregate removes the join step that currently lives in every researcher's notebook. The FCER schema is versioned (`schema_version` field, JSON Schema shipped in repo, semver-tracked) so downstream notebooks don't break across releases.
- **Local GUI = future webapp.** The architecture intentionally collapses the v1→v2 cost. Same SPA, same FastAPI; deployment is the only thing that changes.
- **v2 hooks designed in from day one.** Optional `--tree <newick>` argument from v1 to support CORASON-style phylogeny-anchored analysis later. Per-genome results structured for tree joins. Plug-in feature interface ready for InterProScan, EffectorP, defense-finder, and community contributions.

**Related work and positioning.** BiG-SCAPE clusters BGCs across genomes; CORASON anchors neighborhoods to phylogenies; EvoMining mines for evolutionary signatures of biosynthesis; gecco/DeepBGC predict BGCs from sequence. None of them combine cblaster-style discovery, antiSMASH-style annotation, *and* a defensible per-flank statistical enrichment harness in a single artifact. FLANDERS occupies the gap between discovery and downstream comparative analysis — the layer above, not the layer beside.

## Who This Serves

**v1 primary user — the author and similar-skilled bioinformaticians** running BGC neighborhood analyses on their own workstations. They install the dependencies (Docker bootstrap or conda env), drop the CLI into Snakemake/Nextflow pipelines, and use the local GUI for interactive exploration of their own results. The dogfooding case is the *ebo* analysis itself.

**v1 secondary user — the bioRxiv reader.** Peer reviewer or downstream researcher who needs to evaluate whether the *ebo* enrichment findings are real. They get a defensible methodology, a Docker image they can pull, and the option to rerun the statistics with different choices against the published FCERs.

**v2 audience — non-coding biologists and microbial ecologists.** Same SPA, hosted, no install required. The local-GUI architecture in v1 is intentionally the v2 webapp prototype; serving non-coders is a v2 deliverable, not a v1 one.

## Success Criteria

- **bioRxiv preprint posted** — primary deliverable. Framed explicitly as a **method paper with cyanobacterial case study**: the 92 *ebo* genomes are the demonstration vehicle; broader-applicability claims are deferred to a follow-up applications paper rather than crammed into v1. This sets reviewer expectations honestly and keeps v1 scope finite.
- **Reproducibility contract met** — the canonical reproducibility target is a **Zenodo-archived Docker image** that bundles the full dependency closure plus a frozen local BLAST database snapshot. `pip` and `conda` installs are best-effort and may diverge as upstream HMM databases re-version; remote-BLAST mode is documented as explicitly non-reproducible. Every FCER carries dependency versions and HMM-DB checksums.
- **Defensibility under review** — methodology pre-reviewed by ≥1 external statistician before submission; the preprint addresses paralog inflation, gene-length/GC bias, and background-choice sensitivity head-on rather than reactively.
- **Citability and discovery** — every release tagged, semver-versioned, archived to Zenodo with a per-version DOI; CITATION.cff in repo; bio.tools entry registered; cross-link PRs to cblaster and antiSMASH READMEs at preprint time.
- **Adoption signal (bonus, not target)** — bioconda install count and GitHub stars as ambient signal that the tool is useful beyond the demonstration case.

## Scope

**In for v1:**

- cblaster + antiSMASH 7 orchestration, full parameter pass-through, version-pinned
- Feature panel: SignalP + TMHMM + **Pfam-A domain scanning (hmmscan)**, with fallback chain (SignalP 5 / DeepSig / Phobius); v1 ships a **predictor-concordance / sensitivity analysis** on the demonstration corpus so enrichment claims are reported under each predictor, not just the default
- Enrichment harness: binomial baseline against a **paralog-collapsed** per-genome ORF background (mmseqs2 clustering at a documented identity threshold); pluggable test interface; FDR (BH) and Bonferroni correction; per-output reporting of GC% and gene-length distributions for flank vs background
- Unified CSV+JSON artifact (FCER): per-(genome × location) records plus a cross-genome aggregate; `schema_version` field; JSON Schema shipped in repo
- CLI distributed as: **Docker image (canonical, cross-platform)** + a `install-flanders.sh` bootstrap script that handles Docker setup and PATH wiring on Linux / macOS / WSL; pip and bioconda available as developer/expert install paths with a pinned env.yml shipped alongside the conda recipe
- Local GUI: `flanders gui` → localhost FastAPI + browser SPA; pre-built static assets shipped in the wheel (no `npm` for end users)
- Reference dataset: 92 *ebo* cyanobacterial genomes (NCBI accession list, expected wall-clock budget, and minimum hardware spec documented), runnable end-to-end as both validation suite and demonstration case
- CI against multiple upstream antiSMASH and cblaster releases; Renovate/Dependabot opens PRs on upstream releases; public compatibility matrix in the README
- **Citability deliverables**: Zenodo-GitHub release archival with per-version DOIs, CITATION.cff, "If you used FLANDERS, cite: …" line printed at end of every CLI run, and citation string embedded in the FCER metadata block
- **Discoverability deliverables**: bio.tools registration; cross-link PRs to cblaster and antiSMASH READMEs at preprint time
- **Documentation**: Read-the-Docs site with quickstart; Jupyter tutorial notebook on the 92-genome corpus shipped in `/docs`

**Out for v1, with v1 hooks designed in:**

- CORASON-style phylogeny-anchored neighborhood analysis *(v1 hook: `--tree <newick>` argument; per-genome result structure joinable by accession)*
- Phylogenetic-signal tests (Pagel's λ, Blomberg's K), ancestral state reconstruction *(v1 hook: same as above)*
- InterProScan and additional analyzers in the feature panel *(v1 hook: `--features` plug-in interface)*
- Hosted webapp deployment with auth, persistence, sharing *(v1 hook: GUI is the same SPA + same FastAPI)*
- Live cblaster runs through the UI *(v1 hook: same orchestration code already wraps cblaster)*

## Risks

- **DTU-licensed predictor redistribution (SignalP 6 *and* TMHMM 2.0c).** Both are DTU-restricted; neither can be bundled in conda. Mitigated by the fallback chain (SignalP 5 / DeepSig / Phobius) shipped from v1, the predictor-concordance analysis turning the chain into a strength rather than a liability, and an academic-use clarification email to DTU. Fallback chain stays regardless of DTU's response.
- **Enrichment methodology defensibility.** Per-genome ORF background can be attacked on paralog inflation, gene-length bias, and Pfam-domain non-independence. Mitigated by paralog-collapsed nulls, GC/length covariate reporting, and shipping a label-shuffling permutation test as a secondary baseline so reviewers can verify against a non-parametric null without changing the pipeline.
- **Dependency churn (antiSMASH, cblaster move fast).** Mitigated by version pinning, Renovate-driven upstream PR tracking, CI against multiple upstream releases, public compat matrix, and loud failure on parser breakage. Compatibility-patch SLA documented in CONTRIBUTING.
- **cblaster team could absorb the layer.** Proximity and maintainer attention favor them. Mitigated by FLANDERS positioning as the statistics + reproducibility layer (not a discovery tool) and by pre-publication outreach to the cblaster and antiSMASH teams to convert "could absorb" into "endorses."
- **Local GUI on locked-down institutional laptops.** Lower priority for v1 (primary v1 users have working bioinformatics stacks and admin rights on their own machines), but localhost FastAPI + browser SPA can hit CORS, port-conflict, and corporate-AV friction in the wild. Mitigated by configurable port and clear localhost-only binding; a hardening pass on this surface is a v2 prerequisite when the audience expands to non-coders via the hosted webapp.
- **Frontend rot.** SPA dependency churn (SvelteKit/Vite/npm) outpaces the bioinformatics stack. Mitigated by aggressive frontend pinning, shipping pre-built static assets in the wheel, and feature-freezing the GUI between major releases so Python-only patches don't touch the frontend.
- **Maintenance decay / solo-author bus factor.** Open-source academic tools often die after the preprint. v1 explicitly accepts solo-author risk; concrete mitigations are keeping the code small, the dependency surface narrow, and the FCER schema versioned so users on older releases aren't stranded. Co-maintainer and institutional-GitHub-org questions are deferred and revisited before the v2 hosted-webapp scope locks.

## Vision

**v1.5 — applications follow-up paper.** A second-case demonstration (lanthipeptides in *Streptomyces*, NRPS in *Pseudomonas*, or another contrasting system) showing the framework generalizes past the cyanobacterial origin story. Same FLANDERS, different biology — converts the v1 method paper into a citation pair.

**v2 — hosted webapp + phylogeny.** v2 turns the local GUI into a hosted webapp without rewriting the frontend (shareable result URLs become a citation flywheel); adds CORASON-style phylogeny-anchored analysis with the `--tree` hook already designed in; expands the feature panel via the plug-in interface (InterProScan, EffectorP, defense-finder, MIBiG-similarity scoring) so third-party contributions become a community flywheel; and adds phylogenetic-signal tests on flanking features.

Beyond v2: the FCER schema and the enrichment harness generalize cleanly past BGCs — to operon analysis, defense-system islands, CRISPR cassettes, and plasmid cargo. The harness factored as an importable Python sub-package extends FLANDERS's citation reach well beyond the natural-products community. Aligning the FCER schema with **MIBiG** identifiers positions FLANDERS as an on-ramp for new MIBiG entries.

The longer-term ambition is a tool that lets a non-coding microbial ecologist ask *"what's modular in this clade's BGC neighborhoods?"* and get a publishable answer in an afternoon — the kind of question that today takes a postdoc a quarter.
