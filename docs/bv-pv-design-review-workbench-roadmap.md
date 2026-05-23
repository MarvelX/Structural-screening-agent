# BV PV Design Review Workbench Roadmap

## Purpose

This roadmap turns the long-term goal in `PROJECT_VISION.md` into phased development work.

The product should evolve from the current `Structural-screening-agent` into a BV-style photovoltaic design review workbench, while preserving the existing `Portal Frame Rooftop PV Screening` module as the first implemented technical review module.

## Current State

Already present in the repository:

- Streamlit app entry point with BV PV Design Review Workbench title.
- `BV Review` overview tab in `app.py`.
- Independent `src/structural_screening_agent/bv_review/` package.
- BV review models, basis builder, document checklist, review path, review plan, risk register, workflow, and report preview.
- Tests for BV review models, workflow, UI state, and report.
- Existing portal-frame rooftop PV screening kernel, report export, basis traceability, and tests.
- JD feature mapping documentation in `docs/bv-jd-feature-mapping.md`.
- portfolio narrative page and showcase support material under `docs/showcase/`.
- BV UI helper smoke tests and app import checks that do not require manual Streamlit interaction.
- BV section renderer extraction: simple BV report section rendering now lives in `src/structural_screening_agent/bv_review/ui.py` behind a Streamlit-like protocol and has direct unit coverage.
- BV label formatter extraction: BV form and calculation labels now share `format_bv_label` with language fallback behavior covered by unit tests.
- BV evidence table text extraction: evidence table headings and empty states now share a tested bilingual text helper outside `app.py`.
- BV gate panel text extraction: quality-gate panel headings now share a tested bilingual helper outside `app.py`.
- BV report gate status renderer extraction: ready / blocked report-gate notices, localized reasons, and notes now render through a tested Streamlit-like helper outside `app.py`.
- finding lifecycle summary: the workbench now summarizes open / closed findings, clarification status, and the next lifecycle action for ongoing review management.
- UI / report evidence matrix alignment: workbench rows and exported BV reports now trace final report findings to fields, document versions, intake document status, or missing evidence.
- workspace cleanliness policy in `docs/workspace-cleanliness.md`, with tests that keep ignored local artifact rules documented.

Open caution:

- The repository contains untracked duplicate files named like `* 2.py` and `* 2.md`. They should be ignored unless the user explicitly asks to clean them.
- The default Pytest duplicate-copy exclusion is configured through `--ignore-glob=* 2.py`, so local duplicate test copies do not inflate the default test set.

## Phase 1: Portfolio MVP

Goal: make the workbench credible for interview and portfolio use while retaining engineering substance.

Status: partially implemented.

Completed:

- BV Review Mode entry in the Streamlit app.
- Project intake fields for project type, country / region, stage, standards, review objects, client requirements, and document status.
- Review basis builder for GB / IEC / AS/NZS / Eurocode contexts.
- Document completeness checklist.
- Review path generation for mounting, steel, concrete, foundation, connection, load calculation, and existing rooftop added-load review objects.
- ITP / review plan generation.
- Risk and nonconformity register.
- BV-style report preview and Markdown / Word / PDF export from the app.
- Unit tests for BV review model, workflow, report, and UI state.
- JD feature mapping documentation for BV role responsibilities and interview talking points.
- Portfolio narrative page that explains the current MVP as a BV role-aligned product artifact.
- BV UI helper smoke tests and public demo checks.

Next improvements:

1. Move BV UI rendering helpers out of `app.py` into `src/structural_screening_agent/bv_review/ui.py`.
2. Continue reducing duplicated Streamlit presentation logic in `app.py` while keeping existing workflow behavior intact.
3. Keep portfolio and JD documentation synchronized with tested product behavior after each major workflow slice.

## Phase 2: Technical Review Expansion

Goal: expand from one implemented technical module to a broader PV civil / structural review scope.

Status: started.

Implemented:

- `Foundation Review Evidence Path` domain helper, covering geotechnical parameters, foundation geometry, and foundation reaction evidence readiness before foundation screening calculations.
- 基础证据路径 / foundation evidence gaps now become traceable draft RFI items after engineer review. For example, missing geotechnical evidence can produce `foundation_evidence_blocked_geotechnical_parameters`, which appears in the blocked calculation draft RFI workflow and workbench rows.

Candidate modules:

- mounting structure checklist and risk rules
- foundation review checklist and bearing capacity evidence path deeper rules
- connection detail review checklist
- corrosion and durability review
- PV array layout and O&M access interface review
- basic cable tray / grounding interface checklist

First target status:

`Foundation Review Evidence Path`

Current result:

- BV JD explicitly mentions foundation engineering and bearing capacity.
- It is strongly connected to document completeness through geotechnical reports.
- The current implementation checks 地勘参数证据, 基础几何与布置证据, and 基础最不利反力证据 before screening-level foundation calculations.
- If evidence is incomplete, the workbench can create a 草稿 RFI for engineer review instead of silently proceeding with weak inputs.

## Phase 3: Calculation and Evidence Deepening

Goal: add more deterministic calculators and stronger evidence handling.

Status: started.

Implemented:

- Evidence matrix by finding and document source. Blocking risks and nonconformities can now be traced back to extracted fields, document versions, intake document status, or explicit missing evidence; the workbench shows this as a localized evidence table and BV report packages include the same traceability section.
- UI / report evidence matrix alignment ensures final report findings are traced consistently even when the persisted project-state risk ledger has not yet been synchronized.
- Evidence matrix traceability is covered by report tests, UI-state tests, and default test collection that ignores duplicate local copy files.

Candidate work:

- foundation bearing capacity screening
- mounting structure load path screening
- connection force path screening
- wind / snow / seismic review basis routing
- geotechnical report extraction checklist
- evidence matrix export refinements for Word / PDF formatting

Boundary:

Calculators should remain screening-level unless the repository deliberately adds a formal design module with clear disclaimers and stronger validation.

## Phase 4: Review Project Management

Goal: support ongoing review projects rather than one-off assessments.

Status: started.

Implemented:

- finding lifecycle summary for open findings, blocking findings, closed / accepted findings, client clarification response status, engineer closeout status, and the next lifecycle action.

Candidate work:

- deeper finding lifecycle tracking
- clarification history
- responsible-party status
- review dashboard
- report revision history
- service scope and fee discussion support

This phase should not turn the product into a CRM. Service scope recommendation should remain tied to engineering review findings and document gaps.

## Near-Term Development Steps

Recommended next three small, verifiable steps:

1. Continue extracting BV UI presentation helpers from `app.py` into dedicated BV UI modules, starting with simple protocol-based helpers before moving stateful Streamlit flows.
   - Verification: existing BV review tests pass; app still imports.

2. Keep roadmap, JD mapping, and showcase narrative synchronized with completed workflow slices.
   - Verification: documentation tests check that roadmap claims match implemented traceability and clean-workspace behavior.

3. Strengthen evidence matrix export formatting for Word / PDF.
   - Verification: report export tests confirm traceability content survives generated artifacts.

## Non-Goals

Do not prioritize these until the core review workflow is stable:

- CAD auto-review
- complete finite-element analysis
- automatic official code compliance certification
- full electrical design checking
- CRM or sales pipeline management
- unsupported LLM-generated engineering conclusions
