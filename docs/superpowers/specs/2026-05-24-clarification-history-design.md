# Clarification History Design

## Goal

Add a focused clarification history view for RFI items so the BV PV Design
Review Workbench can show client replies, engineer closeout status, incremental
recheck state, and report revision coverage in one deterministic table.

## Scope

This is a project-management slice. It reads existing `ProjectReviewState`
fields and does not add new workflow states, modify the protected portal-frame
screening kernel, or automate official report issue.

## Design

- Add `src/structural_screening_agent/bv_review/clarification_history.py`.
- Build `ClarificationHistorySummary` from existing `RFIItem` and
  `ReportRevision` data.
- Build localized rows for each RFI with status, owner, opened date, required
  evidence, incremental recheck status, latest report coverage, and next action.
- Add `build_bv_clarification_history_view` in `ui.py`.
- Display the view in the Streamlit project management area before the broader
  project action dashboard.

## Rules

1. Open and reopened RFI items require client / designer response.
2. Responded RFI items require engineer closeout.
3. Responded incremental RFI items are pending recheck until all reopen review
   items are completed.
4. Closed RFI items that are not referenced by the latest report revision need a
   report reissue revision.
5. Closed RFI items already referenced by the latest report revision require no
   further clarification action.

## Testing

- `tests/test_bv_review_clarification_history.py` covers deterministic summary
  and localized row behavior.
- `tests/test_bv_review_ui.py` covers the UI view and Chinese-only display.
- `tests/test_project_layout.py` verifies the app is wired to the helper.

## Boundary

The clarification history is a review-support ledger. It does not certify that a
client response is technically acceptable; engineer closeout and report gate
approval remain separate controlled actions.
