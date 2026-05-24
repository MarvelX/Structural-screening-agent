# Report Reissue Gate Design

## Goal

Add a deterministic report reissue gate for the BV PV Design Review Workbench so
the project lead can see whether a closed RFI package is ready for a new report
revision.

## Scope

This slice connects existing RFI closeout, incremental recheck, report gate, and
report revision history state. It does not issue an official BV report, replace
engineer judgment, or change the protected portal-frame screening kernel.

## Design

- Add `src/structural_screening_agent/bv_review/report_reissue.py`.
- Input is `ProjectReviewState`.
- Output is `ReportReissueGateSummary`, with blocking RFI ids, pending recheck
  ids, latest report revision id, closed RFI ids not covered by the latest
  revision, and a deterministic next action.
- Provide localized rows through `build_report_reissue_gate_rows`.
- Surface the rows through `build_bv_report_reissue_gate_view` in `ui.py`.
- Display the view in the existing project management area of `app.py`.

## Rules

1. Open or reopened RFI items block reissue until the client or designer replies.
2. Responded RFI items block reissue until the engineer closes them.
3. Responded incremental RFI items also show pending recheck evidence.
4. Closed RFI items require report gate approval before reissue.
5. If the latest report revision does not reference a closed RFI, the next
   action is to record a reissue revision.
6. If the latest revision already covers all closed RFI items, no new reissue
   action is required.

## Testing

The feature is covered by:

- `tests/test_bv_review_report_reissue.py` for deterministic gate behavior.
- `tests/test_bv_review_ui.py` for localized UI view rows and Chinese blocking
  reason text.
- `tests/test_project_layout.py` for Streamlit app integration evidence.

## Boundaries

The gate is review-support only. It provides structured readiness evidence and
recommended next action. It does not certify compliance, issue formal reports,
or authorize official BV signing.
