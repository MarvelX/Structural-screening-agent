from structural_screening_agent.bv_review import (
    BVReviewIntake,
    PersistedWorkflowRunResult,
    PersistedWorkflowRunSummary,
    ProjectReviewState,
)
from structural_screening_agent.bv_review.persisted_workflow_session import (
    clear_persisted_workflow_session,
    get_active_persisted_workflow_state,
    get_active_persisted_workflow_summary,
    store_persisted_workflow_result,
)


def test_persisted_workflow_session_keeps_resumed_state_for_matching_project() -> None:
    session_state: dict[str, object] = {}
    result = PersistedWorkflowRunResult(
        state=ProjectReviewState(
            project_id="pv-001",
            intake=_sample_intake(),
            current_phase="engineer_data_lock",
        ),
        summary=PersistedWorkflowRunSummary(
            project_id="pv-001",
            start_phase="intake",
            final_phase="engineer_data_lock",
            applied_agent_event_ids=["agent-event-001"],
            applied_agent_roles=["document_intake"],
            artifact_counts={"agent_events": 1},
            saved=True,
        ),
    )

    store_persisted_workflow_result(session_state, result)

    active_state = get_active_persisted_workflow_state(session_state, "pv-001")
    active_summary = get_active_persisted_workflow_summary(session_state, "pv-001")
    assert active_state is not None
    assert active_state.current_phase == "engineer_data_lock"
    assert active_summary is not None
    assert active_summary.final_phase == "engineer_data_lock"
    assert get_active_persisted_workflow_state(session_state, "pv-002") is None
    assert get_active_persisted_workflow_summary(session_state, "pv-002") is None


def test_clear_persisted_workflow_session_removes_resumed_state_and_summary() -> None:
    session_state: dict[str, object] = {}
    result = PersistedWorkflowRunResult(
        state=ProjectReviewState(project_id="pv-001", intake=_sample_intake()),
        summary=PersistedWorkflowRunSummary(
            project_id="pv-001",
            start_phase="intake",
            final_phase="intake",
            saved=True,
        ),
    )
    store_persisted_workflow_result(session_state, result)

    clear_persisted_workflow_session(session_state)

    assert get_active_persisted_workflow_state(session_state, "pv-001") is None
    assert get_active_persisted_workflow_summary(session_state, "pv-001") is None


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents={
            "structural_drawings": "available",
            "calculation_report": "partial",
            "geotechnical_report": "missing",
        },
    )
