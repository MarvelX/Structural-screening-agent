# Report Revision History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a traceable report revision history layer so the BV PV Design Review Workbench can show draft / issued / superseded report snapshots, related RFI closeout evidence, and the next revision action without becoming a document-management system.

**Architecture:** Build on the existing `ReportRevision` model and `record_report_revision()` gate in `human_gate.py`. Add a focused history helper module that summarizes revision lineage and UI rows, then surface it in the project management dashboard and documentation tests.

**Tech Stack:** Python, Pydantic models, Streamlit UI helper patterns, Pytest, existing BV review state models.

---

## File Map

- Modify: `src/structural_screening_agent/bv_review/project_state.py`
  - Extend `ReportRevision` with optional lineage and status metadata.
- Create: `src/structural_screening_agent/bv_review/report_revision_history.py`
  - Build deterministic revision history summaries and localized rows.
- Modify: `src/structural_screening_agent/bv_review/__init__.py`
  - Export the new helper types and functions.
- Modify: `src/structural_screening_agent/bv_review/ui.py`
  - Add a tested project-management view model for report revision history.
- Modify: `app.py`
  - Render the revision history rows in the BV project management area.
- Modify: `tests/test_bv_review_project_state.py`
  - Cover the new `ReportRevision` metadata validation.
- Create: `tests/test_bv_review_report_revision_history.py`
  - Cover lineage summary, status counts, next action, and localization.
- Modify: `tests/test_bv_review_ui.py`
  - Cover the UI helper for revision history.
- Modify: `tests/test_job_application_package.py`
  - Keep the static app/source contract aligned with the new UI helper.
- Modify: `docs/bv-pv-design-review-workbench-roadmap.md`
  - Move report revision history from candidate work to implemented work after code lands.
- Modify: `docs/bv-jd-feature-mapping.md`
  - Update the design review report row to reflect implemented revision history.
- Modify: `tests/test_bv_jd_feature_mapping.py`
  - Add expected roadmap / JD mapping phrases.

## Task 1: Report Revision Metadata

**Files:**
- Modify: `src/structural_screening_agent/bv_review/project_state.py`
- Modify: `tests/test_bv_review_project_state.py`

- [ ] **Step 1: Write the failing model test**

Add this test to `tests/test_bv_review_project_state.py` after `test_report_revision_records_traceable_report_snapshot_metadata`:

```python
def test_report_revision_carries_status_lineage_and_issue_metadata() -> None:
    revision = ReportRevision(
        revision_id="report-rev-002",
        source_phase="engineer_approval",
        report_title="BV 光伏结构设计审查报告",
        section_count=10,
        rfi_count=0,
        created_by="Engineer B",
        created_at="2026-05-24T10:30:00+08:00",
        revision_status="issued_for_client_response",
        supersedes_revision_id="report-rev-001",
        issue_purpose="Client RFI closeout package",
        related_rfi_ids=["rfi-foundation-001"],
    )

    assert revision.revision_status == "issued_for_client_response"
    assert revision.supersedes_revision_id == "report-rev-001"
    assert revision.issue_purpose == "Client RFI closeout package"
    assert revision.related_rfi_ids == ["rfi-foundation-001"]


def test_report_revision_cannot_supersede_itself() -> None:
    with pytest.raises(ValidationError):
        ReportRevision(
            revision_id="report-rev-003",
            source_phase="engineer_approval",
            report_title="BV 光伏结构设计审查报告",
            section_count=10,
            rfi_count=0,
            created_by="Engineer B",
            revision_status="issued_for_review",
            supersedes_revision_id="report-rev-003",
        )
```

- [ ] **Step 2: Run the focused failing test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_project_state.py::test_report_revision_carries_status_lineage_and_issue_metadata tests/test_bv_review_project_state.py::test_report_revision_cannot_supersede_itself -p no:cacheprovider
```

Expected: FAIL because `ReportRevision` does not yet define the new fields.

- [ ] **Step 3: Extend `ReportRevision`**

Update `ReportRevision` in `src/structural_screening_agent/bv_review/project_state.py`:

```python
ReportRevisionStatus = Literal[
    "draft",
    "issued_for_review",
    "issued_for_client_response",
    "superseded",
    "finalized",
]


class ReportRevision(BaseModel):
    revision_id: str = Field(min_length=1)
    source_phase: ReviewPhase
    report_title: str = Field(min_length=1)
    section_count: int = Field(ge=1)
    rfi_count: int = Field(ge=0)
    blocking_risk_ids: List[str] = Field(default_factory=list)
    calculation_run_ids: List[str] = Field(default_factory=list)
    created_by: str = Field(min_length=1)
    created_at: Optional[str] = None
    note: Optional[str] = None
    revision_status: ReportRevisionStatus = "draft"
    supersedes_revision_id: Optional[str] = None
    issue_purpose: Optional[str] = None
    related_rfi_ids: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_self_supersession(self) -> "ReportRevision":
        if self.supersedes_revision_id == self.revision_id:
            raise ValueError("ReportRevision.supersedes_revision_id cannot reference the same revision_id.")
        return self
```

- [ ] **Step 4: Run the focused test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_project_state.py::test_report_revision_carries_status_lineage_and_issue_metadata tests/test_bv_review_project_state.py::test_report_revision_cannot_supersede_itself -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/structural_screening_agent/bv_review/project_state.py tests/test_bv_review_project_state.py
git commit -m "feat: extend report revision metadata"
```

## Task 2: Revision History Summary Helper

**Files:**
- Create: `src/structural_screening_agent/bv_review/report_revision_history.py`
- Create: `tests/test_bv_review_report_revision_history.py`
- Modify: `src/structural_screening_agent/bv_review/__init__.py`

- [ ] **Step 1: Write the failing helper tests**

Create `tests/test_bv_review_report_revision_history.py`:

```python
from structural_screening_agent.bv_review import (
    BVReviewIntake,
    ProjectReviewState,
    ReportRevision,
    build_report_revision_history_summary,
    build_report_revision_history_rows,
)


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb"],
        review_objects=["mounting_structure", "foundation"],
        documents={"structural_drawings": "available"},
    )


def test_report_revision_history_summary_tracks_lineage_status_and_next_action() -> None:
    state = ProjectReviewState(
        project_id="pv-report-revision-history",
        intake=_sample_intake(),
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=8,
                rfi_count=2,
                created_by="Engineer A",
                created_at="2026-05-20T09:00:00+08:00",
                revision_status="superseded",
            ),
            ReportRevision(
                revision_id="report-rev-002",
                source_phase="engineer_approval",
                report_title="BV 光伏结构设计审查报告",
                section_count=10,
                rfi_count=0,
                created_by="Engineer B",
                created_at="2026-05-24T10:30:00+08:00",
                revision_status="issued_for_client_response",
                supersedes_revision_id="report-rev-001",
                issue_purpose="Client RFI closeout package",
                related_rfi_ids=["rfi-foundation-001"],
            ),
        ],
    )

    summary = build_report_revision_history_summary(state)

    assert summary.total_revision_count == 2
    assert summary.latest_revision_id == "report-rev-002"
    assert summary.latest_revision_status == "issued_for_client_response"
    assert summary.open_revision_count == 1
    assert summary.superseded_revision_count == 1
    assert summary.next_revision_action == "track_client_response"


def test_report_revision_history_rows_are_localized() -> None:
    state = ProjectReviewState(
        project_id="pv-report-revision-history-rows",
        intake=_sample_intake(),
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=8,
                rfi_count=1,
                created_by="Engineer A",
                created_at="2026-05-20T09:00:00+08:00",
                revision_status="issued_for_review",
                issue_purpose="Internal engineer review",
                related_rfi_ids=["rfi-foundation-001"],
            )
        ],
    )

    zh_rows = build_report_revision_history_rows(state, "zh")
    en_rows = build_report_revision_history_rows(state, "en")

    assert zh_rows == [
        {
            "修订 ID": "report-rev-001",
            "状态": "发给复核",
            "生成阶段": "report_draft",
            "生成时间": "2026-05-20T09:00:00+08:00",
            "生成者": "Engineer A",
            "替代版本": "无",
            "关联 RFI": "rfi-foundation-001",
            "用途": "Internal engineer review",
        }
    ]
    assert en_rows[0]["Revision ID"] == "report-rev-001"
    assert en_rows[0]["Status"] == "Issued for Review"
    assert en_rows[0]["Related RFIs"] == "rfi-foundation-001"
```

- [ ] **Step 2: Run the focused failing tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_report_revision_history.py -p no:cacheprovider
```

Expected: FAIL because the helper module and exports do not exist.

- [ ] **Step 3: Create the helper module**

Create `src/structural_screening_agent/bv_review/report_revision_history.py`:

```python
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.project_state import (
    ProjectReviewState,
    ReportRevision,
)


ReportRevisionHistoryLanguage = Literal["zh", "en"]


class ReportRevisionHistorySummary(BaseModel):
    total_revision_count: int = Field(ge=0)
    latest_revision_id: Optional[str] = None
    latest_revision_status: Optional[str] = None
    open_revision_count: int = Field(ge=0)
    superseded_revision_count: int = Field(ge=0)
    next_revision_action: Optional[str] = None


def build_report_revision_history_summary(
    state: ProjectReviewState,
) -> ReportRevisionHistorySummary:
    revisions = _sorted_revisions(state.report_revisions)
    latest = revisions[-1] if revisions else None
    return ReportRevisionHistorySummary(
        total_revision_count=len(revisions),
        latest_revision_id=latest.revision_id if latest else None,
        latest_revision_status=latest.revision_status if latest else None,
        open_revision_count=sum(
            1
            for revision in revisions
            if revision.revision_status
            in {"draft", "issued_for_review", "issued_for_client_response"}
        ),
        superseded_revision_count=sum(
            1 for revision in revisions if revision.revision_status == "superseded"
        ),
        next_revision_action=_next_revision_action(latest),
    )


def build_report_revision_history_rows(
    state: ProjectReviewState,
    language: ReportRevisionHistoryLanguage,
) -> list[dict[str, object]]:
    return [
        _revision_row_zh(revision) if language == "zh" else _revision_row_en(revision)
        for revision in _sorted_revisions(state.report_revisions)
    ]


def _sorted_revisions(revisions: list[ReportRevision]) -> list[ReportRevision]:
    return sorted(
        revisions,
        key=lambda revision: (
            revision.created_at or "",
            revision.revision_id,
        ),
    )


def _next_revision_action(revision: Optional[ReportRevision]) -> Optional[str]:
    if revision is None:
        return "record_first_revision"
    if revision.revision_status == "draft":
        return "complete_engineer_review"
    if revision.revision_status == "issued_for_review":
        return "collect_reviewer_decision"
    if revision.revision_status == "issued_for_client_response":
        return "track_client_response"
    if revision.revision_status == "superseded":
        return "confirm_active_revision"
    if revision.revision_status == "finalized":
        return None
    return None


def _revision_row_zh(revision: ReportRevision) -> dict[str, object]:
    return {
        "修订 ID": revision.revision_id,
        "状态": _status_label(revision.revision_status, "zh"),
        "生成阶段": revision.source_phase,
        "生成时间": revision.created_at or "未记录",
        "生成者": revision.created_by,
        "替代版本": revision.supersedes_revision_id or "无",
        "关联 RFI": ", ".join(revision.related_rfi_ids) or "无",
        "用途": revision.issue_purpose or "未记录",
    }


def _revision_row_en(revision: ReportRevision) -> dict[str, object]:
    return {
        "Revision ID": revision.revision_id,
        "Status": _status_label(revision.revision_status, "en"),
        "Source Phase": revision.source_phase,
        "Created At": revision.created_at or "Not Recorded",
        "Created By": revision.created_by,
        "Supersedes": revision.supersedes_revision_id or "None",
        "Related RFIs": ", ".join(revision.related_rfi_ids) or "None",
        "Purpose": revision.issue_purpose or "Not Recorded",
    }


def _status_label(status: str, language: ReportRevisionHistoryLanguage) -> str:
    labels = {
        "draft": {"zh": "草稿", "en": "Draft"},
        "issued_for_review": {"zh": "发给复核", "en": "Issued for Review"},
        "issued_for_client_response": {
            "zh": "发给客户回复",
            "en": "Issued for Client Response",
        },
        "superseded": {"zh": "已被替代", "en": "Superseded"},
        "finalized": {"zh": "已定稿", "en": "Finalized"},
    }
    return labels.get(status, {}).get(language, status)
```

- [ ] **Step 4: Export helpers**

Update `src/structural_screening_agent/bv_review/__init__.py`:

```python
from structural_screening_agent.bv_review.report_revision_history import (
    ReportRevisionHistorySummary,
    build_report_revision_history_rows,
    build_report_revision_history_summary,
)
```

Add these names to `__all__`:

```python
"ReportRevisionHistorySummary",
"build_report_revision_history_rows",
"build_report_revision_history_summary",
```

- [ ] **Step 5: Run helper tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_report_revision_history.py -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/structural_screening_agent/bv_review/report_revision_history.py src/structural_screening_agent/bv_review/__init__.py tests/test_bv_review_report_revision_history.py
git commit -m "feat: add report revision history summary"
```

## Task 3: UI Helper and App Surface

**Files:**
- Modify: `src/structural_screening_agent/bv_review/ui.py`
- Modify: `tests/test_bv_review_ui.py`
- Modify: `app.py`
- Modify: `tests/test_job_application_package.py`

- [ ] **Step 1: Write the failing UI helper test**

Add this import to `tests/test_bv_review_ui.py`:

```python
from structural_screening_agent.bv_review.project_state import ReportRevision
```

Add `build_bv_report_revision_history_view` to the existing `ui.py` import list.

Add this test:

```python
def test_bv_report_revision_history_view_localizes_rows_and_empty_state() -> None:
    state = ProjectReviewState(
        project_id="pv-ui-report-revisions",
        intake=_sample_intake(),
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=8,
                rfi_count=1,
                created_by="Engineer A",
                created_at="2026-05-20T09:00:00+08:00",
                revision_status="issued_for_review",
                issue_purpose="Internal review package",
            )
        ],
    )

    zh_view = build_bv_report_revision_history_view(state, "zh")
    en_view = build_bv_report_revision_history_view(state, "en")
    empty_view = build_bv_report_revision_history_view(
        ProjectReviewState(project_id="pv-ui-empty-report-revisions", intake=_sample_intake()),
        "en",
    )

    assert zh_view.heading == "报告修订历史"
    assert zh_view.summary_rows[0] == {"指标": "报告修订数", "数值": 1}
    assert zh_view.revision_rows[0]["状态"] == "发给复核"
    assert en_view.heading == "Report Revision History"
    assert en_view.revision_rows[0]["Status"] == "Issued for Review"
    assert empty_view.empty_caption == "No report revision snapshots have been recorded."
```

- [ ] **Step 2: Run the focused failing UI test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_ui.py::test_bv_report_revision_history_view_localizes_rows_and_empty_state -p no:cacheprovider
```

Expected: FAIL because the UI helper does not exist.

- [ ] **Step 3: Add the UI view model and helper**

Update `src/structural_screening_agent/bv_review/ui.py` imports:

```python
from structural_screening_agent.bv_review.report_revision_history import (
    build_report_revision_history_rows,
    build_report_revision_history_summary,
)
```

Add the view model:

```python
class BVReportRevisionHistoryView(BaseModel):
    heading: str = Field(min_length=1)
    summary_rows: list[dict[str, object]] = Field(default_factory=list)
    revision_rows: list[dict[str, object]] = Field(default_factory=list)
    empty_caption: str = Field(min_length=1)
```

Add the helper near the project management dashboard helper:

```python
def build_bv_report_revision_history_view(
    state: ProjectReviewState,
    language: Language,
) -> BVReportRevisionHistoryView:
    heading = "Report Revision History" if language == "en" else "报告修订历史"
    empty_caption = (
        "No report revision snapshots have been recorded."
        if language == "en"
        else "当前还没有报告修订快照。"
    )
    summary = build_report_revision_history_summary(state)
    if language == "en":
        summary_rows = [
            {"Metric": "Report Revisions", "Value": summary.total_revision_count},
            {"Metric": "Latest Revision", "Value": summary.latest_revision_id or "None"},
            {"Metric": "Latest Status", "Value": summary.latest_revision_status or "None"},
            {"Metric": "Open Revisions", "Value": summary.open_revision_count},
            {"Metric": "Superseded Revisions", "Value": summary.superseded_revision_count},
            {"Metric": "Next Revision Action", "Value": summary.next_revision_action or "None"},
        ]
    else:
        summary_rows = [
            {"指标": "报告修订数", "数值": summary.total_revision_count},
            {"指标": "最新修订", "数值": summary.latest_revision_id or "无"},
            {"指标": "最新状态", "数值": summary.latest_revision_status or "无"},
            {"指标": "打开修订", "数值": summary.open_revision_count},
            {"指标": "已替代修订", "数值": summary.superseded_revision_count},
            {"指标": "下一项修订行动", "数值": summary.next_revision_action or "无"},
        ]
    return BVReportRevisionHistoryView(
        heading=heading,
        summary_rows=summary_rows,
        revision_rows=build_report_revision_history_rows(state, language),
        empty_caption=empty_caption,
    )
```

- [ ] **Step 4: Run the focused UI test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_ui.py::test_bv_report_revision_history_view_localizes_rows_and_empty_state -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 5: Add static app contract test expectations**

Update `tests/test_job_application_package.py` in the existing source assertions:

```python
assert "build_bv_report_revision_history_view" in app_source
assert "Report Revision History" in app_source
assert "报告修订历史" in app_source
```

- [ ] **Step 6: Render in `app.py`**

Import the helper from `structural_screening_agent.bv_review.ui`:

```python
build_bv_report_revision_history_view,
```

In the BV project management area, after rendering the project management action dashboard, add:

```python
revision_history_view = build_bv_report_revision_history_view(
    workflow_state,
    ui_language,
)
st.markdown(f"#### {revision_history_view.heading}")
if revision_history_view.revision_rows:
    st.dataframe(revision_history_view.summary_rows, hide_index=True, use_container_width=True)
    st.dataframe(revision_history_view.revision_rows, hide_index=True, use_container_width=True)
else:
    st.caption(revision_history_view.empty_caption)
```

- [ ] **Step 7: Run app-related tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_ui.py::test_bv_report_revision_history_view_localizes_rows_and_empty_state tests/test_job_application_package.py -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 8: Commit**

Run:

```bash
git add src/structural_screening_agent/bv_review/ui.py tests/test_bv_review_ui.py app.py tests/test_job_application_package.py
git commit -m "feat: surface report revision history"
```

## Task 4: Documentation and Full Verification

**Files:**
- Modify: `docs/bv-pv-design-review-workbench-roadmap.md`
- Modify: `docs/bv-jd-feature-mapping.md`
- Modify: `tests/test_bv_jd_feature_mapping.py`

- [ ] **Step 1: Write failing documentation expectation**

Update `tests/test_bv_jd_feature_mapping.py` so the roadmap phrase list includes:

```python
"report revision history",
```

- [ ] **Step 2: Run the failing documentation test**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_jd_feature_mapping.py::test_bv_roadmap_reflects_current_traceability_and_clean_workspace_baseline -p no:cacheprovider
```

Expected: FAIL until the roadmap implemented list includes the phrase.

- [ ] **Step 3: Update roadmap**

In `docs/bv-pv-design-review-workbench-roadmap.md`, under Phase 4 `Implemented`, add:

```markdown
- report revision history with traceable revision status, supersession lineage, related RFI references, latest revision summary, and next revision action.
```

Remove `- report revision history` from Phase 4 `Candidate work`.

- [ ] **Step 4: Update JD mapping**

In `docs/bv-jd-feature-mapping.md`, update the row for `执行或监督设计审核工作，并出具专业的设计审查报告` so current coverage says:

```markdown
已支持本地 deterministic agent workflow、工程师复核队列、报告草稿门禁、报告修订历史、BV 风格报告预览及 Markdown / Word / PDF 导出
```

In the same row, change next strengthening from:

```markdown
增加报告 revision history、审核人签名状态、RFI closeout 后的再签发流程；继续声明不替代 BV 官方签发
```

to:

```markdown
增加审核人签名状态、RFI closeout 后的再签发流程和外部交付版本水印；继续声明不替代 BV 官方签发
```

- [ ] **Step 5: Run documentation tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_jd_feature_mapping.py -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 6: Run final verification**

Run:

```bash
git diff --check
git diff -- src/structural_screening_agent/core src/structural_screening_agent/core/portal_frame.py src/structural_screening_agent/core/calculators
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests
PYTHONDONTWRITEBYTECODE=1 python3 -c "import app; print('app import ok')"
git status --short --branch
```

Expected:

- `git diff --check` exits 0.
- Protected portal-frame core diff is empty.
- Full test suite passes.
- App import exits 0 and prints `app import ok`; Streamlit bare-mode warnings are acceptable.
- Git status shows only intentional files before commit, then clean after commit.

- [ ] **Step 7: Commit and push**

Run:

```bash
git add docs/bv-pv-design-review-workbench-roadmap.md docs/bv-jd-feature-mapping.md tests/test_bv_jd_feature_mapping.py
git commit -m "docs: mark report revision history implemented"
git push origin main
```

## Self-Review

- Spec coverage: This plan advances the long-term multi-agent workflow goal by turning report revision history from a Phase 4 candidate into a traceable project-management workflow slice. It preserves the engineering boundary: report revisions are metadata and workflow evidence, not official BV signing.
- Placeholder scan: No `TODO`, `TBD`, ellipsis placeholders, or “write tests for the above” shortcuts are present.
- Type consistency: The plan consistently uses `ReportRevision`, `ReportRevisionHistorySummary`, `build_report_revision_history_summary`, `build_report_revision_history_rows`, and `build_bv_report_revision_history_view`.
- Protected capability check: No task edits `src/structural_screening_agent/core/`, `portal_frame.py`, or `core/calculators/`.
