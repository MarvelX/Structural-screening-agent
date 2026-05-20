from __future__ import annotations

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
from structural_screening_agent.bv_review.project_state import ProjectReviewState


def apply_authorized_agent_response_to_state(
    state: ProjectReviewState,
    sandbox: AgentResponseSandboxResult,
    plan: AgentResponseApplicationPlan,
    authorization: AgentResponseApplicationAuthorization,
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
        raise ValueError("Engineer authorization response digest must match application plan.")
    if sandbox.response_digest != plan.response_digest:
        raise ValueError("Sandbox response digest must match application plan.")
    if compute_agent_response_digest(sandbox.response_text) != sandbox.response_digest:
        raise ValueError("Sandbox response digest must match sandbox response text.")
    if sandbox.agent_role != plan.agent_role:
        raise ValueError("Sandbox agent role must match application plan agent role.")

    parsed_output = parse_agent_json_response(
        sandbox.agent_role,
        sandbox.response_text,
        state=state,
    )
    return apply_agent_output_to_state(state, parsed_output)
