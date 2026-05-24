from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

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
    AgentWorkflowEvent,
    REVIEW_PHASES,
    ProjectReviewState,
    ReviewPhase,
    ReviewPhaseStatus,
)


AgentWorkflowOutput = Union[
    DocumentIntakeAgentOutput,
    BasisCodeAgentOutput,
    ReviewPlanAgentOutput,
    StructuralReviewAgentOutput,
    CalculationCheckAgentOutput,
    RiskNCRAgentOutput,
    ReportComposerAgentOutput,
]


def apply_agent_output_to_state(
    state: ProjectReviewState,
    output: AgentWorkflowOutput,
) -> ProjectReviewState:
    if output.project_id != state.project_id:
        raise ValueError("Agent output project_id must match project state project_id.")

    if isinstance(output, DocumentIntakeAgentOutput):
        return _copy_with_phase(
            state,
            output,
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
            output,
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
            output,
            "review_plan",
            review_plan=_upsert_by_id(state.review_plan, output.review_plan, "item_id"),
        )

    if isinstance(output, StructuralReviewAgentOutput):
        return _copy_with_phase(
            state,
            output,
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
        return _copy_with_phase(state, output, "calculation_check")

    if isinstance(output, RiskNCRAgentOutput):
        _validate_source_run_ids(output.source_calculation_run_ids, state)
        return _copy_with_phase(
            state,
            output,
            "risk_register",
            risks=_upsert_by_id(state.risks, output.risks, "risk_id"),
        )

    if isinstance(output, ReportComposerAgentOutput):
        _validate_report_draft_rfi_statuses(output)
        return _copy_with_phase(
            state,
            output,
            "report_draft",
            report_sections=output.report_sections,
            rfi_items=_upsert_by_id(state.rfi_items, output.rfi_items, "rfi_id"),
        )

    raise TypeError(f"Unsupported agent output type: {type(output).__name__}")


def _copy_with_phase(
    state: ProjectReviewState,
    output: AgentWorkflowOutput,
    phase: ReviewPhase,
    **updates: object,
) -> ProjectReviewState:
    _ensure_phase_can_accept_output(state, output.agent_role, phase)
    statuses: dict[ReviewPhase, ReviewPhaseStatus] = dict(state.phase_statuses)
    statuses[phase] = "waiting_for_engineer"
    current_index = REVIEW_PHASES.index(state.current_phase)
    target_index = REVIEW_PHASES.index(phase)
    current_phase = phase if target_index > current_index else state.current_phase
    agent_events = [
        *state.agent_events,
        _build_agent_event(state, output, phase),
    ]
    return state.model_copy(
        update={
            **updates,
            "current_phase": current_phase,
            "phase_statuses": statuses,
            "agent_events": agent_events,
        }
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
    if (
        target_index > current_index
        and state.current_phase != "intake"
        and state.phase_statuses.get(state.current_phase) != "approved"
    ):
        raise ValueError(
            f"Cannot apply {agent_role} output before current phase "
            f"{state.current_phase!r} receives engineer approval; "
            "current phase requires engineer approval before advancing."
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


def _build_agent_event(
    state: ProjectReviewState,
    output: AgentWorkflowOutput,
    phase: ReviewPhase,
) -> AgentWorkflowEvent:
    return AgentWorkflowEvent(
        event_id=f"agent-event-{len(state.agent_events) + 1:03d}",
        agent_role=output.agent_role,
        target_phase=phase,
        status="applied",
        output_schema_version=output.schema_version,
        created_at=datetime.now(timezone.utc).isoformat(),
        requires_engineer_review=output.requires_engineer_review,
        summary_counts=_summary_counts_for_output(output),
    )


def _summary_counts_for_output(output: AgentWorkflowOutput) -> dict[str, int]:
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
