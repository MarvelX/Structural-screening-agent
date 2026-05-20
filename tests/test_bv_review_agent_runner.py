from structural_screening_agent.bv_review import (
    BVReviewIntake,
    ProjectReviewState,
    run_persisted_local_agent_workflow_until_blocked,
    run_local_agent_workflow_step,
    run_local_agent_workflow_until_blocked,
)
from structural_screening_agent.bv_review.project_state import CalculationRun, EngineerApproval
from structural_screening_agent.bv_review.state_repository import JsonProjectReviewStateRepository


def test_local_agent_workflow_runs_to_engineer_data_lock_without_external_api() -> None:
    state = ProjectReviewState(project_id="pv-001", intake=_sample_intake())

    final_state = run_local_agent_workflow_until_blocked(state)

    assert final_state.current_phase == "engineer_data_lock"
    assert final_state.phase_statuses["document_check"] == "waiting_for_engineer"
    assert final_state.phase_statuses["basis_build"] == "waiting_for_engineer"
    assert final_state.phase_statuses["review_plan"] == "waiting_for_engineer"
    assert final_state.basis_references
    assert final_state.review_plan
    assert final_state.review_paths
    assert final_state.calculation_runs == []
    assert [event.agent_role for event in final_state.agent_events] == [
        "document_intake",
        "basis_code",
        "review_plan",
        "structural_review",
    ]
    assert final_state.agent_events[-1].target_phase == "engineer_data_lock"


def test_local_agent_workflow_applies_calculation_risk_and_report_after_locked_gate() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        approvals=[
            EngineerApproval(
                approval_id="approval-calculation",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            )
        ],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=[
                    "uplift_force_kn",
                    "compression_force_kn",
                    "horizontal_force_kn",
                ],
                input_locked=True,
                status="completed",
                result_summary={
                    "screening_boundary": "screening-level review support only",
                    "screening_status": "review_required",
                    "controlling_utilization_ratio": 1.21,
                },
            )
        ],
    )

    final_state = run_local_agent_workflow_until_blocked(state)

    assert final_state.current_phase == "report_draft"
    assert final_state.phase_statuses["calculation_check"] == "waiting_for_engineer"
    assert final_state.phase_statuses["risk_register"] == "waiting_for_engineer"
    assert final_state.phase_statuses["report_draft"] == "waiting_for_engineer"
    assert final_state.risks
    assert any(
        item.risk_id == "calculation_review_required_foundation_run_001"
        and item.blocks_report_issue
        for item in final_state.risks
    )
    assert final_state.report_sections
    assert final_state.rfi_items
    assert all(item.status == "open" for item in final_state.rfi_items)
    assert any(
        item.rfi_id == "rfi-calculation_review_required_foundation_run_001"
        and item.triggers_incremental_recheck
        for item in final_state.rfi_items
    )
    assert [event.agent_role for event in final_state.agent_events] == [
        "calculation_check",
        "risk_ncr",
        "report_composer",
    ]


def test_local_agent_workflow_step_returns_none_when_waiting_for_human_data_lock() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
    )

    assert run_local_agent_workflow_step(state) is None


def test_persisted_local_agent_workflow_loads_runs_and_saves_until_blocked(tmp_path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    repository.save(ProjectReviewState(project_id="pv-001", intake=_sample_intake()))

    final_state = run_persisted_local_agent_workflow_until_blocked(repository, "pv-001")
    persisted_state = repository.load("pv-001")

    assert final_state.current_phase == "engineer_data_lock"
    assert persisted_state.current_phase == "engineer_data_lock"
    assert persisted_state.basis_references
    assert persisted_state.review_plan
    assert persisted_state.review_paths
    assert [event.agent_role for event in persisted_state.agent_events] == [
        "document_intake",
        "basis_code",
        "review_plan",
        "structural_review",
    ]


def test_persisted_local_agent_workflow_resumes_locked_calculation_gate_state(tmp_path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    repository.save(
        ProjectReviewState(
            project_id="pv-locked",
            intake=_sample_intake(),
            current_phase="engineer_data_lock",
            approvals=[
                EngineerApproval(
                    approval_id="approval-calculation",
                    target_type="gate",
                    target_id="calculation",
                    status="approved",
                    locked=True,
                )
            ],
            calculation_runs=[
                CalculationRun(
                    run_id="foundation-run-001",
                    engine_name="foundation",
                    engine_version="phase1-deterministic-screening",
                    input_field_ids=[
                        "uplift_force_kn",
                        "compression_force_kn",
                        "horizontal_force_kn",
                    ],
                    input_locked=True,
                    status="completed",
                    result_summary={
                        "screening_boundary": "screening-level review support only",
                        "screening_status": "review_required",
                        "controlling_utilization_ratio": 1.21,
                    },
                )
            ],
        )
    )

    final_state = run_persisted_local_agent_workflow_until_blocked(repository, "pv-locked")
    persisted_state = repository.load("pv-locked")

    assert final_state.current_phase == "report_draft"
    assert persisted_state.current_phase == "report_draft"
    assert persisted_state.risks
    assert persisted_state.report_sections
    assert persisted_state.rfi_items
    assert [event.agent_role for event in persisted_state.agent_events] == [
        "calculation_check",
        "risk_ncr",
        "report_composer",
    ]


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
