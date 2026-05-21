import json

import pytest

from structural_screening_agent.bv_review.agent_application import (
    apply_authorized_agent_response_to_state,
    build_agent_response_application_packet,
    is_agent_response_application_packet_current,
    workflow_state_application_signature,
)
from structural_screening_agent.bv_review.agent_prompting import (
    AgentResponseApplicationAuthorization,
    AgentResponseApplicationPlan,
    AgentResponseSandboxResult,
    build_agent_response_application_plan,
    build_agent_response_engineer_handoff,
    build_agent_prompt_package,
    build_agent_response_sandbox_result,
    build_sample_agent_response_json,
)
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.project_state import ProjectReviewState


def test_apply_authorized_agent_response_requires_ready_plan_and_engineer_authorization() -> None:
    state, sandbox, plan = _ready_document_intake_application()
    authorization = AgentResponseApplicationAuthorization(
        plan_id=plan.plan_id,
        response_digest=plan.response_digest,
        reviewer="Engineer A",
        decision="authorized",
        comment="Move validated intake output into controlled workflow.",
    )

    updated = apply_authorized_agent_response_to_state(
        state,
        sandbox,
        plan,
        authorization,
    )

    assert updated is not state
    assert state.document_versions == []
    assert [document.document_id for document in updated.document_versions]
    assert updated.current_phase == "document_check"
    assert updated.phase_statuses["document_check"] == "waiting_for_engineer"
    assert len(updated.agent_events) == 1
    assert updated.agent_events[0].event_id == "agent-event-001"
    assert updated.agent_events[0].agent_role == "document_intake"
    application_approval = updated.approvals[-1]
    assert application_approval.approval_id == "agent-application-001"
    assert application_approval.target_type == "agent_application"
    assert application_approval.target_id == plan.plan_id
    assert application_approval.status == "approved"
    assert application_approval.reviewer == "Engineer A"
    assert application_approval.comment == (
        "Move validated intake output into controlled workflow."
    )
    assert application_approval.locked is True


def test_apply_authorized_agent_response_rejects_blocked_plan_or_missing_authorization() -> None:
    state = ProjectReviewState(project_id="pv-application-001", intake=_sample_intake())
    sandbox = build_agent_response_sandbox_result(
        build_agent_prompt_package("document_intake", state),
        "not json",
        state=state,
    )
    blocked_plan = build_agent_response_application_plan(
        build_agent_response_engineer_handoff(sandbox)
    )
    authorization = AgentResponseApplicationAuthorization(
        plan_id=blocked_plan.plan_id,
        response_digest=blocked_plan.response_digest,
        reviewer="Engineer A",
        decision="authorized",
    )

    with pytest.raises(ValueError, match="ready"):
        apply_authorized_agent_response_to_state(
            state,
            sandbox,
            blocked_plan,
            authorization,
        )

    ready_state, ready_sandbox, ready_plan = _ready_document_intake_application()
    rejected_authorization = AgentResponseApplicationAuthorization(
        plan_id=ready_plan.plan_id,
        response_digest=ready_plan.response_digest,
        reviewer="Engineer B",
        decision="rejected",
    )

    with pytest.raises(ValueError, match="authorized"):
        apply_authorized_agent_response_to_state(
            ready_state,
            ready_sandbox,
            ready_plan,
            rejected_authorization,
        )


def test_apply_authorized_agent_response_rejects_duplicate_plan_authorization() -> None:
    state, sandbox, plan = _ready_document_intake_application()
    authorization = AgentResponseApplicationAuthorization(
        plan_id=plan.plan_id,
        response_digest=plan.response_digest,
        reviewer="Engineer A",
        decision="authorized",
    )
    updated = apply_authorized_agent_response_to_state(
        state,
        sandbox,
        plan,
        authorization,
    )

    with pytest.raises(ValueError, match="already has an engineer authorization"):
        apply_authorized_agent_response_to_state(
            updated,
            sandbox,
            plan,
            authorization,
        )


def test_apply_authorized_agent_response_rejects_plan_authorization_mismatch() -> None:
    state, sandbox, plan = _ready_document_intake_application()
    wrong_plan_authorization = AgentResponseApplicationAuthorization(
        plan_id="application-plan-other",
        response_digest=plan.response_digest,
        reviewer="Engineer A",
        decision="authorized",
    )

    with pytest.raises(ValueError, match="plan_id"):
        apply_authorized_agent_response_to_state(
            state,
            sandbox,
            plan,
            wrong_plan_authorization,
        )

    wrong_response_authorization = AgentResponseApplicationAuthorization(
        plan_id=plan.plan_id,
        response_digest="wrong-response-digest",
        reviewer="Engineer A",
        decision="authorized",
    )

    with pytest.raises(ValueError, match="response digest"):
        apply_authorized_agent_response_to_state(
            state,
            sandbox,
            plan,
            wrong_response_authorization,
        )


def test_apply_authorized_agent_response_rejects_plan_sandbox_mismatch() -> None:
    state, sandbox, plan = _ready_document_intake_application()
    authorization = AgentResponseApplicationAuthorization(
        plan_id=plan.plan_id,
        response_digest=plan.response_digest,
        reviewer="Engineer A",
        decision="authorized",
    )
    mismatched_digest_sandbox = sandbox.model_copy(
        update={"response_digest": "wrong-response-digest"}
    )

    with pytest.raises(ValueError, match="response digest"):
        apply_authorized_agent_response_to_state(
            state,
            mismatched_digest_sandbox,
            plan,
            authorization,
        )

    mismatched_role_sandbox = sandbox.model_copy(update={"agent_role": "basis_code"})

    with pytest.raises(ValueError, match="agent role"):
        apply_authorized_agent_response_to_state(
            state,
            mismatched_role_sandbox,
            plan,
            authorization,
        )


def test_apply_authorized_agent_response_recomputes_sandbox_response_digest() -> None:
    state, sandbox, plan = _ready_document_intake_application()
    authorization = AgentResponseApplicationAuthorization(
        plan_id=plan.plan_id,
        response_digest=plan.response_digest,
        reviewer="Engineer A",
        decision="authorized",
    )
    tampered_sandbox = sandbox.model_copy(
        update={
            "response_text": json.dumps(
                {
                    "project_id": state.project_id,
                    "document_versions": [],
                    "extracted_fields": [],
                }
            )
        }
    )

    with pytest.raises(ValueError, match="response text"):
        apply_authorized_agent_response_to_state(
            state,
            tampered_sandbox,
            plan,
            authorization,
        )


def test_agent_response_application_packet_tracks_current_workflow_state() -> None:
    state, sandbox, plan = _ready_document_intake_application()

    packet = build_agent_response_application_packet(
        workflow_signature="form-v1",
        state=state,
        sandbox=sandbox,
        plan=plan,
    )

    assert packet.workflow_signature == "form-v1"
    assert packet.workflow_state_signature == workflow_state_application_signature(state)
    assert packet.sandbox_result == sandbox
    assert packet.application_plan == plan
    assert is_agent_response_application_packet_current(
        packet,
        workflow_signature="form-v1",
        state=state,
    )
    assert not is_agent_response_application_packet_current(
        packet,
        workflow_signature="form-v2",
        state=state,
    )
    assert not is_agent_response_application_packet_current(
        packet,
        workflow_signature="form-v1",
        state=state.model_copy(update={"current_phase": "document_check"}),
    )


def _ready_document_intake_application() -> tuple[
    ProjectReviewState,
    AgentResponseSandboxResult,
    AgentResponseApplicationPlan,
]:
    state = ProjectReviewState(project_id="pv-application-001", intake=_sample_intake())
    sandbox = build_agent_response_sandbox_result(
        build_agent_prompt_package("document_intake", state),
        build_sample_agent_response_json("document_intake", state),
        state=state,
    )
    plan = build_agent_response_application_plan(
        build_agent_response_engineer_handoff(sandbox)
    )
    return state, sandbox, plan


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV application demo",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents={
            "structural_drawings": "available",
            "calculation_report": "partial",
            "geotechnical_report": "missing",
        },
    )
