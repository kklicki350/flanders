---
validationTarget: '_bmad-output/planning-artifacts/prd.md'
validationDate: '2026-11-06'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - docs/product-brief.md
  - docs/product-brief-distillate.md
  - _bmad-output/planning-artifacts/flanders-brief-session-state.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - archive/flanders_original_repo/ (legacy code, reference only)
  - archive/skip_smash_original/ (legacy code, reference only)
validationStepsCompleted: [step-v-01-discovery, step-v-02-format-detection, step-v-03-density-validation, step-v-04-brief-coverage-validation, step-v-05-measurability-validation, step-v-06-traceability-validation, step-v-07-implementation-leakage-validation, step-v-08-domain-compliance-validation, step-v-09-project-type-validation, step-v-10-smart-validation, step-v-11-holistic-quality-validation, step-v-12-completeness-validation]
validationStatus: COMPLETE
holisticQualityRating: '4/5 - Good'
overallStatus: Pass
fixesApplied: '2026-11-06'
---

# PRD Validation Report

**PRD Being Validated:** _bmad-output/planning-artifacts/prd.md
**Validation Date:** 2026-11-06

## Input Documents

- PRD: `_bmad-output/planning-artifacts/prd.md` (edited 2026-11-06)
- Product brief: `docs/product-brief.md`
- Brief distillate: `docs/product-brief-distillate.md`
- Brief session state: `_bmad-output/planning-artifacts/flanders-brief-session-state.md`
- Additional reference: `_bmad-output/planning-artifacts/ux-design-specification.md` (source of the 2026-11-06 edit)
- Legacy code (8 files, reference only): `archive/flanders_original_repo/`, `archive/skip_smash_original/`

## Validation Findings


## Format Detection

**PRD Structure:** Executive Summary · Project Classification · Success Criteria · Product Scope · User Journeys · Domain-Specific Requirements · Innovation & Novel Patterns · CLI Tool Specific Requirements · Project Scoping & Phased Development · Functional Requirements · Non-Functional Requirements

**BMAD Core Sections Present:** Executive Summary ✓ · Success Criteria ✓ · Product Scope ✓ · User Journeys ✓ · Functional Requirements ✓ · Non-Functional Requirements ✓

**Format Classification:** BMAD Standard
**Core Sections Present:** 6/6

## Information Density Validation

**Conversational Filler:** 0 occurrences
**Wordy Phrases:** 0 occurrences
**Redundant Phrases:** 0 occurrences
*(Three instances of "not just" — lines 75, 107, 213 — are deliberate contrasts, e.g. "checksums, not just version strings", and are not counted.)*

**Total Violations:** 0
**Severity Assessment:** Pass
**Recommendation:** PRD demonstrates good information density with minimal violations.

## Product Brief Coverage

**Product Brief:** `docs/product-brief.md` (2026-05-02)

### Coverage Map

**Vision Statement:** Fully covered (Executive Summary; Product Scope v1.5/v2/Beyond).
**Target Users:** Fully covered (Journeys 1–3; v2 non-coder actor footnote).
**Problem Statement:** Fully covered (Executive Summary, "orchestration with statistical rigor").
**Key Features:** Fully covered, with intentional supersessions:
- Brief's FastAPI + SPA GUI → **Intentionally Excluded**, replaced by Django + htmx (PRD Decided Constraints, 2026-11-06 edit).
- Brief's "Live cblaster runs through the UI" as out-of-v1 → **Intentionally changed**: GUI launch is now v1 (FR60).
- Brief's pluggable Fisher / hypergeometric tests → **Partially covered**: FR20 names binomial + permutation; FR23 provides the extension interface but Fisher/hypergeometric are not named. *Informational.*
**Goals/Objectives:** Fully covered (Success Criteria; reproducibility contract extended with fresh-snapshot mode).
**Differentiators:** Fully covered; "built for the reviewer" deliberately reordered to second-order claim (Innovation → Risk Mitigation → Framing).
**Constraints / Risks:**
- Compatibility-patch SLA in CONTRIBUTING (brief Risks) → **Not found**. *Informational.*
- Frontend-rot risk (SPA/npm churn) → **Intentionally excluded**; obsoleted by the server-rendered stack.
- Locked-down-laptop GUI friction → covered by the v2 hardening pass.

### Coverage Summary

**Overall Coverage:** High — all core brief content present; every divergence traceable to a recorded decision.
**Critical Gaps:** 0
**Moderate Gaps:** 0
**Informational Gaps:** 2 — Fisher/hypergeometric tests not named; compatibility-patch SLA not stated.

**Recommendation:** PRD provides good coverage of Product Brief content.

## Measurability Validation

### Functional Requirements

**Total FRs Analyzed:** 83 (FR1–FR83)

**Format Violations:** 0 — all FRs use "[actor] can …" or "The system / Every FCER …" capability forms. FR46, FR48, FR55 use passive or conditional phrasing but remain testable.
**Subjective Adjectives Found:** 0
**Vague Quantifiers Found:** 0 ("multiple-testing" is a statistical term, not a quantifier.)
**Implementation Leakage:** 0 — named tools (cblaster, antiSMASH, NCBI), output formats (CSV, JSON), and shells (bash, zsh) are capability-defining: they are the orchestrated dependencies, the published output contract, and the completion targets.

**FR Violations Total:** 0

**Informational — FR ordering:** new FR70–FR83 appear in the document before FR61–FR69 (inserted into *Interactive GUI* and a new *Workspace, Sharing & Search Reproducibility* subsection ahead of *Installation & Distribution*). IDs were kept stable deliberately; readers scanning sequentially may be confused.

### Non-Functional Requirements

**Total NFRs Analyzed:** 27

**Missing Metrics:** 1
- NFR10 (line ~593): "~1,000 genomes … without architectural change" — "without architectural change" is not measurable; the scale target itself is approximate.

**Incomplete Template (no measurement method):** 3
- NFR5: Apple Silicon emulation equivalence — no stated verification method (could reuse the NFR4 corpus test).
- NFR7: ledger survives abrupt termination — no stated test (e.g., kill-injection test at each stage).
- NFR12: <5% orchestration overhead — no stated measurement method.

**Missing Context:** 0

**NFR Violations Total:** 4

**Notable gap (not a template violation):** the UX specification names re-analysis latency as a make-or-break failure ("re-analysis slow enough to break the thinking loop"), but NFR11 deliberately sets no latency targets. The GUI's core loop therefore has no measurable acceptance criterion.

### Overall Assessment

**Total Requirements:** 110
**Total Violations:** 4
**Severity:** Pass
**Recommendation:** Requirements demonstrate good measurability with minimal issues. Consider adding measurement methods to NFR5, NFR7, NFR12, tightening NFR10, and deciding whether light-analytics re-analysis needs a latency target.

## Traceability Validation

### Chain Validation

**Executive Summary → Success Criteria:** Intact. Orchestration, statistics, the FCER, reproducibility, and the GUI (compose/launch/compare/import) all have corresponding success criteria.
**Success Criteria → User Journeys:** Intact. Single-invocation run, light re-analysis, variant + compare, and GUI configuration → J1; reviewer verdict and bundle recapitulation → J2; headless pipeline use → J3; dependency-churn resilience → J4; cross-machine recapitulation → *Innovation → Validation Approach* (business objective).
**User Journeys → Functional Requirements:** Intact.
**Scope → FR Alignment:** Intact. Every v1 must-have item maps to at least one FR.

### Orphan Elements

**Orphan Functional Requirements:** 0
**Unsupported Success Criteria:** 0
**User Journeys Without FRs:** 0

### Traceability Matrix

| Source | FRs |
|---|---|
| J1 — author-runner | FR1–FR16, FR18–FR22, FR24–FR30, FR38, FR44–FR60, FR70–FR73, FR77–FR78, FR81, FR83 |
| J2 — reviewer | FR26–FR31, FR34–FR37, FR58–FR59, FR62, FR65, FR74–FR76, FR79–FR80, FR82 |
| J3 — pipeline integrator | FR2, FR8, FR25–FR26, FR35, FR38–FR43, FR73–FR74 (CLI verbs) |
| J4 — maintainer | FR41, FR66–FR68 |
| Business objectives (v2 hooks, distribution, citability) | FR17, FR23, FR32–FR33, FR61–FR64, FR69 |

**Total Traceability Issues:** 0
**Severity:** Pass
**Recommendation:** Traceability chain is intact — all requirements trace to user needs or business objectives.

## Implementation Leakage Validation

### Leakage by Category

**Frontend Frameworks:** 0
**Backend Frameworks:** 0 in FRs/NFRs. Django and htmx appear only in *Decided Constraints for Architecture* and *editHistory*, a deliberate constraints section, not requirements.
**Databases:** 0 in FRs/NFRs. SQLite appears only in *Decided Constraints*.
**Cloud Platforms:** 0
**Infrastructure:** 0 violations. "Container image" (FR62, FR77, NFR13, NFR25) is capability-relevant: container distribution is the product's install and reproducibility contract.
**Libraries:** 0
**Other Implementation Details:** 0. CSV/JSON (FR25) and `accession.version` (FR83) define the published output contract.

### Summary

**Total Implementation Leakage Violations:** 0
**Severity:** Pass
**Recommendation:** No significant implementation leakage found. Requirements properly specify WHAT without HOW.

## Domain Compliance Validation

**Domain:** scientific (bioinformatics)
**Complexity:** Medium — not regulated; CSV special sections apply.

### Compliance Matrix

| Requirement | Status | Notes |
|---|---|---|
| Validation methodology | Met | *Statistical Validity*; *Innovation → Validation Approach*; external statistician pre-review |
| Accuracy metrics | Met | NFR1–NFR2 (verdict identity + published numeric tolerance); NFR23 (reference-implementation validation) |
| Reproducibility plan | Met | *Reproducibility & Provenance* (three search modes), NFR1–NFR6, NFR27, FR79–FR83 |
| Computational requirements | Met | *Computational Requirements*; NFR10–NFR12 |

**Required Sections Present:** 4/4
**Compliance Gaps:** 0
**Severity:** Pass
**Recommendation:** All required domain compliance sections are present and adequately documented.

## Project-Type Compliance Validation

**Project Type:** cli_tool (secondary traits: developer_tool, web_app)

### Required Sections

**Command structure:** Present — **incomplete** after the edit. Only `flanders run` and `flanders gui` are named; the bundle export/import verbs, snapshot replay, manifest rebuild (FR73–FR74, FR80, FR82), and the light-analytics re-run verb (FR35) are described but not named.
**Output formats:** Present.
**Config schema:** Present (YAML example now includes `search:`).
**Scripting support:** Present.

### Excluded Sections (Should Not Be Present)

**Visual design:** Absent ✓ (delegated to the UX specification)
**UX principles:** Absent ✓
**Touch interactions:** Absent ✓

### Compliance Summary

**Required Sections:** 4/4 present (1 incomplete)
**Excluded Sections Present:** 0
**Compliance Score:** 94%
**Severity:** Warning
**Recommendation:** Name the new CLI verbs in *Command Structure* so the CLI surface is complete for architecture and story breakdown.

## SMART Requirements Validation

**Total Functional Requirements:** 83

### Scoring Summary

**All scores ≥ 3:** 100% (83/83)
**All scores ≥ 4:** 92% (76/83)
**Overall Average Score:** 4.7/5.0

### Scoring Table

| FR # | Specific | Measurable | Attainable | Relevant | Traceable | Average | Flag |
|---|---|---|---|---|---|---|---|
| FR1 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR2 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR3 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR4 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR5 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR6 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR7 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR8 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR9 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR10 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR11 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR12 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR13 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR14 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR15 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR16 | 5 | 4 | 4 | 5 | 5 | 4.6 |  |
| FR17 | 4 | 3 | 5 | 5 | 5 | 4.4 |  |
| FR18 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR19 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR20 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR21 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR22 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR23 | 4 | 3 | 5 | 5 | 5 | 4.4 |  |
| FR24 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR25 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR26 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR27 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR28 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR29 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR30 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR31 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR32 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR33 | 3 | 3 | 5 | 4 | 5 | 4.0 |  |
| FR34 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR35 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR36 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR37 | 4 | 4 | 4 | 5 | 5 | 4.4 |  |
| FR38 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR39 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR40 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR41 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR42 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR43 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR44 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR45 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR46 | 3 | 4 | 5 | 5 | 5 | 4.4 |  |
| FR47 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR48 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR49 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR50 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR51 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR52 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR53 | 3 | 3 | 5 | 5 | 5 | 4.2 |  |
| FR54 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR55 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR56 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR57 | 4 | 4 | 5 | 5 | 5 | 4.6 |  |
| FR58 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR59 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR60 | 4 | 4 | 4 | 5 | 5 | 4.4 |  |
| FR61 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR62 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR63 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR64 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR65 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR66 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR67 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR68 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR69 | 4 | 4 | 5 | 4 | 5 | 4.4 |  |
| FR70 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR71 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR72 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR73 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR74 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR75 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR76 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR77 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR78 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR79 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |
| FR80 | 4 | 4 | 4 | 5 | 5 | 4.4 |  |
| FR81 | 4 | 4 | 3 | 5 | 5 | 4.2 |  |
| FR82 | 4 | 5 | 3 | 5 | 5 | 4.4 |  |
| FR83 | 5 | 4 | 5 | 5 | 5 | 4.8 |  |

**Legend:** 1=Poor, 3=Acceptable, 5=Excellent · **Flag:** X = score < 3 in one or more categories (none)

### Improvement Suggestions (FRs scoring 3 in any category)

- **FR17, FR23:** "a defined extension interface" — state the acceptance test (e.g., a sample analyzer/test added without core changes passes CI).
- **FR33:** "validates it" — specify what is validated (Newick parses; tip labels match genome accessions; unmatched tips reported).
- **FR46:** still says "when an installation is first initialized"; after the edit, the ledger lives in the workspace. Reword to "when a workspace is first initialized".
- **FR53:** "commonly tuned" — reference the documented, versioned curated-parameter list (*GUI Parameter Composer*, item 1).
- **FR81:** attainability depends on taxon size and NCBI retrieval limits; bound it (e.g., up to the NFR10 scale of ~1,000 genomes).
- **FR82:** attainability depends on NCBI retaining suppressed versions; the requirement correctly reports failures, but consider stating the expected behavior when the manifest cannot be fully rebuilt (run still re-analyzable; marked partially reproducible).

### Overall Assessment

**Severity:** Pass (0% flagged)
**Recommendation:** Functional Requirements demonstrate good SMART quality overall.

## Holistic Quality Assessment

### Document Flow & Coherence

**Assessment:** Good

**Strengths:**
- Clear narrative from problem → orchestration claim → honest innovation boundary → requirements.
- Decisions are explicit and dated; superseded choices are named rather than silently dropped.
- The three-mode reproducibility model is stated once in *Domain* and referenced consistently.

**Areas for Improvement:**
- Edit seams: FR70–FR83 sit before FR61–FR69; FR46 wording predates the workspace; the body date line still reads "Updated: 2026-10-01".
- *Command Structure* lags the new capabilities (see Project-Type).
- The GUI core loop has no performance acceptance criterion.

### Dual Audience Effectiveness

**For Humans:** executive-friendly — yes; developer clarity — high; designer clarity — high (paired with the UX spec); stakeholder decision-making — strong (deferred decisions and risks listed).
**For LLMs:** machine-readable structure — strong (consistent ## sections, stable FR/NFR IDs); UX readiness — done; architecture readiness — high (Decided Constraints + Deferred to Architecture); epic/story readiness — high.

**Dual Audience Score:** 4/5

### BMAD PRD Principles Compliance

| Principle | Status | Notes |
|---|---|---|
| Information Density | Met | 0 violations |
| Measurability | Partial | NFR5/7/12 lack methods; NFR10 partly unmeasurable; no re-analysis latency target |
| Traceability | Met | 0 orphans |
| Domain Awareness | Met | 4/4 scientific special sections |
| Zero Anti-Patterns | Met | |
| Dual Audience | Met | |
| Markdown Format | Met | |

**Principles Met:** 6/7

### Overall Quality Rating

**Rating:** 4/5 - Good

### Top 3 Improvements

1. **Decide on a re-analysis latency target.** The UX spec names slow re-analysis as the make-or-break failure, yet NFR11 sets no targets. Either add an NFR (e.g., light-analytics recompute of the *ebo* aggregate returns within a stated time on the minimum hardware spec) or record explicitly that it is measured, not targeted.
2. **Close the edit seams.** Name the new CLI verbs in *Command Structure*; reword FR46 for the workspace; update the body date line; optionally note in the FR section that IDs are stable and FR70–FR83 were added on 2026-11-06.
3. **Finish NFR measurability.** Add verification methods to NFR5, NFR7, NFR12; replace "without architectural change" in NFR10 with a testable statement; sharpen FR17/FR23/FR33/FR53.

### Summary

**This PRD is:** a strong, decision-explicit PRD that is ready for architecture, with a handful of seams from today's edit.
**To make it great:** Focus on the top 3 improvements above.

## Completeness Validation

### Template Completeness

**Template Variables Found:** 0 — no template variables remaining ✓

### Content Completeness by Section

**Executive Summary:** Complete
**Success Criteria:** Complete
**Product Scope:** Complete
**User Journeys:** Complete
**Functional Requirements:** Complete
**Non-Functional Requirements:** Complete

### Section-Specific Completeness

**Success Criteria Measurability:** Some — business criteria (preprint posted, statistician pre-review) are binary and verifiable; user-success criteria are scenario-based rather than metric-based, which is appropriate for this audience.
**User Journeys Coverage:** Yes — author-runner, reviewer, pipeline integrator, maintainer; v2 non-coder noted as designed-for.
**FRs Cover MVP Scope:** Yes
**NFRs Have Specific Criteria:** Some — see Measurability (NFR5, NFR7, NFR10, NFR12).

### Frontmatter Completeness

**stepsCompleted:** Present
**classification:** Present
**inputDocuments:** Present
**date:** Present (`lastEdited`; body date line stale — "Updated: 2026-10-01")

**Frontmatter Completeness:** 4/4

### Completeness Summary

**Overall Completeness:** 100% (6/6 core sections)
**Critical Gaps:** 0
**Minor Gaps:** 2 — stale body date line; FR46 wording.
**Severity:** Pass
**Recommendation:** PRD is complete with all required sections and content present.

## Validation Summary

| Check | Result |
|---|---|
| Format | BMAD Standard (6/6) |
| Information Density | Pass (0) |
| Brief Coverage | High (0 critical, 0 moderate, 2 informational) |
| Measurability | Pass (4 NFR violations) |
| Traceability | Pass (0 orphans) |
| Implementation Leakage | Pass (0) |
| Domain Compliance | Pass (4/4) |
| Project-Type Compliance | Warning (94% — Command Structure incomplete) |
| SMART Quality | 100% ≥ 3; 92% ≥ 4; avg 4.7 |
| Holistic Quality | 4/5 — Good |
| Completeness | 100% |

**Overall Status:** Pass — no critical issues; one warning (Command Structure) and a short list of minor items.

## Fixes Applied (2026-11-06)

Applied at the author's direction ([F]); the latency question resolved as **(b) measure, don't target**.

- *Command Structure*: named `flanders reanalyze`, `bundle export` / `bundle import`, `replay`, `snapshot build` / `snapshot rebuild`, `workspace reindex` → Project-Type warning resolved.
- FR46 reworded for the workspace; FR17, FR23 (reference plug-in acceptance test), FR33 (what is validated), FR53 (curated list), FR81 (scale bound), FR82 (partial-rebuild behavior) sharpened.
- NFR5, NFR7, NFR12 gained verification methods; NFR10 made testable; NFR11 records the deliberate no-latency-target decision.
- FR section notes that IDs are stable and FR70–FR83 are not in document order; body date line updated.

**Post-fix status:** Pass — no open warnings.
