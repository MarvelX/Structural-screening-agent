from structural_screening_agent.bv_review import (
    BVReviewIntake,
    EngineerApproval,
    ProjectReviewState,
    RFIItem,
    ReportRevision,
)
from structural_screening_agent.bv_review.report_reissue import (
    build_report_reissue_gate_rows,
    build_report_reissue_gate_summary,
)


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb"],
        review_objects=["foundation"],
        documents={
            "calculation_report": "available",
            "geotechnical_report": "available",
        },
    )


def _report_approval() -> EngineerApproval:
    return EngineerApproval(
        approval_id="report-gate-approval",
        target_type="report",
        target_id="report",
        status="approved",
        reviewer="Engineer A",
        approved_at="2026-05-24T10:00:00+08:00",
        locked=True,
    )


def _rfi(rfi_id: str, status: str, **updates: object) -> RFIItem:
    values = {
        "rfi_id": rfi_id,
        "question": "请补充基础复核资料。",
        "responsible_party": "client / designer",
        "trigger_basis": "Foundation review evidence path.",
        "required_document_or_field": "geotechnical_report",
        "status": status,
        "opened_at": "2026-05-20",
    }
    values.update(updates)
    return RFIItem(**values)


def test_report_reissue_gate_blocks_open_rfi_before_client_response() -> None:
    state = ProjectReviewState(
        project_id="pv-reissue-open-rfi",
        intake=_sample_intake(),
        current_phase="issue_rfi_closeout",
        rfi_items=[
            _rfi(
                "rfi-foundation-001",
                "open",
                triggers_incremental_recheck=True,
                reopen_review_items=["pile_length_m"],
            )
        ],
        approvals=[_report_approval()],
    )

    summary = build_report_reissue_gate_summary(state)

    assert summary.status == "blocked"
    assert summary.next_reissue_action == "collect_client_response"
    assert summary.open_rfi_ids == ["rfi-foundation-001"]
    assert summary.blocking_reasons == [
        "Open or reopened RFI items require client/designer response: rfi-foundation-001"
    ]


def test_report_reissue_gate_blocks_responded_rfi_until_engineer_closeout_and_recheck() -> None:
    state = ProjectReviewState(
        project_id="pv-reissue-responded-rfi",
        intake=_sample_intake(),
        current_phase="issue_rfi_closeout",
        rfi_items=[
            _rfi(
                "rfi-foundation-002",
                "responded",
                client_response="设计院提交 Rev B 地勘资料。",
                triggers_incremental_recheck=True,
                reopen_review_items=["bearing_capacity_characteristic_kpa"],
            )
        ],
        approvals=[_report_approval()],
    )

    summary = build_report_reissue_gate_summary(state)

    assert summary.status == "blocked"
    assert summary.next_reissue_action == "close_rfi_after_engineer_review"
    assert summary.responded_rfi_ids == ["rfi-foundation-002"]
    assert summary.pending_recheck_rfi_ids == ["rfi-foundation-002"]
    assert summary.blocking_reasons == [
        "Responded RFI items require engineer closeout: rfi-foundation-002",
        "Incremental recheck evidence is incomplete for RFI items: rfi-foundation-002",
    ]


def test_report_reissue_gate_requires_report_gate_approval_after_rfi_closeout() -> None:
    state = ProjectReviewState(
        project_id="pv-reissue-report-gate",
        intake=_sample_intake(),
        current_phase="report_draft",
        rfi_items=[
            _rfi(
                "rfi-foundation-003",
                "closed",
                client_response="设计院提交 Rev B 地勘资料。\nCloseout: 工程师已完成复核。",
                triggers_incremental_recheck=True,
                reopen_review_items=["bearing_capacity_characteristic_kpa"],
                completed_recheck_items=["bearing_capacity_characteristic_kpa"],
            )
        ],
    )

    summary = build_report_reissue_gate_summary(state)

    assert summary.status == "blocked"
    assert summary.next_reissue_action == "approve_report_gate"
    assert summary.report_gate_locked is False
    assert summary.closed_rfi_ids == ["rfi-foundation-003"]


def test_report_reissue_gate_is_ready_when_closed_rfi_needs_new_revision_snapshot() -> None:
    state = ProjectReviewState(
        project_id="pv-reissue-ready",
        intake=_sample_intake(),
        current_phase="report_draft",
        approvals=[_report_approval()],
        rfi_items=[
            _rfi(
                "rfi-foundation-004",
                "closed",
                client_response="设计院提交 Rev B 地勘资料。\nCloseout: 工程师已完成复核。",
                triggers_incremental_recheck=True,
                reopen_review_items=["bearing_capacity_characteristic_kpa"],
                completed_recheck_items=["bearing_capacity_characteristic_kpa"],
            )
        ],
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="PV Design Review Report",
                section_count=5,
                rfi_count=0,
                created_by="Engineer A",
                created_at="2026-05-22T10:00:00+08:00",
                revision_status="issued_for_client_response",
                issue_purpose="Initial issue",
            )
        ],
    )

    summary = build_report_reissue_gate_summary(state)
    zh_rows = build_report_reissue_gate_rows(summary, "zh")
    en_rows = build_report_reissue_gate_rows(summary, "en")

    assert summary.status == "ready"
    assert summary.next_reissue_action == "record_reissue_revision"
    assert summary.latest_revision_id == "report-rev-001"
    assert summary.uncovered_closed_rfi_ids == ["rfi-foundation-004"]
    assert zh_rows[0] == {"指标": "再签发状态", "数值": "可记录新版报告"}
    assert en_rows[0] == {"Metric": "Reissue Status", "Value": "Ready to Record Reissue"}


def test_report_reissue_gate_is_ready_when_latest_revision_covers_closed_rfis() -> None:
    state = ProjectReviewState(
        project_id="pv-reissue-covered",
        intake=_sample_intake(),
        current_phase="report_draft",
        approvals=[_report_approval()],
        rfi_items=[
            _rfi(
                "rfi-foundation-005",
                "closed",
                client_response="设计院提交 Rev B 地勘资料。\nCloseout: 工程师已完成复核。",
                triggers_incremental_recheck=True,
                reopen_review_items=["bearing_capacity_characteristic_kpa"],
                completed_recheck_items=["bearing_capacity_characteristic_kpa"],
            )
        ],
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-002",
                source_phase="report_draft",
                report_title="PV Design Review Report",
                section_count=5,
                rfi_count=1,
                created_by="Engineer A",
                created_at="2026-05-24T10:00:00+08:00",
                revision_status="issued_for_client_response",
                issue_purpose="RFI closeout package",
                related_rfi_ids=["rfi-foundation-005"],
            )
        ],
    )

    summary = build_report_reissue_gate_summary(state)

    assert summary.status == "ready"
    assert summary.next_reissue_action == "ready"
    assert summary.uncovered_closed_rfi_ids == []
    assert summary.covered_rfi_ids == ["rfi-foundation-005"]
