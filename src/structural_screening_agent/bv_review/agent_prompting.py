from __future__ import annotations

import json
from typing import Literal, TypeAlias

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
AgentPromptLanguage = Literal["zh", "en"]


class AgentPromptPackage(BaseModel):
    agent_role: AgentRole
    schema_version: str = AGENT_CONTRACT_SCHEMA_VERSION
    output_model_name: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)
    user_prompt: str = Field(min_length=1)
    output_schema: dict[str, object] = Field(default_factory=dict)


class AgentResponseValidationResult(BaseModel):
    agent_role: AgentRole
    ok: bool
    output_model_name: str = Field(min_length=1)
    summary: str = ""
    error: str = ""


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


def build_agent_prompt_package_rows(
    packages: list[AgentPromptPackage],
    language: AgentPromptLanguage,
) -> list[dict[str, object]]:
    if language == "zh":
        return [
            {
                "Agent": _agent_label(package.agent_role, "zh"),
                "输出模型": package.output_model_name,
                "契约版本": package.schema_version,
                "必填字段": ", ".join(_required_schema_fields(package)),
                "边界": "JSON 输出 / 工程师复核 / 不替代签发",
            }
            for package in packages
        ]
    return [
        {
            "Agent": _agent_label(package.agent_role, "en"),
            "Output Model": package.output_model_name,
            "Schema Version": package.schema_version,
            "Required Fields": ", ".join(_required_schema_fields(package)),
            "Boundary": "JSON output / engineer review / no signing authority",
        }
        for package in packages
    ]


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


def validate_agent_json_response(
    agent_role: AgentRole,
    response_text: str,
    *,
    state: ProjectReviewState | None = None,
) -> AgentResponseValidationResult:
    output_model_name = _output_model_for_role(agent_role).__name__
    try:
        parse_agent_json_response(agent_role, response_text, state=state)
    except ValueError as exc:
        return AgentResponseValidationResult(
            agent_role=agent_role,
            ok=False,
            output_model_name=output_model_name,
            error=str(exc),
        )
    return AgentResponseValidationResult(
        agent_role=agent_role,
        ok=True,
        output_model_name=output_model_name,
        summary=f"Validated {output_model_name} for {agent_role}.",
    )


def build_sample_agent_response_json(
    agent_role: AgentRole,
    state: ProjectReviewState,
) -> str:
    return json.dumps(
        _sample_payload_for_role(agent_role, state),
        ensure_ascii=False,
        indent=2,
    )


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


def _sample_payload_for_role(
    agent_role: AgentRole,
    state: ProjectReviewState,
) -> dict[str, object]:
    base = {
        "project_id": state.project_id,
        "schema_version": AGENT_CONTRACT_SCHEMA_VERSION,
    }
    if agent_role == "document_intake":
        return {
            **base,
            "document_versions": [
                {
                    "document_id": "sample-document-001",
                    "document_type": "calculation_report",
                    "revision": "A",
                    "source_name": "sample-calculation-report.pdf",
                    "status": "partial",
                }
            ],
            "extracted_fields": [],
            "missing_document_keys": [],
            "notes": ["Sample JSON only; replace with traceable source evidence."],
        }
    if agent_role == "basis_code":
        return {
            **base,
            "basis_references": [
                {
                    "basis_id": "sample-review-basis",
                    "title": "Sample project review basis",
                    "source_type": "project_specification",
                    "review_actions": ["Confirm applicability with engineer."],
                }
            ],
        }
    if agent_role == "review_plan":
        return {
            **base,
            "review_plan": [
                {
                    "item_id": "sample-review-plan-item",
                    "phase": "technical_check",
                    "method": "Confirm inputs before deterministic screening.",
                    "responsible_role": "BV structural review engineer",
                    "deliverable": "Traceable review note",
                }
            ],
        }
    if agent_role == "structural_review":
        return {
            **base,
            "review_paths": [
                {
                    "path_id": "sample-foundation-review",
                    "review_object": "foundation",
                    "title": "Sample foundation review path",
                    "method": "Check confirmed geotechnical and reaction inputs.",
                    "status": "manual_confirmation_required",
                }
            ],
        }
    if agent_role == "calculation_check":
        run_ids = [run.run_id for run in state.calculation_runs] or [
            "replace-with-existing-run-id"
        ]
        return {**base, "calculation_run_ids": run_ids[:1]}
    if agent_role == "risk_ncr":
        return {
            **base,
            "risks": [],
            "source_calculation_run_ids": [run.run_id for run in state.calculation_runs],
        }
    if agent_role == "report_composer":
        return {
            **base,
            "report_sections": [
                {
                    "heading": "Review boundary",
                    "items": ["This draft is for screening-level review support only."],
                }
            ],
            "rfi_items": [],
            "boundary_statement": (
                "This draft is for screening-level review-support only."
            ),
        }
    raise ValueError(f"Unsupported agent role: {agent_role}")


def _required_schema_fields(package: AgentPromptPackage) -> list[str]:
    required = package.output_schema.get("required", [])
    if not isinstance(required, list):
        return []
    return [str(field) for field in required]


def _agent_label(agent_role: AgentRole, language: AgentPromptLanguage) -> str:
    labels = {
        "document_intake": {
            "zh": "资料接收 Agent",
            "en": "Document Intake Agent",
        },
        "basis_code": {
            "zh": "依据与标准 Agent",
            "en": "Basis & Code Agent",
        },
        "review_plan": {
            "zh": "审核计划 Agent",
            "en": "Review Plan Agent",
        },
        "structural_review": {
            "zh": "结构审核路径 Agent",
            "en": "Structural Review Agent",
        },
        "calculation_check": {
            "zh": "计算校核 Agent",
            "en": "Calculation Check Agent",
        },
        "risk_ncr": {
            "zh": "风险 / NCR Agent",
            "en": "Risk & NCR Agent",
        },
        "report_composer": {
            "zh": "报告编制 Agent",
            "en": "Report Composer Agent",
        },
    }
    return labels[agent_role][language]
