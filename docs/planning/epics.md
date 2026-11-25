---
stepsCompleted: []
inputDocuments:
  - docs/planning/prd.md
  - docs/planning/architecture.md
  - docs/planning/ux-design-specification.md
---

# FLANDERS - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for FLANDERS, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: A user can define a complete analysis — query, genome set, flank window, feature panel, statistical options, and dependency parameters — in a single run-configuration file.
FR2: A user can override any individual configuration value at invocation time without editing the configuration file.
FR3: A user can supply parameters for cblaster and antiSMASH, scoped to the dependency they apply to, including parameters FLANDERS does not itself recognize.
FR4: A user can specify the query as protein sequences or as sequence accessions.
FR5: A user can specify the genome set to search as a fresh snapshot of current NCBI data (the default), a frozen local sequence database, or a remote search.
FR6: A user can specify the size of the flanking window around each discovered cluster.
FR7: A user can select which per-ORF feature analyzers run.
FR8: The system resolves configuration with a documented, deterministic precedence: invocation override, then configuration file, then FLANDERS default.
FR9: The system can discover homologous gene clusters across the genome set by invoking cblaster with the user's parameters.
FR10: The system can extract the flanking ORFs and flanking nucleotide regions for each discovered cluster.
FR11: The system can annotate biosynthetic gene clusters in flanking regions by invoking antiSMASH with the user's parameters.
FR12: The system can predict signal peptides for each flanking ORF.
FR13: The system can predict transmembrane topology for each flanking ORF.
FR14: The system can identify Pfam-A protein domains in each flanking ORF.
FR15: The system substitutes an alternative signal-peptide predictor when the preferred one is not installed, in the order SignalP 6 → SignalP 5 → DeepSig → Phobius, using whichever are installed; it never prompts during a run, warns on stderr with the command that installs the missing predictor, and records which predictor was used.
FR16: The system can run each available signal-peptide-class predictor on the same corpus and report enrichment results under each.
FR17: A developer can add a new per-ORF feature analyzer through a documented extension interface without modifying the core pipeline, verified by a reference analyzer plug-in that passes CI with no core-module changes.
FR18: The system can test each flank feature for enrichment relative to a per-genome ORF background.
FR19: The system can construct the background with paralogs collapsed at a documented, reported identity threshold.
FR20: The system can compute enrichment with a binomial test and with a label-shuffling permutation test.
FR21: The system can report effect sizes alongside raw p-values and multiple-testing-corrected p-values (Benjamini–Hochberg and Bonferroni).
FR22: The system can report GC% and gene-length distributions for flanking ORFs versus background ORFs for every analysis.
FR23: A developer can add a new statistical test through a documented extension interface, verified by a reference test plug-in that passes CI with no core-module changes.
FR24: The system produces one FCER for each (genome × location) in a run; v1 produces no cross-genome aggregate FCER.
FR25: The system emits every FCER in both tabular (CSV) and structured (JSON) form.
FR26: Every FCER declares its schema version, and the schema is published as a machine-readable specification.
FR27: Every FCER records the effective merged configuration that produced it — not the configuration file as written.
FR28: Every FCER records the FLANDERS version, every dependency version, and checksums of every reference database used.
FR29: Every FCER records which analyzers and statistical tests produced its values, including any fallback substitutions.
FR30: Every FCER embeds the FLANDERS citation.
FR31: Every FCER produced by remote search is marked *discovery not reproducible* and records the search date, the NCBI database name and release metadata, and the search-space size (sequence count and total length).
FR32: The system structures per-genome results so they can be joined to an external phylogeny by genome accession.
FR33: A user can supply a phylogenetic tree (Newick) with a run; the system checks that it parses and that its tip labels match the run's genome accessions, reports unmatched tips, and retains the tree alongside the results.
FR34: A user can change a run's statistical test, multiple-testing correction, background, or statistical parameters and re-run only the enrichment stage (a stats-only replay) from the run's stored enrichment inputs or from an imported full or slim bundle, without re-running discovery, annotation, or feature prediction; the result is recorded as a new variant run linked to the original.
FR35: A user can perform a stats-only replay (FR34) from the command line, without the GUI.
FR36: A user can export the provenance of any saved FCER as a runnable configuration file.
FR37: A recipient holding the same FLANDERS release can reproduce a shared run's enrichment verdicts from its full or slim bundle.
FR38: A user can run the complete pipeline in a single invocation with no interactive input.
FR39: The system signals outcome through distinct, documented exit codes for success, completion with warnings, invalid configuration, dependency failure, and upstream output-format drift.
FR40: The system halts with an attributable error — identifying the dependency and configuration section involved — when a dependency rejects its parameters.
FR41: The system refuses to emit results when it cannot fully parse a dependency's output, and halts the entire run rather than continuing past the affected tag.
FR42: The system keeps result output separate from progress, warnings, and the citation notice.
FR43: A user can tab-complete FLANDERS commands and options in bash and zsh.
FR44: The system prints the FLANDERS citation at the end of every run.
FR45: The system records the state of every long-running or externally mediated task in a persistent run ledger, keyed by an indexable tag such as genome accession.
FR46: The run ledger is created automatically when a workspace is first initialized, with no user setup.
FR47: A user can resume an interrupted run without repeating tasks the ledger records as complete.
FR48: When a task fails for one tag, the system records the failure in the ledger and continues the run for the remaining tags.
FR49: Every run writes a run report listing each failed or excluded tag with its reason; every bundle of the run includes it.
FR50: A user can view the per-tag status of any run: pending, complete, or failed.
FR51: A user can launch a local GUI that is reachable only from their own machine, on a configurable port.
FR52: A user can compose a complete run configuration in the GUI and save it as a configuration file.
FR53: The GUI presents every parameter on the documented, versioned curated-parameter list as a named field and accepts any other dependency parameter as free-form input.
FR54: The GUI presents the exact command that runs a composed configuration.
FR55: A GUI-composed configuration is indistinguishable in effect from an equivalent hand-written configuration.
FR56: A user can browse FCER results in tabular form in the GUI.
FR57: A user can view the genomic neighborhood of a discovered cluster and its flanks.
FR58: A user can inspect the full provenance of any FCER in the GUI.
FR59: A user can launch a stats-only replay (FR34) from the GUI; the GUI never recomputes statistics in place.
FR60: A user can launch a saved configuration as a run from the GUI and cancel it; at most one run executes at a time across the GUI and CLI, and the GUI displays the active run's per-tag ledger status (FR50) while it executes.
FR61: A user can install FLANDERS on Linux, macOS, or WSL by running a single bootstrap script that provisions the container runtime if absent and places a `flanders` command on their PATH.
FR62: A user can obtain FLANDERS as a single container image containing every software dependency except redistribution-restricted predictors; reference data is obtained separately (FR84).
FR63: *(Removed 2026-11-25 — Docker is the only v1 install path; pip/bioconda deferred post-v1.)*
FR64: The installer offers guided setup of each redistribution-restricted predictor (SignalP 6, SignalP 5, TMHMM 2.0c, Phobius): it states the license terms and where to request the software, accepts the path to the user's downloaded archive, verifies it against the release's predictor manifest, installs it into the workspace, and confirms it with a test prediction; setup of any predictor can be skipped.
FR65: A user can run the 92-genome *ebo* reference analysis end to end as a validation of their installation.
FR66: Each FLANDERS release is versioned and archived with its own persistent, citable identifier.
FR67: A user can determine which upstream cblaster and antiSMASH releases a given FLANDERS release supports.
FR68: A maintainer is notified automatically when an upstream dependency publishes a new release.
FR69: A user can access a quickstart guide and a worked tutorial on the *ebo* reference corpus.
FR70: Stopping the GUI stops a run it launched; on the next GUI start, the user is offered to resume that run (FR47).
FR71: A user can browse every run in the workspace with its key parameters, status, date, and origin (local or imported).
FR72: A user can compare any two runs — including a run and its stats-only variant — side by side or as a diff of which features gained or lost significance.
FR73: A user can export a run as a self-contained bundle containing its effective configuration, captured inputs (FR86), all FCERs, the run report (FR49), every recorded dependency invocation, its search manifest or discovery snapshot, and its stored enrichment-stage inputs; unless the user selects a slim bundle, it also contains the raw cblaster and antiSMASH outputs. A slim bundle supports stats-only replay (FR34) and re-execution of every recorded invocation.
FR74: A user can import a shared FCER or run bundle, from the command line, at GUI launch, or from within the GUI; an imported run is read-only and labeled with its origin.
FR75: The system refuses to import an FCER or bundle that fails schema validation or declares an unsupported schema major version, states the reason, and loads nothing from it.
FR76: The system warns when an imported or compared run's FLANDERS version or reference-database checksums differ from the local installation.
FR77: All user state — configurations, drafts, run outputs, FCERs, search snapshots, imported runs, and the run ledger — lives in one user-visible workspace directory on the host that persists across container image upgrades and replacement.
FR78: A user can rebuild the workspace index (run history, ledger summaries, FCER index) from the files the workspace contains.
FR79: The system records every dependency invocation verbatim — tool, version, and the exact parameters passed — so each can be re-executed outside FLANDERS.
FR80: A recipient can replay a bundled run from its captured discovery snapshot, re-executing flank extraction, annotation, feature prediction, and enrichment without searching again.
FR81: A user can build a local search database from the current NCBI release for a genome set or taxon of up to the NFR10 scale (~1,000 genomes); the system records a manifest of every genome's `accession.version`, the retrieval date, the NCBI release metadata, and a content checksum computed over the retrieved sequences in canonical order.
FR82: A recipient can rebuild an identical search database from a run's manifest; the system reports every `accession.version` it cannot retrieve and never builds a smaller database silently. A run whose manifest cannot be fully rebuilt remains stats-replayable from its stored enrichment inputs and is marked partially reproducible, listing the missing entries.
FR83: Every FCER identifies each hit, ORF, and genome by its versioned accession (`accession.version`).
FR84: A user can download the reference data pinned to their FLANDERS release (antiSMASH databases, Pfam-A, the *ebo* BLAST DB snapshot) into the workspace with one command; the system verifies every file's checksum, refuses to run against unverified reference data, and works offline once it is present.
FR85: After installation, a user can install a downloaded restricted predictor, see which predictors are installed, and get acquisition instructions for any predictor, from the command line or from a GUI Predictors page, with the same verification as FR64.
FR86: At run start the system copies the run's inputs (query, genome list, any local database, tree) into the run's folder in the workspace and records their checksums; a missing input path fails the run with the invalid-configuration exit code, naming the path, and never prompts. In the GUI, inputs are chosen with a file picker.
FR87: A user can direct a run to copy its final FCERs and run report to a chosen output directory outside the workspace (`--out`), for workflow managers.
FR88: A user can upgrade FLANDERS with one command that pulls the new release's image and fetches any reference data the new release pins differently; no other workspace content is modified.

### NonFunctional Requirements

NFR1: Two runs of the same FLANDERS release, with the same effective configuration and the same reference-database snapshot, produce identical significance verdicts and effect directions for every feature test on any supported platform.
NFR2: Across such runs, p-values and effect sizes agree within a numeric tolerance that is defined and published with each release.
NFR3: Every stochastic procedure, including permutation tests, uses a seed recorded in the FCER; re-running with that seed on the same platform yields identical values.
NFR4: Cross-machine equivalence (NFR1–NFR2) is verified on the full 92-genome *ebo* corpus across at least two distinct host operating systems before v1 release.
NFR5: Equivalence (NFR1–NFR2) holds between native x86-64 execution and emulated execution on Apple Silicon, verified by running the *ebo* corpus under emulation as one of the NFR4 hosts or as an additional run.
NFR6: No run marked reproducible depends on mutable external state; any run that does is flagged per FR31. Fresh-snapshot runs qualify as reproducible because their manifest pins immutable `accession.version` records; rebuild completeness is reported per FR82.
NFR7: The run ledger survives abrupt termination (process kill, container stop, power loss); on resume, no task recorded complete is lost, and only tasks in flight at termination are repeated. Verified by a kill-injection test that terminates the run during each pipeline stage and confirms correct resume.
NFR8: A task is recorded complete only after all of its outputs are fully written; partial outputs are never treated as complete.
NFR9: Zero silent exclusions — every genome absent from an analysis appears in the failed/excluded list (FR49) with its reason.
NFR10: v1 supports runs of up to 1,000 genomes on the documented minimum hardware specification, demonstrated by the 1,000-genome benchmark run (NFR11) completing successfully on that specification.
NFR11: Pipeline wall-clock and stats-only replay times are measured and published at release for the *ebo* corpus and a ~1,000-genome benchmark; v1 sets no latency targets — including for stats-only replay — by deliberate decision (2026-11-06); measured values inform whether targets are needed later.
NFR12: FLANDERS's own orchestration and ledger overhead stays under 5% of total run wall-clock on the *ebo* corpus, measured as total run wall-clock minus the summed ledger-recorded durations of dependency tasks.
NFR13: Supported hosts are Linux (x86-64), macOS (Intel natively; Apple Silicon via emulation), and Windows via WSL2, served by a single x86-64 container image.
NFR14: Apple Silicon performance under emulation is documented, not targeted.
NFR15: On a clean supported host, the bootstrap installer reaches a working `flanders` command with no manual steps beyond OS-level permission prompts.
NFR16: At v1 launch the supported antiSMASH releases are 8 (primary) and 7 (previous). Each release declares the exact cblaster and antiSMASH versions it is validated against; CI verifies at least the current and previous release of each.
NFR17: Upstream output-format drift is detected in CI against recorded fixture outputs for every supported upstream version.
NFR18: Within a major FCER schema version, changes are additive only; a consumer written against `1.0` reads any `1.x` FCER without modification.
NFR19: FLANDERS runs safely as a workflow step: it requires no TTY, never prompts, and writes only within its configured workspace and output directories.
NFR20: The GUI server binds to the loopback interface only; v1 provides no option to expose it on other interfaces. Local execution only — no shared-server or multi-user deployment in v1.
NFR21: FLANDERS sends no telemetry; network access occurs only for user-requested remote search, sequence and reference-database retrieval, and container pulls.
NFR22: No redistribution-restricted predictor (SignalP 6, SignalP 5, TMHMM 2.0c, Phobius) appears in any distributed artifact; CI verifies this by inspecting the published image.
NFR23: The statistics harness has at least 90% line coverage, and every test and correction is validated against an independent reference implementation on known inputs.
NFR24: Every FCER schema change ships with a semver-correct version bump and a changelog entry describing its effect on consumers.
NFR25: Replacing or upgrading the container image loses no user state; verified in CI by upgrading the image over a populated fixture workspace and confirming every run, FCER, and ledger record is intact.
NFR26: Rebuilding the index of a workspace containing up to 1,000 runs restores every run to run history with zero runs lost, verified against a generated fixture workspace.
NFR27: A manifest rebuild (FR82) of the *ebo* fresh-snapshot DB yields a content checksum identical to the original whenever every manifest entry is retrievable (binary database files may differ, e.g. by embedded build timestamps; the content checksum is the equivalence test).

### Additional Requirements

**Starter template (Epic 1, Story 1):** uv-managed package plus `django-admin startproject` — `uv init --package --name flanders --python 3.11 .`; `uv add "django~=5.2" typer pyyaml jsonschema`; `uv add --dev pytest pytest-django ruff`; `uv run django-admin startproject site src/flanders/web`. Tailwind v4 standalone binary fetched at build time, never committed; htmx 2.x and Alpine.js 3 vendored under `web/static/vendor/`.

**Stack and structure**
- AR1: Python ≥3.11, single `src/flanders/` package split into `cli/`, `config/`, `engine/`, `adapters/`, `features/`, `genomics/`, `harness/`, `fcer/`, `workspace/`, `ncbi/`, `reference/`, `bundles/`, `tools/`, `web/`; no catch-all `utils.py`.
- AR2: Django-free core — `harness/`, `fcer/`, `genomics/`, `config/` never import Django; enforced by an import-linter contract in CI. Only `workspace/` and `web/` touch the ORM.
- AR3: Typer CLI generating bash/zsh completion; CLI verbs lowercase/hyphenated (`run`, `reanalyze`, `replay`, `bundle export|import`, `snapshot build|rebuild`, `reference fetch|verify`, `tools add|status|help`, `workspace reindex`, `gui`, `self-update`).
- AR4: Tests in `tests/` mirroring `src/`; markers `unit`, `adapter`, `e2e`; upstream fixtures at `tests/fixtures/<tool>/<version>/<case>/` with `expected.json`; fixture FCERs at `tests/fixtures/fcer/<schema_version>/`.

**Data and formats**
- AR5: FCER defined by Pydantic v2 models that generate the JSON Schema (draft 2020-12) at `schemas/fcer/<major>.<minor>/fcer.schema.json` via `flanders-dev gen-schema`; CI fails on regeneration diff. JSON canonical, CSV derived from JSON by one writer. `schema_version` is the first key.
- AR6: FCER is a results record (statistics, neighborhood annotations, provenance); per-genome background ORF tables are `enrich`-stage inputs in `runs/<id>/stages/`, included in every bundle.
- AR7: Config: Pydantic models for FLANDERS-owned keys; each dependency section is an opaque mapping passed through verbatim; one merge function (flag > file > default) emits the EffectiveConfig recorded in every FCER.
- AR8: Floats at full precision; no NaN/Infinity — uncomputable statistics are `null` plus a `reason` code; not-computed optional fields present as `null`; tolerance applied only in `harness.compare.within_tolerance()`.
- AR9: Timestamps UTC ISO 8601 with `Z`; durations `_s`; checksums lowercase SHA-256 `_sha256`; canonical serialization only via `fcer.canonical.dumps()`.
- AR10: Coordinates 1-based inclusive with strand `"+"`/`"-"` outside adapters; conversion only via `genomics.coords.to_zero_based()/from_zero_based()`; every coordinate paired with its record `accession.version`.
- AR11: All accessions versioned; genome tag = assembly `accession.version`; unversioned accession is a validation error at every boundary. FCER location values: `upstream`, `seed`, `downstream`.
- AR12: Run ID `YYYYMMDDTHHMMSSZ-<6 hex>` generated only in `workspace.ids`; stages via the `Stage` enum; task key `(run_id, stage, tag)`, run-wide tag `run`.

**Workspace, ledger, and index**
- AR13: Workspace `~/flanders/` with `runs/`, `imports/`, `snapshots/`, `drafts/`, `reference/`, `tools/`, `.flanders/`; per run `inputs/`, `stages/`, `fcer/`, `logs/`, `report.json`. Files are the source of truth; SQLite index rebuildable.
- AR14: SQLite via Django ORM and migrations; journal mode `DELETE` (not WAL), short transactions, busy timeout. **Early spike story** verifies reliability on macOS and WSL bind mounts; fallback DB in a Docker-managed volume.
- AR15: Ledger transitions only via `workspace.ledger` (`start_task`, `complete_task`, `fail_task`), each one transaction; task states `pending → running → complete | failed`, run states add `cancelled`, `interrupted`. Single ledger writer: the scheduler's parent process.
- AR16: Atomic task outputs: write to `<tag>.tmp/`, fsync, rename, then `complete_task`.
- AR17: Run inputs (query, genome list, local DB, tree) copied and checksummed into `runs/<id>/inputs/` at run start.

**Engine and tools**
- AR18: Custom task engine; stages `discover → extract_flanks → annotate_bgc → predict_features → collapse_paralogs → enrich → emit_fcer`; worker pool `--jobs N` (default CPUs − 1).
- AR19: Replay from `extract_flanks` (full bundle discovery outputs) or from `enrich` (stats-only replay; own runs, slim or full bundles); `reanalyze` = `replay --from enrich` with changed statistics, always a new variant run.
- AR20: `engine/report.py` writes `runs/<id>/report.json` of failed/excluded tags with reasons.
- AR21: Every external program through `engine.invoke.run_tool()` (argv list, env name, cwd, timeout; records tool, version, argv, input/output checksums, duration, exit status). Direct `subprocess` banned elsewhere (ruff rule). Tool invocations never auto-retried; NCBI retries with backoff in `ncbi/` only.
- AR22: Each heavy tool in its own micromamba env inside the image (`env-antismash8`, `env-antismash7`, `env-cblaster`, `env-predictors`, `env-hmmer-mmseqs`), invoked as a CLI subprocess; one adapter per tool implementing `ToolAdapter`; version-gated parsers raise `UpstreamDriftError`.
- AR23: Single-run lock: OS file lock `.flanders/run.lock` plus ledger row with PID and heartbeat; dead heartbeat → `interrupted`; cancel = SIGTERM to process group, then SIGKILL after grace.
- AR24: GUI launches runs only by spawning `flanders run -c <config>` via `engine.supervisor`; progress by htmx polling of the ledger (~2 s); no broker, no websockets; no long work inside a request.
- AR25: Exception hierarchy rooted at `FlandersError`: `ConfigError` 2, `DependencyRejectedError` 3, `UpstreamDriftError` 4, `RunLockedError` 5, `ReferenceDataError` 6, `RunCancelled` 130; exit 1 when any tag failed; only `cli/` converts exceptions to exit codes.
- AR26: Logs: JSON Lines per task at `runs/<id>/logs/<stage>/<tag>.jsonl` plus `run.jsonl`; fields `ts, level, run_id, stage, tag, event`; dependency stdout/stderr captured raw; stderr human renderer of the same events; `flanders.logging.get_logger`.
- AR27: Determinism: explicit `numpy.random.Generator` (PCG64) via `harness.rng.child(seed, label)`; no global random state; outputs sorted canonically; no wall-clock values inside results.

**Statistics**
- AR28: numpy + scipy (`binomtest`, `false_discovery_control`), Bonferroni direct, seeded permutation; statsmodels test-only as independent reference; mmseqs2 paralog collapse with a default identity threshold **decided in an early harness story** and recorded in every FCER.
- AR29: Analyzer and statistical-test plug-ins via entry-point groups `flanders.features` and `flanders.stat_tests`.

**Reference data, NCBI, predictors**
- AR30: Per-release reference manifest `src/flanders/reference/manifests/<release>.yaml` (source URL, version, SHA-256) for antiSMASH 7 and 8 DBs, Pfam-A, frozen *ebo* BLAST DB; same manifest defines the Zenodo archive.
- AR31: NCBI via Datasets CLI and E-utilities, optional `ncbi.api_key`, retry with backoff, every request recorded; snapshot content checksum = SHA-256 over protein records sorted by `accession.version`, canonically serialized.
- AR32: Predictor manifest per release; per-predictor install recipes (SignalP 6: pip + weights; SignalP 5: unpack; TMHMM and Phobius: unpack + Perl-path fix) into `~/flanders/tools/`, followed by a test prediction. Image ships DeepSig, PyTorch, Perl.

**Distribution and security**
- AR33: One x86-64 image on a micromamba base, FLANDERS env from `uv.lock` plus per-tool env lockfiles at `docker/envs/<env>.lock`; no reference data in image; published to GHCR and archived to Zenodo per release.
- AR34: `install-flanders.sh`: installs Docker if missing, pulls image by digest, installs shim, creates and initializes workspace, offers `reference fetch`, offers predictor setup. All prompts live here.
- AR35: Shim: `--platform linux/amd64`; mounts workspace rw, CWD and input-file folders ro at the same paths; GUI bound to `127.0.0.1`; forwards args and exit codes; handles `run --out <dir>` mount and `self-update`.
- AR36: Security: no auth; `ALLOWED_HOSTS` localhost; CSRF on (htmx sends the token); bundle import schema-validated before any write, archive paths sanitized (no absolute, no `..`); no telemetry.
- AR37: CI (GitHub Actions): unit tests; adapter fixture tests for antiSMASH 7 and 8 × cblaster pins; reduced *ebo* e2e per release candidate; full *ebo* recapitulation on two OSes before v1; image-layer scan for restricted predictors; upgrade-over-populated-workspace test; kill-injection resume test; reference- and predictor-manifest checks; ruff, import-linter, schema diff, ≥90% harness coverage; Renovate.

### UX Design Requirements

**Foundation**
- UX-DR1: Semantic token layer (Tailwind v4 theme) with light and dark themes: neutral slate base, teal accent, tokens `significant`, `not-significant`, `failure` (red, failures only), `warning` (amber), `stale` (amber dashed + label), `changed`; Okabe–Ito track palette (antiSMASH `#E69F00`, signal peptide `#56B4E9`, transmembrane `#009E73`, Pfam `#CC79A7`); contrast ≥4.5:1 text and ≥3:1 UI in both themes, checked in CI.
- UX-DR2: Typography: self-hosted Inter and JetBrains Mono (no CDN); scale 12/13/14/16/20/24 px; tabular numerals; p/q in scientific notation with two significant figures, effect sizes two decimals; accessions, parameters and checksums monospace, middle-truncated with full value on hover and copy.
- UX-DR3: Layout: 4 px base, 28 px compact rows (36 px comfortable), 32 px controls; top nav Genomes · Runs · Compose · Predictors with run switcher (name, kind, status); sticky statistics bar; full-width main; right overlay drawer; ledger bar under nav while a run is active; minimum 1280 px with horizontal scroll below; ≥1600 px wide layout; `rem`-based sizing.
- UX-DR4: Design-system partials as Django includes with documented context: button (primary/secondary/ghost/danger), select, segmented control, number input, checkbox/toggle, text/number/file-path input, file picker, tabs, breadcrumbs (`Run › Genome › Feature`), tooltip, drawer shell (Esc closes, focus trapped and restored), confirm dialog, banner (info/warning/failure), code block with copy, shared `_spinner.html`.
- UX-DR5: Debug-only `/_components` gallery rendering every component in every state from fixtures; it is the visual-regression and accessibility test surface (axe-core in CI over every state).

**Custom components**
- UX-DR6: Results table, `genomes` variant (home): columns genome (accession.version, organism), location, significant-feature count, top features by q, flank ORFs, status, provenance link; run denominator above; sortable, filterable; states default, refreshing, stale, empty, unavailable; real `<table>` with `aria-sort`, arrow-key row focus, Enter drills down; htmx fragment with sort/filter in URL (`hx-push-url`); scroll restored on back; ~1,000 rows server-rendered without virtualization.
- UX-DR7: Results table, `features` variant (genome page): feature (category dot), flank ORFs with feature `k/n`, background rate, effect size, raw p, corrected q, significance badge, predictor column in concordance mode, provenance link; footer note that correction applies across all features of the genome × location.
- UX-DR8: Feature tally strip and tally chip: `<feature> · k/N genomes significant`, sorted by k, fixed note "Counts of per-genome results — not a cross-genome test", never a p-value; clicking a chip filters the Genomes table (removable filter chip, in URL).
- UX-DR9: Significance badge (significant ●, not significant ○, `changed` persistent marker with tooltip of the other run's verdict, labelled "changed from published" for imported sources) with screen-reader text; denominator cell `n/N · k failed · j excluded` with expandable red list of reasons, never hidden.
- UX-DR10: Statistics bar: read-only active test, correction, threshold, background; heavy-parameter chips with "requires a re-run" tooltips and **Launch variant…**; **Change statistics…** expands in place into a native form pre-filled from the run with *changed from <run>* markers, one-line explanation, and **Replay statistics · creates a variant**; states default, expanded, replay running, another run active (unavailable with explanation), imported (orientation strip), FCER-only import (view-only notice), compare mode.
- UX-DR11: Neighborhood map: server-rendered SVG from FCER coordinates; shared kb axis, strand-directed gene arrows (seed dark slate, flanks light gray, selected feature's ORFs accent outline), toggleable tracks (CSS only), legend, scale bar, upstream/downstream label; hover tooltip, click opens gene drawer; hatched "not available" segment with reason for partial annotation; focusable gene groups with `aria-label`; companion gene-table toggle; long neighborhoods scroll horizontally; no pan/zoom.
- UX-DR12: Ledger bar and panel: bar shows run name, kind (run / statistics replay), stage, `done · failed · pending`, elapsed, expand, Cancel; panel lists per-genome rows (accession, stage, status, reason) with filter and "failures are not retried" note and links to finished neighborhoods; states running, cancelled (resumable), interrupted banner (Resume/Dismiss), halted (distinct, names dependency and version, "No results were emitted"), complete notice linking to Genomes or to the replay's comparison; `role="progressbar"`, `aria-live` polite (assertive for halted); ~2 s polling only while active.
- UX-DR13: Provenance drawer: tabs Config (effective YAML, pass-through marked unvalidated), Versions, Databases (names, snapshot IDs, checksums), Analyzers (predictors and tests incl. fallbacks, link to Predictors page); Export as config; citation with copy; banners for version/reference mismatch and remote-search non-reproducible.
- UX-DR14: Run composer: one scrolling page with section index — Inputs (query, genome set as fresh snapshot / local DB / remote, optional tree; file pickers, note that files are copied into the run), Neighborhood, Features (signal-peptide chain line, unavailable features with **Set up predictors** link), Dependencies (curated fields with plain labels and upstream flag in monospace; escape-hatch key–value rows tagged *passed through unvalidated* at all times); defaults show value and source; validation on blur and at pre-flight; review panel with merged YAML and exact `flanders run -c …`; drafts autosave to `drafts/` (Compose → Drafts); states blank, variant pre-filled with *changed from <run>*, pre-flight errors (`aria-describedby`), another run active (Save config), launching.
- UX-DR15: Run list and compare selector: columns name, kind (run / heavy variant / statistics replay), source run, status, date, genome count, key parameters, local/imported tag, bundle type; row checkboxes; Compare enabled with exactly two; Import…; import refused banner.
- UX-DR16: Compare view: side-by-side (aligned Genomes tables; stacked at 1280 px, side by side ≥1600 px) and diff (gained, lost, only in A, only in B, tallies before/after); header lists differing heavy and statistical parameters; offer **Replay B with A's statistics** when a heavy variant also differs in statistics; mismatch banner for reference data or FLANDERS version.
- UX-DR17: Imported-run orientation strip (run name, genome count, published test/correction/threshold, bundle type, provenance link), dismissible and remembered per run; FCER-only view-only notice.
- UX-DR18: Predictors table: fallback-chain line; rows (name/version, role, status bundled/installed/not installed, license type, chain position); **How to get it** expander (license summary, request page in new tab, file to download); **Add archive…** file picker with inline states uploading, verifying, installing, testing, installed, failed (not recognized with expected name/version, checksum mismatch, test failed with Details and log path).

**Interaction patterns**
- UX-DR19: URL is state: run, sort, filter, selected genome/feature, compare pair in snake_case query params; back/forward restore view and scroll; drawers are not history entries.
- UX-DR20: Cost labelling: Launch, Launch variant…, Resume carry clock icon and "· re-runs pipeline"; Replay statistics carries "· creates a variant"; one primary action per view; danger style only for Cancel run; confirm dialogs only for Cancel and Resume.
- UX-DR21: Feedback: messages at point of cause; page banners only for page-spanning state (interrupted, mismatch, halted, refused import, view-only FCER); no toasts except "Copied"; message shape what happened · what it affects · what to do, naming dependency and config section; tracebacks behind Details with log path; never blank on fragment error (last good content kept, marked stale).
- UX-DR22: Empty and loading states: first launch offers Compose a run, Import a run bundle, Open the *ebo* reference corpus, and Set up predictors (when any is missing); run-in-progress Genomes page explains why results are hidden and links to ledger and finished neighborhoods; filter-matches-nothing shows filter with clear; filters never change denominators or statistics.
- UX-DR23: Keyboard: `/` filter, ↑/↓ rows, Enter drill down, Esc closes drawer or collapses replay form, `s` opens Change statistics, `?` shortcut overlay; no single-key shortcuts in text inputs; visible focus rings; htmx swaps return focus to the triggering control, drill-down focuses the page heading; scripted keyboard-only e2e of the core loop.
- UX-DR24: Accessibility baseline: semantic HTML and landmarks, no color-only meaning, `aria-live` for table refresh and run status, `prefers-reduced-motion` disables animations; tested in current Chrome, Firefox, Safari at 1280 and 1920 px; one-time deuteranopia/protanopia check of the palette.
- UX-DR25: Terminology used identically in UI, CLI, and docs: run, variant, statistics replay, imported run, tally, feature, neighborhood, failed, excluded, view settings, statistical settings, heavy parameters, bundled predictor, restricted predictor.

### FR Coverage Map

{{requirements_coverage_map}}

## Epic List

{{epics_list}}

<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Epic {{N}}: {{epic_title_N}}

{{epic_goal_N}}

<!-- Repeat for each story (M = 1, 2, 3...) within epic N -->

### Story {{N}}.{{M}}: {{story_title_N_M}}

As a {{user_type}},
I want {{capability}},
So that {{value_benefit}}.

**Acceptance Criteria:**

<!-- for each AC on this story -->

**Given** {{precondition}}
**When** {{action}}
**Then** {{expected_outcome}}
**And** {{additional_criteria}}

<!-- End story repeat -->
