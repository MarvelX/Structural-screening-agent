from __future__ import annotations

from collections.abc import MutableMapping
from typing import Literal

from structural_screening_agent.bv_review.agent_runner import (
    PersistedWorkflowRunResult,
    PersistedWorkflowRunSummary,
)
from structural_screening_agent.bv_review.agent_application import (
    apply_authorized_agent_response_to_state,
)
from structural_screening_agent.bv_review.agent_prompting import (
    AgentResponseApplicationAuthorization,
    AgentResponseApplicationPlan,
    AgentResponseSandboxResult,
)
from structural_screening_agent.bv_review.calculation_workflow import (
    run_incremental_calculation_recheck_for_rfi,
)
from structural_screening_agent.bv_review.human_gate import (
    ReportDraftGateResult,
    close_rfi_after_engineer_review,
    issue_blocked_calculation_draft_rfi,
    record_agent_review_decision,
    record_report_revision,
    record_rfi_client_response,
)
from structural_screening_agent.bv_review.models import BVReportPreview
from structural_screening_agent.bv_review.project_state import ProjectReviewState
from structural_screening_agent.bv_review.state_repository import (
    JsonProjectReviewStateRepository,
)


_PROJECT_ID_KEY = "bv_persisted_workflow_summary_project_id"
_SUMMARY_KEY = "bv_persisted_workflow_summary"
_STATE_KEY = "bv_persisted_workflow_state"


def store_persisted_workflow_result(
    session_state: MutableMapping[str, object],
    result: PersistedWorkflowRunResult,
) -> None:
    session_state[_PROJECT_ID_KEY] = result.summary.project_id
    session_state[_SUMMARY_KEY] = result.summary
    session_state[_STATE_KEY] = result.state


def store_persisted_workflow_state(
    session_state: MutableMapping[str, object],
    state: ProjectReviewState,
) -> None:
    session_state[_PROJECT_ID_KEY] = state.project_id
    session_state[_STATE_KEY] = state
    existing_summary = session_state.get(_SUMMARY_KEY)
    if (
        isinstance(existing_summary, PersistedWorkflowRunSummary)
        and existing_summary.project_id == state.project_id
    ):
        session_state[_SUMMARY_KEY] = existing_summary.model_copy(
            update={
                "final_phase": state.current_phase,
                "artifact_counts": _artifact_counts_for_state(state),
            }
        )


def clear_persisted_workflow_session(session_state: MutableMapping[str, object]) -> None:
    session_state.pop(_PROJECT_ID_KEY, None)
    session_state.pop(_SUMMARY_KEY, None)
    session_state.pop(_STATE_KEY, None)


def get_active_persisted_project_id(
    session_state: MutableMapping[str, object],
) -> str | None:
    project_id = session_state.get(_PROJECT_ID_KEY)
    if isinstance(project_id, str) and project_id:
        return project_id
    return None


def _artifact_counts_for_state(state: ProjectReviewState) -> dict[str, int]:
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
        "report_revisions": len(state.report_revisions),
        "agent_events": len(state.agent_events),
        "approvals": len(state.approvals),
    }


def get_active_persisted_workflow_state(
    session_state: MutableMapping[str, object],
    project_id: str,
) -> ProjectReviewState | None:
    if session_state.get(_PROJECT_ID_KEY) != project_id:
        return None
    state = session_state.get(_STATE_KEY)
    if isinstance(state, ProjectReviewState):
        return state
    return None


def get_active_persisted_workflow_summary(
    session_state: MutableMapping[str, object],
    project_id: str,
) -> PersistedWorkflowRunSummary | None:
    if session_state.get(_PROJECT_ID_KEY) != project_id:
        return None
    summary = session_state.get(_SUMMARY_KEY)
    if isinstance(summary, PersistedWorkflowRunSummary):
        return summary
    return None


def record_persisted_agent_review_decision(
    session_state: MutableMapping[str, object],
    repository: JsonProjectReviewStateRepository,
    *,
    project_id: str,
    event_id: str,
    decision: Literal["approved", "rejected"],
    reviewer: str,
    comment: str = "",
) -> ProjectReviewState:
    state = get_active_persisted_workflow_state(session_state, project_id)
    if state is None:
        raise ValueError("No active persisted workflow state is loaded for this project.")

    updated_state = record_agent_review_decision(
        state,
        event_id=event_id,
        decision=decision,
        reviewer=reviewer,
        comment=comment,
    )
    repository.save(updated_state)
    store_persisted_workflow_state(session_state, updated_state)
    return updated_state


def apply_persisted_authorized_agent_response(
    session_state: MutableMapping[str, object],
    repository: JsonProjectReviewStateRepository,
    *,
    project_id: str,
    sandbox: AgentResponseSandboxResult,
    plan: AgentResponseApplicationPlan,
    authorization: AgentResponseApplicationAuthorization,
) -> ProjectReviewState:
    state = get_active_persisted_workflow_state(session_state, project_id)
    if state is None:
        raise ValueError("No active persisted workflow state is loaded for this project.")

    updated_state = apply_authorized_agent_response_to_state(
        state,
        sandbox,
        plan,
        authorization,
    )
    repository.save(updated_state)
    store_persisted_workflow_state(session_state, updated_state)
    return updated_state


def record_persisted_report_revision(
    session_state: MutableMapping[str, object],
    repository: JsonProjectReviewStateRepository,
    *,
    project_id: str,
    revision_id: str,
    report_preview: BVReportPreview,
    gate_result: ReportDraftGateResult,
    reviewer: str,
    note: str = "",
    created_at: str | None = None,
) -> ProjectReviewState:
    state = get_active_persisted_workflow_state(session_state, project_id)
    if state is None:
        raise ValueError("No active persisted workflow state is loaded for this project.")

    updated_state = record_report_revision(
        state,
        revision_id=revision_id,
        report_preview=report_preview,
        gate_result=gate_result,
        reviewer=reviewer,
        note=note,
        created_at=created_at,
    )
    repository.save(updated_state)
    store_persisted_workflow_state(session_state, updated_state)
    return updated_state


def record_persisted_rfi_client_response(
    session_state: MutableMapping[str, object],
    repository: JsonProjectReviewStateRepository,
    *,
    project_id: str,
    rfi_id: str,
    client_response: str,
) -> ProjectReviewState:
    state = get_active_persisted_workflow_state(session_state, project_id)
    if state is None:
        raise ValueError("No active persisted workflow state is loaded for this project.")

    updated_state = record_rfi_client_response(
        state,
        rfi_id=rfi_id,
        client_response=client_response,
    )
    repository.save(updated_state)
    store_persisted_workflow_state(session_state, updated_state)
    return updated_state


def close_persisted_rfi_after_engineer_review(
    session_state: MutableMapping[str, object],
    repository: JsonProjectReviewStateRepository,
    *,
    project_id: str,
    rfi_id: str,
    closeout_note: str,
    completed_recheck_item_ids: list[str] | None = None,
) -> ProjectReviewState:
    state = get_active_persisted_workflow_state(session_state, project_id)
    if state is None:
        raise ValueError("No active persisted workflow state is loaded for this project.")

    updated_state = close_rfi_after_engineer_review(
        state,
        rfi_id=rfi_id,
        closeout_note=closeout_note,
        completed_recheck_item_ids=completed_recheck_item_ids,
    )
    repository.save(updated_state)
    store_persisted_workflow_state(session_state, updated_state)
    return updated_state


def run_persisted_rfi_incremental_calculation_recheck(
    session_state: MutableMapping[str, object],
    repository: JsonProjectReviewStateRepository,
    *,
    project_id: str,
    rfi_id: str,
) -> ProjectReviewState:
    state = get_active_persisted_workflow_state(session_state, project_id)
    if state is None:
        raise ValueError("No active persisted workflow state is loaded for this project.")

    updated_state = run_incremental_calculation_recheck_for_rfi(
        state,
        rfi_id=rfi_id,
    )
    repository.save(updated_state)
    store_persisted_workflow_state(session_state, updated_state)
    return updated_state


def issue_persisted_blocked_calculation_draft_rfi(
    session_state: MutableMapping[str, object],
    repository: JsonProjectReviewStateRepository,
    *,
    project_id: str,
    rfi_id: str,
    reviewer: str,
    comment: str = "",
    approved_at: str | None = None,
) -> ProjectReviewState:
    state = get_active_persisted_workflow_state(session_state, project_id)
    if state is None:
        raise ValueError("No active persisted workflow state is loaded for this project.")

    updated_state = issue_blocked_calculation_draft_rfi(
        state,
        rfi_id=rfi_id,
        reviewer=reviewer,
        comment=comment,
        approved_at=approved_at,
    )
    repository.save(updated_state)
    store_persisted_workflow_state(session_state, updated_state)
    return updated_state
