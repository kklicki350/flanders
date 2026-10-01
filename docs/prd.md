---
stepsCompleted:
  - step-01-init
  - step-01b-continue
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-12-complete
releaseMode: phased
classification:
  projectType: cli_tool
  secondaryTraits:
    - developer_tool
    - web_app
  domain: scientific
  complexity: medium-high
  projectContext: greenfield
inputDocuments:
  - docs/product-brief.md
  - docs/product-brief-distillate.md
  - _bmad-output/planning-artifacts/flanders-brief-session-state.md
  - archive/flanders_original_repo/README.md
  - archive/flanders_original_repo/flanders_mgbloop.py
  - archive/flanders_original_repo/test_cluster_list.txt
  - archive/skip_smash_original/annotation_getter.py
  - archive/skip_smash_original/concatenate_tsv.py
  - archive/skip_smash_original/genomes.py
  - archive/skip_smash_original/synth_counter.py
  - archive/skip_smash_original/transporter_counter.py
documentCounts:
  briefs: 1
  distillates: 1
  sessionState: 1
  legacyCode: 8
workflowType: 'prd'
projectType: greenfield
---

# Product Requirements Document - FLANDERS

**Author:** Kevin Klicki
**Date:** 2026-05-02 · **Updated:** 2026-10-01

## Executive Summary

FLANDERS-2026 is a **reproducibility-and-statistics layer for biosynthetic-gene-cluster (BGC) neighborhood analysis** — a decade-later rebuild by the original author that fixes what modern dependencies broke and what the original FLANDERS got wrong about statistics. It orchestrates **cblaster** (cluster discovery + flank extraction) and **antiSMASH 7** (BGC annotation) as first-class, version-pinned dependencies with full parameter pass-through, then layers on a **pluggable per-ORF feature panel** (SignalP, TMHMM, Pfam-A `hmmscan`) and a **statistical enrichment harness** that reports effect sizes with multiple-testing-corrected p-values against an explicit, reviewable null. The pipeline emits one named, versioned artifact — the **FLANDERS Cluster Enrichment Record (FCER)** — per (genome × location) plus a cross-genome aggregate, replacing the bespoke glue every lab currently rewrites to join per-tool outputs into something analyzable.

The target problem is **orchestration with statistical rigor**, not discovery or annotation: no tool today takes "this protein family across this clade" and returns a single defensible artifact answering *which flank features are enriched, with what effect size, at what corrected significance, against what background distribution*. v1 serves the author and similar-skilled bioinformaticians through a Docker-canonical CLI and a local GUI. The GUI composes run configurations, browses results, and inspects provenance, so cblaster and antiSMASH become invisible infrastructure rather than tools the user must learn; it is architected as a localhost FastAPI + browser SPA so it becomes the v2 hosted webapp without a rewrite. Development is build-first: v1 is completed through UI-led exploration, then used to produce the primary research deliverable — a **bioRxiv method paper** demonstrated on the *ebo* gene family across 92 cyanobacterial genomes.

### What Makes This Special

**The orchestration is the product.** FLANDERS takes "this protein family across this clade" from query to a single analyzable artifact in one invocation, driving cblaster and antiSMASH 7 as pass-through dependencies rather than forking or reimplementing them. No component is new; the disciplined, assembled path through them is (see *Innovation & Novel Patterns*).

The second-order claim: FLANDERS is **built for the reviewer**, not just the runner. Pass-through architecture means any result can be re-verified by re-running cblaster or antiSMASH directly with the captured parameters, and the enrichment harness lets a reviewer swap the statistical test, the correction, or the background distribution and rerun against the *saved FCER* without touching the heavy pipeline — there is no "FLANDERS magic" to take on faith. Two further commitments distinguish it: **statistics are a first-class output** (effect sizes + BH/Bonferroni-corrected p-values against an explicit, documented null, with GC% and gene-length covariate reporting in every record) rather than counts in a footnote; and **one versioned artifact** (`schema_version`, JSON Schema shipped in repo, semver-tracked) removes the join step that lives in everyone's notebook.

The core insight is timing: the underlying tools only recently became programmatically composable — antiSMASH 7 (2023) ships stable JSON and a Python API, cblaster exposes a clean API, and MIBiG 4 + antiSMASH-DB v4 finally ground the "what counts as a known BGC" denominator. The missing piece was never another discovery or annotation tool; it was disciplined orchestration plus a defensible enrichment artifact. Nothing in the adjacent landscape — BiG-SCAPE (cross-genome clustering), CORASON (phylogeny-anchored neighborhoods), EvoMining (evolutionary signatures), gecco/DeepBGC (ML prediction) — occupies the gap between discovery and downstream comparative analysis.

## Project Classification

- **Project type:** CLI tool (primary), with developer-tool and web-app secondary traits
- **Domain:** Scientific / bioinformatics (microbial natural-products genomics)
- **Complexity:** Medium-high — heavy external dependency surface (cblaster, antiSMASH 7, HMMER, mmseqs2, DTU-licensed predictors), statistical-defensibility requirements, and a two-interface (CLI + local GUI) codebase sharing one backend
- **Project context:** Greenfield rebuild — the 2021 FLANDERS (`archive/`, ~500 LOC, broken on modern deps) is reference-only, not a template

## Success Criteria

### User Success

- A bioinformatician can take a protein-family query + a genome set and obtain a complete set of FCERs **in a single `flanders run` invocation**, with no hand-written glue between cblaster, antiSMASH, the feature panel, and the enrichment stats.
- The "aha" moment for the **runner**: the join step disappears — one versioned artifact lands ready for downstream analysis (phylogenetic comparison, hypothesis testing, manuscript figures) with no parsing project.
- The "aha" moment for the **reviewer** (the differentiator-aligned success): they can swap the statistical test, the correction, or the background distribution and rerun against a *published* FCER — getting an independent verdict on an enrichment claim without re-running the heavy pipeline or trusting any "FLANDERS magic."
- A pipeline user can drop `flanders run` into Snakemake/Nextflow and consume JSON programmatically, headless, no GUI.
- A user can configure a complete run in the GUI without learning any cblaster or antiSMASH flag.

### Business Success *(academic / publication impact — no commercial intent; license MIT)*

- **Primary:** a **bioRxiv preprint posted**, framed as a *method paper with cyanobacterial* ebo *case study* — broader-applicability claims deferred to a v1.5 follow-up. Produced after v1 is complete, using the finished tool (see *Project Scoping & Phased Development*).
- **Defensibility under review:** methodology pre-reviewed by **≥1 external statistician** before submission; the preprint addresses paralog inflation, gene-length/GC bias, and background-choice sensitivity proactively.
- **Citability:** every release semver-tagged and Zenodo-archived with a per-version DOI; `CITATION.cff` in repo; bio.tools entry registered; cross-link PRs opened to the cblaster and antiSMASH READMEs at preprint time.
- **Adoption signal (bonus, not a target):** bioconda install count and GitHub stars as ambient evidence of usefulness beyond the demonstration case.

### Technical Success

- **Reproducibility contract:** a **Zenodo-archived Docker image** bundles the full dependency closure plus a frozen local BLAST DB snapshot, and reproduces the published *ebo* FCERs (equivalence per NFR1–NFR2). Every FCER carries dependency versions **and HMM-DB checksums** (not just version strings). `pip`/`conda` are best-effort; remote-BLAST mode is documented as explicitly non-reproducible.
- **Dependency-churn resilience:** CI runs against at least the current and previous antiSMASH and cblaster releases; Renovate/Dependabot opens PRs on upstream releases; parser breakage fails loudly; a public compatibility matrix is maintained in the README.
- **Predictor robustness:** the SignalP 5 / DeepSig / Phobius fallback chain works from day one, and v1 ships a **predictor-concordance / sensitivity analysis** so enrichment is reported under each predictor, not just the default.
- **Statistical correctness:** binomial + label-shuffling permutation baselines both produce BH- and Bonferroni-corrected outputs against a paralog-collapsed (mmseqs2) per-genome ORF null, with GC%/gene-length covariates reported per record.

### Measurable Outcomes

- The **92-genome *ebo* corpus runs end-to-end** as both validation suite and demonstration case; the **wall-clock budget and minimum hardware spec are documented and measured at release** (no pre-committed target number).
- **Cross-machine recapitulation passes:** the *ebo* corpus run on two distinct host operating systems yields identical significance verdicts and effect directions, with numeric values within the published tolerance (NFR1–NFR4).
- **v1 exit gate:** recapitulation passes and the FCER schema is frozen at `1.0`.
- FCER schema is versioned (`schema_version`), with a JSON Schema shipped in-repo and validated in CI.
- **Predictor concordance across the SignalP-class chain is reported descriptively** as a robustness figure (enrichment under each predictor), with **no pass/fail threshold** — a stability bar can be set later once benchmarked.

## Product Scope

Phases follow the product brief: **v1** (tool + method preprint), **v1.5** (applications paper), **v2** (hosted webapp + phylogeny), and beyond. The full v1 feature set, development sequence, and exit gate are in *Project Scoping & Phased Development*.

### v1 — Tool and Method Preprint

cblaster + antiSMASH 7 orchestration with full parameter pass-through (version-pinned); YAML run-config with flag override; feature panel of SignalP + TMHMM + Pfam-A `hmmscan` with fallback chain; enrichment harness (binomial + permutation baselines, BH/Bonferroni, paralog-collapsed null, GC/length covariates); versioned FCER artifact (per-(genome × location) + cross-genome aggregate, JSON Schema); run ledger with resume and per-genome failure tolerance; headless CLI and local GUI (run composer, results browser, provenance inspector); Docker-canonical install + `install-flanders.sh` bootstrap (pip/bioconda as expert paths); CI compatibility matrix; citability, discoverability, and documentation deliverables; the 92-genome *ebo* reference corpus runnable end to end.

### v1.5 — Applications Paper

A second, contrasting demonstration (lanthipeptides in *Streptomyces*, NRPS in *Pseudomonas*, or similar). Same FLANDERS, different biology — a citation pair with the v1 method paper.

### v2 — Hosted Webapp + Phylogeny

Run-from-UI behind the existing composer (job runner, progress, cancellation); hosted deployment of the same SPA + FastAPI with shareable result URLs (citation flywheel); GUI hardening for non-coder users (CORS, port conflicts, corporate-AV friction, accessibility); CORASON-style phylogeny-anchored analysis via the `--tree` hook; feature-panel plug-ins via `--features` (InterProScan, EffectorP, defense-finder, MIBiG similarity); phylogenetic-signal tests (Pagel's λ, Blomberg's K).

### Beyond v2

The FCER schema and enrichment harness generalize past BGCs — operon analysis, defense-system islands, CRISPR cassettes, plasmid cargo; harness factored as an importable Python sub-package; FCER ↔ MIBiG identifier alignment.

## User Journeys

### Journey 1 — Kevin, the author-runner (primary happy path)

**Opening scene.** Kevin has 92 cyanobacterial genomes and a hypothesis about the *ebo* gene family. In the old world this means a week of glue: run cblaster, parse flanks, feed antiSMASH, hand-roll SignalP/TMHMM loops, then write yet another enrichment script whose statistics Kevin doesn't fully trust.

**Rising action.** Instead Kevin opens `flanders gui` and composes the run — query family, genome set, flank window, feature panel, and the handful of cblaster and antiSMASH parameters that matter — without looking up a single dependency flag. The GUI writes the run-config and hands back the command; `flanders run -c ebo-run.yaml` orchestrates discovery, flank extraction, annotation, the feature panel, and the enrichment harness (binomial + permutation, BH/Bonferroni, paralog-collapsed null), recording each genome's progress in the run ledger. When an NCBI timeout fails one genome, the run logs it and moves on; when the machine is interrupted mid-run, the run resumes where it stopped.

**Climax.** It emits **FCERs** — per-(genome × location) records plus a cross-genome aggregate — each carrying effect sizes, corrected p-values, and GC%/gene-length covariates against an explicit null. The join step that used to live in Kevin's notebook is gone.

**Resolution.** Back in the GUI, Kevin browses the enrichment table and synteny view and re-runs *light* analytics (different background, different correction) without re-running the heavy pipeline. Exploring results this way is where the paper's questions come from; the FCERs become its figures.

*Reveals capabilities:* GUI run composition; single-invocation orchestration; full parameter pass-through; run ledger with resume and per-genome failure tolerance; pluggable feature panel; enrichment harness with covariate reporting; versioned FCER emission; local GUI with light-analytics re-run.

### Journey 2 — The reviewer (the differentiator journey / edge case: independent verification)

**Opening scene.** A bioRxiv reviewer reads the *ebo* enrichment claims and is skeptical — is this real, or an artifact of paralog inflation or a poorly-matched background?

**Rising action.** They pull the **Zenodo-archived Docker image** cited by DOI and load the published FCERs. They don't need to re-run cblaster or antiSMASH — the saved artifact carries every parameter and the background distribution, and the provenance inspector shows exactly what produced each record.

**Climax.** They swap the statistical test (binomial → permutation), change the multiple-testing correction, and re-run the enrichment harness *against the saved FCER*. The signal holds. There was no "FLANDERS magic" to take on faith.

**Resolution.** They can also fully reproduce the pipeline from the captured parameters if they want. Their review says "verified independently."

*Reveals capabilities:* reproducibility contract (Docker + frozen DB + versioned deps/checksums); provenance inspection and config export; harness that re-runs against a saved FCER with swapped test/correction/background; parameter capture enabling full pipeline re-run.

### Journey 3 — The pipeline integrator (API/headless consumer)

**Opening scene.** A bioinformatician in another lab wants FLANDERS enrichment as one stage in a larger Snakemake/Nextflow workflow across many query families — no interactive UI, fully headless.

**Rising action.** They drop `flanders run …` into a rule, point it at their genome DB, and consume the FCER **JSON** programmatically downstream. Exit codes and loud-on-breakage failures let the DAG fail cleanly rather than silently producing garbage.

**Climax.** The versioned FCER schema (`schema_version`, JSON Schema in repo) means their parsing code doesn't break when they upgrade FLANDERS.

**Resolution.** FLANDERS is just another well-behaved pipeline stage; they never touch the GUI.

*Reveals capabilities:* headless CLI with scriptable exit codes; machine-consumable JSON; schema versioning + stability contract; loud failure on parser breakage.

### Journey 4 — The maintainer keeping pace with upstream churn (operations / failure-recovery)

**Opening scene.** antiSMASH ships a point release; its JSON schema shifts subtly. Historically this is where a solo-authored academic tool silently rots.

**Rising action.** Renovate/Dependabot opens a PR on the upstream bump. CI — which runs against *multiple* upstream antiSMASH and cblaster releases — flags the parser breakage loudly instead of emitting subtly-wrong FCERs.

**Climax.** Kevin patches the adapter, the compatibility matrix in the README updates, and a new semver release is tagged and Zenodo-archived with a fresh DOI.

**Resolution.** Users on older releases aren't stranded (versioned FCER schema); users on the new one get a documented compat status. The bus-factor risk is bounded by keeping the code small and the failure loud.

*Reveals capabilities:* CI matrix against multiple upstream versions; Renovate/Dependabot integration; loud-failure parser contracts; public compatibility matrix; semver + Zenodo release automation.

### Journey Requirements Summary

The journeys collectively demand these capability areas:
- **Orchestration core:** single-invocation run wrapping cblaster + antiSMASH with full parameter pass-through and capture.
- **Feature panel:** pluggable per-ORF analyzers (SignalP/TMHMM/Pfam-A) with fallback chain.
- **Enrichment harness:** multiple tests + corrections against an explicit, swappable, paralog-collapsed null; re-runnable against a saved FCER.
- **FCER artifact:** versioned schema, JSON + CSV, covariate + provenance (versions/checksums/parameters/citation) metadata.
- **Interfaces:** headless scriptable CLI *and* localhost GUI (run composition, results table, synteny, provenance inspection, light-analytics re-run) on one backend.
- **Run resilience:** ledger-tracked tasks, resume after interruption, per-genome failure tolerance with explicit warnings.
- **Reproducibility & distribution:** Docker-canonical image + frozen DB, Zenodo/DOI archival, bootstrap installer.
- **Maintenance surface:** CI compat matrix, upstream-bump automation, loud failure, public compat matrix.

*(v2 designed-for actor, no v1 journey: the non-coding microbial ecologist using the hosted webapp — served by the same SPA + FastAPI without a rewrite.)*

## Domain-Specific Requirements

*Domain: scientific / bioinformatics (microbial natural-products genomics). Not a regulated/compliance domain — no statutory certification applies. The binding constraints are scientific-method rigor, reproducibility, dependency provenance, and third-party software licensing.*

### Reproducibility & Provenance

- **Canonical reproducibility target is a Zenodo-archived Docker image** bundling the full dependency closure plus a **frozen local BLAST DB snapshot**; it must reproduce the published *ebo* FCERs with identical enrichment verdicts and numeric values within the published tolerance (NFR1–NFR2).
- Every FCER records the **full provenance block**: FLANDERS version, cblaster/antiSMASH/HMMER/mmseqs2 versions, **HMM-DB checksums** (not just version strings — antiSMASH HMM databases re-version without git tag changes), all pass-through parameters, and the citation string.
- **`pip`/`conda` installs are best-effort** and may diverge as upstream HMM databases re-version; **remote-BLAST mode (live NCBI nr) is documented as explicitly non-reproducible** and excluded from the reproducibility contract.

### Statistical Validity (validation methodology + accuracy)

- Enrichment must be defensible against the three standard attacks: **paralog inflation** (mitigated by mmseqs2 paralog-collapsed nulls at a documented identity threshold), **gene-length / GC bias** (mitigated by per-record covariate reporting for flank vs background), and **Pfam-domain non-independence / background-choice sensitivity** (mitigated by shipping a label-shuffling permutation test as a secondary non-parametric baseline).
- Multiple-testing correction (**BH + Bonferroni**) is first-class output, never a footnote.
- Methodology **pre-reviewed by ≥1 external statistician** before preprint submission.

### Peer-Review Readiness

- Every enrichment claim must be **independently re-runnable by a reviewer** against the saved FCER with a swapped test, correction, or background — without re-running the heavy pipeline.
- **Predictor concordance** across the SignalP-class chain reported descriptively so claims are shown under each predictor, not just the default.

### Third-Party Licensing Constraints

- **SignalP 6 *and* TMHMM 2.0c are both DTU-licensed and redistribution-restricted** — neither may be bundled in the Docker image or conda recipe. This is a hard constraint, not a preference.
- Mitigated architecturally by the **SignalP 5 / DeepSig / Phobius fallback chain**, shipped from day one and retained regardless of any DTU academic-use clarification. The concordance analysis turns the fallback chain from a liability into a reported strength.
- **Pfam-A / HMMER** carries no such restriction (HMMER is already a transitive antiSMASH dependency); Pfam-A adds essentially no install or licensing cost.

### Computational Requirements

- The heavy pipeline (cblaster BLAST + antiSMASH annotation) is resource-intensive; **local-BLAST mode against a frozen DB** is the reproducible path and drives the minimum-hardware spec.
- The GUI performs only **light analytics**, run-config composition, and provenance inspection — it can never trigger a heavy run (FR60).
- Wall-clock budget and minimum hardware spec for the 92-genome corpus are **documented and measured at release** (per the deferred benchmark decision; NFR11).

### Dependency-Churn Risk (domain-specific integration)

- antiSMASH and cblaster **move fast and their JSON schemas are not fully stable across point releases**. Parser adapters must **fail loudly** on schema drift rather than emit subtly-wrong FCERs.
- CI runs against **at least the current and previous antiSMASH/cblaster releases**; Renovate/Dependabot tracks upstream bumps; a public **compatibility matrix** is maintained.
- **bioconda is mandatory for community uptake** in this niche even though Docker is canonical — but the antiSMASH + cblaster recipe solve is fragile (biopython/diamond pin conflicts; BiG-SCAPE precedent), so a **pinned `env.yml` ships** and conda is documented as expert-mode.

## Innovation & Novel Patterns

### Detected Innovation Areas

**Primary claim — orchestration.** The innovation FLANDERS stakes is *compositional*, not algorithmic: taking "this protein family across this clade" from query to a single analyzable artifact in one invocation, with cblaster and antiSMASH 7 driven as first-class pass-through dependencies rather than forked or reimplemented. No component of the stack is new; the assembled path through it is. This is explicitly **not** a claim to novel statistics — FLANDERS uses standard tests, and inventing one is out of scope.

**Secondary claim — the shareable, self-describing artifact.** The FCER is designed so an analysis can travel: its creator hands it to a collaborator or reviewer who holds the same FLANDERS container, and that recipient can reach an independent verdict. Version control is native to the artifact rather than a convention layered on top — `schema_version`, dependency versions, HMM-DB checksums, and every pass-through parameter ride inside the record.

**Supporting pattern — artifact-as-standard.** Naming, versioning, and semver-tracking a scientific output record, with a JSON Schema in-repo validated in CI, is uncommon discipline in academic bioinformatics tooling. It is what converts "here are my results" into "here is a record with a stability contract."

**Why now.** antiSMASH 7 (2023) ships stable JSON and a Python API; cblaster exposes a clean API; MIBiG 4 and antiSMASH-DB v4 finally ground the "what counts as a known BGC" denominator. The orchestration claim was not available to make before roughly 2023.

**Honest boundary.** FLANDERS introduces no new discovery capability, no new prediction model, and no new statistical method. The innovation is composition plus provenance discipline — and stating that plainly is itself the move that de-risks the preprint, because it refuses an attack surface rather than inviting one.

### Market Context & Competitive Landscape

Positioning here is derived **from first principles rather than from a prior-art survey** — a deliberate choice to reason about what the layer *should* be before absorbing what exists. The reasoned conclusion: the adjacent tools each answer a different question. BiG-SCAPE clusters BGCs across genomes. CORASON anchors neighborhoods to a phylogeny (a v2 hook target, not a v1 competitor). EvoMining looks for evolutionary signatures. gecco and DeepBGC predict BGCs from sequence — a different layer entirely. cblaster and antiSMASH are dependencies, not rivals, which makes the relationship *coopetition*: the cblaster team is the party best positioned to absorb this layer themselves.

Because the positioning is first-principles, the possibility that comparable prior art exists is an open risk rather than a settled question — addressed below.

### Validation Approach

**The orchestration claim is validated by cross-machine recapitulation.** The concrete test: build the Docker image, install it on a second machine running a different OS, re-run the 92-genome *ebo* corpus, and confirm the FCERs agree — identical enrichment verdicts, with numeric values within the published tolerance (NFR1–NFR2). This is the single test that exercises the whole claim at once: if the orchestration is genuinely disciplined and the provenance block genuinely complete, the artifact survives the move; if either is sloppy, it won't.

**The share-and-recapitulate loop is validated by exercising it.** Creator → recipient holding the same container → independent verdict from the FCER and its provenance block. The cross-machine test above is the first instance of this with the author on both ends; a collaborator-run instance is the stronger version.

**Statistical methodology is validated separately.** Pre-review by ≥1 external statistician before preprint submission is a distinct exercise from the portability test — it attacks paralog inflation, gene-length/GC bias, and background-choice sensitivity, not reproducibility. The two must not be conflated or collapsed into one reviewer.

**Predictor robustness is reported, not gated.** Concordance across the SignalP-class fallback chain is a descriptive robustness figure with no pass/fail threshold in v1.

### Risk Mitigation

- **Artifact insufficiency (low expected).** No part of the enrichment recompute is expected to be too heavy to re-run from a saved FCER. If a case proves otherwise, the pipeline **fails loudly**, records the limitation explicitly, and the fix is deferred to a later version. v1 makes **no commitment** to embedding the full background distribution inside the FCER.
- **Unsurveyed prior art.** First-principles positioning means a reviewer may name precedent the PRD never considered. Mitigation: a prior-art sweep before preprint submission — better found by the author than by a reviewer.
- **cblaster absorption.** Proximity and maintainer attention favor them. Mitigation: position as the orchestration-and-provenance layer rather than a discovery tool, plus pre-publication outreach to convert "could absorb" into "endorses."
- **Framing.** The Executive Summary leads with orchestration, reordering the brief's "built for the reviewer" emphasis; the reviewer-rerun story is the second-order claim. Revisit the balance before the preprint abstract is written.

## CLI Tool Specific Requirements

### Project-Type Overview

FLANDERS is a **scriptable-primary CLI** with an interactive adjunct. The headless path (`flanders run`) is the contract that matters: it must behave as a well-mannered pipeline stage — deterministic, exit-code-correct, machine-readable output, no interactive prompts, no TTY assumptions. The GUI (`flanders gui`) is a second entry point onto the same backend, not a second product. Its purpose is to make cblaster and antiSMASH **invisible infrastructure**: a user composes, inspects, and re-analyzes runs through FLANDERS without ever learning a dependency's command-line interface.

Per CSV guidance for this project type, `visual_design`, `ux_principles`, and `touch_interactions` are out of scope; `seo_strategy` is inapplicable to a localhost-only server.

### Technical Architecture Considerations

**Language and runtime.** Python, **3.11 minimum floor** (3.12 likely by release). The dependency stack — cblaster, antiSMASH 7, HMMER, mmseqs2 — sets the real constraint; FLANDERS's own code is thin by design. The CLI is built on a **completion-capable framework**; the specific choice belongs to architecture, but the requirement is that shell completion be generated rather than hand-maintained.

**Two front doors, one backend.** CLI and GUI both call the same orchestration layer. The GUI reaches it through localhost FastAPI, which keeps a single internal boundary rather than two public contracts requiring independent stability guarantees.

### Command Structure

- `flanders run` — the heavy pipeline: discovery → flank extraction → annotation → feature panel → enrichment → FCER emission. Headless, non-interactive, scriptable. **The only entry point that launches heavy compute.**
- `flanders gui` — starts localhost FastAPI and serves the pre-built SPA. Configurable port, localhost-only binding. Three responsibilities: **compose** a run-config, **browse** results, **inspect** provenance.
- **Light-analytics re-run** against a saved FCER (swap test, correction, or background) is a first-class CLI verb *and* available in the GUI — the reviewer path must never require a browser.
- Every run terminates with the **"If you used FLANDERS, cite: …"** line on stderr, so it never contaminates piped stdout.

### Config Schema

**A YAML run-config is the primary input; CLI flags override individual keys.** This is a reproducibility decision as much as an ergonomics one: the config file is a single shareable, archivable, diffable object that seeds the FCER provenance block.

```yaml
query: ebo_family.fasta
genomes: genomes.txt
flank_orfs: 4
features: [signalp, tmhmm, pfam]
cblaster:
  max_distance: 20000
  min_identity: 30
antismash:
  taxon: bacteria
  genefinding-tool: prodigal
```

**Pass-through routing:** named config sections per dependency, with `--cblaster-*` / `--antismash-*` prefixed flags for inline override.

Derived requirements:

1. **Precedence is explicit, documented, and deterministic:** CLI flag > config file > FLANDERS default.
2. **The FCER records the effective merged configuration**, not the config file as written. Because flags override, the file alone does not describe what ran; recording it would produce a provenance block that passes inspection while being wrong.
3. **Dependency parameters pass through without semantic validation** but are recorded verbatim. FLANDERS does not enumerate or mirror upstream flags. When a dependency rejects its arguments, FLANDERS **fails loudly and attributably**, identifying which config section produced the bad argument.

### GUI Parameter Composer

The GUI is a form over the run-config schema. A user configures query, genome set, flank window, feature panel, and dependency parameters without hand-writing YAML or knowing any dependency flag name; the GUI then **writes the config file and presents the exact command to run it**. Composition is a UI act; execution remains a CLI act. This delivers the native-app experience at minimal architectural cost — composition is stateless, so no job runner, progress streaming, cancellation, or crash recovery is required in v1.

**Dependency parameter rendering — curated subset plus escape hatch.** Real form fields for the parameters actually tuned in practice (cblaster: minimum identity, maximum distance, hits per gene, coverage; antiSMASH: taxon, gene-finding tool, detection strictness), plus a free-form key–value block for all other parameters, passed through opaquely.

1. **The curated parameter list is a documented, versioned artifact** with an explicit policy that it may lag upstream. Lag is not a defect; the escape hatch guarantees no parameter is ever unreachable, so FLANDERS never has to chase upstream flag additions to remain functional.
2. **Escape-hatch parameters receive exactly the validation CLI pass-through receives** — opaque in, recorded verbatim, loud and attributable failure on rejection. The UI must not imply a validation guarantee it does not provide.
3. **A GUI-composed config is identical in effect to a hand-written one.** No GUI-only parameters, no GUI-only defaults, no hidden state. This is a **testable invariant**: CI verifies that equivalent GUI-composed and hand-written configs produce identical FCERs, preventing the composer from becoming an unreproducible side channel.

### GUI Provenance Inspector

Given a saved FCER, the GUI renders the effective merged configuration, dependency versions, and HMM-DB checksums that produced it, and can **export that provenance back as a runnable config file**. Any published result can therefore be re-composed into an executable configuration: *result → exact config that produced it → a run anyone can execute.* This is the reviewer's first move when auditing a claim.

### Output Formats

CSV **and** JSON per FCER, plus the cross-genome aggregate. `schema_version` on every record; JSON Schema shipped in-repo and validated in CI. The provenance block carries FLANDERS version, dependency versions, HMM-DB checksums, the effective merged config, and the citation string. stdout stays machine-clean; progress, warnings, and the citation line go to stderr.

### Scripting Support

- **Exit codes are a contract.** Distinct, documented codes separate success, bad configuration, dependency failure, and parser/schema drift, so a Snakemake or Nextflow DAG fails cleanly rather than proceeding over subtly wrong output.
- **Fail loudly on parser breakage.** Never emit a partially populated FCER when an upstream JSON schema has drifted.
- **No interactive prompts and no TTY requirement** on any `flanders run` path.
- **Shell completion for bash and zsh**, generated by the CLI framework.

### Installation Methods

The Docker image is canonical and cross-platform (Linux / macOS / WSL). `install-flanders.sh` detects the platform, installs Docker if absent, pulls the image, and places a `flanders` shim on PATH. pip and bioconda are expert-mode paths with a pinned `env.yml`. Pre-built SPA assets ship in the wheel — **end users never run `npm`**.

### API Surface

**Internal only for v1.** The CLI and GUI are the supported surfaces; `flanders` is not a documented importable library and carries no API stability guarantee. The importable-harness sub-package remains a Beyond-v2 item. v1 therefore holds exactly one public stability contract — the FCER schema.

### Code Examples & Documentation

Read-the-Docs site with quickstart; Jupyter tutorial notebook on the 92-genome *ebo* corpus shipped in `/docs`. With no public Python API, examples are CLI invocations, GUI-composed configs, and FCER consumption in pandas — the realistic downstream usage.

### Browser & Performance Considerations (GUI)

Current evergreen Chrome, Firefox, and Safari; no legacy-browser support. **Accessibility is deliberately minimal in v1** given the author-and-peers audience; the hardening pass (CORS, port conflicts, corporate-AV friction, accessibility) is a stated v2 prerequisite tied to the non-coder audience.

**Invariant:** the GUI performs light analytics, config composition, and provenance inspection only; **it has no code path that initiates the heavy pipeline.** The v1 hook for v2's run-from-UI is that the composer already produces the exact config a job runner would consume — v2 adds execution behind the composer rather than rewriting it.

### Migration Guide

**Not applicable.** Greenfield rebuild with zero existing users; the 2021 implementation in `archive/` is reference-only.

### Deferred to Architecture

Frontend framework (SvelteKit vs React+Vite), synteny visualization library (clinker vs pyGenomeViz vs GenomeView), and CLI framework. All are implementation choices with no requirements impact; `bmad-create-architecture` owns them.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**Approach: build-first, exploration-led.** v1 is developed to completion through interactive, UI-led exploration; research and the preprint follow as a distinct phase using the finished tool. This inverts the usual paper-driven tool sequence: rather than building only what a pre-specified analysis needs, the tool is built to the author's satisfaction and the analysis questions emerge from using it. The GUI therefore serves double duty during development — it is a v1 deliverable *and* the author's primary instrument for discovering what the paper should ask.

**Resource requirements:** solo author (bus factor explicitly accepted for v1). Skills span Python orchestration, bioinformatics dependency management, statistics, containerization, and a browser SPA frontend. No timeline commitment.

### v1 Development Sequence

1. **Build** — develop all of v1, UI-led. The FCER schema and fixture FCERs are established early so the results browser and provenance inspector can be built and explored before the full pipeline runs end to end.
2. **Research and write** — use the finished v1 to run the *ebo* analysis and author the method preprint.

**Proposed v1 exit gate:** v1 is complete when (a) the cross-machine recapitulation test passes on the 92-genome *ebo* corpus and (b) the FCER schema is frozen at `1.0`. This gives "done" an objective floor without imposing a timeline.

### v1 Feature Set

**Core user journeys supported:** all four — author-runner (J1), reviewer verification (J2), pipeline integrator (J3), maintainer upstream-churn response (J4).

**Must-have capabilities (all of v1; the preprint waits for the complete set):**

- cblaster + antiSMASH 7 orchestration, full parameter pass-through, version-pinned
- YAML run-config with flag override; effective merged config recorded in every FCER
- Run ledger: resume after interruption; per-genome failures recorded, warned, and skipped
- Feature panel: SignalP + TMHMM + Pfam-A `hmmscan`, with SignalP 5 / DeepSig / Phobius fallback chain and predictor-concordance reporting
- Enrichment harness: binomial + label-shuffling permutation baselines; BH + Bonferroni; mmseqs2 paralog-collapsed null; GC% and gene-length covariates
- FCER: per-(genome × location) + cross-genome aggregate, CSV + JSON, `schema_version`, JSON Schema in-repo
- Light-analytics re-run against a saved FCER (CLI verb and GUI)
- GUI: parameter composer (curated subset + escape hatch), results browser with synteny view, provenance inspector with config export
- Headless CLI with exit-code contract and bash/zsh completion
- Docker image (canonical) + `install-flanders.sh`; pip and bioconda with pinned `env.yml`
- CI against multiple upstream antiSMASH/cblaster releases; Renovate/Dependabot; public compatibility matrix
- `--tree <newick>` and `--features` plug-in hooks for v2
- Reference dataset: 92-genome *ebo* corpus runnable end to end
- Documentation: Read-the-Docs quickstart; Jupyter tutorial on the *ebo* corpus
- Citability: Zenodo per-version DOIs, `CITATION.cff`, citation line in CLI and FCER, bio.tools registration, cross-link PRs to cblaster and antiSMASH

**Nice-to-have:** none designated within v1.

### Post-v1 Features

v1.5, v2, and beyond are defined in *Product Scope*.

### Risk Mitigation Strategy

**Technical risks.** Upstream schema drift in antiSMASH/cblaster — mitigated by version pinning, loud-failure parsers, and the CI matrix. DTU licensing on SignalP 6 and TMHMM 2.0c — mitigated by the fallback chain shipped regardless of DTU's answer. The bioconda solve is the highest-uncertainty build item (BiG-SCAPE precedent) — mitigated by the pinned `env.yml` and Docker as the canonical path. UI-first development risks building views over an unsettled data model — mitigated by fixing the FCER schema early and developing against fixtures.

**Market risks.** cblaster team absorbing the layer — mitigated by orchestration-and-provenance positioning and pre-publication outreach. Unsurveyed prior art — mitigated by a prior-art sweep during the research phase, before submission.

**Resource risks.** Solo author, no timeline, and an open-ended exploration phase together raise the risk that v1 never reaches release. Mitigated by the objective exit gate above, a deliberately small codebase, and the versioned FCER schema so early adopters are never stranded.

## Functional Requirements

This list is the capability contract: a capability not listed here is not part of v1.

### Run Configuration

- FR1: A user can define a complete analysis — query, genome set, flank window, feature panel, statistical options, and dependency parameters — in a single run-configuration file.
- FR2: A user can override any individual configuration value at invocation time without editing the configuration file.
- FR3: A user can supply parameters for cblaster and antiSMASH, scoped to the dependency they apply to, including parameters FLANDERS does not itself recognize.
- FR4: A user can specify the query as protein sequences or as sequence accessions.
- FR5: A user can specify the genome set to search, either as a local sequence database or via remote search.
- FR6: A user can specify the size of the flanking window around each discovered cluster.
- FR7: A user can select which per-ORF feature analyzers run.
- FR8: The system resolves configuration with a documented, deterministic precedence: invocation override, then configuration file, then FLANDERS default.

### Cluster Discovery & Flank Annotation

- FR9: The system can discover homologous gene clusters across the genome set by invoking cblaster with the user's parameters.
- FR10: The system can extract the flanking ORFs and flanking nucleotide regions for each discovered cluster.
- FR11: The system can annotate biosynthetic gene clusters in flanking regions by invoking antiSMASH 7 with the user's parameters.
- FR12: The system can predict signal peptides for each flanking ORF.
- FR13: The system can predict transmembrane topology for each flanking ORF.
- FR14: The system can identify Pfam-A protein domains in each flanking ORF.
- FR15: The system can substitute an alternative signal-peptide predictor when the preferred predictor is unavailable, and records which predictor was used.
- FR16: The system can run each available signal-peptide-class predictor on the same corpus and report enrichment results under each.
- FR17: A developer can add a new per-ORF feature analyzer through a defined extension interface without modifying the core pipeline.

### Enrichment Analysis

- FR18: The system can test each flank feature for enrichment relative to a per-genome ORF background.
- FR19: The system can construct the background with paralogs collapsed at a documented, reported identity threshold.
- FR20: The system can compute enrichment with a binomial test and with a label-shuffling permutation test.
- FR21: The system can report effect sizes alongside raw p-values and multiple-testing-corrected p-values (Benjamini–Hochberg and Bonferroni).
- FR22: The system can report GC% and gene-length distributions for flanking ORFs versus background ORFs for every analysis.
- FR23: A developer can add a new statistical test through a defined extension interface.

### Results Artifact & Provenance

- FR24: The system produces an FCER for each (genome × location) and a cross-genome aggregate FCER for each run.
- FR25: The system emits every FCER in both tabular (CSV) and structured (JSON) form.
- FR26: Every FCER declares its schema version, and the schema is published as a machine-readable specification.
- FR27: Every FCER records the effective merged configuration that produced it — not the configuration file as written.
- FR28: Every FCER records the FLANDERS version, every dependency version, and checksums of every reference database used.
- FR29: Every FCER records which analyzers and statistical tests produced its values, including any fallback substitutions.
- FR30: Every FCER embeds the FLANDERS citation.
- FR31: Every FCER produced in a non-reproducible mode (remote search against live databases) is marked as non-reproducible.
- FR32: The system structures per-genome results so they can be joined to an external phylogeny by genome accession.
- FR33: A user can supply a phylogenetic tree with a run; the system validates it and retains it alongside the results.

### Re-analysis & Verification

- FR34: A user can re-run enrichment against a saved FCER with a different statistical test, multiple-testing correction, or background, without re-running discovery, annotation, or feature prediction.
- FR35: A user can perform re-analysis from the command line, without the GUI.
- FR36: A user can export the provenance of any saved FCER as a runnable configuration file.
- FR37: A recipient holding the same FLANDERS release can reproduce a shared FCER's enrichment verdicts from its provenance alone.

### Command-Line Operation

- FR38: A user can run the complete pipeline in a single invocation with no interactive input.
- FR39: The system signals outcome through distinct, documented exit codes for success, completion with warnings, invalid configuration, dependency failure, and upstream output-format drift.
- FR40: The system halts with an attributable error — identifying the dependency and configuration section involved — when a dependency rejects its parameters.
- FR41: The system refuses to emit results when it cannot fully parse a dependency's output, and halts the entire run rather than continuing past the affected tag.
- FR42: The system keeps result output separate from progress, warnings, and the citation notice.
- FR43: A user can tab-complete FLANDERS commands and options in bash and zsh.
- FR44: The system prints the FLANDERS citation at the end of every run.

### Run Resilience & Task Ledger

- FR45: The system records the state of every long-running or externally mediated task in a persistent run ledger, keyed by an indexable tag such as genome accession.
- FR46: The run ledger is created automatically when an installation is first initialized, with no user setup.
- FR47: A user can resume an interrupted run without repeating tasks the ledger records as complete.
- FR48: When a task fails for one tag, the system records the failure in the ledger and continues the run for the remaining tags.
- FR49: Every run's output report and aggregate FCER list each failed or excluded tag with its reason.
- FR50: A user can view the per-tag status of any run: pending, complete, or failed.

### Interactive GUI

- FR51: A user can launch a local GUI that is reachable only from their own machine, on a configurable port.
- FR52: A user can compose a complete run configuration in the GUI and save it as a configuration file.
- FR53: The GUI presents commonly tuned dependency parameters as named fields and accepts any other dependency parameter as free-form input.
- FR54: The GUI presents the exact command that runs a composed configuration.
- FR55: A GUI-composed configuration is indistinguishable in effect from an equivalent hand-written configuration.
- FR56: A user can browse FCER results in tabular form in the GUI.
- FR57: A user can view the genomic neighborhood of a discovered cluster and its flanks.
- FR58: A user can inspect the full provenance of any FCER in the GUI.
- FR59: A user can perform re-analysis (FR34) from the GUI.
- FR60: The GUI cannot initiate a heavy pipeline run.

### Installation & Distribution

- FR61: A user can install FLANDERS on Linux, macOS, or WSL by running a single bootstrap script that provisions the container runtime if absent and places a `flanders` command on their PATH.
- FR62: A user can obtain FLANDERS as a single container image containing every dependency except redistribution-restricted predictors.
- FR63: An expert user can install FLANDERS via pip or bioconda, using a published pinned environment specification.
- FR64: A user can install redistribution-restricted predictors separately and have FLANDERS detect and use them.
- FR65: A user can run the 92-genome *ebo* reference analysis end to end as a validation of their installation.

### Release, Compatibility & Citation

- FR66: Each FLANDERS release is versioned and archived with its own persistent, citable identifier.
- FR67: A user can determine which upstream cblaster and antiSMASH releases a given FLANDERS release supports.
- FR68: A maintainer is notified automatically when an upstream dependency publishes a new release.
- FR69: A user can access a quickstart guide and a worked tutorial on the *ebo* reference corpus.

### Decided Constraints for Architecture

- The run ledger (FR45–FR50) is a table in a local SQLite database created during container initialization.
- Failed tasks are not retried automatically; a per-tag failure is recorded and the run continues (FR48). Resume (FR47) is the recovery path.
- Per-tag failures are recoverable; upstream output-format drift (FR41) is not, and halts the run.
- Input formats are greenfield only; no legacy FLANDERS 2021 or MultiGeneBlast input formats are accepted.

## Non-Functional Requirements

### Reproducibility & Determinism

- NFR1: Two runs of the same FLANDERS release, with the same effective configuration and the same reference-database snapshot, produce identical significance verdicts and effect directions for every feature test on any supported platform.
- NFR2: Across such runs, p-values and effect sizes agree within a numeric tolerance that is defined and published with each release.
- NFR3: Every stochastic procedure, including permutation tests, uses a seed recorded in the FCER; re-running with that seed on the same platform yields identical values.
- NFR4: Cross-machine equivalence (NFR1–NFR2) is verified on the full 92-genome *ebo* corpus across at least two distinct host operating systems before v1 release.
- NFR5: Equivalence holds between native x86-64 execution and emulated execution on Apple Silicon.
- NFR6: No run marked reproducible depends on mutable external state; any run that does is flagged per FR31.

### Reliability

- NFR7: The run ledger survives abrupt termination (process kill, container stop, power loss); on resume, no task recorded complete is lost, and only tasks in flight at termination are repeated.
- NFR8: A task is recorded complete only after all of its outputs are fully written; partial outputs are never treated as complete.
- NFR9: Zero silent exclusions — every genome absent from an analysis appears in the failed/excluded list (FR49) with its reason.

### Performance & Scale

- NFR10: v1 supports runs of up to ~1,000 genomes on a documented minimum hardware specification without architectural change.
- NFR11: Pipeline wall-clock and re-analysis times are measured and published at release for the *ebo* corpus and a ~1,000-genome benchmark; v1 sets no latency targets.
- NFR12: FLANDERS's own orchestration and ledger overhead stays under 5% of total run wall-clock on the *ebo* corpus.

### Portability

- NFR13: Supported hosts are Linux (x86-64), macOS (Intel natively; Apple Silicon via emulation), and Windows via WSL2, served by a single x86-64 container image.
- NFR14: Apple Silicon performance under emulation is documented, not targeted.
- NFR15: On a clean supported host, the bootstrap installer reaches a working `flanders` command with no manual steps beyond OS-level permission prompts.

### Integration

- NFR16: Each release declares the exact cblaster and antiSMASH versions it is validated against; CI verifies at least the current and previous release of each.
- NFR17: Upstream output-format drift is detected in CI against recorded fixture outputs for every supported upstream version.
- NFR18: Within a major FCER schema version, changes are additive only; a consumer written against `1.0` reads any `1.x` FCER without modification.
- NFR19: FLANDERS runs safely as a workflow step: it requires no TTY, never prompts, and writes only within its configured output and state directories.

### Security

- NFR20: The GUI server binds to the loopback interface only; v1 provides no option to expose it on other interfaces. Local execution only — no shared-server or multi-user deployment in v1.
- NFR21: FLANDERS sends no telemetry; network access occurs only for user-requested remote search, sequence and reference-database retrieval, and container pulls.
- NFR22: No redistribution-restricted predictor binary appears in any distributed artifact; CI verifies this by inspecting the published image.

### Maintainability

- NFR23: The statistics harness has at least 90% line coverage, and every test and correction is validated against an independent reference implementation on known inputs.
- NFR24: Every FCER schema change ships with a semver-correct version bump and a changelog entry describing its effect on consumers.
