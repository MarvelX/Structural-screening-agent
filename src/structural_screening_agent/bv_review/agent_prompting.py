from __future__ import annotations

import json
from typing import TypeAlias

from pydantic import BaseModel, Field, ValidationError

from structural_screening_agent.bv_review.agent_contracts import (
    AGENT_CONTRACT_SCHEMA_VERSION,
    AGENT_ROLE_SEQUENCE,
    AgentRole,
    BasisCodeAgentOutput,
    CalculationCheckAgentOutput,
    DocumentIntakeAgentOutput,
    ReportComposerAgentOutput,
    ReviewPlanAgentOutput,
    RiskNCRAgentOutput,
    StructuralReviewAgentOutput,
    validate_calculation_check_output_against_state,
)
from structural_screening_agent.bv_review.project_state import ProjectReviewState


AgentOutputModel: TypeAlias = (
    type[DocumentIntakeAgentOutput]
    | type[BasisCodeAgentOutput]
    | type[ReviewPlanAgentOutput]
    | type[StructuralReviewAgentOutput]
    | type[CalculationCheckAgentOutput]
    | type[RiskNCRAgentOutput]
    | type[ReportComposerAgentOutput]
)
AgentParsedOutput: TypeAlias = (
    DocumentIntakeAgentOutput
    | BasisCodeAgentOutput
    | ReviewPlanAgentOutput
    | StructuralReviewAgentOutput
    | CalculationCheckAgentOutput
    | RiskNCRAgentOutput
    | ReportComposerAgentOutput
)


class AgentPromptPackage(BaseModel):
    agent_role: AgentRole
    schema_version: str = AGENT_CONTRACT_SCHEMA_VERSION
    output_model_name: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)
    user_prompt: str = Field(min_length=1)
    output_schema: dict[str, object] = Field(default_factory=dict)


def build_agent_prompt_package(
    agent_role: AgentRole,
    state: ProjectReviewState,
) -> AgentPromptPackage:
    output_model = _output_model_for_role(agent_role)
    return AgentPromptPackage(
        agent_role=agent_role,
        output_model_name=output_model.__name__,
        system_prompt=_build_system_prompt(agent_role, output_model),
        user_prompt=_build_user_prompt(agent_role, state),
        output_schema=output_model.model_json_schema(),
    )


def build_agent_prompt_packages(state: ProjectReviewState) -> list[AgentPromptPackage]:
    return [build_agent_prompt_package(role, state) for role in AGENT_ROLE_SEQUENCE]


def parse_agent_json_response(
    agent_role: AgentRole,
    response_text: str,
    *,
    state: ProjectReviewState | None = None,
) -> AgentParsedOutput:
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Agent response must be a valid JSON object.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Agent response must be a valid JSON object.")
    if payload.get("agent_role", agent_role) != agent_role:
        raise ValueError("Agent response role does not match requested agent role.")
    if agent_role == "calculation_check" and state is None:
        raise ValueError("Calculation check response validation requires project state.")

    output_model = _output_model_for_role(agent_role)
    try:
        parsed = output_model.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

    if isinstance(parsed, CalculationCheckAgentOutput):
        validate_calculation_check_output_against_state(parsed, state)
    return parsed


def _build_system_prompt(
    agent_role: AgentRole,
    output_model: AgentOutputModel,
) -> str:
    return "\n".join(
        [
            f"You are the {agent_role} specialist in a BV-style PV design review workflow.",
            "Return exactly one JSON object that conforms to the provided JSON schema.",
            "Do not include Markdown, prose outside JSON, comments, or trailing text.",
            f"Set schema_version to {AGENT_CONTRACT_SCHEMA_VERSION}.",
            "Do not produce formal engineering conclusions.",
            "Do not claim official BV signing or issue authority.",
            "All engineering conclusions must stay traceable to evidence, deterministic checks, and engineer review.",
            "Calculation safety decisions must come from existing deterministic calculation runs, not from the agent.",
            _role_specific_instruction(agent_role),
            f"Output model: {output_model.__name__}.",
        ]
    )


def _build_user_prompt(agent_role: AgentRole, state: ProjectReviewState) -> str:
    intake = state.intake
    lines = [
        f"Project ID: {state.project_id}",
        f"Project name: {intake.project_name}",
        f"Country or region: {intake.country_or_region}",
        f"Project type: {intake.project_type}",
        f"Design stage: {intake.design_stage}",
        "Standards systems: " + ", ".join(intake.standards_systems),
        "Review objects: " + ", ".join(intake.review_objects),
        "Document statuses: "
        + ", ".join(
            f"{document_key}={status}"
            for document_key, status in sorted(intake.documents.items())
        ),
        f"Current phase: {state.current_phase}",
        "Existing calculation runs: "
        + ", ".join(run.run_id for run in state.calculation_runs),
        "Existing RFI items: " + ", ".join(item.rfi_id for item in state.rfi_items),
        "Existing risks: " + ", ".join(item.risk_id for item in state.risks),
    ]
    if agent_role == "calculation_check":
        lines.append(
            "Use only existing calculation_run_ids listed above. Do not create calculation results."
        )
    if agent_role == "report_composer":
        lines.append(
            "Draft report sections and open RFI items only; do not close or respond to RFI items."
        )
    return "\n".join(lines)


def _role_specific_instruction(agent_role: AgentRole) -> str:
    instructions = {
        "document_intake": (
            "Extract only traceable candidate fields and document versions with source evidence."
        ),
        "basis_code": (
            "Recommend review basis references from project country, standards, contract, and selected review objects."
        ),
        "review_plan": (
            "Create review plan and ITP items with method, responsible role, blocking condition, and deliverable."
        ),
        "structural_review": (
            "Split the review path into support structure, foundation, load, connection, and interface checks."
        ),
        "calculation_check": (
            "Do not create calculation results; only reference deterministic calculation runs already present in state."
        ),
        "risk_ncr": (
            "Draft risks and NCR wording from document gaps, deterministic calculation runs, and evidence only."
        ),
        "report_composer": (
            "Draft report sections and open RFI items with screening-level or review-support boundary wording."
        ),
    }
    return instructions[agent_role]


def _output_model_for_role(agent_role: AgentRole) -> AgentOutputModel:
    models: dict[AgentRole, AgentOutputModel] = {
        "document_intake": DocumentIntakeAgentOutput,
        "basis_code": BasisCodeAgentOutput,
        "review_plan": ReviewPlanAgentOutput,
        "structural_review": StructuralReviewAgentOutput,
        "calculation_check": CalculationCheckAgentOutput,
        "risk_ncr": RiskNCRAgentOutput,
        "report_composer": ReportComposerAgentOutput,
    }
    return models[agent_role]
