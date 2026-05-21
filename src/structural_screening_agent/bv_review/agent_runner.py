from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.agent_contracts import (
    BasisCodeAgentOutput,
    CalculationCheckAgentOutput,
    DocumentIntakeAgentOutput,
    ReportComposerAgentOutput,
    ReviewPlanAgentOutput,
    RiskNCRAgentOutput,
    StructuralReviewAgentOutput,
)
from structural_screening_agent.bv_review.agent_workflow import apply_agent_output_to_state
from structural_screening_agent.bv_review.basis import build_review_basis
from structural_screening_agent.bv_review.checklist import build_document_checklist
from structural_screening_agent.bv_review.human_gate import record_agent_review_decision
from structural_screening_agent.bv_review.project_state import (
    DocumentVersion,
    ProjectReviewState,
)
from structural_screening_agent.bv_review.report import (
    build_bv_open_rfi_items,
    build_bv_report_preview,
)
from structural_screening_agent.bv_review.review_path import build_structural_review_path
from structural_screening_agent.bv_review.review_plan import build_review_plan
from structural_screening_agent.bv_review.risk_register import build_risk_register
from structural_screening_agent.bv_review.state_repository import (
    JsonProjectReviewStateRepository,
)


class PersistedWorkflowRunSummary(BaseModel):
    project_id: str
    start_phase: str
    final_phase: str
    applied_agent_event_ids: list[str] = Field(default_factory=list)
    applied_agent_roles: list[str] = Field(default_factory=list)
    artifact_counts: dict[str, int] = Field(default_factory=dict)
    saved: bool = False


class PersistedWorkflowRunResult(BaseModel):
    state: ProjectReviewState
    summary: PersistedWorkflowRunSummary


def resume_local_agent_workflow_after_review_decisions(
    state: ProjectReviewState,
    decision_records: Mapping[str, object],
    *,
    reviewer: str,
) -> ProjectReviewState:
    review_event = _next_pending_review_event_with_decision(
        state,
        decision_records,
    )
    if review_event is None:
        return state

    decision_record = decision_records[review_event.event_id]
    if not isinstance(decision_record, Mapping):
        return state
    decision = str(decision_record.get("decision", ""))
    if decision not in {"approved", "rejected"}:
        return state

    reviewed_state = record_agent_review_decision(
        state,
        event_id=review_event.event_id,
        decision=decision,
        reviewer=reviewer,
        comment=str(decision_record.get("comment") or ""),
    )
    if decision != "approved":
        return reviewed_state
    return run_local_agent_workflow_until_blocked(reviewed_state)


def run_local_agent_workflow_step(state: ProjectReviewState) -> ProjectReviewState | None:
    if (
        state.current_phase != "intake"
        and state.phase_statuses.get(state.current_phase) != "approved"
    ):
        return None
    output = _build_local_agent_output_for_current_phase(state)
    if output is None:
        return None
    return apply_agent_output_to_state(state, output)


def run_local_agent_workflow_until_blocked(
    state: ProjectReviewState,
    *,
    max_steps: int = 8,
) -> ProjectReviewState:
    current = state
    for _ in range(max_steps):
        next_state = run_local_agent_workflow_step(current)
        if next_state is None or next_state == current:
            return current
        current = next_state
    return current


def _next_pending_review_event_with_decision(
    state: ProjectReviewState,
    decision_records: Mapping[str, object],
):
    for event in state.agent_events:
        if (
            event.requires_engineer_review
            and state.phase_statuses.get(event.target_phase) == "waiting_for_engineer"
            and event.event_id in decision_records
        ):
            return event
    return None


def run_persisted_local_agent_workflow_until_blocked(
    repository: JsonProjectReviewStateRepository,
    project_id: str,
    *,
    max_steps: int = 8,
) -> ProjectReviewState:
    return run_persisted_local_agent_workflow_with_summary(
        repository,
        project_id,
        max_steps=max_steps,
    ).state


def run_persisted_local_agent_workflow_with_summary(
    repository: JsonProjectReviewStateRepository,
    project_id: str,
    *,
    max_steps: int = 8,
) -> PersistedWorkflowRunResult:
    state = repository.load(project_id)
    start_event_count = len(state.agent_events)
    final_state = run_local_agent_workflow_until_blocked(state, max_steps=max_steps)
    path = repository.save(final_state)
    new_events = final_state.agent_events[start_event_count:]
    return PersistedWorkflowRunResult(
        state=final_state,
        summary=PersistedWorkflowRunSummary(
            project_id=project_id,
            start_phase=state.current_phase,
            final_phase=final_state.current_phase,
            applied_agent_event_ids=[event.event_id for event in new_events],
            applied_agent_roles=[event.agent_role for event in new_events],
            artifact_counts=_artifact_counts(final_state),
            saved=path.exists(),
        ),
    )


def _artifact_counts(state: ProjectReviewState) -> dict[str, int]:
    return {
        "document_versions": len(state.document_versions),
        "extracted_fields": len(state.extracted_fields),
        "basis_references": len(state.basis_references),
        "review_plan": len(state.review_plan),
        "review_paths": len(state.review_paths),
        "calculation_runs": len(state.calculation_runs),
        "risks": len(state.risks),
        "rfi_items": len(state.rfi_items),
        "report_sections": len(state.report_sections),
        "agent_events": len(state.agent_events),
    }


def _build_local_agent_output_for_current_phase(
    state: ProjectReviewState,
) -> (
    DocumentIntakeAgentOutput
    | BasisCodeAgentOutput
    | ReviewPlanAgentOutput
    | StructuralReviewAgentOutput
    | CalculationCheckAgentOutput
    | RiskNCRAgentOutput
    | ReportComposerAgentOutput
    | None
):
    if state.current_phase == "intake":
        return DocumentIntakeAgentOutput(
            project_id=state.project_id,
            document_versions=_document_versions_from_intake(state),
            extracted_fields=list(state.extracted_fields),
            missing_document_keys=[
                key for key, status in state.intake.documents.items() if status == "missing"
            ],
            notes=["Local deterministic intake output; replace with parsed evidence when available."],
        )

    if state.current_phase == "document_check":
        return BasisCodeAgentOutput(
            project_id=state.project_id,
            basis_references=build_review_basis(state.intake),
        )

    if state.current_phase == "basis_build":
        checklist = build_document_checklist(state.intake)
        review_paths = build_structural_review_path(state.intake, checklist)
        return ReviewPlanAgentOutput(
            project_id=state.project_id,
            review_plan=build_review_plan(state.intake, checklist, review_paths),
        )

    if state.current_phase == "review_plan":
        checklist = build_document_checklist(state.intake)
        return StructuralReviewAgentOutput(
            project_id=state.project_id,
            review_paths=build_structural_review_path(state.intake, checklist),
        )

    if state.current_phase == "engineer_data_lock":
        if not state.is_gate_locked("calculation") or not state.calculation_runs:
            return None
        run_ids = [
            run.run_id
            for run in state.calculation_runs
            if run.input_locked and run.status in {"ready", "completed"}
        ]
        if not run_ids:
            return None
        return CalculationCheckAgentOutput(
            project_id=state.project_id,
            calculation_run_ids=run_ids,
        )

    if state.current_phase == "calculation_check":
        checklist = build_document_checklist(state.intake)
        review_paths = state.review_paths or build_structural_review_path(
            state.intake, checklist
        )
        return RiskNCRAgentOutput(
            project_id=state.project_id,
            risks=build_risk_register(
                state.intake,
                checklist,
                review_paths,
                calculation_runs=state.calculation_runs,
            ),
            source_calculation_run_ids=[run.run_id for run in state.calculation_runs],
        )

    if state.current_phase == "risk_register":
        preview = build_bv_report_preview(state.intake, _result_like_state(state))
        return ReportComposerAgentOutput(
            project_id=state.project_id,
            report_sections=preview.sections,
            rfi_items=build_bv_open_rfi_items(state.risks),
            boundary_statement="This draft is for screening-level review-support only.",
        )

    return None


def _document_versions_from_intake(state: ProjectReviewState) -> list[DocumentVersion]:
    return [
        DocumentVersion(
            document_id=document_key,
            document_type=document_key,
            revision="intake",
            source_name=document_key,
            status=status,
        )
        for document_key, status in state.intake.documents.items()
    ]


def _result_like_state(state: ProjectReviewState):
    from structural_screening_agent.bv_review.models import BVReviewResult

    return BVReviewResult(
        decision="review_with_holds",
        basis_references=state.basis_references,
        checklist_items=build_document_checklist(state.intake),
        review_paths=state.review_paths,
        risks=state.risks,
        review_plan=state.review_plan,
    )
