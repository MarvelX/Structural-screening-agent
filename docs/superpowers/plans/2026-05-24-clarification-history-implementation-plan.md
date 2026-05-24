# Clarification History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic clarification history view that tracks RFI status, recheck state, and report revision coverage.

**Architecture:** Implement a focused helper that reads `ProjectReviewState` and returns typed summary plus localized rows. Surface it through `ui.py` and the existing Streamlit project management section.

**Tech Stack:** Python 3.9-compatible typing, Pydantic models, Pytest, Streamlit UI composition.

---

### Task 1: Clarification History Helper

**Files:**
- Create: `src/structural_screening_agent/bv_review/clarification_history.py`
- Test: `tests/test_bv_review_clarification_history.py`

- [x] **Step 1: Write failing tests**

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_clarification_history.py -p no:cacheprovider`

Expected before implementation: import failure for `structural_screening_agent.bv_review.clarification_history`.

- [x] **Step 2: Implement summary and row builders**

Implement:

- `ClarificationHistorySummary`
- `build_clarification_history_summary`
- `build_clarification_history_rows`

- [x] **Step 3: Verify green**

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_clarification_history.py -p no:cacheprovider`

Expected: all tests pass.

### Task 2: UI and App Integration

**Files:**
- Modify: `src/structural_screening_agent/bv_review/ui.py`
- Modify: `app.py`
- Test: `tests/test_bv_review_ui.py`
- Test: `tests/test_project_layout.py`

- [x] **Step 1: Write failing UI and app wiring tests**

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_ui.py::test_bv_clarification_history_view_localizes_summary_and_rows tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture -p no:cacheprovider`

Expected before implementation: import failure or missing app wiring assertion.

- [x] **Step 2: Add `build_bv_clarification_history_view` and app display**

The view must have localized headings, summary rows, and history rows. Chinese
output must not display English labels such as `Clarification`.

- [x] **Step 3: Verify green**

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_clarification_history.py tests/test_bv_review_ui.py::test_bv_clarification_history_view_localizes_summary_and_rows tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture -p no:cacheprovider`

Expected: all selected tests pass.

### Task 3: Documentation and Final Verification

**Files:**
- Modify: `docs/bv-pv-design-review-workbench-roadmap.md`
- Modify: `docs/bv-jd-feature-mapping.md`
- Modify: `tests/test_bv_jd_feature_mapping.py`

- [x] **Step 1: Mark clarification history implemented**

Roadmap Phase 4 should list clarification history as implemented and no longer
as a candidate item. JD mapping should include clarification history in current
coverage for communication and project management responsibilities.

- [x] **Step 2: Run focused and full verification**

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_clarification_history.py tests/test_bv_review_ui.py tests/test_project_layout.py tests/test_bv_jd_feature_mapping.py -p no:cacheprovider`

Run: `PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider`

Expected: all tests pass.

- [x] **Step 3: Check clean diff**

Run: `git diff --check`

Expected: no whitespace errors.
