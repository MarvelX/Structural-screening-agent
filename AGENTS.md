# AGENTS.md

## Project Mission

This repository is evolving into `BV PV Design Review Workbench`, a long-term portfolio product for BV-style photovoltaic design review work.

The long-term goal is to cover the major responsibilities of a PV civil / structural / mounting / foundation design review engineer:

- project intake
- review basis
- document completeness
- design review plan and ITP
- technical checks
- risk and nonconformity register
- optimization advice
- report export
- client clarification
- service scope recommendation

## Protected Existing Capability

The existing `Portal Frame Rooftop PV Screening` capability is the first real technical review module and must be preserved.

Do not delete, rewrite, or weaken:

- `src/structural_screening_agent/core/`
- `src/structural_screening_agent/core/portal_frame.py`
- `src/structural_screening_agent/core/calculators/`
- existing portal-frame workflow tests
- existing report export behavior

BV workbench logic should be added as a separate layer, mainly under:

- `src/structural_screening_agent/bv_review/`
- `tests/test_bv_review_*.py`
- `docs/`

## Engineering Boundaries

This tool is for screening-level and review-support work only.

It must not claim to replace:

- formal engineering design
- statutory approval
- stamped calculations
- finite-element analysis
- qualified engineer judgment
- official BV signing workflow

Engineering conclusions must be traceable to deterministic rules, review basis, input data, evidence, and structured findings. LLM output may assist explanation and drafting, but must not create unsupported engineering conclusions.

## Development Rules

Before editing:

1. Inspect the relevant existing files.
2. Identify the files to change.
3. Keep diffs small and reviewable.
4. Preserve existing behavior unless the task explicitly asks to change it.
5. Add or update tests for behavior changes.
6. Run the fastest relevant verification command.

Prefer this rhythm:

```text
Inspect -> Plan -> Implement -> Test -> Document -> Commit
```

## Current Known Workspace Note

The repository may contain untracked duplicate files named like `* 2.py` or `* 2.md`.

Do not delete or modify those files unless the user explicitly asks. Ignore them for normal BV Workbench development.

## Product Reference

Use `PROJECT_VISION.md` as the long-term product constitution.

Use `docs/bv-pv-design-review-workbench-roadmap.md` as the phase roadmap.

Use `docs/superpowers/specs/2026-05-17-bv-pv-design-review-workbench-design.md` as the detailed product design reference.
