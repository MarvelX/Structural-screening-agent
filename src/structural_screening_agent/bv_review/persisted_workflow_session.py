from collections.abc import MutableMapping

from structural_screening_agent.bv_review.agent_runner import (
    PersistedWorkflowRunResult,
    PersistedWorkflowRunSummary,
)
from structural_screening_agent.bv_review.project_state import ProjectReviewState


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


def clear_persisted_workflow_session(session_state: MutableMapping[str, object]) -> None:
    session_state.pop(_PROJECT_ID_KEY, None)
    session_state.pop(_SUMMARY_KEY, None)
    session_state.pop(_STATE_KEY, None)


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
