---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - docs/planning/prd.md
  - docs/planning/ux-design-specification.md
  - docs/planning/validation-report-2026-11-06.md
  - docs/product-brief.md
  - docs/product-brief-distillate.md
workflowType: 'architecture'
project_name: 'flanders'
user_name: 'Kevin Klicki'
date: '2026-11-06'
lastStep: 8
status: 'complete'
completedAt: '2026-11-22'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements** (83, in 11 groups):

| Group | FRs | Architectural meaning |
|---|---|---|
| Run configuration | FR1–FR8 | Typed config model with deterministic precedence (flag > file > default); opaque per-dependency pass-through sections |
| Discovery & flank annotation | FR9–FR17 | Dependency adapters (cblaster, antiSMASH, SignalP-class chain, TMHMM, `hmmscan`); predictor fallback and concordance; analyzer plug-in interface |
| Enrichment | FR18–FR23 | Pure-Python statistics harness (binomial, permutation, BH/Bonferroni, mmseqs2-collapsed null, covariates); test plug-in interface |
| Artifact & provenance | FR24–FR33 | FCER schema (per genome × location; no cross-genome aggregate in v1), JSON Schema, CSV + JSON writers, provenance block, tree validation and retention |
| Re-analysis & verification | FR34–FR37 | Stats-only replay from the `enrich` stage using stored stage outputs (own runs) or a bundle (shared runs), producing a variant run |
| CLI operation | FR38–FR44 | Exit-code taxonomy, stdout/stderr separation, fail loudly on output drift, shell completion |
| Run ledger | FR45–FR50 | Persistent per-tag task state, resume, failure isolation |
| GUI | FR51–FR60, FR70–FR72 | Local Django app: composer, launch/cancel, live ledger, results, compare, provenance |
| Workspace, sharing, search reproducibility | FR73–FR83 | Workspace layout and index, bundle export/import/replay, NCBI snapshot build and rebuild, verbatim invocation records |
| Installation & distribution | FR61–FR65 | Single x86-64 image (Docker is the only v1 install path), bootstrap installer + shim, installer-guided setup of user-supplied predictors, `self-update` |
| Release & compatibility | FR66–FR69 | Upstream version matrix in CI, Zenodo releases, docs |

**Non-Functional Requirements that shape the architecture:**
- **Determinism** (NFR1–NFR6): every random step seeded and recorded; verdicts identical across hosts; numeric tolerance published; native and emulated runs equivalent.
- **Crash safety** (NFR7–NFR9): a task counts as complete only after its outputs are fully written (atomic); resume repeats only tasks that were in flight; zero silent exclusions.
- **Scale and overhead** (NFR10–NFR12): up to 1,000 genomes; FLANDERS's own overhead under 5% of wall-clock; no latency targets.
- **Integration** (NFR16–NFR19): fixture-based drift detection per upstream version; additive-only FCER schema within a major version; never prompts and writes only inside the workspace.
- **Security** (NFR20–NFR22): loopback-only GUI, no telemetry, no DTU binaries in any distributed artifact.
- **Durability** (NFR25–NFR27): user state survives image upgrades; the index can be rebuilt; a manifest rebuild matches the original content checksum.
- **Maintainability** (NFR23–NFR24): ≥90% test coverage on the harness, validated against reference implementations.

**Scale & Complexity:**
- Primary domain: scientific batch pipeline plus a local server-rendered web app (full-stack Python).
- Complexity level: **medium-high**. One user and no multi-tenancy, but a heavy external-tool surface, long crash-safe runs and strict reproducibility.
- Estimated architectural components: about 12 — CLI, config model, pipeline engine, dependency adapters, NCBI snapshot service, enrichment harness, FCER schema and I/O, workspace and ledger store, run supervisor, bundle service, GUI web app, packaging/CI.

**UX implications:**
- **Live state comes from polling.** The ledger polls about every 2 s over htmx; no websockets.
- **Statistics changes are replays.** Changing the test, correction or statistical parameters in the GUI launches a stats-only replay from the `enrich` stage as a new variant run; it appears in run history and can be compared with the original. Nothing is recomputed inside the web request.
- **The neighborhood map is drawn on the server,** as SVG built from FCER coordinates.
- **Views are addressable.** All view state lives in the URL.
- **The GUI must work offline.** Fonts and CSS are self-hosted.

### Technical Constraints & Dependencies

- Python 3.11 or newer; one x86-64 Docker image as the canonical runtime (Linux, macOS Intel, Apple Silicon via emulation, WSL2).
- **Decided stack:** Django with server-rendered templates, htmx, Tailwind (compiled CSS) and Alpine.js. The ledger, run history and FCER index live in SQLite inside the workspace.
- **Orchestrated tools, version-pinned:** cblaster, antiSMASH (8 primary, 7 supported), HMMER (`hmmscan`) with Pfam-A, mmseqs2, and the predictor chain (DeepSig in the image; SignalP 6, SignalP 5, TMHMM 2.0c and Phobius supplied by the user).
- **Conflicting dependency pins** between antiSMASH and cblaster make a shared Python environment fragile.
- **NCBI retrieval** is needed for fresh snapshots and manifest rebuilds (versioned assembly and protein accessions), subject to NCBI availability, rate limits and suppressed records.
- **Reference data and image size:** antiSMASH databases, Pfam-A and the frozen *ebo* BLAST snapshot.
- **Workspace on host mounts:** SQLite reliability over macOS and WSL folder mounts is unverified (fallback: database in a Docker volume).
- **Still open from the brief:** the mmseqs2 identity threshold for collapsing paralogs; whether Pfam-A is bundled or fetched.
- **Rejected ideas, not to be re-proposed:** Tauri/Electron wrappers, PyInstaller/AppImage, Pixi, forking cblaster or antiSMASH, server compute.

### Cross-Cutting Concerns Identified

1. **Provenance capture.** Every dependency call goes through one recorder that logs tool, version, exact arguments, input and output checksums, and duration (FR27–FR29, FR79).
2. **Task model and idempotency.** Each stage is a task keyed by (run, stage, tag). Outputs are written to a temporary location, atomically renamed, then recorded as complete (NFR7–NFR8).
3. **Error taxonomy.** Per-tag failure → record and continue; upstream format drift → halt the run; configuration and dependency rejections → error naming the source. These map onto the documented exit codes (FR39–FR41).
4. **Determinism.** One convention for seeds, numeric tolerance, and canonical ordering for checksums.
5. **Single active run.** One workspace-wide lock shared by CLI and GUI; cancellation reaches dependency subprocesses (FR60, FR70).
6. **Workspace layout.** One path convention for runs, snapshots, bundles and imports; every file is rediscoverable by re-indexing (FR77–FR78).
7. **Schema versioning.** The FCER JSON Schema is the single public contract; additive-only within a major version; import validates against it (FR26, FR75, NFR18).
8. **Output channels.** Results to stdout; progress, warnings and citation to stderr; never prompt (FR42, NFR19).
9. **Upstream drift.** Version-gated parsers backed by recorded fixtures for every supported upstream version (NFR16–NFR17).

## Starter Template Evaluation

### Primary Technology Domain

Full-stack Python: a CLI-first scientific pipeline plus a local server-rendered Django web app, packaged as one Python distribution and shipped in one Docker image.

### Starter Options Considered

| Option | Verdict |
|---|---|
| **cookiecutter-django** | Rejected. Brings Postgres, Celery/Redis, user auth, email and a multi-container compose setup — none fit a single-user local tool, and removing them costs more than starting clean. |
| **SaaS / htmx boilerplates** | Rejected. Built around accounts, payments and hosted deployment — v2 concerns at most. |
| **Plain `django-admin startproject` inside a uv-managed package** | **Selected.** Minimal, current, nothing to remove. Pipeline, CLI and web app live in one `src/` package. |

### Selected Starter: uv package + `django-admin startproject`

**Rationale for Selection:**
- FLANDERS is mostly a pipeline; the web app is one subpackage. A web-first starter would invert that structure.
- uv provides a lockfile for FLANDERS's own Python dependencies (reproducibility, NFR1; pinned expert-install path). Dependency tools (antiSMASH, cblaster, etc.) are **not** managed by uv — their environments are decided in Core Architectural Decisions.
- **Django 5.2 LTS** (supported to April 2028), not 6.1: a Zenodo-archived reproducibility tool benefits from an LTS base. 5.2 became the current LTS when 4.2 reached end of life in April 2026.
- **Tailwind v4 standalone CLI** compiles CSS without Node.js ("end users never run npm"). htmx 2.x and Alpine.js are vendored as static files for offline use.

**Upstream targets confirmed in this step:** **antiSMASH 8 is the primary target, antiSMASH 7 the supported previous release** (NFR16; PRD updated 2026-11-06). antiSMASH 8 requires Python ≥3.11 and extends its JSON output. cblaster 1.3.x (v1.3.20 the latest observed), exact pin set at image build.

**Initialization Commands:**

```bash
# from the repository root
uv init --package --name flanders --python 3.11 .
uv add "django~=5.2" typer pyyaml jsonschema
uv add --dev pytest pytest-django ruff
mkdir -p src/flanders/web
uv run django-admin startproject site src/flanders/web
# Tailwind v4 standalone binary fetched in the build step, never committed
```

*Exact package layout is set in Project Structure; pinned versions are captured in `uv.lock` at initialization. Typer is confirmed as the CLI framework (see Infrastructure & Deployment).*

**Architectural Decisions Provided by Starter:**

- **Language & runtime:** Python ≥3.11 (also antiSMASH 8's floor); `src/` layout; uv lockfile.
- **Styling:** Tailwind v4 via standalone CLI; compiled CSS is a build artifact shipped in the wheel and image.
- **Build tooling:** uv build backend for the wheel; Tailwind build runs before packaging; Docker image built separately.
- **Testing:** pytest + pytest-django; fixture FCERs and recorded upstream outputs under `tests/fixtures/` (NFR17).
- **Code organization:** single `flanders` package, Django project as `flanders.web`; pipeline and harness importable without Django settings (headless CLI, stats-only replay).
- **Development experience:** `uv run` for everything; Django dev server with `/_components` gallery in debug mode; ruff for lint and format.

**Note:** Project initialization using these commands should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical (block implementation):** dependency execution model · pipeline engine · ledger and index store · run supervisor and single-run lock · FCER and config data models · reference-data placement · exit-code taxonomy.
**Important (shape the architecture):** NCBI snapshot mechanics · statistics stack · CLI framework · image composition · CI matrix.
**Deferred (post-v1):** stage reuse across variant runs (stage outputs kept per stage and content-addressed so it can be added) · multi-user auth and Postgres (v2 webapp) · Snakemake/Nextflow wrapper modules (stretch).

**Author decisions recorded in this step (2026-11-06):**
- **Pipeline engine: custom, lightweight task engine** ("whatever is standard"). Bioinformatics *tools* (antiSMASH, cblaster, BiG-SCAPE) run their own internal orchestration; workflow managers are the standard one level up, where users compose tools. FLANDERS is meant to be dropped into Snakemake/Nextflow as a stage (J3), so embedding a workflow manager inside it would be inverted.
- **Reference data: downloaded once into the workspace, not baked into the image.** The PRD was updated accordingly (FR62 revised, FR84 added, reproducibility contract = image + Zenodo reference-data archive).

### Data Architecture

- **Workspace layout is the source of truth.** Files live under `~/flanders/`: `runs/`, `imports/`, `snapshots/`, `drafts/`, `reference/`, `tools/`, `.flanders/`. The database is an index and can be rebuilt (FR78).
- **Index store: SQLite through Django's ORM** (Django 5.2 LTS) for all database access, ledger included. Django migrations own the schema. The CLI bootstraps Django with minimal settings, so headless runs need no web server. **FCER I/O and the statistics harness stay Django-free**, so `reanalyze` and the future importable-harness goal stay clean.
- **SQLite on host mounts:** journal mode `DELETE` (not WAL, which is unreliable over macOS/WSL folder mounts), short transactions, busy timeout. A dedicated early story verifies this on macOS and WSL. Fallback: database in a Docker-managed volume, files in the visible workspace.
- **FCER model:** Pydantic v2 models are the source of truth and generate the published JSON Schema (draft 2020-12), checked in and validated in CI. JSON is canonical; CSV is derived. Additive-only within a major version (NFR18).
- **Config model:** Pydantic models for FLANDERS-owned keys; each dependency section (`cblaster:`, `antismash:`, …) is an opaque mapping passed through verbatim. One merge function applies flag > file > default and emits the **effective config** recorded in every FCER (FR8, FR27).
- **FCER is a results record.** It carries statistics, annotations of the neighborhood, and provenance — not the per-genome background ORF tables. Those are `enrich`-stage inputs kept in `runs/<id>/stages/` and in every bundle (including slim bundles), which is what statistics replays read. There is no cross-genome aggregate FCER in v1.
- **Run inputs are captured.** At run start the query, genome list and any local database are copied into `runs/<id>/inputs/` (checksummed, recorded in provenance), so every run and bundle is self-contained. A missing input path fails with exit 2 naming the path; `flanders run` never prompts. The GUI composer's file picker is where interactive selection happens.
- **Atomic task outputs:** each task writes to `runs/<id>/stages/<stage>/<tag>.tmp/`, fsyncs, renames to its final name, then marks itself complete in the ledger in one transaction (NFR7–NFR8).
- **Checksums:** SHA-256 throughout. Snapshot content checksum = SHA-256 over protein records sorted by `accession.version` and canonically serialized (FR81, NFR27).
- **Reference data:** `reference/<release>/` holds antiSMASH 7 and 8 databases, Pfam-A, and the frozen *ebo* BLAST DB. A per-release manifest (shipped in the package) lists each file's source URL, version and SHA-256. `flanders reference fetch` downloads and verifies; every run refuses unverified reference data and records the checksums it used (FR28, FR84). The same manifest defines the Zenodo reference-data archive.
- **Caching:** no cache layer in v1; content-addressed stage outputs prepare for later stage reuse.

### Authentication & Security

- **No authentication.** Single user, loopback only. The shim publishes the GUI as `-p 127.0.0.1:<port>:<port>`; Django's `ALLOWED_HOSTS` = localhost; CSRF stays on (htmx sends the token) (NFR20).
- **No telemetry.** Network calls only for user-requested NCBI retrieval, remote search, reference-data download and image pull (NFR21).
- **DTU predictors** (SignalP 6, TMHMM 2.0c) are installed by the user into `~/flanders/tools/` and detected at run time. CI inspects the published image layers to confirm no DTU binary is present (NFR22).
- **Untrusted imports:** bundles are schema-validated before anything is written to the index; archive paths are sanitized (no absolute paths, no `..`); imported runs are read-only (FR74–FR75).

### API & Communication Patterns

- **No public API in v1.** CLI and GUI call the same Python orchestration layer.
- **GUI → run:** the GUI launches `flanders run -c <saved config>` as a child process in its own process group; pipeline code never runs inside the web process. Progress is read by **polling the ledger** (htmx, ~2 s). No message broker, no websockets.
- **Single-run lock:** an OS-level file lock (`.flanders/run.lock`) plus a ledger row holding PID and heartbeat. A dead heartbeat with a stale lock marks the run *interrupted* and offers resume (FR47, FR70). Cancel sends SIGTERM to the process group, then SIGKILL after a grace period.
- **Exit codes (FR39):** `0` success · `1` completed with per-tag failures · `2` invalid configuration · `3` dependency rejected its parameters · `4` upstream output-format drift (run halted) · `5` another run holds the lock · `6` reference data missing or unverified · `130` cancelled. One exception hierarchy maps to these codes.
- **NCBI:** NCBI Datasets CLI and E-utilities, optional `ncbi.api_key` (raises NCBI's rate limit), retry with backoff; every request recorded in the run's provenance.

### Dependency Execution Model

- **Each heavy tool runs in its own isolated conda environment inside the image** (micromamba): e.g. `env-antismash8`, `env-antismash7`, `env-cblaster`, `env-predictors`, `env-hmmer-mmseqs`. Each is invoked **as a subprocess through its CLI**, never imported. This sidesteps antiSMASH/cblaster pin conflicts, makes "every invocation recorded verbatim" (FR79) literal, lets cancellation reach the tool, and lets antiSMASH 7 and 8 coexist.
- **One adapter per tool** builds the argument list (FLANDERS-owned parameters + opaque pass-through section), executes through the shared **invocation recorder**, and parses outputs with a **version-gated parser**; an unknown version or failed schema check raises drift (exit 4, FR41).
- **Predictor fallback chain:** SignalP 6 → SignalP 5 → DeepSig → Phobius, whichever are present; the chain actually used is recorded per run (FR15). Concordance mode runs every available predictor, and each statistic carries a `predictor` key (FR16).
- **Only DeepSig ships in the image.** SignalP 6, SignalP 5 and TMHMM 2.0c (DTU) and Phobius (registration-gated) are user-supplied. The image includes PyTorch and Perl so every supplied predictor runs without further downloads.
- **Predictor setup:** the installer optionally walks through each restricted predictor — explains the license terms, opens the request page, then asks for the path to the downloaded archive; FLANDERS identifies and verifies it against the release's predictor manifest, installs it with a per-predictor recipe (pip + weights for SignalP 6; unpack for SignalP 5; unpack + Perl-path fix for TMHMM and Phobius) into `~/flanders/tools/`, and runs a test prediction. `flanders tools add <archive>` / `tools status` / `tools help <name>` and a GUI Predictors page do the same later. Runs never prompt: a missing preferred predictor produces a fallback, a stderr warning with the exact `tools add` command, and a provenance record.

### Pipeline Engine

- **Custom task engine; the SQLite ledger is its state.**
- Stages: `discover → extract_flanks → annotate_bgc → predict_features → collapse_paralogs → enrich → emit_fcer`. Tasks keyed by `(run, stage, tag)`, tag = genome accession (or `run` for run-wide stages).
- A worker pool runs per-genome tasks in parallel (`--jobs N`, default CPU count − 1); the engine only schedules, tools do the heavy work.
- **Single ledger writer:** only the scheduler's parent process writes to the ledger; workers run tasks and report results back to it. This avoids SQLite lock contention over host mounts.
- **Replay** (FR80) starts at `extract_flanks` from a full bundle's captured discovery outputs, or at `enrich` for a **stats-only replay** (works from own runs and from slim or full bundles). `flanders reanalyze` is a convenience for `replay --from enrich` with changed statistical settings; it always creates a new variant run.
- **Run report:** `engine/report.py` writes `runs/<id>/report.json` listing every failed or excluded tag with its reason (FR49, NFR9); bundles include it.

### Statistics Stack

- numpy + scipy (`binomtest`; `false_discovery_control` for BH); Bonferroni implemented directly; permutation tests use a seeded `numpy.random.Generator` (PCG64), seed recorded (NFR3).
- statsmodels is a **test-only** dependency serving as the independent reference implementation (NFR23).
- mmseqs2 paralog collapsing at a configurable identity threshold; **the default is set in an early harness story** (open from the brief) and recorded in every FCER (FR19).

### Frontend Architecture

As specified in the UX spec: Django templates with partials as components, htmx 2.x, Alpine.js 3, Tailwind v4 standalone CLI, server-rendered SVG neighborhood maps, view state in the URL query string, no JS bundler. Static assets vendored for offline use; debug-only `/_components` gallery.

### Infrastructure & Deployment

- **Image:** one x86-64 image on a micromamba base: FLANDERS's environment from `uv.lock` plus per-tool conda environments with explicit lockfiles. **No reference data in the image.** Published to GHCR; each release saved as a tarball to Zenodo with its own DOI, alongside the reference-data archive DOI.
- **Install path:** Docker is the only supported install in v1; pip/bioconda are deferred post-v1 (recorded trade-off: the brief flagged bioconda as important for community uptake).
- **Installer** (`install-flanders.sh`): installs Docker if missing, pulls the image by digest, installs the `flanders` shim, creates and initializes the workspace, offers `flanders reference fetch`, and offers the predictor setup flow. All prompts live here, never in `flanders run`.
- **Shim** (`flanders` on PATH): runs the container with `--platform linux/amd64`, mounts the workspace read-write and the current directory plus the folders of any input paths read-only (at the same paths), binds the GUI to loopback, and forwards arguments and exit codes unchanged. `flanders run --out <dir>` additionally mounts `<dir>` and copies final FCERs there for workflow managers. `flanders self-update` is handled by the shim itself: it pulls the new image and then runs `reference fetch` for any reference data the new release pins differently; the workspace is never modified otherwise.
- **CI (GitHub Actions):**
  - Unit tests: harness, config, schema.
  - Adapter fixture tests: antiSMASH 7 and 8 × supported cblaster pins (NFR16–NFR17).
  - Reduced *ebo* subset end to end on every release candidate.
  - Full *ebo* recapitulation on two OSes before v1 (NFR4).
  - Image-layer scan for restricted predictor binaries (SignalP, TMHMM, Phobius); upgrade-over-populated-workspace test (NFR25); kill-injection resume test (NFR7); reference- and predictor-manifest checks.
  - Renovate for upstream releases.
- **Logging:** per-run logs in `runs/<id>/logs/` (one per task, plus each dependency's stdout/stderr); human progress on stderr; no external monitoring.
- **Scaling:** one machine, one run at a time; parallelism within a run via the worker pool.
- **CLI framework: Typer** (Click-based), generating bash/zsh completion (FR43).

### Decision Impact Analysis

**Implementation sequence:**
1. Project skeleton
2. FCER Pydantic models, JSON Schema, fixture FCERs
3. Statistics harness (driven by fixture `enrich` inputs)
4. Workspace layout, index and ledger, SQLite-on-mount spike
5. GUI results views on fixtures (UX Phase 1)
6. Reference-data manifest + `reference fetch/verify`
7. Image with tool environments; adapters with fixture parsers
8. Engine, invocation recorder, run lock, exit codes
9. NCBI snapshot build/rebuild
10. GUI composer, launch, ledger panel (UX Phase 2)
11. Bundles: export, import, replay
12. GUI compare and import (UX Phase 3)
13. CI matrix and release pipeline (image + reference-data archives)

**Cross-component dependencies:**
- FCER models → harness, GUI, bundles, import validation.
- Ledger schema → engine, supervisor, GUI ledger panel, resume, reindex.
- Invocation recorder → every adapter, provenance block, bundles, replay.
- Tool-environment layout → adapters, image build, CI.
- Predictor manifest → installer predictor flow, `tools add`, provenance.
- Reference manifest → `reference fetch`, run pre-flight, provenance checksums, Zenodo archive.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 14 areas where AI agents could make different choices — genomic coordinates, genome identity, FCER serialization, run/stage/tag identifiers, database naming, module layout, test layout, error-to-exit-code mapping, subprocess invocation, randomness, logging, timestamps, GUI partials/URLs, and ledger state transitions. Generic web concerns (public API envelopes, event buses, client state stores, auth flows) do not apply: there is no public API, no broker, and no auth in v1.

### Domain Conventions (bioinformatics)

**Genomic coordinates — 1-based, inclusive, everywhere outside adapters.**
- FCER, database, GUI, logs and CSV all use `start`/`end` as 1-based inclusive integers (`start <= end`), matching GenBank/GFF/NCBI. Gene length = `end - start + 1`.
- Strand is the string `"+"` or `"-"`. Never `1`/`-1`, never `None` for a located feature.
- Conversion to and from 0-based half-open (Biopython `FeatureLocation`, BED, Python slicing) happens **only inside a tool adapter**, through the two helpers in `flanders.genomics.coords` (`to_zero_based()`, `from_zero_based()`). No other module does coordinate arithmetic with off-by-one adjustments.
- Every coordinate is paired with the nucleotide record `accession.version` it belongs to; a bare coordinate is meaningless.

**Accessions — always versioned.**
- Genome tag (ledger task key, per-genome FCER key, directory name) = **assembly accession.version**, e.g. `GCA_000017845.1`.
- Loci = nucleotide record `accession.version` + coordinates + strand, e.g. `CP002198.1:10521-11834(+)` in human-readable form.
- Proteins = protein `accession.version`. An unversioned accession is a validation error at every boundary (config, adapter output, bundle import).

### Naming Patterns

**Database Naming Conventions:**
- Django defaults: app label prefix + snake_case model name (`ledger_task`, `index_run`). Do not set `db_table`.
- Models are singular CamelCase (`Run`, `Task`, `Snapshot`); fields snake_case; foreign keys named after the related model (`run`, producing `run_id`).
- Status fields use `models.TextChoices` with lowercase values (`pending`, `running`, `complete`, `failed`, `cancelled`, `interrupted`).

**Identifier Conventions:**
- Run ID: `YYYYMMDDTHHMMSSZ-<6 lowercase hex>`, e.g. `20261118T143005Z-a3f9c1`. Generated in one place (`flanders.workspace.ids`).
- Stage IDs: snake_case verbs from the engine's fixed list (`discover`, `extract_flanks`, `annotate_bgc`, `predict_features`, `collapse_paralogs`, `enrich`, `emit_fcer`). Referenced via the `Stage` enum, never as string literals.
- Task key: `(run_id, stage, tag)`; run-wide tasks use tag `run`.
- Location values in FCERs: `upstream`, `seed`, `downstream`.

**Code Naming Conventions:**
- PEP 8, enforced by ruff: `snake_case` functions/variables/modules, `CamelCase` classes, `UPPER_SNAKE` constants.
- Adapters named for the tool: `flanders.adapters.antismash`, `.cblaster`, `.signalp`, … each exposing an `Adapter` class implementing the shared `ToolAdapter` protocol.
- Pydantic models suffixed by role only when ambiguous (`FcerRecord`, `RunConfig`, `EffectiveConfig`); no `Model`/`Schema` suffixes otherwise.
- CLI commands are lowercase single words or hyphenated (`run`, `reanalyze`, `reference fetch`, `bundle export`, `tools add`, `self-update`).

**GUI URL & Template Naming:**
- URLs: lowercase, hyphenated, plural collections — `/runs/`, `/runs/<run_id>/`, `/runs/<run_id>/ledger/`, `/compare/?a=<run_id>&b=<run_id>`.
- All view state (filters, sort, selected test/correction, toggled tracks) lives in query parameters, snake_case.
- Every URL has a `name=` in the form `<app>:<noun>[_<verb>]` (`runs:detail`, `runs:ledger`); templates use `{% url %}`, never hard-coded paths.
- Full pages `<name>.html`; htmx partials `_<name>.html` in the same app's template folder.

### Structure Patterns

**Project Organization:**
- One package, `src/flanders/`, split by responsibility: `cli/`, `config/`, `engine/`, `adapters/`, `features/`, `genomics/`, `harness/`, `fcer/`, `workspace/`, `ncbi/`, `reference/`, `bundles/`, `web/` (Django project + apps). The full tree is in *Project Structure & Boundaries*.
- **Django-free core:** `harness/`, `fcer/`, `genomics/` and `config/` must not import Django (enforced by an import-linter contract in CI).
- Only `workspace/` and `web/` touch the ORM. The engine talks to the ledger through `workspace.ledger` functions, not models directly.
- Shared helpers belong in the module that owns the concept; no catch-all `utils.py`.

**File Structure Patterns:**
- Tests in `tests/`, mirroring `src/flanders/` (`tests/harness/test_binomial.py`). Markers: `unit` (default), `adapter` (fixture-parsed upstream outputs), `e2e` (ebo subset; needs the image).
- Upstream fixtures: `tests/fixtures/<tool>/<version>/<case>/` holding the raw tool output plus an `expected.json` of the parsed result.
- Fixture FCERs: `tests/fixtures/fcer/<schema_version>/`.
- JSON Schema: `schemas/fcer/<major>.<minor>/fcer.schema.json`, generated from Pydantic by `uv run flanders-dev gen-schema`, checked in; CI fails if regeneration produces a diff.
- Per-tool environment lockfiles: `docker/envs/<env-name>.lock`. Reference manifests: `src/flanders/reference/manifests/<release>.yaml`.
- Static assets vendored under `src/flanders/web/static/vendor/`; compiled Tailwind CSS is a build artifact, never committed.

### Format Patterns

**FCER & Data Exchange Formats:**
- JSON keys snake_case. JSON is canonical; CSV is derived from it by one writer, never built independently.
- Floats: written at **full precision** (Python's shortest round-trip repr). Never rounded in an artifact. Cross-host agreement is judged by the published tolerance (NFR2) at comparison time, via `flanders.harness.compare.within_tolerance()` — the only place tolerance is applied.
- Non-finite values: forbidden in FCER JSON. A statistic that cannot be computed is `null` and accompanied by a `reason` code in the same object (e.g. `{"p_value": null, "reason": "zero_background"}`).
- Missing vs not-applicable: an optional field that was not computed is **present with `null`**, never omitted, so additive schema evolution stays unambiguous.
- Booleans are JSON `true`/`false`. Single items are never wrapped in arrays unless the field is inherently a list.
- Timestamps: UTC, ISO 8601 with `Z`, second precision unless sub-second is needed (`2026-11-18T14:30:05Z`). Durations in seconds as floats, field suffix `_s` (`duration_s`).
- Checksums: lowercase hex SHA-256, field suffix `_sha256`.
- Canonical serialization (for checksums): keys sorted, UTF-8, no insignificant whitespace, lists in their defined canonical order — one function, `flanders.fcer.canonical.dumps()`.
- Every FCER has `schema_version` as its first key.

**CLI Output Formats:**
- Results (paths, JSON with `--json`) to stdout only; progress, warnings, and the citation line to stderr. Never prompt; never read stdin unless given `-`.

### Communication Patterns

**Ledger State (in place of an event system):**
- Task states: `pending → running → complete | failed`; run states add `cancelled` and `interrupted`. Only `workspace.ledger` writes state, and only via named transitions (`start_task`, `complete_task`, `fail_task`), each a single transaction.
- `complete_task` is called **only after** the task's `.tmp/` output is fsynced and atomically renamed (NFR7). Nothing else marks completion.
- The GUI never writes ledger state; it reads it (htmx poll ~2 s) and acts only by launching/cancelling the `flanders run` child process.

**Logging Patterns:**
- FLANDERS's own logs: **JSON Lines**, one file per task at `runs/<id>/logs/<stage>/<tag>.jsonl`, plus `runs/<id>/logs/run.jsonl`.
- Every line carries: `ts`, `level`, `run_id`, `stage`, `tag`, `event` (snake_case verb phrase, e.g. `tool_invoked`, `task_completed`), plus event-specific fields.
- Dependency stdout/stderr captured raw beside it: `<tag>.<tool>.stdout` / `.stderr`.
- Levels: `debug` internals, `info` lifecycle events, `warning` per-tag failure or degraded fallback (e.g. predictor chain stepped down), `error` run-halting. Human-readable progress on stderr is a separate, plain-text renderer of the same events.
- Use the stdlib `logging` module via `flanders.logging.get_logger(__name__)`; no `print()` outside the CLI's stdout writer.

### Process Patterns

**Error Handling Patterns:**
- One hierarchy rooted at `FlandersError`, one subclass per exit code: `ConfigError` (2), `DependencyRejectedError` (3), `UpstreamDriftError` (4), `RunLockedError` (5), `ReferenceDataError` (6); cancellation via `RunCancelled` (130). Each class carries its exit code.
- **Per-tag failures do not raise past the engine**: the engine catches them, calls `fail_task` with a reason, logs `warning`, and continues; the run exits `1` if any tag failed.
- Only `flanders.cli` converts exceptions to exit codes and user-facing messages. Library code never calls `sys.exit()`.
- A missing or unreadable input path raises `ConfigError` (exit 2) naming the path and how to make it visible (run from its folder or pass it explicitly).
- User-facing messages name the source (`antismash rejected parameter --foo: <tool stderr excerpt>`) and the next action; full tracebacks go to the log, not stderr (unless `--debug`).
- GUI errors render a partial with the same message text; no separate wording.

**Tool Invocation Patterns:**
- Every external program runs through `flanders.engine.invoke.run_tool()` (the invocation recorder): argv list (never `shell=True`), env name, working dir, timeout. It records tool, version, argv verbatim, input/output checksums, duration, exit status.
- Direct `subprocess` use is banned outside `invoke.py` (ruff `S603`/banned-api rule).
- Retries only for network operations (NCBI), in `flanders.ncbi` with exponential backoff and jitter, every attempt recorded. Tool invocations are never auto-retried.

**Determinism Patterns:**
- Every random operation takes an explicit `numpy.random.Generator` (PCG64) derived from the run seed via `flanders.harness.rng.child(seed, label)`; no `np.random.*` globals, no `random` module.
- Anything that becomes output or feeds a checksum is sorted canonically first (genomes by tag, loci by accession then start, features by ID).
- No wall-clock values inside computed results; timestamps live only in provenance.

**Validation Timing:**
- Validate at boundaries, once: config on load (Pydantic), adapter outputs on parse (version-gated parser + schema check → `UpstreamDriftError`), bundles on import (JSON Schema before any write). Internal code trusts validated models.

**Loading / Progress (GUI):**
- Long work is never done in a request. Requests return immediately; progress shown from ledger polling. Loading indicators use htmx's `hx-indicator` with one shared `_spinner.html`.

### Enforcement Guidelines

**All AI Agents MUST:**
- Use 1-based inclusive coordinates with `"+"`/`"-"` strand outside adapters, and convert only via `genomics.coords`.
- Use versioned accessions everywhere; key genomes by assembly `accession.version`.
- Route every external process through `run_tool()` and every ledger change through `workspace.ledger` transitions.
- Keep `harness/`, `fcer/`, `genomics/`, `config/` free of Django imports.
- Write FCER floats at full precision, `null` + `reason` for uncomputable values, and serialize for checksums only via `fcer.canonical.dumps()`.
- Raise `FlandersError` subclasses; never `sys.exit()` outside the CLI.
- Pass an explicit RNG; never use global random state.
- Add or update a recorded fixture when touching any adapter parser.

**Pattern Enforcement:**
- CI: ruff (style + banned APIs), import-linter (Django-free core), schema regeneration diff check, pytest with ≥90% coverage on `harness/` (NFR23).
- Code review (`bmad-code-review`) checks the MUST list explicitly.
- Changing a pattern means editing this section first, in the same PR as the code.

### Pattern Examples

**Good Examples:**

```python
# adapter boundary: Biopython 0-based half-open -> FLANDERS 1-based inclusive
start, end = coords.from_zero_based(feat.location.start, feat.location.end)  # 1000,1500 -> 1001,1500
locus = Locus(record="CP002198.1", start=start, end=end, strand="+" if feat.location.strand == 1 else "-")

result = run_tool(env="env-antismash8", argv=["antismash", "--taxon", "bacteria", str(fasta)], cwd=task_dir)

rng = rng_mod.child(cfg.seed, "permutation:GCA_000017845.1")
```

```json
{"schema_version": "1.0", "tag": "GCA_000017845.1", "location": "upstream",
 "p_value": 0.0003172839506172839, "p_value_bh": null, "reason": "not_tested"}
```

**Anti-Patterns:**
- `seq[start-1:end-1]` anywhere outside `genomics.coords` (the original FLANDERS bug — drops the last base).
- Keying anything by `"AOGW02000018"` (unversioned) or by organism name.
- `subprocess.run(["antismash", ...])` directly; `shell=True`.
- `round(p, 4)` before writing an FCER; writing `NaN` or `Infinity`.
- Building the CSV from anything other than the FCER JSON.
- Mutating DataFrame rows inside `iterrows()` (the original FLANDERS bug — results silently lost).
- `np.random.seed(...)` / `random.shuffle(...)`.

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
flanders/                                   # repository root
├── README.md                               # quickstart + upstream compatibility matrix (FR67)
├── LICENSE                                 # MIT
├── CITATION.cff                            # FR66
├── CONTRIBUTING.md
├── pyproject.toml                          # uv package; entry points: flanders, flanders-dev; plug-in groups
├── uv.lock
├── .python-version                         # 3.11
├── .importlinter                           # Django-free core contract
├── .gitignore
├── renovate.json                           # FR68
├── install-flanders.sh                     # bootstrap shim installer (FR61)
├── .github/
│   └── workflows/
│       ├── ci.yml                          # ruff, import-linter, unit + adapter tests, schema diff
│       ├── compat-matrix.yml               # antiSMASH 7/8 × cblaster pins (NFR16–17)
│       ├── e2e.yml                         # reduced ebo subset in image (release candidates)
│       ├── recapitulation.yml              # full ebo, two OSes (NFR4; manual/pre-v1)
│       └── release.yml                     # image → GHCR + Zenodo; wheel; DTU layer scan (NFR22)
├── docker/
│   ├── Dockerfile                          # micromamba base, x86-64
│   ├── flanders-shim.sh                    # the `flanders` wrapper installed on PATH
│   └── envs/
│       ├── env-antismash8.yml / .lock
│       ├── env-antismash7.yml / .lock
│       ├── env-cblaster.yml / .lock
│       ├── env-predictors.yml / .lock      # DeepSig + PyTorch + Perl; user-supplied predictors install here
│       └── env-hmmer-mmseqs.yml / .lock
├── schemas/
│   └── fcer/
│       └── 1.0/fcer.schema.json            # generated from Pydantic, checked in (FR26)
├── docs/
│   ├── planning/                           # BMad planning artifacts (this document)
│   ├── index.md                            # Read-the-Docs root (FR69)
│   ├── quickstart.md
│   ├── fcer-reference.md
│   ├── extending.md                        # feature-analyzer + stat-test plug-in guides (FR17, FR23)
│   ├── exit-codes.md                       # FR39
│   ├── curated-parameters.md               # versioned curated list for the GUI composer (FR53)
│   └── tutorial/ebo.ipynb                  # FR69
├── examples/
│   ├── ebo-run.yaml
│   └── plugins/
│       ├── reference_analyzer/             # reference feature-analyzer plug-in (FR17 CI proof)
│       └── reference_stat_test/            # reference stat-test plug-in (FR23 CI proof)
├── src/flanders/
│   ├── __init__.py                         # __version__, CITATION string
│   ├── __main__.py
│   ├── errors.py                           # FlandersError hierarchy + exit codes
│   ├── logging.py                          # get_logger, JSONL handler, stderr renderer
│   ├── cli/
│   │   ├── app.py                          # Typer root; exception → exit code; citation on stderr
│   │   ├── run.py                          # flanders run
│   │   ├── reanalyze.py                    # = replay --from enrich with new stats settings
│   │   ├── bundle.py                       # export / import
│   │   ├── replay.py
│   │   ├── snapshot.py                     # build / rebuild
│   │   ├── reference.py                    # fetch / verify
│   │   ├── workspace.py                    # reindex, init
│   │   ├── gui.py                          # starts Django server on loopback
│   │   ├── tools.py                        # tools status / add / help (predictor setup)
│   │   └── dev.py                          # flanders-dev: gen-schema, record-fixture
│   ├── config/                             # Django-free
│   │   ├── models.py                       # RunConfig (Pydantic), FLANDERS-owned keys
│   │   ├── loader.py                       # YAML load, --cblaster-*/--antismash-* flag parsing
│   │   ├── merge.py                        # flag > file > default → EffectiveConfig (FR8, FR27)
│   │   └── export.py                       # provenance → runnable config (FR36)
│   ├── genomics/                           # Django-free
│   │   ├── coords.py                       # the only 0↔1-based conversion
│   │   ├── accessions.py                   # versioned-accession parsing/validation (FR83)
│   │   ├── models.py                       # Locus, Orf, Neighborhood
│   │   └── tree.py                         # Newick parse + tip matching (FR33)
│   ├── engine/
│   │   ├── stages.py                       # Stage enum, stage order, task fan-out
│   │   ├── scheduler.py                    # worker pool, per-tag failure isolation, resume (FR47–48)
│   │   ├── supervisor.py                   # run lock, heartbeat, SIGTERM/SIGKILL cancel
│   │   ├── invoke.py                       # run_tool(): invocation recorder (FR79)
│   │   ├── atomic.py                       # .tmp → fsync → rename
│   │   ├── report.py                       # run report: failed/excluded tags (FR49)
│   │   └── pipeline.py                     # run(), replay(from_stage) entry points used by CLI and GUI
│   ├── adapters/
│   │   ├── base.py                         # ToolAdapter protocol, version gate, drift detection
│   │   ├── cblaster.py
│   │   ├── antismash.py                    # v7 + v8 parsers
│   │   ├── signalp.py                      # SignalP 6 (user-installed) / 5
│   │   ├── deepsig.py
│   │   ├── phobius.py
│   │   ├── tmhmm.py                        # user-installed (FR64)
│   │   ├── hmmscan.py
│   │   └── mmseqs.py
│   ├── features/
│   │   ├── base.py                         # FeatureAnalyzer interface + entry-point discovery (FR17)
│   │   ├── signal_peptide.py               # fallback chain + concordance (FR15–16)
│   │   ├── transmembrane.py
│   │   └── pfam.py
│   ├── harness/                            # Django-free; ≥90% coverage
│   │   ├── background.py                   # paralog-collapsed per-genome null (FR18–19)
│   │   ├── tests/                          # (statistical tests, not pytest)
│   │   │   ├── base.py                     # StatTest interface + entry-point discovery (FR23)
│   │   │   ├── binomial.py
│   │   │   └── permutation.py
│   │   ├── correction.py                   # BH, Bonferroni (FR21)
│   │   ├── effect.py                       # effect sizes
│   │   ├── covariates.py                   # GC%, gene length (FR22)
│   │   ├── rng.py                          # seeded child generators
│   │   └── compare.py                      # within_tolerance(), run diff (FR72)
│   ├── fcer/                               # Django-free
│   │   ├── models.py                       # Pydantic FCER (source of the JSON Schema)
│   │   ├── provenance.py                   # versions, checksums, invocations, fallbacks (FR27–31)
│   │   ├── canonical.py                    # canonical dumps() for checksums
│   │   ├── io.py                           # JSON read/write + schema validation
│   │   └── csv.py                          # CSV derived from JSON (FR25)
│   ├── ncbi/
│   │   ├── client.py                       # Datasets CLI + E-utilities, api_key, backoff
│   │   ├── snapshot.py                     # build DB + manifest (FR81)
│   │   └── rebuild.py                      # rebuild from manifest, report missing (FR82)
│   ├── reference/
│   │   ├── manifests/<release>.yaml        # URL, version, SHA-256 per file
│   │   └── fetch.py                        # download + verify; run pre-flight (FR84)
│   ├── tools/                              # user-supplied predictor setup (FR64)
│   │   ├── manifests/<release>.yaml        # request URL, expected archive names, versions, checksums
│   │   ├── manifest.py
│   │   ├── install.py                      # identify → verify → install → test prediction
│   │   └── recipes/{signalp6,signalp5,tmhmm,phobius}.py
│   ├── workspace/                          # ORM access lives here
│   │   ├── layout.py                       # path convention for every workspace file
│   │   ├── ids.py                          # run IDs
│   │   ├── ledger.py                       # start/complete/fail transitions (FR45–50)
│   │   ├── index.py                        # run history + FCER index queries (FR71)
│   │   ├── reindex.py                      # rebuild DB from files (FR78)
│   │   ├── django_setup.py                 # minimal settings bootstrap for headless CLI
│   │   └── models.py                       # Run, Task, Snapshot, FcerEntry, Import (Django models)
│   ├── bundles/
│   │   ├── export.py                       # full / --slim (FR73)
│   │   ├── importer.py                     # validate → sanitize paths → read-only import (FR74–76)
│   │   └── replay.py                       # from discovery snapshot (FR80)
│   └── web/
│       ├── site/                           # Django project: settings, urls, wsgi
│       ├── core/                           # base layout, shared partials, components gallery (debug)
│       │   ├── templates/core/{base.html,_spinner.html,_error.html,components.html}
│       │   └── templatetags/
│       ├── runs/                           # history, detail, launch/cancel, live ledger (FR60, FR70–71)
│       │   ├── views.py, urls.py
│       │   └── templates/runs/{list.html,detail.html,_ledger.html,_run_row.html}
│       ├── composer/                       # run composer, curated + free-form params (FR52–55)
│       │   ├── forms.py, views.py, urls.py
│       │   └── templates/composer/{compose.html,_command.html}
│       ├── results/                        # enrichment table, neighborhood map, provenance, stats-replay launch (FR56–59)
│       │   ├── views.py, urls.py, svg.py   # server-side neighborhood SVG
│       │   └── templates/results/{fcer.html,_enrichment_table.html,_stats_bar.html,_neighborhood.html,_provenance.html}
│       ├── compare/                        # FR72
│       │   └── templates/compare/{compare.html,_diff_table.html}
│       ├── imports/                        # GUI import (FR74)
│       ├── predictors/                     # Predictors page: status, instructions, archive picker
│       ├── static/
│       │   ├── vendor/{htmx.min.js,alpine.min.js,fonts/}
│       │   └── css/input.css               # Tailwind source; compiled output not committed
│       └── migrations/                     # per app, as Django lays out
└── tests/
    ├── conftest.py                         # tmp workspace fixture, Django settings
    ├── cli/  config/  genomics/  adapters/  features/  tools/
    ├── engine/                             # incl. test_kill_resume.py (NFR7 kill-injection per stage)
    ├── harness/                            # incl. statsmodels reference comparisons (NFR23)
    ├── fcer/  ncbi/  reference/  bundles/
    ├── workspace/                          # incl. test_reindex_1000.py (NFR26)
    ├── web/                                # pytest-django view + partial tests
    ├── plugins/                            # loads examples/plugins/*, asserts no core changes needed
    ├── e2e/                                # ebo subset (marker: e2e)
    └── fixtures/
        ├── cblaster/<version>/<case>/
        ├── antismash/{7.x,8.x}/<case>/
        ├── signalp/ deepsig/ phobius/ tmhmm/ hmmscan/ mmseqs/
        ├── fcer/1.0/
        └── bundles/
```

**User workspace (runtime, on host; not in repo)** — owned by `workspace/layout.py`:

```text
~/flanders/
├── .flanders/            # index.sqlite3, run.lock, workspace version
├── drafts/               # GUI-composed configs not yet run
├── runs/<run_id>/
│   ├── config.yaml               # as submitted
│   ├── inputs/                   # copied query, genome list, local DB (checksummed)
│   ├── config.effective.yaml     # merged (FR27)
│   ├── manifest.json             # snapshot manifest or remote-search metadata
│   ├── invocations.jsonl         # every recorded tool call (FR79)
│   ├── stages/<stage>/<tag>/     # content-addressed stage outputs (raw tool outputs here)
│   ├── fcer/<tag>.<location>.json|.csv
│   ├── report.json               # failed/excluded tags with reasons (FR49)
│   ├── tree.nwk                  # if supplied (FR33)
│   └── logs/{run.jsonl,<stage>/<tag>.jsonl,<tag>.<tool>.stdout|stderr}
├── imports/<run_id>/     # read-only, same layout + origin.json
├── snapshots/<snapshot_id>/      # BLAST DB + manifest
├── reference/<release>/          # antiSMASH DBs, Pfam-A, ebo DB
└── tools/                        # user-supplied SignalP 6 / SignalP 5 / TMHMM 2.0c / Phobius
```

### Architectural Boundaries

**API Boundaries:**
- No network API in v1. The **public programmatic surface** is: the CLI (verbs + exit codes), the FCER JSON Schema, the run-config YAML, and the two plug-in entry-point groups (`flanders.features`, `flanders.stat_tests`). Everything else is internal and may change between minor versions.
- The GUI is loopback-only HTTP serving HTML; its URLs are not an API.

**Component Boundaries:**
- `cli/` and `web/` are thin; both call `engine.pipeline` (run and replay, including stats-only replay), `bundles`, `tools`, `workspace.index`. Neither contains pipeline logic.
- `web/` launches runs only by spawning `flanders run -c <config>` via `engine.supervisor`; it never imports `engine.scheduler`.
- `adapters/` know one tool each and nothing about stages; `features/` and `engine/` know about adapters; `harness/` knows only FCER/genomics models.

**Service Boundaries (external processes):**
- Every tool runs in its own conda env through `engine.invoke.run_tool()`. NCBI is reached only via `ncbi/`. Reference downloads only via `reference/fetch.py`.

**Data Boundaries:**
- Files under the workspace are the source of truth; `workspace/models.py` is a rebuildable index.
- Only `workspace/` imports Django models. `harness/`, `fcer/`, `genomics/`, `config/` are Django-free (import-linter).
- FCERs and bundles are the only formats crossing machine boundaries.

### Requirements to Structure Mapping

| FR group | Primary location | Tests |
|---|---|---|
| Run configuration (FR1–FR8) | `config/`, `cli/run.py` | `tests/config/` |
| Discovery & flank annotation (FR9–FR17) | `adapters/`, `features/`, `engine/stages.py` | `tests/adapters/`, `tests/features/`, `tests/plugins/` |
| Enrichment (FR18–FR23) | `harness/` | `tests/harness/`, `tests/plugins/` |
| Artifact & provenance (FR24–FR33) | `fcer/`, `engine/report.py`, `genomics/tree.py`, `schemas/` | `tests/fcer/` |
| Re-analysis & verification (FR34–FR37) | `engine/pipeline.py` (replay from `enrich`), `bundles/replay.py`, `config/export.py`, `cli/reanalyze.py` | `tests/engine/`, `tests/bundles/` |
| CLI operation (FR38–FR44) | `cli/`, `errors.py`, `logging.py` | `tests/cli/` |
| Run ledger (FR45–FR50) | `workspace/ledger.py`, `engine/scheduler.py` | `tests/workspace/`, `tests/engine/` |
| GUI (FR51–FR60, FR70–FR72) | `web/{runs,composer,results,compare}/`, `engine/supervisor.py` | `tests/web/` |
| Workspace & sharing (FR73–FR80) | `workspace/`, `bundles/` | `tests/workspace/`, `tests/bundles/` |
| Search reproducibility (FR81–FR83) | `ncbi/`, `genomics/accessions.py` | `tests/ncbi/` |
| Reference data (FR84) | `reference/` | `tests/reference/` |
| Install & distribution (FR61–FR65) | `docker/` (incl. shim + `self-update`), `install-flanders.sh`, `tools/`, `web/predictors/` | `tests/tools/`, `e2e.yml` |
| Release & compatibility (FR66–FR69) | `.github/workflows/`, `renovate.json`, `CITATION.cff`, `docs/` | `compat-matrix.yml` |

**Cross-Cutting Concerns:**
- Provenance capture → `engine/invoke.py` + `fcer/provenance.py`
- Atomic task outputs → `engine/atomic.py` + `workspace/ledger.py`
- Error taxonomy → `errors.py` (raised everywhere, mapped only in `cli/app.py`)
- Determinism → `harness/rng.py`, `fcer/canonical.py`
- Single active run → `engine/supervisor.py`
- Upstream drift → `adapters/base.py` + `tests/fixtures/<tool>/<version>/`

### Integration Points

**Internal Communication:** direct Python calls inside one process for CLI runs; GUI ↔ run via child process + ledger polling (SQLite) + SIGTERM for cancel. No queues, sockets, or threads shared with the web server.

**External Integrations:** cblaster, antiSMASH 7/8, DeepSig (bundled) and user-supplied SignalP/Phobius/TMHMM, HMMER, mmseqs2 (subprocesses in per-tool envs); NCBI Datasets + E-utilities (HTTPS); reference-data hosts + Zenodo (HTTPS, fetch only); GHCR (image pull, shim only).

**Data Flow:**
`config.yaml` → `config.merge` → EffectiveConfig → `discover` (cblaster) → `extract_flanks` → `annotate_bgc` (antiSMASH) → `predict_features` (feature analyzers) → `collapse_paralogs` (mmseqs2) → `enrich` (harness) → `emit_fcer` (fcer) → `runs/<id>/fcer/` + `report.json` → index → GUI / bundle; stats-only replay re-enters at `enrich`.

### File Organization Patterns

**Configuration Files:** project tooling in `pyproject.toml` (ruff, pytest, uv, entry points); import contracts in `.importlinter`; per-tool envs in `docker/envs/`; Django settings in `web/site/settings.py`, overridden only by `FLANDERS_WORKSPACE` and `FLANDERS_GUI_PORT` env vars; no `.env` files.

**Source Organization:** one package by responsibility (above); one adapter per tool; plug-in interfaces in `features/base.py` and `harness/tests/base.py`.

**Test Organization:** mirrors `src/`; markers `unit` / `adapter` / `e2e`; plug-in proof in `tests/plugins/`; fixtures by tool and version.

**Asset Organization:** vendored JS and fonts in `web/static/vendor/`; Tailwind source in `web/static/css/input.css`, compiled at build into `web/static/css/app.css` (gitignored, shipped in wheel/image).

### Development Workflow Integration

**Development Server Structure:** `uv run flanders gui --dev` runs Django's dev server with debug, the `/_components` gallery, and Tailwind in watch mode; pipeline work is tested without the image via adapter fixtures; tool-dependent work runs inside the image with the repo bind-mounted.

**Build Process Structure:** Tailwind compile → `uv build` (wheel with compiled CSS, schemas, reference manifests) → `docker build` (micromamba envs from lockfiles + wheel).

**Deployment Structure:** release workflow tags → GHCR image + wheel → Zenodo DOI for image tarball; reference-data archive DOI per manifest release; shim pulls by digest.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:** Python ≥3.11 satisfies Django 5.2 LTS, Typer, Pydantic v2, numpy/scipy (`false_discovery_control` needs scipy ≥1.11); antiSMASH 7/8, cblaster, HMMER, mmseqs2 and DeepSig run in isolated per-tool environments, so their pins never meet FLANDERS's own. SQLite (DELETE journal, single writer) fits one-run-at-a-time on a host mount. No contradictory decisions remain (Typer "provisional" note removed).

**Pattern Consistency:** naming, coordinates (1-based inclusive), versioned accessions, FCER serialization, error taxonomy and logging conventions are applied consistently in the structure and examples. The ledger has a single writer (the scheduler's parent process), which matches the SQLite-on-mount constraint.

**Structure Alignment:** every decision has a home in the tree; the Django-free core (`config/`, `genomics/`, `harness/`, `fcer/`) is enforceable by import-linter; the GUI reaches the pipeline only through a child `flanders run` process.

### Requirements Coverage Validation ✅ (with PRD/UX changes pending — see below)

**Functional Requirements Coverage:** all FR groups map to modules (Requirements to Structure Mapping). Changes decided during validation alter FR24, FR34–FR37, FR49, FR59, FR63, FR72, FR73 and add capabilities (input capture, predictor setup, self-update); these must be applied to the PRD before epics are created.

**Non-Functional Requirements Coverage:**
- Determinism (NFR1–6): seeded child RNGs, canonical serialization, full-precision floats with comparison-time tolerance, versioned accessions, manifest-pinned snapshots, captured run inputs.
- Reliability (NFR7–9): atomic task outputs, single-writer ledger, named kill-injection test, run report listing every excluded tag.
- Scale (NFR10–12): worker pool per run; overhead measured from invocation-recorder durations.
- Portability (NFR13–15): one x86-64 image, shim with `--platform linux/amd64`, installer handles Docker provisioning.
- Integration (NFR16–19): version-gated parsers + fixtures per upstream version; additive-only schema; no prompts outside installer/GUI; `run --out` for workflow steps.
- Security (NFR20–22): loopback-only GUI, no telemetry, image ships no DTU or registration-gated binaries (DeepSig only), CI layer scan.
- Maintainability & Durability (NFR23–27): harness coverage + statsmodels reference tests; workspace-as-truth with rebuildable index; upgrade-over-fixture test; named 1,000-run reindex test.

### Implementation Readiness Validation ✅

**Decision Completeness:** all blocking decisions made and versioned; remaining open items are deliberately deferred to named early stories (mmseqs2 identity threshold; SQLite-on-mount spike).

**Structure Completeness:** full repository tree and runtime workspace layout defined, with file-level placement for every FR group.

**Pattern Completeness:** 14 conflict areas covered with MUST rules, CI enforcement, and good/anti-pattern examples (including both bugs from the original FLANDERS).

### Gap Analysis Results

**Critical (resolved during validation):**
- *Re-analysis data dependency:* FR34's "re-analyze from a saved FCER alone" would have required embedding full per-genome background ORF tables in FCER 1.0. **Resolved:** statistics-only re-analysis from an FCER is dropped; statistics changes are a stats-only replay from the `enrich` stage using stored stage outputs (own runs) or a bundle (shared runs). Slim bundles retain the `enrich` inputs.

**Important (resolved during validation):**
- Shim could not see input files outside the workspace → shim mounts CWD and input-file folders read-only; inputs copied into `runs/<id>/inputs/`; `run --out` for workflow integration.
- Concurrent SQLite writes from workers → single writer (scheduler parent).
- Cross-genome aggregate method unspecified → **aggregate FCER dropped from v1**; failed/excluded tags reported in the run report.
- Predictor licensing → SignalP 5 and Phobius are also restricted; image ships DeepSig only; installer prompts for user-downloaded archives and installs them; `flanders tools add` for later.
- Upgrade path undefined → `flanders self-update`.
- Non-Docker installs → **Docker is the only v1 install path**; pip/bioconda deferred post-v1 (recorded trade-off: the brief identified bioconda as important for community uptake).

**Nice-to-have (deferred):**
- Exact predictor archive names/checksums once DTU files are obtained.
- Measured image, reference-data and snapshot sizes (architecture-to-verify items from the PRD).

### Validation Issues Addressed

All issues above were resolved with the author between 2026-11-18 and 2026-11-22. Resulting **PRD changes required** (apply via `bmad-edit-prd` before epics):
- FR24: remove cross-genome aggregate FCER (per-genome × location only).
- FR49: failed/excluded tags listed in the run report (and bundle), not an aggregate FCER.
- FR34–FR37, FR59: re-analysis = stats-only replay from stored stage outputs or a bundle, creating a variant run; FR37 reproduces from a bundle, not provenance alone.
- FR72: comparison of runs, including stats-only variants.
- FR73: slim bundles keep `enrich` inputs.
- FR63: removed for v1 (Docker only).
- FR15/FR64: predictor setup via installer prompt for downloaded archives + `flanders tools add`.
- New: input capture into the run folder (no run-time prompts; GUI file picker); `run --out`; `flanders self-update`.
- Journeys 2 (reviewer uses bundle replay) and 3 (`--out`); NFR11 (re-analysis time = stats-only replay time); brief/distillate note on bioconda deferral.

**UX spec changes required:** Flow 2 "Interrogate the Aggregate" and the aggregate enrichment table / statistics bar (no aggregate in v1; stats changes launch a stats-only replay); Flow 5 (reviewer verifies via bundle); new installer/Predictors page flow.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION once the listed PRD and UX changes are applied.

**Confidence Level:** medium-high — architecture is internally coherent; confidence is capped until PRD/UX are brought in line and the SQLite-on-mount spike passes.

**Key Strengths:**
- Reproducibility is structural (image + checksummed reference data + manifest-pinned snapshots + captured inputs + verbatim invocations), not a promise.
- Upstream tools are isolated and version-gated, so churn fails loudly in CI instead of silently in results.
- One replay mechanism serves resume, variant runs, statistics changes and reviewer verification.
- Patterns explicitly prevent both known failure modes of the original FLANDERS.

**Areas for Future Enhancement:** pip/bioconda install path; cross-genome aggregate statistics; stage reuse across variant runs; v2 hosted webapp.

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and boundaries
- Refer to this document for all architectural questions

**First Implementation Priority:** project skeleton — `uv init --package --name flanders --python 3.11 .`, then the FCER Pydantic models and JSON Schema (implementation sequence steps 1–2).
