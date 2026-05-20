import pytest

from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.project_state import EngineerApproval, ProjectReviewState
from structural_screening_agent.bv_review.state_machine import advance_project_phase


def _sample_state(current_phase: str = "intake") -> ProjectReviewState:
    intake = BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents={"structural_drawings": "available"},
    )
    return ProjectReviewState(project_id="pv-state-001", intake=intake, current_phase=current_phase)


def test_state_transition_starts_next_phase_and_approves_previous_phase() -> None:
    state = _sample_state()

    advanced = advance_project_phase(state, "document_check")

    assert advanced.current_phase == "document_check"
    assert advanced.phase_statuses["intake"] == "approved"
    assert advanced.phase_statuses["document_check"] == "running"


def test_state_transition_rejects_skipping_required_phase() -> None:
    with pytest.raises(ValueError):
        advance_project_phase(_sample_state(), "calculation_check")


def test_state_transition_blocks_calculation_until_engineer_data_lock_is_locked() -> None:
    blocked = advance_project_phase(_sample_state("engineer_data_lock"), "calculation_check")

    assert blocked.current_phase == "engineer_data_lock"
    assert blocked.phase_statuses["engineer_data_lock"] == "waiting_for_engineer"
    assert blocked.phase_statuses["calculation_check"] == "blocked"


def test_state_transition_enters_calculation_after_engineer_data_lock() -> None:
    state = _sample_state("engineer_data_lock").model_copy(
        update={
            "approvals": [
                EngineerApproval(
                    approval_id="approval-001",
                    target_type="gate",
                    target_id="calculation",
                    status="approved",
                    locked=True,
                )
            ]
        }
    )

    advanced = advance_project_phase(state, "calculation_check")

    assert advanced.current_phase == "calculation_check"
    assert advanced.phase_statuses["engineer_data_lock"] == "approved"
    assert advanced.phase_statuses["calculation_check"] == "running"
