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
from structural_screening_agent.bv_review.project_state import (
    REVIEW_PHASES,
    ProjectReviewState,
    ReviewPhase,
)


AGENT_PROVIDER_DEFAULT_MODELS = {
    "minimax": "MiniMax-M2.5",
    "openai": "gpt-4.1-mini",
    "mock": "demo-mock",
}

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


class AgentResponseImpactPreview(BaseModel):
    agent_role: AgentRole
    output_model_name: str = Field(min_length=1)
    target_phase: ReviewPhase
    requires_engineer_review: bool
    summary_counts: dict[str, int] = Field(default_factory=dict)
    would_update: list[str] = Field(default_factory=list)
    passes_apply_prechecks: bool
    apply_blockers: list[str] = Field(default_factory=list)
    blocks_direct_apply: bool = True
    boundary_statement: str = (
        "Preview only; engineer approval is still required before applying agent output."
    )


class AgentProviderInvocationRequest(BaseModel):
    agent_role: AgentRole
    provider_name: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    mode: Literal["preview"] = "preview"
    messages: list[dict[str, str]] = Field(min_length=2)
    response_format: dict[str, object] = Field(default_factory=dict)
    temperature: float = 0.0
    output_schema: dict[str, object] = Field(default_factory=dict)
    network_request_sent: bool = False
    boundary_statement: str = (
        "Invocation preview only; no network request is sent and no API key is stored."
    )


class AgentResponseSandboxResult(BaseModel):
    agent_role: AgentRole
    mode: Literal["sandbox_preview"] = "sandbox_preview"
    invocation_request: AgentProviderInvocationRequest
    response_text: str
    validation_result: AgentResponseValidationResult
    impact_preview: AgentResponseImpactPreview | None = None
    ready_for_engineer_review: bool = False
    network_request_sent: bool = False
    project_state_changed: bool = False
    boundary_statement: str = (
        "Sandbox result only; no network request is sent and project state is unchanged."
    )


class AgentResponseEngineerHandoff(BaseModel):
    review_packet_id: str = Field(min_length=1)
    agent_role: AgentRole
    handoff_status: Literal["ready_for_engineer_review", "blocked"]
    target_phase: ReviewPhase | None = None
    validation_ok: bool
    apply_prechecks_ok: bool
    requires_engineer_review: bool
    blockers: list[str] = Field(default_factory=list)
    suggested_action: str = Field(min_length=1)
    network_request_sent: bool = False
    project_state_changed: bool = False
    boundary_statement: str = (
        "Handoff preview only; engineer review must be recorded through controlled workflow state."
    )


class AgentResponseApplicationPlan(BaseModel):
    plan_id: str = Field(min_length=1)
    agent_role: AgentRole
    plan_status: Literal["ready_for_controlled_application", "blocked"]
    target_phase: ReviewPhase | None = None
    requires_engineer_authorization: bool = True
    would_create_agent_event: bool = False
    would_set_phase_status: Literal["waiting_for_engineer"] | None = None
    blockers: list[str] = Field(default_factory=list)
    project_state_changed: bool = False
    boundary_statement: str = (
        "Application plan only; no agent output is applied until an engineer authorizes the controlled workflow step."
    )


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


def build_agent_provider_invocation_request(
    package: AgentPromptPackage,
    *,
    provider_name: str = "minimax",
    model_name: str | None = None,
) -> AgentProviderInvocationRequest:
    return AgentProviderInvocationRequest(
        agent_role=package.agent_role,
        provider_name=provider_name,
        model_name=model_name or default_agent_provider_model(provider_name),
        messages=[
            {"role": "system", "content": package.system_prompt},
            {"role": "user", "content": package.user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": package.output_model_name,
                "strict": True,
                "schema": package.output_schema,
            },
        },
        output_schema=package.output_schema,
    )


def default_agent_provider_model(provider_name: str) -> str:
    return AGENT_PROVIDER_DEFAULT_MODELS.get(
        provider_name,
        AGENT_PROVIDER_DEFAULT_MODELS["minimax"],
    )


def build_agent_provider_invocation_rows(
    request: AgentProviderInvocationRequest,
    language: AgentPromptLanguage,
) -> list[dict[str, object]]:
    response_format = request.response_format.get("type", "")
    json_schema = request.response_format.get("json_schema", {})
    schema_is_strict = bool(
        isinstance(json_schema, dict) and json_schema.get("strict") is True
    )
    if language == "zh":
        return [
            {"项目": "Agent", "内容": _agent_label(request.agent_role, "zh")},
            {"项目": "供应商", "内容": request.provider_name},
            {"项目": "模型", "内容": request.model_name},
            {"项目": "模式", "内容": request.mode},
            {"项目": "消息数", "内容": len(request.messages)},
            {"项目": "响应格式", "内容": response_format},
            {"项目": "Schema 严格模式", "内容": "是" if schema_is_strict else "否"},
            {"项目": "温度", "内容": request.temperature},
            {"项目": "网络调用", "内容": "是" if request.network_request_sent else "否"},
            {"项目": "边界", "内容": "仅调用预览；不发送网络请求，也不保存密钥。"},
        ]
    return [
        {"Item": "Agent", "Value": _agent_label(request.agent_role, "en")},
        {"Item": "Provider", "Value": request.provider_name},
        {"Item": "Model", "Value": request.model_name},
        {"Item": "Mode", "Value": request.mode},
        {"Item": "Message Count", "Value": len(request.messages)},
        {"Item": "Response Format", "Value": response_format},
        {"Item": "Schema Strict", "Value": "Yes" if schema_is_strict else "No"},
        {"Item": "Temperature", "Value": request.temperature},
        {"Item": "Network Request", "Value": "Yes" if request.network_request_sent else "No"},
        {"Item": "Boundary", "Value": request.boundary_statement},
    ]


def build_agent_response_sandbox_result(
    package: AgentPromptPackage,
    response_text: str,
    *,
    state: ProjectReviewState,
    provider_name: str = "minimax",
    model_name: str | None = None,
) -> AgentResponseSandboxResult:
    invocation_request = build_agent_provider_invocation_request(
        package,
        provider_name=provider_name,
        model_name=model_name,
    )
    validation_result = validate_agent_json_response(
        package.agent_role,
        response_text,
        state=state,
    )
    impact_preview = (
        preview_agent_response_impact(package.agent_role, response_text, state=state)
        if validation_result.ok
        else None
    )
    return AgentResponseSandboxResult(
        agent_role=package.agent_role,
        invocation_request=invocation_request,
        response_text=response_text,
        validation_result=validation_result,
        impact_preview=impact_preview,
        ready_for_engineer_review=bool(
            validation_result.ok
            and impact_preview is not None
            and impact_preview.requires_engineer_review
            and impact_preview.passes_apply_prechecks
        ),
    )


def build_agent_response_sandbox_rows(
    sandbox: AgentResponseSandboxResult,
    language: AgentPromptLanguage,
) -> list[dict[str, object]]:
    target_phase = sandbox.impact_preview.target_phase if sandbox.impact_preview else "-"
    output_summary = (
        _format_summary_counts(sandbox.impact_preview.summary_counts)
        if sandbox.impact_preview
        else "-"
    )
    if language == "zh":
        return [
            {"项目": "Agent", "内容": _agent_label(sandbox.agent_role, "zh")},
            {
                "项目": "校验结果",
                "内容": "通过" if sandbox.validation_result.ok else "未通过",
            },
            {"项目": "目标阶段", "内容": target_phase},
            {"项目": "产物摘要", "内容": output_summary},
            {"项目": "模式", "内容": sandbox.mode},
            {
                "项目": "可进入工程师复核",
                "内容": "是" if sandbox.ready_for_engineer_review else "否",
            },
            {"项目": "网络调用", "内容": "是" if sandbox.network_request_sent else "否"},
            {
                "项目": "项目状态",
                "内容": "已修改" if sandbox.project_state_changed else "未修改",
            },
            {"项目": "边界", "内容": "仅沙盒结果；不发送网络请求，项目状态不变。"},
        ]
    return [
        {"Item": "Agent", "Value": _agent_label(sandbox.agent_role, "en")},
        {
            "Item": "Validation",
            "Value": "Pass" if sandbox.validation_result.ok else "Fail",
        },
        {"Item": "Target Phase", "Value": target_phase},
        {"Item": "Output Summary", "Value": output_summary},
        {"Item": "Mode", "Value": sandbox.mode},
        {
            "Item": "Ready For Engineer Review",
            "Value": "Yes" if sandbox.ready_for_engineer_review else "No",
        },
        {
            "Item": "Network Request",
            "Value": "Yes" if sandbox.network_request_sent else "No",
        },
        {
            "Item": "Project State",
            "Value": "Changed" if sandbox.project_state_changed else "Unchanged",
        },
        {"Item": "Boundary", "Value": sandbox.boundary_statement},
    ]


def build_agent_response_engineer_handoff(
    sandbox: AgentResponseSandboxResult,
) -> AgentResponseEngineerHandoff:
    impact_preview = sandbox.impact_preview
    blockers = _agent_response_handoff_blockers(sandbox)
    handoff_is_ready = not blockers
    return AgentResponseEngineerHandoff(
        review_packet_id=f"sandbox-review-{sandbox.agent_role}",
        agent_role=sandbox.agent_role,
        handoff_status=(
            "ready_for_engineer_review" if handoff_is_ready else "blocked"
        ),
        target_phase=impact_preview.target_phase if impact_preview else None,
        validation_ok=sandbox.validation_result.ok,
        apply_prechecks_ok=bool(
            impact_preview and impact_preview.passes_apply_prechecks
        ),
        requires_engineer_review=bool(
            impact_preview and impact_preview.requires_engineer_review
        ),
        blockers=blockers,
        suggested_action=(
            "Review validated agent output and impact preview before any state application."
            if handoff_is_ready
            else "Resolve validation or workflow pre-check blockers before engineer review."
        ),
        network_request_sent=sandbox.network_request_sent,
        project_state_changed=sandbox.project_state_changed,
    )


def build_agent_response_engineer_handoff_rows(
    handoff: AgentResponseEngineerHandoff,
    language: AgentPromptLanguage,
) -> list[dict[str, object]]:
    target_phase = handoff.target_phase or "-"
    blockers = _format_apply_blockers(handoff.blockers, language)
    if language == "zh":
        return [
            {"项目": "复核包", "内容": handoff.review_packet_id},
            {"项目": "Agent", "内容": _agent_label(handoff.agent_role, "zh")},
            {
                "项目": "移交状态",
                "内容": (
                    "可进入工程师复核"
                    if handoff.handoff_status == "ready_for_engineer_review"
                    else "阻塞"
                ),
            },
            {"项目": "目标阶段", "内容": target_phase},
            {"项目": "校验通过", "内容": "是" if handoff.validation_ok else "否"},
            {
                "项目": "应用前置检查",
                "内容": "通过" if handoff.apply_prechecks_ok else "阻塞",
            },
            {"项目": "阻断项", "内容": blockers},
            {"项目": "建议动作", "内容": _localized_handoff_action(handoff, "zh")},
            {"项目": "网络调用", "内容": "是" if handoff.network_request_sent else "否"},
            {
                "项目": "项目状态",
                "内容": "已修改" if handoff.project_state_changed else "未修改",
            },
        ]
    return [
        {"Item": "Review Packet", "Value": handoff.review_packet_id},
        {"Item": "Agent", "Value": _agent_label(handoff.agent_role, "en")},
        {
            "Item": "Handoff Status",
            "Value": (
                "Ready For Engineer Review"
                if handoff.handoff_status == "ready_for_engineer_review"
                else "Blocked"
            ),
        },
        {"Item": "Target Phase", "Value": target_phase},
        {"Item": "Validation", "Value": "Pass" if handoff.validation_ok else "Fail"},
        {
            "Item": "Apply Pre-checks",
            "Value": "Pass" if handoff.apply_prechecks_ok else "Blocked",
        },
        {"Item": "Blockers", "Value": blockers},
        {"Item": "Suggested Action", "Value": handoff.suggested_action},
        {
            "Item": "Network Request",
            "Value": "Yes" if handoff.network_request_sent else "No",
        },
        {
            "Item": "Project State",
            "Value": "Changed" if handoff.project_state_changed else "Unchanged",
        },
    ]


def build_agent_response_application_plan(
    handoff: AgentResponseEngineerHandoff,
) -> AgentResponseApplicationPlan:
    blockers = _agent_response_application_plan_blockers(handoff)
    plan_is_ready = not blockers
    return AgentResponseApplicationPlan(
        plan_id=f"application-plan-{handoff.review_packet_id}",
        agent_role=handoff.agent_role,
        plan_status=(
            "ready_for_controlled_application" if plan_is_ready else "blocked"
        ),
        target_phase=handoff.target_phase if plan_is_ready else None,
        would_create_agent_event=plan_is_ready,
        would_set_phase_status="waiting_for_engineer" if plan_is_ready else None,
        blockers=blockers,
        project_state_changed=False,
    )


def build_agent_response_application_plan_rows(
    plan: AgentResponseApplicationPlan,
    language: AgentPromptLanguage,
) -> list[dict[str, object]]:
    target_phase = plan.target_phase or "-"
    blockers = _format_apply_blockers(plan.blockers, language)
    if language == "zh":
        return [
            {"项目": "应用计划", "内容": plan.plan_id},
            {"项目": "Agent", "内容": _agent_label(plan.agent_role, "zh")},
            {
                "项目": "计划状态",
                "内容": (
                    "可进入受控应用"
                    if plan.plan_status == "ready_for_controlled_application"
                    else "阻塞"
                ),
            },
            {"项目": "目标阶段", "内容": target_phase},
            {
                "项目": "需要工程师授权",
                "内容": "是" if plan.requires_engineer_authorization else "否",
            },
            {
                "项目": "会创建 Agent 事件",
                "内容": "是" if plan.would_create_agent_event else "否",
            },
            {
                "项目": "阶段状态",
                "内容": plan.would_set_phase_status or "-",
            },
            {"项目": "阻断项", "内容": blockers},
            {
                "项目": "项目状态",
                "内容": "已修改" if plan.project_state_changed else "未修改",
            },
            {
                "项目": "边界",
                "内容": "仅应用计划；工程师授权前不应用 Agent 输出。",
            },
        ]
    return [
        {"Item": "Application Plan", "Value": plan.plan_id},
        {"Item": "Agent", "Value": _agent_label(plan.agent_role, "en")},
        {
            "Item": "Plan Status",
            "Value": (
                "Ready For Controlled Application"
                if plan.plan_status == "ready_for_controlled_application"
                else "Blocked"
            ),
        },
        {"Item": "Target Phase", "Value": target_phase},
        {
            "Item": "Requires Engineer Authorization",
            "Value": "Yes" if plan.requires_engineer_authorization else "No",
        },
        {
            "Item": "Would Create Agent Event",
            "Value": "Yes" if plan.would_create_agent_event else "No",
        },
        {"Item": "Phase Status", "Value": plan.would_set_phase_status or "-"},
        {"Item": "Blockers", "Value": blockers},
        {
            "Item": "Project State",
            "Value": "Changed" if plan.project_state_changed else "Unchanged",
        },
        {"Item": "Boundary", "Value": plan.boundary_statement},
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

    if state is not None and parsed.project_id != state.project_id:
        raise ValueError("Agent response project_id must match project state project_id.")

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


def preview_agent_response_impact(
    agent_role: AgentRole,
    response_text: str,
    *,
    state: ProjectReviewState,
) -> AgentResponseImpactPreview:
    parsed = parse_agent_json_response(agent_role, response_text, state=state)
    summary_counts = _summary_counts_for_parsed_output(parsed)
    target_phase = _target_phase_for_parsed_output(parsed)
    apply_blockers = _apply_precheck_blockers(state, parsed, target_phase)
    return AgentResponseImpactPreview(
        agent_role=agent_role,
        output_model_name=type(parsed).__name__,
        target_phase=target_phase,
        requires_engineer_review=parsed.requires_engineer_review,
        summary_counts=summary_counts,
        would_update=[
            artifact_name
            for artifact_name, count in summary_counts.items()
            if count > 0
        ],
        passes_apply_prechecks=not apply_blockers,
        apply_blockers=apply_blockers,
    )


def build_agent_response_impact_rows(
    preview: AgentResponseImpactPreview,
    language: AgentPromptLanguage,
) -> list[dict[str, object]]:
    summary = _format_summary_counts(preview.summary_counts)
    would_update = ", ".join(preview.would_update) if preview.would_update else "-"
    if language == "zh":
        return [
            {"项目": "目标阶段", "值": preview.target_phase},
            {"项目": "输出模型", "值": preview.output_model_name},
            {"项目": "统计", "值": summary},
            {"项目": "会更新", "值": would_update},
            {
                "项目": "应用前置检查",
                "值": "通过" if preview.passes_apply_prechecks else "阻塞",
            },
            {
                "项目": "应用阻断项",
                "值": _format_apply_blockers(preview.apply_blockers, "zh"),
            },
            {
                "项目": "需要工程师复核",
                "值": "是" if preview.requires_engineer_review else "否",
            },
            {"项目": "边界", "值": "仅预览；应用 Agent 输出前仍需工程师批准。"},
        ]
    return [
        {"Item": "Target Phase", "Value": preview.target_phase},
        {"Item": "Output Model", "Value": preview.output_model_name},
        {"Item": "Summary Counts", "Value": summary},
        {"Item": "Would Update", "Value": would_update},
        {
            "Item": "Apply Pre-checks",
            "Value": "Pass" if preview.passes_apply_prechecks else "Blocked",
        },
        {
            "Item": "Apply Blockers",
            "Value": _format_apply_blockers(preview.apply_blockers, "en"),
        },
        {
            "Item": "Requires Engineer Review",
            "Value": "Yes" if preview.requires_engineer_review else "No",
        },
        {"Item": "Boundary", "Value": preview.boundary_statement},
    ]


def build_sample_agent_response_json(
    agent_role: AgentRole,
    state: ProjectReviewState,
) -> str:
    return json.dumps(
        _sample_payload_for_role(agent_role, state),
        ensure_ascii=False,
        indent=2,
    )


def _target_phase_for_parsed_output(output: AgentParsedOutput) -> ReviewPhase:
    if isinstance(output, DocumentIntakeAgentOutput):
        return "document_check"
    if isinstance(output, BasisCodeAgentOutput):
        return "basis_build"
    if isinstance(output, ReviewPlanAgentOutput):
        return "review_plan"
    if isinstance(output, StructuralReviewAgentOutput):
        return "engineer_data_lock"
    if isinstance(output, CalculationCheckAgentOutput):
        return "calculation_check"
    if isinstance(output, RiskNCRAgentOutput):
        return "risk_register"
    if isinstance(output, ReportComposerAgentOutput):
        return "report_draft"
    raise TypeError(f"Unsupported agent output type: {type(output).__name__}")


def _summary_counts_for_parsed_output(output: AgentParsedOutput) -> dict[str, int]:
    if isinstance(output, DocumentIntakeAgentOutput):
        return {
            "document_versions": len(output.document_versions),
            "extracted_fields": len(output.extracted_fields),
            "missing_document_keys": len(output.missing_document_keys),
        }
    if isinstance(output, BasisCodeAgentOutput):
        return {"basis_references": len(output.basis_references)}
    if isinstance(output, ReviewPlanAgentOutput):
        return {"review_plan": len(output.review_plan)}
    if isinstance(output, StructuralReviewAgentOutput):
        return {"review_paths": len(output.review_paths)}
    if isinstance(output, CalculationCheckAgentOutput):
        return {"calculation_run_ids": len(output.calculation_run_ids)}
    if isinstance(output, RiskNCRAgentOutput):
        return {
            "risks": len(output.risks),
            "source_calculation_run_ids": len(output.source_calculation_run_ids),
        }
    if isinstance(output, ReportComposerAgentOutput):
        return {
            "report_sections": len(output.report_sections),
            "rfi_items": len(output.rfi_items),
        }
    raise TypeError(f"Unsupported agent output type: {type(output).__name__}")


def _apply_precheck_blockers(
    state: ProjectReviewState,
    output: AgentParsedOutput,
    target_phase: ReviewPhase,
) -> list[str]:
    blockers: list[str] = []
    current_index = REVIEW_PHASES.index(state.current_phase)
    target_index = REVIEW_PHASES.index(target_phase)
    if target_index > current_index + 1:
        blockers.append(
            f"Cannot apply {output.agent_role} output while project is in "
            f"{state.current_phase!r}; target phase {target_phase!r} is not current or next."
        )
    if isinstance(output, CalculationCheckAgentOutput) and not state.is_gate_locked(
        "calculation"
    ):
        blockers.append(
            "Calculation gate must be locked before applying calculation check output."
        )
    if isinstance(output, RiskNCRAgentOutput):
        state_run_ids = {run.run_id for run in state.calculation_runs}
        missing_run_ids = [
            run_id
            for run_id in output.source_calculation_run_ids
            if run_id not in state_run_ids
        ]
        if missing_run_ids:
            blockers.append(
                "Risk/NCR agent output references calculation runs that do not exist: "
                + ", ".join(missing_run_ids)
            )
    if isinstance(output, ReportComposerAgentOutput):
        non_open_rfi_ids = [
            rfi_item.rfi_id for rfi_item in output.rfi_items if rfi_item.status != "open"
        ]
        if non_open_rfi_ids:
            blockers.append(
                "Report composer output can only draft open RFI items: "
                + ", ".join(non_open_rfi_ids)
            )
    return blockers


def _agent_response_handoff_blockers(
    sandbox: AgentResponseSandboxResult,
) -> list[str]:
    if not sandbox.validation_result.ok:
        return [sandbox.validation_result.error or "Agent response validation failed."]
    if sandbox.impact_preview is None:
        return ["Impact preview is unavailable for this agent response."]
    blockers: list[str] = []
    if not sandbox.impact_preview.requires_engineer_review:
        blockers.append("Agent response does not require engineer review.")
    blockers.extend(sandbox.impact_preview.apply_blockers)
    return blockers


def _agent_response_application_plan_blockers(
    handoff: AgentResponseEngineerHandoff,
) -> list[str]:
    blockers = list(handoff.blockers)
    if handoff.handoff_status != "ready_for_engineer_review":
        return blockers or ["Engineer handoff is not ready for controlled application."]
    if not handoff.validation_ok:
        blockers.append("Agent response validation has not passed.")
    if not handoff.apply_prechecks_ok:
        blockers.append("Agent response apply pre-checks have not passed.")
    if not handoff.requires_engineer_review:
        blockers.append("Agent response does not require engineer review.")
    if handoff.target_phase is None:
        blockers.append("Ready handoff requires a target phase.")
    return blockers


def _localized_handoff_action(
    handoff: AgentResponseEngineerHandoff,
    language: AgentPromptLanguage,
) -> str:
    if language == "en":
        return handoff.suggested_action
    if handoff.handoff_status == "ready_for_engineer_review":
        return "复核已校验的 Agent 产物和影响预览，再决定是否进入受控工作流。"
    return "先处理校验或工作流前置检查阻断项，再进入工程师复核。"


def _format_summary_counts(summary_counts: dict[str, int]) -> str:
    if not summary_counts:
        return "-"
    return ", ".join(
        f"{artifact_name}={count}"
        for artifact_name, count in summary_counts.items()
    )


def _format_apply_blockers(blockers: list[str], language: AgentPromptLanguage) -> str:
    if not blockers:
        return "-" if language == "en" else "无"
    return " | ".join(blockers)


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
