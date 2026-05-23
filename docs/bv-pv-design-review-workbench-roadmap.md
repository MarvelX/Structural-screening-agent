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

Open caution:

- The repository contains untracked duplicate files named like `* 2.py` and `* 2.md`. They should be ignored unless the user explicitly asks to clean them.

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

Next improvements:

1. Move BV UI rendering helpers out of `app.py` into `src/structural_screening_agent/bv_review/ui.py`.
2. Add `docs/bv-jd-feature-mapping.md` to map each feature to BV JD responsibilities and interview talking points.
3. Add a portfolio narrative page under `docs/showcase/` that explains how the current MVP maps to the BV role.
4. Add a small regression test or smoke test that imports the BV UI helper without requiring Streamlit runtime interaction.

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

Candidate work:

- finding lifecycle tracking
- clarification history
- responsible-party status
- review dashboard
- report revision history
- service scope and fee discussion support

This phase should not turn the product into a CRM. Service scope recommendation should remain tied to engineering review findings and document gaps.

## Near-Term Development Steps

Recommended next three small, verifiable steps:

1. Extract BV UI presentation helpers from `app.py` into a dedicated module.
   - Verification: existing BV review tests pass; app still imports.

2. Add BV JD feature mapping documentation.
   - Verification: document includes each major JD responsibility and maps it to current or planned functionality.

3. Strengthen the BV report boundary and portfolio narrative.
   - Verification: tests confirm the report still states screening / review-support boundary and does not claim official BV signing.

## Non-Goals

Do not prioritize these until the core review workflow is stable:

- CAD auto-review
- complete finite-element analysis
- automatic official code compliance certification
- full electrical design checking
- CRM or sales pipeline management
- unsupported LLM-generated engineering conclusions
