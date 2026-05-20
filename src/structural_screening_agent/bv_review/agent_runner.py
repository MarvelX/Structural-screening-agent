from __future__ import annotations

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


def run_local_agent_workflow_step(state: ProjectReviewState) -> ProjectReviewState | None:
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
