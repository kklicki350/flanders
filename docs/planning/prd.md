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
lastEdited: '2026-11-25'
editHistory:
  - date: '2026-11-06'
    workflow: bmad-edit-prd
    source: _bmad-output/planning-artifacts/ux-design-specification.md (PRD Changes Pending) + author decisions
    changes: >-
      GUI launches runs (FR60 rewritten; FR70); run history and comparison (FR71-72);
      workspace model (FR77-78, Workspace subsection, NFR25-26); run bundles with raw
      outputs + recorded invocations, import/export, snapshot replay (FR73-76, FR79-80);
      fresh-snapshot search as default with accession.version manifest and rebuild
      (FR5, FR31 revised, FR81-83, NFR6, NFR27); Django + htmx replace FastAPI + SPA;
      stage reuse deferred post-v1.
  - date: '2026-11-06'
    workflow: bmad-validate-prd fixes
    source: _bmad-output/planning-artifacts/validation-report-2026-11-06.md
    changes: >-
      Reference data moves out of the image into the workspace, downloaded and checksum-verified
      (FR62 revised, FR84 added; reproducibility contract = image + reference-data archive).
      antiSMASH 8 is the primary target with 7 as previous release (architecture step 3).
      Named new CLI verbs (reanalyze, bundle, replay, snapshot, workspace reindex); FR46 workspace
      wording; FR17/23/33/53/81/82 sharpened; NFR5/7/10/12 verification methods; NFR11 records the
      no-latency-target decision; FR ID-order note; body date updated.
  - date: '2026-11-25'
    workflow: bmad-edit-prd
    source: docs/planning/architecture.md (Validation Issues Addressed) + author decisions 2026-11-18..22
    changes: >-
      Cross-genome aggregate FCER removed (FR24); failed/excluded tags in a run report (FR49).
      Re-analysis is a stats-only replay from stored enrich inputs or a bundle, creating a variant
      run (FR34-35, FR37, FR59, FR72); slim bundles keep enrich inputs and captured inputs (FR73).
      Docker-only install, pip/bioconda deferred (FR63 removed). Only DeepSig ships; installer-guided
      predictor setup and tools commands (FR15, FR64, FR85). New FR86 input capture, FR87 --out,
      FR88 self-update. Journeys 1-3, scope, CLI, workspace, install, domain, innovation, NFR11,
      NFR22 aligned.
---

# Product Requirements Document - FLANDERS

**Author:** Kevin Klicki
**Date:** 2026-05-02 · **Updated:** 2026-11-25

## Executive Summary

FLANDERS-2026 is a **reproducibility-and-statistics layer for biosynthetic-gene-cluster (BGC) neighborhood analysis** — a decade-later rebuild by the original author that fixes what modern dependencies broke and what the original FLANDERS got wrong about statistics. It orchestrates **cblaster** (cluster discovery + flank extraction) and **antiSMASH** (BGC annotation; 8 primary, 7 supported) as first-class, version-pinned dependencies with full parameter pass-through, then layers on a **pluggable per-ORF feature panel** (SignalP, TMHMM, Pfam-A `hmmscan`) and a **statistical enrichment harness** that reports effect sizes with multiple-testing-corrected p-values against an explicit, reviewable null. The pipeline emits one named, versioned artifact — the **FLANDERS Cluster Enrichment Record (FCER)** — per (genome × location), replacing the bespoke glue every lab currently rewrites to join per-tool outputs into something analyzable.

The target problem is **orchestration with statistical rigor**, not discovery or annotation: no tool today takes "this protein family across this clade" and returns a single defensible artifact answering *which flank features are enriched, with what effect size, at what corrected significance, against what background distribution*. v1 serves the author and similar-skilled bioinformaticians through a Docker-canonical CLI and a local GUI. The GUI composes and launches runs, browses and compares results, imports runs shared by others, and inspects provenance, so cblaster and antiSMASH become invisible infrastructure rather than tools the user must learn; it is a local web application built so it becomes the v2 hosted webapp without a rewrite. All user state lives in a host-side workspace, and searches default to a fresh, manifest-pinned snapshot of current NCBI data, so results are both current and reproducible. Development is build-first: v1 is completed through UI-led exploration, then used to produce the primary research deliverable — a **bioRxiv method paper** demonstrated on the *ebo* gene family across 92 cyanobacterial genomes.

### What Makes This Special

**The orchestration is the product.** FLANDERS takes "this protein family across this clade" from query to a single analyzable artifact in one invocation, driving cblaster and antiSMASH as pass-through dependencies rather than forking or reimplementing them. No component is new; the disciplined, assembled path through them is (see *Innovation & Novel Patterns*).

The second-order claim: FLANDERS is **built for the reviewer**, not just the runner. Pass-through architecture means any result can be re-verified by re-running cblaster or antiSMASH directly with the captured parameters, and a reviewer holding the shared run bundle can swap the statistical test, the correction, or the background distribution and replay only the statistics as a new variant run, without touching the heavy pipeline — there is no "FLANDERS magic" to take on faith. Two further commitments distinguish it: **statistics are a first-class output** (effect sizes + BH/Bonferroni-corrected p-values against an explicit, documented null, with GC% and gene-length covariate reporting in every record) rather than counts in a footnote; and **one versioned artifact** (`schema_version`, JSON Schema shipped in repo, semver-tracked) removes the join step that lives in everyone's notebook.

The core insight is timing: the underlying tools only recently became programmatically composable — antiSMASH 7 (2023) and 8 (2025) ship stable JSON and a Python API, cblaster exposes a clean API, and MIBiG 4 + antiSMASH-DB v4 finally ground the "what counts as a known BGC" denominator. The missing piece was never another discovery or annotation tool; it was disciplined orchestration plus a defensible enrichment artifact. Nothing in the adjacent landscape — BiG-SCAPE (cross-genome clustering), CORASON (phylogeny-anchored neighborhoods), EvoMining (evolutionary signatures), gecco/DeepBGC (ML prediction) — occupies the gap between discovery and downstream comparative analysis.

## Project Classification

- **Project type:** CLI tool (primary), with developer-tool and web-app secondary traits
- **Domain:** Scientific / bioinformatics (microbial natural-products genomics)
- **Complexity:** Medium-high — heavy external dependency surface (cblaster, antiSMASH, HMMER, mmseqs2, DTU-licensed predictors), statistical-defensibility requirements, and a two-interface (CLI + local GUI) codebase sharing one backend
- **Project context:** Greenfield rebuild — the 2021 FLANDERS (`archive/`, ~500 LOC, broken on modern deps) is reference-only, not a template

## Success Criteria

### User Success

- A bioinformatician can take a protein-family query + a genome set and obtain a complete set of FCERs **in a single `flanders run` invocation**, with no hand-written glue between cblaster, antiSMASH, the feature panel, and the enrichment stats.
- The "aha" moment for the **runner**: the join step disappears — one versioned artifact lands ready for downstream analysis (phylogenetic comparison, hypothesis testing, manuscript figures) with no parsing project.
- The "aha" moment for the **reviewer** (the differentiator-aligned success): they can swap the statistical test, the correction, or the background distribution and replay the statistics from a *published* run bundle — getting an independent verdict on an enrichment claim without re-running the heavy pipeline or trusting any "FLANDERS magic."
- A pipeline user can drop `flanders run` into Snakemake/Nextflow and consume JSON programmatically, headless, no GUI.
- A user can configure and launch a complete run in the GUI without learning any cblaster or antiSMASH flag.
- A user can answer a heavy-parameter "what if?" by launching a variant run from the GUI and comparing it against the original.
- A recipient can load a collaborator's run bundle into their own workspace and recapitulate its results — a stats-only replay from the bundle's stored enrichment inputs, a replay from the captured discovery snapshot, or a full re-run from the manifest and recorded invocations.

### Business Success *(academic / publication impact — no commercial intent; license MIT)*

- **Primary:** a **bioRxiv preprint posted**, framed as a *method paper with cyanobacterial* ebo *case study* — broader-applicability claims deferred to a v1.5 follow-up. Produced after v1 is complete, using the finished tool (see *Project Scoping & Phased Development*).
- **Defensibility under review:** methodology pre-reviewed by **≥1 external statistician** before submission; the preprint addresses paralog inflation, gene-length/GC bias, and background-choice sensitivity proactively.
- **Citability:** every release semver-tagged and Zenodo-archived with a per-version DOI; `CITATION.cff` in repo; bio.tools entry registered; cross-link PRs opened to the cblaster and antiSMASH READMEs at preprint time.
- **Adoption signal (bonus, not a target):** container image pulls and GitHub stars as ambient evidence of usefulness beyond the demonstration case.

### Technical Success

- **Reproducibility contract:** a **Zenodo-archived Docker image** (the full software dependency closure) plus a **Zenodo-archived, checksummed reference-data set** (antiSMASH databases, Pfam-A, and the frozen *ebo* BLAST DB snapshot) together reproduce the published *ebo* FCERs (equivalence per NFR1–NFR2). Every FCER carries dependency versions **and HMM-DB checksums** (not just version strings). Day-to-day runs use **fresh-snapshot mode**: a local search DB built from current NCBI data and pinned by a manifest of `accession.version` identifiers and checksums, from which a recipient can rebuild the identical DB. Docker is the only v1 install path (pip/bioconda deferred post-v1); remote-BLAST mode is documented as discovery-not-reproducible.
- **Dependency-churn resilience:** CI runs against at least the current and previous antiSMASH and cblaster releases; Renovate/Dependabot opens PRs on upstream releases; parser breakage fails loudly; a public compatibility matrix is maintained in the README.
- **Predictor robustness:** the SignalP 6 → SignalP 5 → DeepSig → Phobius fallback chain works from day one — DeepSig ships in the image, so signal-peptide prediction works with no user-supplied predictor, and the installer guides setup of the others — and v1 ships a **predictor-concordance / sensitivity analysis** so enrichment is reported under each predictor, not just the default.
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

cblaster + antiSMASH orchestration (8 primary, 7 as previous release) with full parameter pass-through (version-pinned); YAML run-config with flag override; feature panel of SignalP + TMHMM + Pfam-A `hmmscan` with fallback chain and installer-guided setup of user-supplied predictors; enrichment harness (binomial + permutation baselines, BH/Bonferroni, paralog-collapsed null, GC/length covariates); versioned FCER artifact (per-(genome × location), JSON Schema) and run report; stats-only replay as variant runs; run inputs captured into the run folder; run ledger with resume and per-genome failure tolerance; three search modes (fresh snapshot — default — frozen local, remote) with `accession.version` pinning and manifest rebuild; host-side workspace holding all user state; run bundles for sharing (export, import, replay); headless CLI and local GUI (run composer with launch, live ledger, results browser, run history and comparison, import of shared runs, provenance inspector); Docker-only install via the `install-flanders.sh` bootstrap, with `self-update` (pip/bioconda deferred post-v1); CI compatibility matrix; citability, discoverability, and documentation deliverables; the 92-genome *ebo* reference corpus runnable end to end.

### v1.5 — Applications Paper

A second, contrasting demonstration (lanthipeptides in *Streptomyces*, NRPS in *Pseudomonas*, or similar). Same FLANDERS, different biology — a citation pair with the v1 method paper.

### v2 — Hosted Webapp + Phylogeny

Hosted deployment of the same web application with shareable result URLs (citation flywheel); stage reuse across variant runs (unchanged stages such as cblaster searches and per-ORF predictions reused, keyed by inputs, tool version, and database checksum); GUI hardening for non-coder users (CORS, port conflicts, corporate-AV friction, accessibility); CORASON-style phylogeny-anchored analysis via the `--tree` hook; feature-panel plug-ins via `--features` (InterProScan, EffectorP, defense-finder, MIBiG similarity); phylogenetic-signal tests (Pagel's λ, Blomberg's K).

### Beyond v2

The FCER schema and enrichment harness generalize past BGCs — operon analysis, defense-system islands, CRISPR cassettes, plasmid cargo; harness factored as an importable Python sub-package; FCER ↔ MIBiG identifier alignment.

## User Journeys

### Journey 1 — Kevin, the author-runner (primary happy path)

**Opening scene.** Kevin has 92 cyanobacterial genomes and a hypothesis about the *ebo* gene family. In the old world this means a week of glue: run cblaster, parse flanks, feed antiSMASH, hand-roll SignalP/TMHMM loops, then write yet another enrichment script whose statistics Kevin doesn't fully trust.

**Rising action.** Instead Kevin opens `flanders gui` and composes the run — query family, genome set (a fresh snapshot of current NCBI cyanobacterial genomes, pinned by manifest), flank window, feature panel, and the handful of cblaster and antiSMASH parameters that matter — without looking up a single dependency flag. The GUI saves the run-config into the workspace, shows the equivalent `flanders run -c ebo-run.yaml` command, and launches it as a background run. The pipeline orchestrates discovery, flank extraction, annotation, the feature panel, and the enrichment harness (binomial + permutation, BH/Bonferroni, paralog-collapsed null), recording each genome's progress in the run ledger, which the GUI displays live. When an NCBI timeout fails one genome, the run logs it and moves on; when the machine is interrupted mid-run, the next `flanders gui` start offers to resume where it stopped.

**Climax.** It emits **FCERs** — per-(genome × location) records — each carrying effect sizes, corrected p-values, and GC%/gene-length covariates against an explicit null. The join step that used to live in Kevin's notebook is gone.

**Resolution.** Back in the GUI, Kevin browses the enrichment table and synteny view and changes the statistics (different background, different correction) as a stats-only replay that skips the heavy pipeline and lands as a variant run beside the original. To test a *heavy* parameter — a wider flank window — he launches a variant run from the current one and, when it finishes, compares the two to see which features gained or lost significance. Every run stays in the workspace's run history. Exploring results this way is where the paper's questions come from; the FCERs become its figures, and a run bundle is what he sends a collaborator.

*Reveals capabilities:* GUI run composition and launch; fresh-snapshot search with manifest; single-invocation orchestration; full parameter pass-through; run ledger with resume and per-genome failure tolerance, shown live in the GUI; pluggable feature panel; enrichment harness with covariate reporting; versioned FCER emission; stats-only replay; variant runs, run history, and comparison; run bundle export.

### Journey 2 — The reviewer (the differentiator journey / edge case: independent verification)

**Opening scene.** A bioRxiv reviewer reads the *ebo* enrichment claims and is skeptical — is this real, or an artifact of paralog inflation or a poorly-matched background?

**Rising action.** They pull the **Zenodo-archived Docker image** cited by DOI and open the published run bundle with `flanders gui --open`, which imports it into their own workspace as a read-only run. They don't need to re-run cblaster or antiSMASH — the bundle carries the captured inputs, every parameter, every recorded dependency invocation, the stored enrichment inputs, and (in a full bundle) the raw dependency outputs, and the provenance inspector shows exactly what produced each record and flags any difference between the bundle's FLANDERS version or database snapshot and their own.

**Climax.** They swap the statistical test (binomial → permutation), change the multiple-testing correction, and launch a stats-only replay from the bundle's stored enrichment inputs; it lands as a variant run they compare against the imported original. The signal holds. There was no "FLANDERS magic" to take on faith.

**Resolution.** If they want more, they can replay the pipeline from the bundle's captured discovery snapshot, or rebuild the identical search database from the manifest and re-run everything from the recorded invocations. Their review says "verified independently."

*Reveals capabilities:* reproducibility contract (Docker image + checksummed reference data + versioned deps/checksums); run-bundle import with schema and version checks; provenance inspection and config export; stats-only replay from a full or slim bundle with swapped test/correction/background, as a comparable variant run; recorded invocations, snapshot replay, and manifest rebuild enabling full pipeline re-run.

### Journey 3 — The pipeline integrator (API/headless consumer)

**Opening scene.** A bioinformatician in another lab wants FLANDERS enrichment as one stage in a larger Snakemake/Nextflow workflow across many query families — no interactive UI, fully headless.

**Rising action.** They drop `flanders run … --out results/` into a rule, point it at their genome DB, and consume the FCER **JSON** that lands in the rule's output directory. Exit codes and loud-on-breakage failures let the DAG fail cleanly rather than silently producing garbage.

**Climax.** The versioned FCER schema (`schema_version`, JSON Schema in repo) means their parsing code doesn't break when they upgrade FLANDERS.

**Resolution.** FLANDERS is just another well-behaved pipeline stage; they never touch the GUI.

*Reveals capabilities:* headless CLI with scriptable exit codes; `--out` output directory; machine-consumable JSON; schema versioning + stability contract; loud failure on parser breakage.

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
- **Enrichment harness:** multiple tests + corrections against an explicit, swappable, paralog-collapsed null; statistics replayable from stored enrichment inputs as variant runs.
- **FCER artifact:** versioned schema, JSON + CSV, covariate + provenance (versions/checksums/parameters/citation) metadata.
- **Interfaces:** headless scriptable CLI *and* localhost GUI (run composition and launch, live ledger, results table, synteny, run history and comparison, import of shared runs, provenance inspection, stats-only replay, predictor setup) on one backend.
- **Run resilience:** ledger-tracked tasks, resume after interruption, per-genome failure tolerance with explicit warnings.
- **Workspace & sharing:** all user state in one host-side workspace; run bundles exported, imported, and replayed by recipients.
- **Search reproducibility:** fresh-snapshot default with `accession.version` manifest and rebuild; remote mode recorded and replayable after discovery.
- **Reproducibility & distribution:** Docker-only image + checksummed reference-data set, Zenodo/DOI archival of both, bootstrap installer with guided predictor setup, self-update.
- **Maintenance surface:** CI compat matrix, upstream-bump automation, loud failure, public compat matrix.

*(v2 designed-for actor, no v1 journey: the non-coding microbial ecologist using the hosted webapp — served by the same web application without a rewrite.)*

## Domain-Specific Requirements

*Domain: scientific / bioinformatics (microbial natural-products genomics). Not a regulated/compliance domain — no statutory certification applies. The binding constraints are scientific-method rigor, reproducibility, dependency provenance, and third-party software licensing.*

### Reproducibility & Provenance

- **Canonical reproducibility target is a Zenodo-archived Docker image** bundling the full software dependency closure, **plus a Zenodo-archived reference-data set** (antiSMASH databases, Pfam-A, frozen *ebo* BLAST DB snapshot) downloaded once into the workspace and verified by checksum; together they must reproduce the published *ebo* FCERs with identical enrichment verdicts and numeric values within the published tolerance (NFR1–NFR2).
- Every FCER records the **full provenance block**: FLANDERS version, cblaster/antiSMASH/HMMER/mmseqs2 versions, **HMM-DB checksums** (not just version strings — antiSMASH HMM databases re-version without git tag changes), all pass-through parameters, and the citation string.
- **Docker is the only v1 install path.** pip/bioconda installs are deferred post-v1 because they cannot pin the HMM databases and tool closure the reproducibility contract depends on.
- **Three search modes, with different reproducibility guarantees:**
  - **Fresh snapshot (default).** FLANDERS builds a local search DB from the current NCBI release for the genome set or taxon and records a manifest: every genome's `accession.version`, retrieval date, NCBI release metadata, and a content checksum over the retrieved sequences. NCBI versions are immutable (a sequence change increments the version and older versions stay retrievable), so a recipient can rebuild the identical DB from the manifest. NCBI occasionally suppresses records; a rebuild reports any version it cannot fetch rather than silently building a smaller DB.
  - **Frozen local.** A pre-built DB snapshot with a fixed checksum, such as the one in the Zenodo-archived image that underwrites the published *ebo* FCERs.
  - **Remote (live NCBI nr).** Current but **discovery-not-reproducible**: NCBI's remote service searches only the current database, which changes continuously. The FCER records the search date, NCBI DB metadata, and search-space size (needed to interpret E-values); every hit is pinned by `accession.version`; and a run bundle's captured discovery snapshot lets a recipient replay everything downstream of discovery.

### Statistical Validity (validation methodology + accuracy)

- Enrichment must be defensible against the three standard attacks: **paralog inflation** (mitigated by mmseqs2 paralog-collapsed nulls at a documented identity threshold), **gene-length / GC bias** (mitigated by per-record covariate reporting for flank vs background), and **Pfam-domain non-independence / background-choice sensitivity** (mitigated by shipping a label-shuffling permutation test as a secondary non-parametric baseline).
- Multiple-testing correction (**BH + Bonferroni**) is first-class output, never a footnote.
- Methodology **pre-reviewed by ≥1 external statistician** before preprint submission.

### Peer-Review Readiness

- Every enrichment claim must be **independently re-runnable by a reviewer** from the shared run bundle (full or slim) with a swapped test, correction, or background — a stats-only replay that does not re-run the heavy pipeline.
- **Predictor concordance** across the SignalP-class chain reported descriptively so claims are shown under each predictor, not just the default.

### Third-Party Licensing Constraints

- **SignalP 6, SignalP 5 and TMHMM 2.0c (DTU-licensed) and Phobius (registration-gated) are redistribution-restricted** — none may be bundled in the Docker image. This is a hard constraint, not a preference.
- Mitigated by shipping **DeepSig** (redistributable) in the image, so signal-peptide prediction works on a fresh install, and by **installer-guided setup**: for each restricted predictor the installer explains the license terms, points to the request page, and installs the archive the user downloads. The fallback chain (SignalP 6 → SignalP 5 → DeepSig → Phobius) uses whichever are installed, and the concordance analysis turns it from a liability into a reported strength.
- **Pfam-A / HMMER** carries no such restriction (HMMER is already a transitive antiSMASH dependency); Pfam-A adds essentially no install or licensing cost.

### Computational Requirements

- The heavy pipeline (cblaster BLAST + antiSMASH annotation) is resource-intensive; **local search (fresh snapshot or frozen DB)** is the reproducible path and drives the minimum-hardware spec, including the disk needed to hold snapshot DBs in the workspace.
- **At most one heavy run executes at a time**, launched from either the CLI or the GUI (FR60); both reach the pipeline through the same orchestration entry point.
- Wall-clock budget and minimum hardware spec for the 92-genome corpus are **documented and measured at release** (per the deferred benchmark decision; NFR11).

### Dependency-Churn Risk (domain-specific integration)

- antiSMASH and cblaster **move fast and their JSON schemas are not fully stable across point releases**. Parser adapters must **fail loudly** on schema drift rather than emit subtly-wrong FCERs.
- CI runs against **at least the current and previous antiSMASH/cblaster releases**; Renovate/Dependabot tracks upstream bumps; a public **compatibility matrix** is maintained.
- **pip/bioconda distribution is deferred post-v1.** The product brief treats bioconda as mandatory for community uptake; v1 departs from that deliberately, because the antiSMASH + cblaster recipe solve is fragile (biopython/diamond pin conflicts; BiG-SCAPE precedent) and a second install path would split the reproducibility contract.

## Innovation & Novel Patterns

### Detected Innovation Areas

**Primary claim — orchestration.** The innovation FLANDERS stakes is *compositional*, not algorithmic: taking "this protein family across this clade" from query to a single analyzable artifact in one invocation, with cblaster and antiSMASH driven as first-class pass-through dependencies rather than forked or reimplemented. No component of the stack is new; the assembled path through it is. This is explicitly **not** a claim to novel statistics — FLANDERS uses standard tests, and inventing one is out of scope.

**Secondary claim — the shareable, self-describing artifact.** The FCER, carried in a run bundle, is designed so an analysis can travel: its creator hands the bundle to a collaborator or reviewer who holds the same FLANDERS container, and that recipient can reach an independent verdict. Version control is native to the artifact rather than a convention layered on top — `schema_version`, dependency versions, HMM-DB checksums, and every pass-through parameter ride inside the record.

**Supporting pattern — artifact-as-standard.** Naming, versioning, and semver-tracking a scientific output record, with a JSON Schema in-repo validated in CI, is uncommon discipline in academic bioinformatics tooling. It is what converts "here are my results" into "here is a record with a stability contract."

**Why now.** antiSMASH 7 (2023) and 8 (2025) ship stable JSON and a Python API; cblaster exposes a clean API; MIBiG 4 and antiSMASH-DB v4 finally ground the "what counts as a known BGC" denominator. The orchestration claim was not available to make before roughly 2023.

**Honest boundary.** FLANDERS introduces no new discovery capability, no new prediction model, and no new statistical method. The innovation is composition plus provenance discipline — and stating that plainly is itself the move that de-risks the preprint, because it refuses an attack surface rather than inviting one.

### Market Context & Competitive Landscape

Positioning here is derived **from first principles rather than from a prior-art survey** — a deliberate choice to reason about what the layer *should* be before absorbing what exists. The reasoned conclusion: the adjacent tools each answer a different question. BiG-SCAPE clusters BGCs across genomes. CORASON anchors neighborhoods to a phylogeny (a v2 hook target, not a v1 competitor). EvoMining looks for evolutionary signatures. gecco and DeepBGC predict BGCs from sequence — a different layer entirely. cblaster and antiSMASH are dependencies, not rivals, which makes the relationship *coopetition*: the cblaster team is the party best positioned to absorb this layer themselves.

Because the positioning is first-principles, the possibility that comparable prior art exists is an open risk rather than a settled question — addressed below.

### Validation Approach

**The orchestration claim is validated by cross-machine recapitulation.** The concrete test: build the Docker image, install it on a second machine running a different OS, re-run the 92-genome *ebo* corpus, and confirm the FCERs agree — identical enrichment verdicts, with numeric values within the published tolerance (NFR1–NFR2). This is the single test that exercises the whole claim at once: if the orchestration is genuinely disciplined and the provenance block genuinely complete, the artifact survives the move; if either is sloppy, it won't.

**The share-and-recapitulate loop is validated by exercising it.** Creator → recipient holding the same container → independent verdict from the run bundle and its provenance block. The cross-machine test above is the first instance of this with the author on both ends; a collaborator-run instance is the stronger version.

**Statistical methodology is validated separately.** Pre-review by ≥1 external statistician before preprint submission is a distinct exercise from the portability test — it attacks paralog inflation, gene-length/GC bias, and background-choice sensitivity, not reproducibility. The two must not be conflated or collapsed into one reviewer.

**Predictor robustness is reported, not gated.** Concordance across the SignalP-class fallback chain is a descriptive robustness figure with no pass/fail threshold in v1.

### Risk Mitigation

- **Artifact insufficiency (resolved).** An FCER alone cannot support statistics re-analysis without embedding the per-genome background ORF tables. v1 instead keeps those enrichment-stage inputs in every run and every bundle (slim bundles included), so statistics changes are a stats-only replay and FCER 1.0 stays a results record.
- **Unsurveyed prior art.** First-principles positioning means a reviewer may name precedent the PRD never considered. Mitigation: a prior-art sweep before preprint submission — better found by the author than by a reviewer.
- **cblaster absorption.** Proximity and maintainer attention favor them. Mitigation: position as the orchestration-and-provenance layer rather than a discovery tool, plus pre-publication outreach to convert "could absorb" into "endorses."
- **Framing.** The Executive Summary leads with orchestration, reordering the brief's "built for the reviewer" emphasis; the reviewer-rerun story is the second-order claim. Revisit the balance before the preprint abstract is written.

## CLI Tool Specific Requirements

### Project-Type Overview

FLANDERS is a **scriptable-primary CLI** with an interactive adjunct. The headless path (`flanders run`) is the contract that matters: it must behave as a well-mannered pipeline stage — deterministic, exit-code-correct, machine-readable output, no interactive prompts, no TTY assumptions. The GUI (`flanders gui`) is a second entry point onto the same backend, not a second product. Its purpose is to make cblaster and antiSMASH **invisible infrastructure**: a user composes, inspects, and re-analyzes runs through FLANDERS without ever learning a dependency's command-line interface.

Per CSV guidance for this project type, `visual_design`, `ux_principles`, and `touch_interactions` are out of scope; `seo_strategy` is inapplicable to a localhost-only server.

### Technical Architecture Considerations

**Language and runtime.** Python, **3.11 minimum floor** (3.12 likely by release). The dependency stack — cblaster, antiSMASH, HMMER, mmseqs2 — sets the real constraint; FLANDERS's own code is thin by design. The CLI is built on a **completion-capable framework**; the specific choice belongs to architecture, but the requirement is that shell completion be generated rather than hand-maintained.

**Two front doors, one backend.** CLI and GUI both call the same orchestration layer. The GUI is a server-rendered local web application in the same Python codebase, which keeps a single internal boundary rather than two public contracts requiring independent stability guarantees.

### Command Structure

- `flanders run` — the heavy pipeline: discovery → flank extraction → annotation → feature panel → enrichment → FCER emission. Headless, non-interactive, scriptable. **The headless entry point to heavy compute**; the GUI's Launch calls the same orchestration entry point. `--out <dir>` also copies the final FCERs and run report to a directory of the caller's choosing (FR87).
- `flanders gui` — starts the local web application and opens the browser. Configurable port, localhost-only binding. Responsibilities: **compose and launch** runs, show the live **ledger**, **browse** results, keep **run history** and **compare** runs, **import** shared runs, **inspect** provenance. `flanders gui --open <fcer-or-bundle>` imports a shared FCER or run bundle into the workspace and opens it. Stopping `flanders gui` stops a run it launched; the ledger resumes it.
- `flanders reanalyze` — stats-only replay: re-runs only the enrichment stage with a different test, correction, background, or statistical parameter, from a run's stored enrichment inputs or an imported bundle, and records the result as a new variant run; also available in the GUI; the reviewer path never requires a browser (FR34–FR35).
- `flanders bundle export` / `flanders bundle import` — write a run as a self-contained bundle (`--slim` omits raw dependency outputs but keeps everything needed for stats-only replay and re-execution) and import a shared FCER or bundle into the workspace, so sharing never requires the GUI (FR73–FR75).
- `flanders replay` — re-execute a bundled run from its captured discovery snapshot, without searching again (FR80).
- `flanders snapshot build` / `flanders snapshot rebuild` — build a fresh-snapshot search DB from current NCBI data with its manifest, or rebuild an identical DB from a run's manifest (FR81–FR82).
- `flanders workspace reindex` — rebuild the workspace index from the files it contains (FR78).
- `flanders reference fetch` / `flanders reference verify` — download the reference data pinned to this release into the workspace and verify its checksums (FR84).
- `flanders tools add <archive>` / `flanders tools status` / `flanders tools help <name>` — install a user-downloaded restricted predictor, show which predictors are installed, and explain how to obtain one (FR64, FR85).
- `flanders self-update` — pull the latest image and fetch any reference data the new release pins (FR88).

*Command names are working names; the CLI framework choice in architecture may adjust spelling but not the set of verbs.*
- Every run terminates with the **"If you used FLANDERS, cite: …"** line on stderr, so it never contaminates piped stdout.

### Config Schema

**A YAML run-config is the primary input; CLI flags override individual keys.** This is a reproducibility decision as much as an ergonomics one: the config file is a single shareable, archivable, diffable object that seeds the FCER provenance block.

```yaml
query: ebo_family.fasta
genomes: genomes.txt
search: snapshot        # snapshot (default) | local | remote
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

The GUI is a form over the run-config schema. A user configures query, genome set, flank window, feature panel, and dependency parameters without hand-writing YAML or knowing any dependency flag name; the GUI then **saves the config file into the workspace, presents the exact command that runs it, and can launch it** as a background run. At most one run executes at a time; it can be cancelled, and its progress is read from the run ledger, which already provides crash recovery and resume (FR45–FR50). A composed config is always saved before launch, so a GUI-launched run is exactly the run its saved config describes.

**Dependency parameter rendering — curated subset plus escape hatch.** Real form fields for the parameters actually tuned in practice (cblaster: minimum identity, maximum distance, hits per gene, coverage; antiSMASH: taxon, gene-finding tool, detection strictness), plus a free-form key–value block for all other parameters, passed through opaquely.

1. **The curated parameter list is a documented, versioned artifact** with an explicit policy that it may lag upstream. Lag is not a defect; the escape hatch guarantees no parameter is ever unreachable, so FLANDERS never has to chase upstream flag additions to remain functional.
2. **Escape-hatch parameters receive exactly the validation CLI pass-through receives** — opaque in, recorded verbatim, loud and attributable failure on rejection. The UI must not imply a validation guarantee it does not provide.
3. **A GUI-composed config is identical in effect to a hand-written one.** No GUI-only parameters, no GUI-only defaults, no hidden state. This is a **testable invariant**: CI verifies that equivalent GUI-composed and hand-written configs produce identical FCERs, preventing the composer from becoming an unreproducible side channel.

### GUI Provenance Inspector

Given a saved FCER, the GUI renders the effective merged configuration, dependency versions, and HMM-DB checksums that produced it, and can **export that provenance back as a runnable config file**. Any published result can therefore be re-composed into an executable configuration: *result → exact config that produced it → a run anyone can execute.* This is the reviewer's first move when auditing a claim.

### Workspace

All user state lives in one host-side **workspace** directory (default `~/flanders/`), mounted into the container by the `flanders` shim: run configs and drafts, per-run captured inputs and outputs (including raw dependency outputs and recorded invocations), FCERs, fresh-snapshot search DBs with their manifests, the checksummed reference data, imported runs, and a local database that indexes all of it (run ledger, run history, FCER index). The container image holds only code and tool environments and is identical for every user, so upgrading or replacing it never touches user state.

- **The index is rebuildable.** The database is derived from the workspace's files; deleting it and re-scanning reconstructs run history. FCERs and run bundles — not the database — are the portable artifacts.
- **Run bundles** contain the effective config, the captured inputs, all FCERs, the run report (every failed or excluded tag with its reason), every recorded dependency invocation, the search manifest or discovery snapshot, the stored enrichment-stage inputs, and — by default — the raw cblaster and antiSMASH outputs. A slim option omits only the raw outputs, so a slim bundle still supports stats-only replay and re-execution of every recorded invocation.
- **Imported runs are read-only** and labeled with their origin; they appear in run history beside local runs.

### Output Formats

CSV **and** JSON per FCER; each run also writes a run report listing every failed or excluded tag with its reason. `schema_version` on every record; JSON Schema shipped in-repo and validated in CI. The provenance block carries FLANDERS version, dependency versions, HMM-DB checksums, the effective merged config, and the citation string. stdout stays machine-clean; progress, warnings, and the citation line go to stderr.

### Scripting Support

- **Exit codes are a contract.** Distinct, documented codes separate success, bad configuration, dependency failure, and parser/schema drift, so a Snakemake or Nextflow DAG fails cleanly rather than proceeding over subtly wrong output.
- **Fail loudly on parser breakage.** Never emit a partially populated FCER when an upstream JSON schema has drifted.
- **No interactive prompts and no TTY requirement** on any `flanders run` path.
- **Shell completion for bash and zsh**, generated by the CLI framework.

### Installation Methods

The Docker image is the only v1 install path and is cross-platform (Linux / macOS / WSL); pip and bioconda are deferred post-v1. `install-flanders.sh` detects the platform, installs Docker if absent, pulls the image, and places a `flanders` shim on PATH. It then offers guided setup of each redistribution-restricted predictor — stating the license terms, opening the request page, asking for the path to the downloaded archive, verifying and installing it into the workspace, and running a test prediction. Every predictor can be skipped and added later with `flanders tools add`. Compiled GUI stylesheets ship in the image — **end users never run `npm`**. The shim mounts the workspace read-write and the current directory plus the folders of any input paths read-only, binds the GUI port to the loopback interface, and handles `flanders self-update`, so users never type Docker flags.

### API Surface

**Internal only for v1.** The CLI and GUI are the supported surfaces; `flanders` is not a documented importable library and carries no API stability guarantee. The importable-harness sub-package remains a Beyond-v2 item. v1 therefore holds exactly one public stability contract — the FCER schema.

### Code Examples & Documentation

Read-the-Docs site with quickstart; Jupyter tutorial notebook on the 92-genome *ebo* corpus shipped in `/docs`. With no public Python API, examples are CLI invocations, GUI-composed configs, and FCER consumption in pandas — the realistic downstream usage.

### Browser & Performance Considerations (GUI)

Current evergreen Chrome, Firefox, and Safari; no legacy-browser support. **Accessibility is deliberately minimal in v1** given the author-and-peers audience; the hardening pass (CORS, port conflicts, corporate-AV friction, accessibility) is a stated v2 prerequisite tied to the non-coder audience.

**Invariant:** the GUI and the CLI launch heavy runs through **the same orchestration entry point, from a saved config**. The GUI has no execution path of its own, no GUI-only parameters, and no state outside the workspace; a GUI-launched run and `flanders run -c` on the same config are the same run.

### Migration Guide

**Not applicable.** Greenfield rebuild with zero existing users; the 2021 implementation in `archive/` is reference-only.

### Deferred to Architecture

Synteny visualization approach (the UX specification recommends a project-owned server-rendered SVG; clinker, pyGenomeViz, or GenomeView remain candidates for figure export), CLI framework, background-run supervision, and NCBI snapshot retrieval mechanics. All are implementation choices with no requirements impact; `bmad-create-architecture` owns them. The GUI stack is decided (see *Decided Constraints for Architecture*).

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**Approach: build-first, exploration-led.** v1 is developed to completion through interactive, UI-led exploration; research and the preprint follow as a distinct phase using the finished tool. This inverts the usual paper-driven tool sequence: rather than building only what a pre-specified analysis needs, the tool is built to the author's satisfaction and the analysis questions emerge from using it. The GUI therefore serves double duty during development — it is a v1 deliverable *and* the author's primary instrument for discovering what the paper should ask.

**Resource requirements:** solo author (bus factor explicitly accepted for v1). Skills span Python orchestration, bioinformatics dependency management, statistics, containerization, and a server-rendered web frontend. No timeline commitment.

### v1 Development Sequence

1. **Build** — develop all of v1, UI-led. The FCER schema and fixture FCERs are established early so the results browser and provenance inspector can be built and explored before the full pipeline runs end to end.
2. **Research and write** — use the finished v1 to run the *ebo* analysis and author the method preprint.

**Proposed v1 exit gate:** v1 is complete when (a) the cross-machine recapitulation test passes on the 92-genome *ebo* corpus and (b) the FCER schema is frozen at `1.0`. This gives "done" an objective floor without imposing a timeline.

### v1 Feature Set

**Core user journeys supported:** all four — author-runner (J1), reviewer verification (J2), pipeline integrator (J3), maintainer upstream-churn response (J4).

**Must-have capabilities (all of v1; the preprint waits for the complete set):**

- cblaster + antiSMASH orchestration (antiSMASH 8 primary, 7 as previous release), full parameter pass-through, version-pinned
- YAML run-config with flag override; effective merged config recorded in every FCER; run inputs captured into the run folder; `--out` for workflow managers
- Run ledger: resume after interruption; per-genome failures recorded, warned, and skipped
- Feature panel: SignalP + TMHMM + Pfam-A `hmmscan`, with SignalP 6 → SignalP 5 → DeepSig → Phobius fallback chain (DeepSig in the image; the others user-supplied via installer-guided setup or `flanders tools add`) and predictor-concordance reporting
- Enrichment harness: binomial + label-shuffling permutation baselines; BH + Bonferroni; mmseqs2 paralog-collapsed null; GC% and gene-length covariates
- FCER: per-(genome × location), CSV + JSON, `schema_version`, JSON Schema in-repo; run report of failed and excluded tags
- Stats-only replay (CLI verb and GUI): change the test, correction, or background and re-run only enrichment as a variant run, from own runs or full or slim bundles
- Search modes: fresh snapshot (default) with `accession.version` manifest and rebuild, frozen local DB, remote with discovery capture
- Workspace holding all user state, with a rebuildable index; run bundles (export, import, snapshot replay)
- GUI: parameter composer (curated subset + escape hatch) with launch, live ledger, results browser with synteny view, run history and comparison, import of shared runs, provenance inspector with config export
- Headless CLI with exit-code contract and bash/zsh completion
- Docker image (the only v1 install path) + `install-flanders.sh` with guided predictor setup; `flanders self-update`
- CI against multiple upstream antiSMASH/cblaster releases; Renovate/Dependabot; public compatibility matrix
- `--tree <newick>` and `--features` plug-in hooks for v2
- Reference dataset: 92-genome *ebo* corpus runnable end to end
- Documentation: Read-the-Docs quickstart; Jupyter tutorial on the *ebo* corpus
- Citability: Zenodo per-version DOIs, `CITATION.cff`, citation line in CLI and FCER, bio.tools registration, cross-link PRs to cblaster and antiSMASH

**Nice-to-have:** none designated within v1.

### Post-v1 Features

v1.5, v2, and beyond are defined in *Product Scope*. Deferred from v1 during architecture validation (2026-11), not yet scheduled: pip/bioconda installation; cross-genome / pan-genome aggregate statistics.

### Risk Mitigation Strategy

**Technical risks.** Upstream schema drift in antiSMASH/cblaster — mitigated by version pinning, loud-failure parsers, and the CI matrix. Licensing on SignalP 6/5, TMHMM 2.0c, and Phobius — mitigated by shipping DeepSig in the image, the fallback chain, and installer-guided setup of user-supplied predictors. The bioconda solve (BiG-SCAPE precedent) is avoided in v1 by making Docker the only install path. UI-first development risks building views over an unsettled data model — mitigated by fixing the FCER schema early and developing against fixtures.

**Market risks.** cblaster team absorbing the layer — mitigated by orchestration-and-provenance positioning and pre-publication outreach. Unsurveyed prior art — mitigated by a prior-art sweep during the research phase, before submission.

**Resource risks.** Solo author, no timeline, and an open-ended exploration phase together raise the risk that v1 never reaches release. Mitigated by the objective exit gate above, a deliberately small codebase, and the versioned FCER schema so early adopters are never stranded.

## Functional Requirements

This list is the capability contract: a capability not listed here is not part of v1.

*Requirement IDs are stable. FR70–FR84 were added on 2026-11-06 and FR85–FR88 on 2026-11-25; they appear within the subsections they belong to, so IDs are not in document order. Removed requirements keep their ID as a placeholder.*

### Run Configuration

- FR1: A user can define a complete analysis — query, genome set, flank window, feature panel, statistical options, and dependency parameters — in a single run-configuration file.
- FR2: A user can override any individual configuration value at invocation time without editing the configuration file.
- FR3: A user can supply parameters for cblaster and antiSMASH, scoped to the dependency they apply to, including parameters FLANDERS does not itself recognize.
- FR4: A user can specify the query as protein sequences or as sequence accessions.
- FR5: A user can specify the genome set to search as a fresh snapshot of current NCBI data (the default), a frozen local sequence database, or a remote search.
- FR6: A user can specify the size of the flanking window around each discovered cluster.
- FR7: A user can select which per-ORF feature analyzers run.
- FR8: The system resolves configuration with a documented, deterministic precedence: invocation override, then configuration file, then FLANDERS default.
- FR86: At run start the system copies the run's inputs (query, genome list, any local database, tree) into the run's folder in the workspace and records their checksums; a missing input path fails the run with the invalid-configuration exit code, naming the path, and never prompts. In the GUI, inputs are chosen with a file picker.

### Cluster Discovery & Flank Annotation

- FR9: The system can discover homologous gene clusters across the genome set by invoking cblaster with the user's parameters.
- FR10: The system can extract the flanking ORFs and flanking nucleotide regions for each discovered cluster.
- FR11: The system can annotate biosynthetic gene clusters in flanking regions by invoking antiSMASH with the user's parameters.
- FR12: The system can predict signal peptides for each flanking ORF.
- FR13: The system can predict transmembrane topology for each flanking ORF.
- FR14: The system can identify Pfam-A protein domains in each flanking ORF.
- FR15: The system substitutes an alternative signal-peptide predictor when the preferred one is not installed, in the order SignalP 6 → SignalP 5 → DeepSig → Phobius, using whichever are installed; it never prompts during a run, warns on stderr with the command that installs the missing predictor, and records which predictor was used.
- FR16: The system can run each available signal-peptide-class predictor on the same corpus and report enrichment results under each.
- FR17: A developer can add a new per-ORF feature analyzer through a documented extension interface without modifying the core pipeline, verified by a reference analyzer plug-in that passes CI with no core-module changes.

### Enrichment Analysis

- FR18: The system can test each flank feature for enrichment relative to a per-genome ORF background.
- FR19: The system can construct the background with paralogs collapsed at a documented, reported identity threshold.
- FR20: The system can compute enrichment with a binomial test and with a label-shuffling permutation test.
- FR21: The system can report effect sizes alongside raw p-values and multiple-testing-corrected p-values (Benjamini–Hochberg and Bonferroni).
- FR22: The system can report GC% and gene-length distributions for flanking ORFs versus background ORFs for every analysis.
- FR23: A developer can add a new statistical test through a documented extension interface, verified by a reference test plug-in that passes CI with no core-module changes.

### Results Artifact & Provenance

- FR24: The system produces one FCER for each (genome × location) in a run; v1 produces no cross-genome aggregate FCER.
- FR25: The system emits every FCER in both tabular (CSV) and structured (JSON) form.
- FR26: Every FCER declares its schema version, and the schema is published as a machine-readable specification.
- FR27: Every FCER records the effective merged configuration that produced it — not the configuration file as written.
- FR28: Every FCER records the FLANDERS version, every dependency version, and checksums of every reference database used.
- FR29: Every FCER records which analyzers and statistical tests produced its values, including any fallback substitutions.
- FR30: Every FCER embeds the FLANDERS citation.
- FR31: Every FCER produced by remote search is marked *discovery not reproducible* and records the search date, the NCBI database name and release metadata, and the search-space size (sequence count and total length).
- FR32: The system structures per-genome results so they can be joined to an external phylogeny by genome accession.
- FR33: A user can supply a phylogenetic tree (Newick) with a run; the system checks that it parses and that its tip labels match the run's genome accessions, reports unmatched tips, and retains the tree alongside the results.

### Re-analysis & Verification

- FR34: A user can change a run's statistical test, multiple-testing correction, background, or statistical parameters and re-run only the enrichment stage (a stats-only replay) from the run's stored enrichment inputs or from an imported full or slim bundle, without re-running discovery, annotation, or feature prediction; the result is recorded as a new variant run linked to the original.
- FR35: A user can perform a stats-only replay (FR34) from the command line, without the GUI.
- FR36: A user can export the provenance of any saved FCER as a runnable configuration file.
- FR37: A recipient holding the same FLANDERS release can reproduce a shared run's enrichment verdicts from its full or slim bundle.

### Command-Line Operation

- FR38: A user can run the complete pipeline in a single invocation with no interactive input.
- FR39: The system signals outcome through distinct, documented exit codes for success, completion with warnings, invalid configuration, dependency failure, and upstream output-format drift.
- FR40: The system halts with an attributable error — identifying the dependency and configuration section involved — when a dependency rejects its parameters.
- FR41: The system refuses to emit results when it cannot fully parse a dependency's output, and halts the entire run rather than continuing past the affected tag.
- FR42: The system keeps result output separate from progress, warnings, and the citation notice.
- FR43: A user can tab-complete FLANDERS commands and options in bash and zsh.
- FR44: The system prints the FLANDERS citation at the end of every run.
- FR87: A user can direct a run to copy its final FCERs and run report to a chosen output directory outside the workspace (`--out`), for workflow managers.

### Run Resilience & Task Ledger

- FR45: The system records the state of every long-running or externally mediated task in a persistent run ledger, keyed by an indexable tag such as genome accession.
- FR46: The run ledger is created automatically when a workspace is first initialized, with no user setup.
- FR47: A user can resume an interrupted run without repeating tasks the ledger records as complete.
- FR48: When a task fails for one tag, the system records the failure in the ledger and continues the run for the remaining tags.
- FR49: Every run writes a run report listing each failed or excluded tag with its reason; every bundle of the run includes it.
- FR50: A user can view the per-tag status of any run: pending, complete, or failed.

### Interactive GUI

- FR51: A user can launch a local GUI that is reachable only from their own machine, on a configurable port.
- FR52: A user can compose a complete run configuration in the GUI and save it as a configuration file.
- FR53: The GUI presents every parameter on the documented, versioned curated-parameter list as a named field and accepts any other dependency parameter as free-form input.
- FR54: The GUI presents the exact command that runs a composed configuration.
- FR55: A GUI-composed configuration is indistinguishable in effect from an equivalent hand-written configuration.
- FR56: A user can browse FCER results in tabular form in the GUI.
- FR57: A user can view the genomic neighborhood of a discovered cluster and its flanks.
- FR58: A user can inspect the full provenance of any FCER in the GUI.
- FR59: A user can launch a stats-only replay (FR34) from the GUI; the GUI never recomputes statistics in place.
- FR60: A user can launch a saved configuration as a run from the GUI and cancel it; at most one run executes at a time across the GUI and CLI, and the GUI displays the active run's per-tag ledger status (FR50) while it executes.
- FR70: Stopping the GUI stops a run it launched; on the next GUI start, the user is offered to resume that run (FR47).
- FR71: A user can browse every run in the workspace with its key parameters, status, date, and origin (local or imported).
- FR72: A user can compare any two runs — including a run and its stats-only variant — side by side or as a diff of which features gained or lost significance.

### Workspace, Sharing & Search Reproducibility

- FR73: A user can export a run as a self-contained bundle containing its effective configuration, captured inputs (FR86), all FCERs, the run report (FR49), every recorded dependency invocation, its search manifest or discovery snapshot, and its stored enrichment-stage inputs; unless the user selects a slim bundle, it also contains the raw cblaster and antiSMASH outputs. A slim bundle supports stats-only replay (FR34) and re-execution of every recorded invocation.
- FR74: A user can import a shared FCER or run bundle, from the command line, at GUI launch, or from within the GUI; an imported run is read-only and labeled with its origin.
- FR75: The system refuses to import an FCER or bundle that fails schema validation or declares an unsupported schema major version, states the reason, and loads nothing from it.
- FR76: The system warns when an imported or compared run's FLANDERS version or reference-database checksums differ from the local installation.
- FR77: All user state — configurations, drafts, run outputs, FCERs, search snapshots, imported runs, and the run ledger — lives in one user-visible workspace directory on the host that persists across container image upgrades and replacement.
- FR78: A user can rebuild the workspace index (run history, ledger summaries, FCER index) from the files the workspace contains.
- FR79: The system records every dependency invocation verbatim — tool, version, and the exact parameters passed — so each can be re-executed outside FLANDERS.
- FR80: A recipient can replay a bundled run from its captured discovery snapshot, re-executing flank extraction, annotation, feature prediction, and enrichment without searching again.
- FR81: A user can build a local search database from the current NCBI release for a genome set or taxon of up to the NFR10 scale (~1,000 genomes); the system records a manifest of every genome's `accession.version`, the retrieval date, the NCBI release metadata, and a content checksum computed over the retrieved sequences in canonical order.
- FR82: A recipient can rebuild an identical search database from a run's manifest; the system reports every `accession.version` it cannot retrieve and never builds a smaller database silently. A run whose manifest cannot be fully rebuilt remains stats-replayable from its stored enrichment inputs and is marked partially reproducible, listing the missing entries.
- FR83: Every FCER identifies each hit, ORF, and genome by its versioned accession (`accession.version`).
- FR84: A user can download the reference data pinned to their FLANDERS release (antiSMASH databases, Pfam-A, the *ebo* BLAST DB snapshot) into the workspace with one command; the system verifies every file's checksum, refuses to run against unverified reference data, and works offline once it is present.

### Installation & Distribution

- FR61: A user can install FLANDERS on Linux, macOS, or WSL by running a single bootstrap script that provisions the container runtime if absent and places a `flanders` command on their PATH.
- FR62: A user can obtain FLANDERS as a single container image containing every software dependency except redistribution-restricted predictors; reference data is obtained separately (FR84).
- FR63: *(Removed 2026-11-25 — Docker is the only v1 install path; pip/bioconda deferred post-v1.)*
- FR64: The installer offers guided setup of each redistribution-restricted predictor (SignalP 6, SignalP 5, TMHMM 2.0c, Phobius): it states the license terms and where to request the software, accepts the path to the user's downloaded archive, verifies it against the release's predictor manifest, installs it into the workspace, and confirms it with a test prediction; setup of any predictor can be skipped.
- FR85: After installation, a user can install a downloaded restricted predictor, see which predictors are installed, and get acquisition instructions for any predictor, from the command line or from a GUI Predictors page, with the same verification as FR64.
- FR88: A user can upgrade FLANDERS with one command that pulls the new release's image and fetches any reference data the new release pins differently; no other workspace content is modified.
- FR65: A user can run the 92-genome *ebo* reference analysis end to end as a validation of their installation.

### Release, Compatibility & Citation

- FR66: Each FLANDERS release is versioned and archived with its own persistent, citable identifier.
- FR67: A user can determine which upstream cblaster and antiSMASH releases a given FLANDERS release supports.
- FR68: A maintainer is notified automatically when an upstream dependency publishes a new release.
- FR69: A user can access a quickstart guide and a worked tutorial on the *ebo* reference corpus.

### Decided Constraints for Architecture

- The run ledger (FR45–FR50), run history, and FCER index are tables in a SQLite database **inside the workspace**, created automatically when the workspace is first initialized (this is the "installation is first initialized" moment of FR46). The database is an index rebuildable from workspace files (FR78).
- **GUI stack: Django with server-rendered templates and htmx** (replacing the earlier FastAPI + SPA decision); compiled CSS ships in the package and image. The same Django application becomes the v2 hosted webapp.
- The container image holds only code and tool environments; reference data lives in the workspace (`reference/`), pinned per release by version and checksum and archived on Zenodo with its own DOI (FR84); all user state is in the mounted workspace (FR77).
- **Architecture to verify:** SQLite reliability over macOS and WSL bind mounts (fallback: database in a Docker-managed volume, files in the visible workspace); image size of the tool environments; reference-data download size; disk footprint of fresh-snapshot DBs.
- **Architecture to preserve:** per-stage outputs kept in a reusable form so post-v1 stage reuse across variant runs can be added without restructuring.
- Failed tasks are not retried automatically; a per-tag failure is recorded and the run continues (FR48). Resume (FR47) is the recovery path.
- Per-tag failures are recoverable; upstream output-format drift (FR41) is not, and halts the run.
- Input formats are greenfield only; no legacy FLANDERS 2021 or MultiGeneBlast input formats are accepted.

## Non-Functional Requirements

### Reproducibility & Determinism

- NFR1: Two runs of the same FLANDERS release, with the same effective configuration and the same reference-database snapshot, produce identical significance verdicts and effect directions for every feature test on any supported platform.
- NFR2: Across such runs, p-values and effect sizes agree within a numeric tolerance that is defined and published with each release.
- NFR3: Every stochastic procedure, including permutation tests, uses a seed recorded in the FCER; re-running with that seed on the same platform yields identical values.
- NFR4: Cross-machine equivalence (NFR1–NFR2) is verified on the full 92-genome *ebo* corpus across at least two distinct host operating systems before v1 release.
- NFR5: Equivalence (NFR1–NFR2) holds between native x86-64 execution and emulated execution on Apple Silicon, verified by running the *ebo* corpus under emulation as one of the NFR4 hosts or as an additional run.
- NFR6: No run marked reproducible depends on mutable external state; any run that does is flagged per FR31. Fresh-snapshot runs qualify as reproducible because their manifest pins immutable `accession.version` records; rebuild completeness is reported per FR82.

### Reliability

- NFR7: The run ledger survives abrupt termination (process kill, container stop, power loss); on resume, no task recorded complete is lost, and only tasks in flight at termination are repeated. Verified by a kill-injection test that terminates the run during each pipeline stage and confirms correct resume.
- NFR8: A task is recorded complete only after all of its outputs are fully written; partial outputs are never treated as complete.
- NFR9: Zero silent exclusions — every genome absent from an analysis appears in the failed/excluded list (FR49) with its reason.

### Performance & Scale

- NFR10: v1 supports runs of up to 1,000 genomes on the documented minimum hardware specification, demonstrated by the 1,000-genome benchmark run (NFR11) completing successfully on that specification.
- NFR11: Pipeline wall-clock and stats-only replay times are measured and published at release for the *ebo* corpus and a ~1,000-genome benchmark; v1 sets no latency targets — including for stats-only replay — by deliberate decision (2026-11-06); measured values inform whether targets are needed later.
- NFR12: FLANDERS's own orchestration and ledger overhead stays under 5% of total run wall-clock on the *ebo* corpus, measured as total run wall-clock minus the summed ledger-recorded durations of dependency tasks.

### Portability

- NFR13: Supported hosts are Linux (x86-64), macOS (Intel natively; Apple Silicon via emulation), and Windows via WSL2, served by a single x86-64 container image.
- NFR14: Apple Silicon performance under emulation is documented, not targeted.
- NFR15: On a clean supported host, the bootstrap installer reaches a working `flanders` command with no manual steps beyond OS-level permission prompts.

### Integration

- NFR16: At v1 launch the supported antiSMASH releases are 8 (primary) and 7 (previous). Each release declares the exact cblaster and antiSMASH versions it is validated against; CI verifies at least the current and previous release of each.
- NFR17: Upstream output-format drift is detected in CI against recorded fixture outputs for every supported upstream version.
- NFR18: Within a major FCER schema version, changes are additive only; a consumer written against `1.0` reads any `1.x` FCER without modification.
- NFR19: FLANDERS runs safely as a workflow step: it requires no TTY, never prompts, and writes only within its configured workspace and output directories.

### Security

- NFR20: The GUI server binds to the loopback interface only; v1 provides no option to expose it on other interfaces. Local execution only — no shared-server or multi-user deployment in v1.
- NFR21: FLANDERS sends no telemetry; network access occurs only for user-requested remote search, sequence and reference-database retrieval, and container pulls.
- NFR22: No redistribution-restricted predictor (SignalP 6, SignalP 5, TMHMM 2.0c, Phobius) appears in any distributed artifact; CI verifies this by inspecting the published image.

### Maintainability

- NFR23: The statistics harness has at least 90% line coverage, and every test and correction is validated against an independent reference implementation on known inputs.
- NFR24: Every FCER schema change ships with a semver-correct version bump and a changelog entry describing its effect on consumers.

### Workspace Durability

- NFR25: Replacing or upgrading the container image loses no user state; verified in CI by upgrading the image over a populated fixture workspace and confirming every run, FCER, and ledger record is intact.
- NFR26: Rebuilding the index of a workspace containing up to 1,000 runs restores every run to run history with zero runs lost, verified against a generated fixture workspace.
- NFR27: A manifest rebuild (FR82) of the *ebo* fresh-snapshot DB yields a content checksum identical to the original whenever every manifest entry is retrievable (binary database files may differ, e.g. by embedded build timestamps; the content checksum is the equivalence test).
