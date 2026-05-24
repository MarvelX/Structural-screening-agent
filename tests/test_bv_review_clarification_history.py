from structural_screening_agent.bv_review import (
    ProjectReviewState,
    RFIItem,
    ReportRevision,
)
from structural_screening_agent.bv_review.clarification_history import (
    build_clarification_history_rows,
    build_clarification_history_summary,
)
from structural_screening_agent.bv_review.ui_state import default_bv_review_intake


def _rfi(rfi_id: str, status: str, **updates: object) -> RFIItem:
    values = {
        "rfi_id": rfi_id,
        "question": "Please clarify foundation evidence.",
        "responsible_party": "client / designer",
        "trigger_basis": "Foundation review evidence gap.",
        "required_document_or_field": "geotechnical_report",
        "status": status,
        "opened_at": "2026-05-20",
    }
    values.update(updates)
    return RFIItem(**values)


def test_clarification_history_summary_tracks_status_recheck_and_report_coverage() -> None:
    state = ProjectReviewState(
        project_id="pv-clarification-history",
        intake=default_bv_review_intake(),
        rfi_items=[
            _rfi(
                "rfi-open",
                "open",
                triggers_incremental_recheck=True,
                reopen_review_items=["pile_length_m"],
            ),
            _rfi(
                "rfi-responded",
                "responded",
                client_response="Designer submitted Rev B calculation.",
                triggers_incremental_recheck=True,
                reopen_review_items=["bearing_capacity_characteristic_kpa"],
            ),
            _rfi(
                "rfi-closed-covered",
                "closed",
                client_response="Designer submitted Rev C geotechnical note.",
                triggers_incremental_recheck=True,
                reopen_review_items=["side_resistance_standard_kpa"],
                completed_recheck_items=["side_resistance_standard_kpa"],
            ),
            _rfi(
                "rfi-closed-uncovered",
                "closed",
                client_response="Designer submitted Rev D pile layout.",
            ),
        ],
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-002",
                source_phase="report_draft",
                report_title="PV Design Review Report",
                section_count=6,
                rfi_count=1,
                created_by="Engineer A",
                created_at="2026-05-24T10:00:00+08:00",
                revision_status="issued_for_client_response",
                related_rfi_ids=["rfi-closed-covered"],
            )
        ],
    )

    summary = build_clarification_history_summary(state)

    assert summary.total_rfi_count == 4
    assert summary.open_rfi_count == 1
    assert summary.responded_rfi_count == 1
    assert summary.closed_rfi_count == 2
    assert summary.incremental_recheck_rfi_count == 3
    assert summary.pending_recheck_rfi_ids == ["rfi-responded"]
    assert summary.closed_uncovered_rfi_ids == ["rfi-closed-uncovered"]
    assert summary.latest_report_revision_id == "report-rev-002"
    assert summary.next_clarification_action == "collect_client_response"


def test_clarification_history_rows_are_localized_and_show_next_action() -> None:
    state = ProjectReviewState(
        project_id="pv-clarification-history-rows",
        intake=default_bv_review_intake(),
        rfi_items=[
            _rfi(
                "rfi-responded",
                "responded",
                client_response="Designer submitted Rev B calculation.",
                triggers_incremental_recheck=True,
                reopen_review_items=["bearing_capacity_characteristic_kpa"],
            ),
            _rfi(
                "rfi-closed",
                "closed",
                client_response="Designer submitted Rev C geotechnical note.",
                triggers_incremental_recheck=True,
                reopen_review_items=["side_resistance_standard_kpa"],
                completed_recheck_items=["side_resistance_standard_kpa"],
            ),
        ],
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-003",
                source_phase="report_draft",
                report_title="PV Design Review Report",
                section_count=6,
                rfi_count=1,
                created_by="Engineer A",
                created_at="2026-05-24T11:00:00+08:00",
                revision_status="issued_for_client_response",
                related_rfi_ids=["rfi-closed"],
            )
        ],
    )

    zh_rows = build_clarification_history_rows(state, "zh")
    en_rows = build_clarification_history_rows(state, "en")

    assert zh_rows[0] == {
        "澄清 ID": "rfi-responded",
        "状态": "已回复",
        "责任方": "客户 / 设计院",
        "打开日期": "2026-05-20",
        "所需资料/字段": "geotechnical_report",
        "需要增量复核": "是",
        "复核状态": "待复核",
        "最新报告已覆盖": "否",
        "下一步": "工程师复核并关闭",
    }
    assert "Awaiting" not in str(zh_rows)
    assert en_rows[1]["Clarification ID"] == "rfi-closed"
    assert en_rows[1]["Latest Report Coverage"] == "Covered"
    assert en_rows[1]["Next Action"] == "No clarification action"
