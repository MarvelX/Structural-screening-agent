from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.agent_prompting import (
    AgentResponseApplicationAuthorization,
    AgentResponseApplicationPlan,
    AgentResponseSandboxResult,
    compute_agent_response_digest,
    parse_agent_json_response,
)
from structural_screening_agent.bv_review.agent_workflow import (
    apply_agent_output_to_state,
)
from structural_screening_agent.bv_review.project_state import (
    EngineerApproval,
    ProjectReviewState,
)


class AgentResponseApplicationPacket(BaseModel):
    workflow_signature: str = Field(min_length=1)
    workflow_state_signature: str = Field(min_length=1)
    sandbox_result: AgentResponseSandboxResult
    application_plan: AgentResponseApplicationPlan


def workflow_state_application_signature(state: ProjectReviewState) -> str:
    return state.model_dump_json()


def build_agent_response_application_packet(
    *,
    workflow_signature: str,
    state: ProjectReviewState,
    sandbox: AgentResponseSandboxResult,
    plan: AgentResponseApplicationPlan,
) -> AgentResponseApplicationPacket:
    return AgentResponseApplicationPacket(
        workflow_signature=workflow_signature,
        workflow_state_signature=workflow_state_application_signature(state),
        sandbox_result=sandbox,
        application_plan=plan,
    )


def is_agent_response_application_packet_current(
    packet: AgentResponseApplicationPacket,
    *,
    workflow_signature: str,
    state: ProjectReviewState,
) -> bool:
    return (
        packet.workflow_signature == workflow_signature
        and packet.workflow_state_signature == workflow_state_application_signature(state)
    )


def apply_authorized_agent_response_to_state(
    state: ProjectReviewState,
    sandbox: AgentResponseSandboxResult,
    plan: AgentResponseApplicationPlan,
    authorization: AgentResponseApplicationAuthorization,
    *,
    approved_at: str | None = None,
) -> ProjectReviewState:
    if plan.plan_status != "ready_for_controlled_application":
        raise ValueError("Application plan must be ready before applying agent output.")
    if authorization.decision != "authorized":
        raise ValueError(
            "Engineer authorization must be authorized before applying agent output."
        )
    if authorization.plan_id != plan.plan_id:
        raise ValueError("Engineer authorization plan_id must match application plan.")
    if authorization.response_digest != plan.response_digest:
        raise ValueError(
            "Engineer authorization response digest must match application plan."
        )
    if sandbox.response_digest != plan.response_digest:
        raise ValueError("Sandbox response digest must match application plan.")
    if compute_agent_response_digest(sandbox.response_text) != sandbox.response_digest:
        raise ValueError("Sandbox response digest must match sandbox response text.")
    if sandbox.agent_role != plan.agent_role:
        raise ValueError("Sandbox agent role must match application plan agent role.")
    if any(
        approval.target_type == "agent_application"
        and approval.target_id == plan.plan_id
        for approval in state.approvals
    ):
        raise ValueError(
            "Application plan already has an engineer authorization record."
        )

    parsed_output = parse_agent_json_response(
        sandbox.agent_role,
        sandbox.response_text,
        state=state,
    )
    updated_state = apply_agent_output_to_state(state, parsed_output)
    return updated_state.model_copy(
        update={
            "approvals": [
                *updated_state.approvals,
                _build_agent_application_approval(
                    updated_state,
                    plan,
                    authorization,
                    approved_at or datetime.now(timezone.utc).isoformat(),
                ),
            ]
        }
    )


def _build_agent_application_approval(
    state: ProjectReviewState,
    plan: AgentResponseApplicationPlan,
    authorization: AgentResponseApplicationAuthorization,
    approved_at: str,
) -> EngineerApproval:
    return EngineerApproval(
        approval_id=f"agent-application-{len(state.approvals) + 1:03d}",
        target_type="agent_application",
        target_id=plan.plan_id,
        status="approved",
        reviewer=authorization.reviewer,
        approved_at=approved_at,
        comment=authorization.comment,
        locked=True,
    )
