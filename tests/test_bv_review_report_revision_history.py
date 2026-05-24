from structural_screening_agent.bv_review import (
    BVReviewIntake,
    ProjectReviewState,
    ReportRevision,
    build_report_revision_history_rows,
    build_report_revision_history_summary,
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
