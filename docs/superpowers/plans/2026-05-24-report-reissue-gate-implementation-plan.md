# Report Reissue Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic report reissue gate that links RFI closeout to report revision readiness.

**Architecture:** Add a focused `report_reissue.py` helper that reads `ProjectReviewState` and returns a typed summary plus localized rows. Surface the same rows through `ui.py` and `app.py` without changing portal-frame screening behavior.

**Tech Stack:** Python 3.9-compatible typing, Pydantic models, Pytest, Streamlit UI composition.

---

### Task 1: Deterministic Gate Model

**Files:**
- Create: `src/structural_screening_agent/bv_review/report_reissue.py`
- Test: `tests/test_bv_review_report_reissue.py`

- [x] **Step 1: Write failing tests for open, responded, closed, and covered RFI cases**

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_report_reissue.py -p no:cacheprovider`

Expected before implementation: import failure for `structural_screening_agent.bv_review.report_reissue`.

- [x] **Step 2: Implement `ReportReissueGateSummary` and row helpers**

The helper computes:

- `open_rfi_ids`
- `responded_rfi_ids`
- `pending_recheck_rfi_ids`
- `closed_rfi_ids`
- `report_gate_locked`
- `latest_revision_id`
- `covered_rfi_ids`
- `uncovered_closed_rfi_ids`
- `next_reissue_action`
- `blocking_reasons`

- [x] **Step 3: Verify green**

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_report_reissue.py -p no:cacheprovider`

Expected: all tests pass.

### Task 2: UI View and App Integration

**Files:**
- Modify: `src/structural_screening_agent/bv_review/ui.py`
- Modify: `app.py`
- Test: `tests/test_bv_review_ui.py`
- Test: `tests/test_project_layout.py`

- [x] **Step 1: Write failing UI tests**

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_ui.py::test_bv_report_reissue_gate_view_localizes_summary_rows -p no:cacheprovider`

Expected before implementation: import failure for `build_bv_report_reissue_gate_view`.

- [x] **Step 2: Add `BVReportReissueGateView`**

The view exposes localized heading, rows, and blocking reasons. Chinese UI must
not display the raw English blocking reason strings from the deterministic
summary.

- [x] **Step 3: Show the view in `app.py`**

The view is displayed in the project management section after report revision
history and before project timeline.

- [x] **Step 4: Verify app integration**

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_report_reissue.py tests/test_bv_review_ui.py::test_bv_report_reissue_gate_view_localizes_summary_rows tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture -p no:cacheprovider`

Expected: all selected tests pass.

### Task 3: Documentation Synchronization

**Files:**
- Modify: `docs/bv-pv-design-review-workbench-roadmap.md`
- Modify: `docs/bv-jd-feature-mapping.md`
- Create: `docs/superpowers/specs/2026-05-24-report-reissue-gate-design.md`
- Create: `docs/superpowers/plans/2026-05-24-report-reissue-gate-implementation-plan.md`

- [x] **Step 1: Mark the feature implemented**

Roadmap Phase 4 should mention the report reissue gate. JD mapping should move
RFI closeout report reissue from a future gap into current coverage.

- [x] **Step 2: Run doc and integration tests**

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_report_reissue.py tests/test_bv_review_ui.py tests/test_project_layout.py tests/test_bv_jd_feature_mapping.py -p no:cacheprovider`

Expected: all selected tests pass.

- [x] **Step 3: Final verification**

Run: `git diff --check`

Expected: no whitespace errors.
