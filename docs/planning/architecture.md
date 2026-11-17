---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/validation-report-2026-11-06.md
  - docs/product-brief.md
  - docs/product-brief-distillate.md
workflowType: 'architecture'
project_name: 'flanders'
user_name: 'Kevin Klicki'
date: '2026-11-06'
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
| Artifact & provenance | FR24–FR33 | FCER schema (JSON Schema, CSV + JSON writers), provenance block, tree validation and retention |
| Re-analysis & verification | FR34–FR37 | Harness runs from a saved FCER alone, with no access to heavy outputs |
| CLI operation | FR38–FR44 | Exit-code taxonomy, stdout/stderr separation, fail loudly on output drift, shell completion |
| Run ledger | FR45–FR50 | Persistent per-tag task state, resume, failure isolation |
| GUI | FR51–FR60, FR70–FR72 | Local Django app: composer, launch/cancel, live ledger, results, compare, provenance |
| Workspace, sharing, search reproducibility | FR73–FR83 | Workspace layout and index, bundle export/import/replay, NCBI snapshot build and rebuild, verbatim invocation records |
| Installation & distribution | FR61–FR65 | Single x86-64 image, bootstrap shim, conda/pip expert path, user-installed DTU predictors |
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
- **Re-analysis runs on the server.** Light-analytics changes recompute on the server and return a table fragment, so the harness must run in-process from a saved FCER (a design goal, not a target).
- **The neighborhood map is drawn on the server,** as SVG built from FCER coordinates.
- **Views are addressable.** All view state lives in the URL.
- **The GUI must work offline.** Fonts and CSS are self-hosted.

### Technical Constraints & Dependencies

- Python 3.11 or newer; one x86-64 Docker image as the canonical runtime (Linux, macOS Intel, Apple Silicon via emulation, WSL2).
- **Decided stack:** Django with server-rendered templates, htmx, Tailwind (compiled CSS) and Alpine.js. The ledger, run history and FCER index live in SQLite inside the workspace.
- **Orchestrated tools, version-pinned:** cblaster, antiSMASH 7, HMMER (`hmmscan`) with Pfam-A, mmseqs2, and the predictor chain (SignalP 5 / DeepSig / Phobius in the image; SignalP 6 and TMHMM 2.0c installed by the user only).
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

*Exact package layout is set in Project Structure; pinned versions are captured in `uv.lock` at initialization. Typer is provisional pending the CLI-framework decision.*

**Architectural Decisions Provided by Starter:**

- **Language & runtime:** Python ≥3.11 (also antiSMASH 8's floor); `src/` layout; uv lockfile.
- **Styling:** Tailwind v4 via standalone CLI; compiled CSS is a build artifact shipped in the wheel and image.
- **Build tooling:** uv build backend for the wheel; Tailwind build runs before packaging; Docker image built separately.
- **Testing:** pytest + pytest-django; fixture FCERs and recorded upstream outputs under `tests/fixtures/` (NFR17).
- **Code organization:** single `flanders` package, Django project as `flanders.web`; pipeline and harness importable without Django settings (headless CLI, `reanalyze`).
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
- **Predictor fallback chain:** SignalP 6 → SignalP 5 → DeepSig → Phobius, whichever are present; the chain actually used is recorded per run (FR15). Concordance mode runs every available predictor (FR16).

### Pipeline Engine

- **Custom task engine; the SQLite ledger is its state.**
- Stages: `discover → extract_flanks → annotate_bgc → predict_features → collapse_paralogs → enrich → emit_fcer`. Tasks keyed by `(run, stage, tag)`, tag = genome accession (or `run` for run-wide stages).
- A worker pool runs per-genome tasks in parallel (`--jobs N`, default CPU count − 1); the engine only schedules, tools do the heavy work.
- **Replay** (FR80) starts at `extract_flanks` from a bundle's captured discovery outputs. **Reanalyze** runs only the harness, from FCERs.

### Statistics Stack

- numpy + scipy (`binomtest`; `false_discovery_control` for BH); Bonferroni implemented directly; permutation tests use a seeded `numpy.random.Generator` (PCG64), seed recorded (NFR3).
- statsmodels is a **test-only** dependency serving as the independent reference implementation (NFR23).
- mmseqs2 paralog collapsing at a configurable identity threshold; **the default is set in an early harness story** (open from the brief) and recorded in every FCER (FR19).

### Frontend Architecture

As specified in the UX spec: Django templates with partials as components, htmx 2.x, Alpine.js 3, Tailwind v4 standalone CLI, server-rendered SVG neighborhood maps, view state in the URL query string, no JS bundler. Static assets vendored for offline use; debug-only `/_components` gallery.

### Infrastructure & Deployment

- **Image:** one x86-64 image on a micromamba base: FLANDERS's environment from `uv.lock` plus per-tool conda environments with explicit lockfiles. **No reference data in the image.** Published to GHCR; each release saved as a tarball to Zenodo with its own DOI, alongside the reference-data archive DOI.
- **Shim** (`install-flanders.sh`): installs Docker if missing, pulls the image, installs a `flanders` wrapper that mounts the workspace, passes `--platform linux/amd64`, binds the GUI to loopback, and forwards arguments and exit codes unchanged. First use prompts in the installer (not in `flanders run`) to run `flanders reference fetch`.
- **CI (GitHub Actions):**
  - Unit tests: harness, config, schema.
  - Adapter fixture tests: antiSMASH 7 and 8 × supported cblaster pins (NFR16–NFR17).
  - Reduced *ebo* subset end to end on every release candidate.
  - Full *ebo* recapitulation on two OSes before v1 (NFR4).
  - Image-layer scan for DTU binaries; upgrade-over-populated-workspace test (NFR25); reference-manifest checksum check.
  - Renovate for upstream releases.
- **Logging:** per-run logs in `runs/<id>/logs/` (one per task, plus each dependency's stdout/stderr); human progress on stderr; no external monitoring.
- **Scaling:** one machine, one run at a time; parallelism within a run via the worker pool.
- **CLI framework: Typer** (Click-based), generating bash/zsh completion (FR43).

### Decision Impact Analysis

**Implementation sequence:**
1. Project skeleton
2. FCER Pydantic models, JSON Schema, fixture FCERs
3. Statistics harness + `reanalyze`
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
- Tool-environment layout → adapters, image build, CI, conda expert path (pinned `env.yml` becomes one file per tool environment).
- Reference manifest → `reference fetch`, run pre-flight, provenance checksums, Zenodo archive.
