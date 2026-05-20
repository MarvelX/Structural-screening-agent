from __future__ import annotations

from typing import TypeAlias

from structural_screening_agent.bv_review.agent_contracts import (
    BasisCodeAgentOutput,
    CalculationCheckAgentOutput,
    DocumentIntakeAgentOutput,
    ReportComposerAgentOutput,
    ReviewPlanAgentOutput,
    RiskNCRAgentOutput,
    StructuralReviewAgentOutput,
    resolve_calculation_check_output_against_state,
)
from structural_screening_agent.bv_review.project_state import (
    REVIEW_PHASES,
    ProjectReviewState,
    ReviewPhase,
    ReviewPhaseStatus,
)


AgentWorkflowOutput: TypeAlias = (
    DocumentIntakeAgentOutput
    | BasisCodeAgentOutput
    | ReviewPlanAgentOutput
    | StructuralReviewAgentOutput
    | CalculationCheckAgentOutput
    | RiskNCRAgentOutput
    | ReportComposerAgentOutput
)


def apply_agent_output_to_state(
    state: ProjectReviewState,
    output: AgentWorkflowOutput,
) -> ProjectReviewState:
    if output.project_id != state.project_id:
        raise ValueError("Agent output project_id must match project state project_id.")

    if isinstance(output, DocumentIntakeAgentOutput):
        return _copy_with_phase(
            state,
            output.agent_role,
            "document_check",
            document_versions=_upsert_by_id(
                state.document_versions,
                output.document_versions,
                "document_id",
            ),
            extracted_fields=_upsert_by_id(
                state.extracted_fields,
                output.extracted_fields,
                "field_id",
            ),
        )

    if isinstance(output, BasisCodeAgentOutput):
        return _copy_with_phase(
            state,
            output.agent_role,
            "basis_build",
            basis_references=_upsert_by_id(
                state.basis_references,
                output.basis_references,
                "basis_id",
            ),
        )

    if isinstance(output, ReviewPlanAgentOutput):
        return _copy_with_phase(
            state,
            output.agent_role,
            "review_plan",
            review_plan=_upsert_by_id(state.review_plan, output.review_plan, "item_id"),
        )

    if isinstance(output, StructuralReviewAgentOutput):
        return _copy_with_phase(
            state,
            output.agent_role,
            "engineer_data_lock",
            review_paths=_upsert_by_id(
                state.review_paths,
                output.review_paths,
                "path_id",
            ),
        )

    if isinstance(output, CalculationCheckAgentOutput):
        if not state.is_gate_locked("calculation"):
            raise ValueError("Calculation gate must be locked before applying calculation check output.")
        resolve_calculation_check_output_against_state(output, state)
        return _copy_with_phase(state, output.agent_role, "calculation_check")

    if isinstance(output, RiskNCRAgentOutput):
        _validate_source_run_ids(output.source_calculation_run_ids, state)
        return _copy_with_phase(
            state,
            output.agent_role,
            "risk_register",
            risks=_upsert_by_id(state.risks, output.risks, "risk_id"),
        )

    if isinstance(output, ReportComposerAgentOutput):
        _validate_report_draft_rfi_statuses(output)
        return _copy_with_phase(
            state,
            output.agent_role,
            "report_draft",
            report_sections=output.report_sections,
            rfi_items=_upsert_by_id(state.rfi_items, output.rfi_items, "rfi_id"),
        )

    raise TypeError(f"Unsupported agent output type: {type(output).__name__}")


def _copy_with_phase(
    state: ProjectReviewState,
    agent_role: str,
    phase: ReviewPhase,
    **updates: object,
) -> ProjectReviewState:
    _ensure_phase_can_accept_output(state, agent_role, phase)
    statuses: dict[ReviewPhase, ReviewPhaseStatus] = dict(state.phase_statuses)
    statuses[phase] = "waiting_for_engineer"
    current_index = REVIEW_PHASES.index(state.current_phase)
    target_index = REVIEW_PHASES.index(phase)
    current_phase = phase if target_index > current_index else state.current_phase
    return state.model_copy(
        update={**updates, "current_phase": current_phase, "phase_statuses": statuses}
    )


def _ensure_phase_can_accept_output(
    state: ProjectReviewState,
    agent_role: str,
    phase: ReviewPhase,
) -> None:
    current_index = REVIEW_PHASES.index(state.current_phase)
    target_index = REVIEW_PHASES.index(phase)
    if target_index > current_index + 1:
        raise ValueError(
            f"Cannot apply {agent_role} output while project is in "
            f"{state.current_phase!r}; target phase {phase!r} is not current or next."
        )


def _upsert_by_id(items: list[object], updates: list[object], id_attribute: str) -> list[object]:
    by_id = {getattr(item, id_attribute): item for item in items}
    for item in updates:
        by_id[getattr(item, id_attribute)] = item
    return list(by_id.values())


def _validate_source_run_ids(
    run_ids: list[str],
    state: ProjectReviewState,
) -> None:
    state_run_ids = {run.run_id for run in state.calculation_runs}
    missing_run_ids = [run_id for run_id in run_ids if run_id not in state_run_ids]
    if missing_run_ids:
        raise ValueError(
            "Risk/NCR agent output references calculation runs that do not exist: "
            + ", ".join(missing_run_ids)
        )


def _validate_report_draft_rfi_statuses(output: ReportComposerAgentOutput) -> None:
    non_open_rfi_ids = [
        rfi_item.rfi_id for rfi_item in output.rfi_items if rfi_item.status != "open"
    ]
    if non_open_rfi_ids:
        raise ValueError(
            "Report composer output can only draft open RFI items: "
            + ", ".join(non_open_rfi_ids)
        )
