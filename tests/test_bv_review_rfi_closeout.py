import pytest

from structural_screening_agent.bv_review import (
    BVReviewIntake,
    ProjectReviewState,
    RFIItem,
)
from structural_screening_agent.bv_review.human_gate import (
    close_rfi_after_engineer_review,
    build_report_draft_gate_result,
    record_rfi_client_response,
)
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
    )

    rfi = closed.rfi_items[0]
    assert rfi.status == "closed"
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
