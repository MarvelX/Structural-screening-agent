import pytest

from structural_screening_agent.bv_review.human_gate import (
    build_calculation_gate_run,
    build_engineer_approval,
    record_agent_review_decision,
    fields_ready_for_calculation,
)
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.project_state import (
    AgentWorkflowEvent,
    EngineerApproval,
    ExtractedField,
    ProjectReviewState,
)


def _review_state() -> ProjectReviewState:
    intake = BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb"],
        review_objects=["mounting_structure", "foundation"],
        documents={"structural_drawings": "available"},
    )
    return ProjectReviewState(
        project_id="pv-human-review",
        intake=intake,
        current_phase="document_check",
        phase_statuses={
            "intake": "approved",
            "document_check": "waiting_for_engineer",
            "basis_build": "pending",
            "review_plan": "pending",
            "engineer_data_lock": "pending",
            "calculation_check": "pending",
            "risk_register": "pending",
            "report_draft": "pending",
            "engineer_approval": "pending",
            "issue_rfi_closeout": "pending",
        },
        agent_events=[
            AgentWorkflowEvent(
                event_id="agent-event-001",
                agent_role="document_intake",
                target_phase="document_check",
                status="applied",
                output_schema_version="phase2-agent-contracts-v1",
                requires_engineer_review=True,
                summary_counts={"document_versions": 1},
            )
        ],
    )


def test_fields_ready_for_calculation_blocks_unconfirmed_fields() -> None:
    unconfirmed = ExtractedField(
        field_id="pile_length",
        name="Pile length",
        candidate_value="3.5",
        source_document_id="foundation-drawing-f201",
        page_or_section="Sheet F-201, foundation schedule",
        quote="Pile length L=3.5m",
        confidence=0.85,
    )

    assert fields_ready_for_calculation([unconfirmed]) is False


def test_fields_ready_for_calculation_requires_at_least_one_calculation_field() -> None:
    confirmed_but_excluded = ExtractedField(
        field_id="drawing_note",
        name="Drawing note",
        candidate_value="Issued for review",
        source_document_id="structural-drawing-a101",
        page_or_section="Title block",
        quote="Issued for review",
        confidence=0.8,
        is_confirmed=True,
        confirmed_value="Issued for review",
    )

    assert fields_ready_for_calculation([confirmed_but_excluded]) is False


def test_build_engineer_approval_returns_locked_gate_approval() -> None:
    approval = build_engineer_approval(
        approval_id="approval-001",
        target_id="calculation",
        reviewer="Engineer A",
        comment="Inputs confirmed for Phase 1 gate.",
    )

    assert approval.target_type == "gate"
    assert approval.target_id == "calculation"
    assert approval.status == "approved"
    assert approval.locked is True
    assert approval.reviewer == "Engineer A"


def test_record_agent_review_decision_approves_pending_agent_event_phase() -> None:
    state = _review_state()

    reviewed = record_agent_review_decision(
        state,
        event_id="agent-event-001",
        decision="approved",
        reviewer="Engineer A",
        comment="Document intake evidence reviewed.",
    )

    assert reviewed.phase_statuses["document_check"] == "approved"
    assert reviewed.approvals[-1] == EngineerApproval(
        approval_id="agent-review-agent-event-001",
        target_type="agent_event",
        target_id="agent-event-001",
        status="approved",
        reviewer="Engineer A",
        comment="Document intake evidence reviewed.",
        locked=True,
    )
    assert state.phase_statuses["document_check"] == "waiting_for_engineer"
    assert state.approvals == []


def test_record_agent_review_decision_rejects_pending_agent_event_without_locking() -> None:
    reviewed = record_agent_review_decision(
        _review_state(),
        event_id="agent-event-001",
        decision="rejected",
        reviewer="Engineer B",
        comment="Source evidence is incomplete.",
    )

    assert reviewed.phase_statuses["document_check"] == "rejected"
    assert reviewed.approvals[-1].target_type == "agent_event"
    assert reviewed.approvals[-1].target_id == "agent-event-001"
    assert reviewed.approvals[-1].status == "rejected"
    assert reviewed.approvals[-1].locked is False


def test_record_agent_review_decision_rejects_unknown_or_non_review_event() -> None:
    with pytest.raises(ValueError, match="Agent event"):
        record_agent_review_decision(
            _review_state(),
            event_id="missing-event",
            decision="approved",
            reviewer="Engineer A",
        )

    non_review_state = _review_state().model_copy(
        update={
            "agent_events": [
                _review_state().agent_events[0].model_copy(
                    update={"requires_engineer_review": False}
                )
            ]
        }
    )
    with pytest.raises(ValueError, match="does not require"):
        record_agent_review_decision(
            non_review_state,
            event_id="agent-event-001",
            decision="approved",
            reviewer="Engineer A",
        )


def test_record_agent_review_decision_rejects_duplicate_or_non_pending_event() -> None:
    reviewed = record_agent_review_decision(
        _review_state(),
        event_id="agent-event-001",
        decision="approved",
        reviewer="Engineer A",
    )

    with pytest.raises(ValueError, match="already has"):
        record_agent_review_decision(
            reviewed,
            event_id="agent-event-001",
            decision="approved",
            reviewer="Engineer A",
        )

    non_pending_state = _review_state().model_copy(
        update={
            "phase_statuses": {
                **_review_state().phase_statuses,
                "document_check": "blocked",
            }
        }
    )
    with pytest.raises(ValueError, match="not pending"):
        record_agent_review_decision(
            non_pending_state,
            event_id="agent-event-001",
            decision="approved",
            reviewer="Engineer A",
        )


def test_build_calculation_gate_run_blocks_when_fields_are_not_locked() -> None:
    run = build_calculation_gate_run(
        run_id="run-001",
        engine_name="foundation",
        fields=[
            ExtractedField(
                field_id="tilt",
                name="Tilt angle",
                candidate_value="25",
                source_document_id="structural-drawing-a101",
                page_or_section="Sheet S-101, mounting layout note 3",
                quote="Tilt angle: 25 deg",
                confidence=0.9,
            )
        ],
    )

    assert run.status == "blocked"
    assert run.input_locked is False
    assert run.structured_errors


def test_build_calculation_gate_run_returns_ready_placeholder_for_confirmed_fields() -> None:
    run = build_calculation_gate_run(
        run_id="run-002",
        engine_name="superstructure",
        fields=[
            ExtractedField(
                field_id="tilt",
                name="Tilt angle",
                candidate_value="25",
                source_document_id="structural-drawing-a101",
                page_or_section="Sheet S-101, mounting layout note 3",
                quote="Tilt angle: 25 deg",
                confidence=0.95,
                is_confirmed=True,
                confirmed_value="25",
                include_in_calculation=True,
            ),
            ExtractedField(
                field_id="pile_length",
                name="Pile length",
                candidate_value="3.5",
                source_document_id="foundation-drawing-f201",
                page_or_section="Sheet F-201, foundation schedule",
                quote="Pile length L=3.5m",
                confidence=0.9,
                is_confirmed=True,
                confirmed_value="3.5",
                include_in_calculation=True,
            ),
        ],
    )

    assert run.status == "ready"
    assert run.input_locked is True
    assert run.input_field_ids == ["tilt", "pile_length"]
    assert run.result_summary == {}
