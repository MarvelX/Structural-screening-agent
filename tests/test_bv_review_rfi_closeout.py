import pytest

from structural_screening_agent.bv_review import (
    BVReviewIntake,
    ProjectReviewState,
    RFIItem,
)
from structural_screening_agent.bv_review.human_gate import (
    close_rfi_after_engineer_review,
    build_report_draft_gate_result,
    issue_blocked_calculation_draft_rfi,
    record_rfi_client_response,
)
from structural_screening_agent.bv_review.report import build_bv_report_preview
from structural_screening_agent.bv_review.project_state import CalculationRun
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


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


def _state_with_open_incremental_rfi() -> ProjectReviewState:
    return ProjectReviewState(
        project_id="pv-rfi-001",
        intake=_sample_intake(),
        current_phase="report_draft",
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-run-001",
                question="请确认基础筛查级风险的处置意见。",
                responsible_party="client / designer",
                trigger_basis="确定性筛查计算 foundation-run-001: 控制利用率=1.21。",
                required_document_or_field="uplift_force_kn, compression_force_kn",
                status="open",
                reopen_review_items=["uplift_force_kn", "compression_force_kn"],
                triggers_incremental_recheck=True,
            )
        ],
    )


def test_record_rfi_client_response_marks_rfi_responded_and_keeps_gate_blocked() -> None:
    responded = record_rfi_client_response(
        _state_with_open_incremental_rfi(),
        rfi_id="rfi-foundation-run-001",
        client_response="设计院提交 Rev B 计算书并确认基础反力取值。",
    )

    rfi = responded.rfi_items[0]
    assert rfi.status == "responded"
    assert rfi.client_response == "设计院提交 Rev B 计算书并确认基础反力取值。"
    assert rfi.triggers_incremental_recheck is True
    assert rfi.reopen_review_items == ["uplift_force_kn", "compression_force_kn"]
    assert responded.current_phase == "issue_rfi_closeout"
    assert responded.phase_statuses["issue_rfi_closeout"] == "waiting_for_engineer"

    gate = build_report_draft_gate_result(responded, evaluate_bv_review(_sample_intake()))

    assert gate.status == "blocked"
    assert gate.incremental_recheck_rfi_ids == ["rfi-foundation-run-001"]


def test_close_rfi_after_engineer_review_closes_responded_rfi_and_unblocks_incremental_rfi_gate() -> None:
    responded = record_rfi_client_response(
        _state_with_open_incremental_rfi(),
        rfi_id="rfi-foundation-run-001",
        client_response="设计院提交 Rev B 计算书并确认基础反力取值。",
    )

    closed = close_rfi_after_engineer_review(
        responded,
        rfi_id="rfi-foundation-run-001",
        closeout_note="工程师已完成增量复核，RFI 可关闭。",
        completed_recheck_item_ids=["uplift_force_kn", "compression_force_kn"],
    )

    rfi = closed.rfi_items[0]
    assert rfi.status == "closed"
    assert rfi.completed_recheck_items == ["uplift_force_kn", "compression_force_kn"]
    assert (rfi.client_response or "").startswith("设计院提交 Rev B 计算书并确认基础反力取值。")
    assert "工程师已完成增量复核" in (rfi.client_response or "")
    assert closed.phase_statuses["issue_rfi_closeout"] == "approved"

    gate = build_report_draft_gate_result(closed, evaluate_bv_review(_sample_intake()))

    assert "rfi-foundation-run-001" not in gate.incremental_recheck_rfi_ids


def test_rfi_closeout_rejects_unknown_duplicate_or_wrong_status_rfi() -> None:
    state = _state_with_open_incremental_rfi()

    with pytest.raises(ValueError, match="does not exist"):
        record_rfi_client_response(
            state,
            rfi_id="rfi-missing",
            client_response="设计院回复。",
        )

    with pytest.raises(ValueError, match="Only responded RFI"):
        close_rfi_after_engineer_review(
            state,
            rfi_id="rfi-foundation-run-001",
            closeout_note="工程师关闭。",
            completed_recheck_item_ids=["uplift_force_kn", "compression_force_kn"],
        )

    duplicate_state = state.model_copy(
        update={"rfi_items": [*state.rfi_items, state.rfi_items[0]]}
    )
    with pytest.raises(ValueError, match="duplicated"):
        record_rfi_client_response(
            duplicate_state,
            rfi_id="rfi-foundation-run-001",
            client_response="设计院回复。",
        )


def test_close_incremental_rfi_requires_completed_recheck_items() -> None:
    responded = record_rfi_client_response(
        _state_with_open_incremental_rfi(),
        rfi_id="rfi-foundation-run-001",
        client_response="设计院提交 Rev B 计算书并确认基础反力取值。",
    )

    with pytest.raises(ValueError, match="completed recheck items"):
        close_rfi_after_engineer_review(
            responded,
            rfi_id="rfi-foundation-run-001",
            closeout_note="工程师关闭。",
        )

    with pytest.raises(ValueError, match="missing"):
        close_rfi_after_engineer_review(
            responded,
            rfi_id="rfi-foundation-run-001",
            closeout_note="工程师关闭。",
            completed_recheck_item_ids=["uplift_force_kn"],
        )

    with pytest.raises(ValueError, match="unknown"):
        close_rfi_after_engineer_review(
            responded,
            rfi_id="rfi-foundation-run-001",
            closeout_note="工程师关闭。",
            completed_recheck_item_ids=[
                "uplift_force_kn",
                "compression_force_kn",
                "untracked_item",
            ],
        )


def test_issue_blocked_calculation_draft_rfi_requires_engineer_review_and_keeps_calculation_gate_blocked() -> None:
    state = ProjectReviewState(
        project_id="pv-rfi-002",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        calculation_runs=[
            CalculationRun(
                run_id="foundation-failed-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["pile_length_m"],
                input_locked=False,
                status="failed",
                structured_errors=["foundation calculation failed."],
            )
        ],
    )

    issued = issue_blocked_calculation_draft_rfi(
        state,
        rfi_id="rfi-calculation_blocked_foundation_failed_001",
        reviewer="Engineer A",
        comment="Issue RFI to request corrected foundation inputs.",
        approved_at="2026-05-21T12:00:00+08:00",
    )

    assert issued.current_phase == "issue_rfi_closeout"
    assert issued.phase_statuses["issue_rfi_closeout"] == "waiting_for_client"
    assert issued.phase_statuses["calculation_check"] == "pending"
    assert issued.agent_events == []
    assert issued.risks == []
    assert [item.rfi_id for item in issued.rfi_items] == [
        "rfi-calculation_blocked_foundation_failed_001"
    ]
    assert issued.rfi_items[0].status == "open"
    assert issued.rfi_items[0].opened_at == "2026-05-21"
    assert issued.rfi_items[0].triggers_incremental_recheck is True
    approval = issued.approvals[-1]
    assert approval.target_type == "rfi"
    assert approval.target_id == "rfi-calculation_blocked_foundation_failed_001"
    assert approval.status == "approved"
    assert approval.reviewer == "Engineer A"
    assert approval.comment == "Issue RFI to request corrected foundation inputs."
    assert approval.approved_at == "2026-05-21T12:00:00+08:00"
    assert approval.locked is True


def test_issued_blocked_calculation_rfi_feeds_report_sla_status() -> None:
    state = ProjectReviewState(
        project_id="pv-rfi-report-sla",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        calculation_runs=[
            CalculationRun(
                run_id="foundation-failed-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["pile_length_m"],
                input_locked=False,
                status="failed",
                structured_errors=["foundation calculation failed."],
            )
        ],
    )

    issued = issue_blocked_calculation_draft_rfi(
        state,
        rfi_id="rfi-calculation_blocked_foundation_failed_001",
        reviewer="Engineer A",
        approved_at="2026-05-21T12:00:00+08:00",
    )
    preview = build_bv_report_preview(
        issued.intake,
        evaluate_bv_review(issued.intake),
        project_state=issued,
    )
    section = next(section for section in preview.sections if section.heading == "项目管理待办")
    text = "\n".join(section.items)

    assert "责任方时限 | 责任方: 客户 / 设计院" in text
    assert "最早到期: 2026-05-28" in text


def test_issue_blocked_calculation_draft_rfi_rejects_unknown_or_duplicate_rfi() -> None:
    state = ProjectReviewState(
        project_id="pv-rfi-003",
        intake=_sample_intake(),
        calculation_runs=[
            CalculationRun(
                run_id="foundation-failed-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["pile_length_m"],
                input_locked=False,
                status="failed",
                structured_errors=["foundation calculation failed."],
            )
        ],
    )
    issued = issue_blocked_calculation_draft_rfi(
        state,
        rfi_id="rfi-calculation_blocked_foundation_failed_001",
        reviewer="Engineer A",
    )

    with pytest.raises(ValueError, match="does not match a blocked calculation draft"):
        issue_blocked_calculation_draft_rfi(
            state,
            rfi_id="rfi-missing",
            reviewer="Engineer A",
        )

    with pytest.raises(ValueError, match="reviewer must not be empty"):
        issue_blocked_calculation_draft_rfi(
            state,
            rfi_id="rfi-calculation_blocked_foundation_failed_001",
            reviewer=" ",
        )

    with pytest.raises(ValueError, match="already exists"):
        issue_blocked_calculation_draft_rfi(
            issued,
            rfi_id="rfi-calculation_blocked_foundation_failed_001",
            reviewer="Engineer A",
        )


def test_issue_foundation_evidence_draft_rfi_requires_engineer_review() -> None:
    state = ProjectReviewState(
        project_id="pv-rfi-foundation-evidence",
        intake=BVReviewIntake(
            project_name="Ground PV design review",
            country_or_region="China",
            project_type="utility_pv",
            design_stage="detailed_design",
            standards_systems=["gb"],
            review_objects=["foundation"],
            documents={
                "calculation_report": "partial",
                "geotechnical_report": "missing",
            },
        ),
        current_phase="engineer_data_lock",
    )

    issued = issue_blocked_calculation_draft_rfi(
        state,
        rfi_id="rfi-foundation_evidence_blocked_geotechnical_parameters",
        reviewer="Engineer A",
        comment="Issue RFI to request geotechnical evidence before calculation.",
    )

    assert issued.current_phase == "issue_rfi_closeout"
    assert issued.phase_statuses["issue_rfi_closeout"] == "waiting_for_client"
    assert issued.rfi_items[0].rfi_id == "rfi-foundation_evidence_blocked_geotechnical_parameters"
    assert issued.rfi_items[0].status == "open"
    assert issued.rfi_items[0].triggers_incremental_recheck is True
    assert "geotechnical_report" in issued.rfi_items[0].required_document_or_field
    assert "side_resistance_standard_kpa" in issued.rfi_items[0].required_document_or_field
    approval = issued.approvals[-1]
    assert approval.target_type == "rfi"
    assert approval.target_id == "rfi-foundation_evidence_blocked_geotechnical_parameters"
    assert approval.locked is True
