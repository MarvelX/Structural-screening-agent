from __future__ import annotations

from structural_screening_agent.bv_review.project_state import (
    REVIEW_PHASES,
    ProjectReviewState,
    ReviewPhase,
)


def _next_phase_after(current_phase: ReviewPhase) -> ReviewPhase | None:
    current_index = REVIEW_PHASES.index(current_phase)
    next_index = current_index + 1
    if next_index >= len(REVIEW_PHASES):
        return None
    return REVIEW_PHASES[next_index]


def advance_project_phase(state: ProjectReviewState, target_phase: ReviewPhase) -> ProjectReviewState:
    expected_phase = _next_phase_after(state.current_phase)
    if target_phase != expected_phase:
        raise ValueError(
            f"Cannot advance from {state.current_phase!r} to {target_phase!r}; "
            f"expected next phase is {expected_phase!r}."
        )

    statuses = dict(state.phase_statuses)

    if target_phase == "calculation_check" and not state.is_gate_locked("calculation"):
        statuses[state.current_phase] = "waiting_for_engineer"
        statuses[target_phase] = "blocked"
        return state.model_copy(update={"phase_statuses": statuses})

    statuses[state.current_phase] = "approved"
    statuses[target_phase] = "running"
    return state.model_copy(
        update={"current_phase": target_phase, "phase_statuses": statuses}
    )
