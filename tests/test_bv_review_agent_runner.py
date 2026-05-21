from structural_screening_agent.bv_review import (
    BVReviewIntake,
    ProjectReviewState,
    run_persisted_local_agent_workflow_until_blocked,
    run_persisted_local_agent_workflow_with_summary,
    resume_local_agent_workflow_after_review_decisions,
    run_local_agent_workflow_step,
    run_local_agent_workflow_until_blocked,
)
from structural_screening_agent.bv_review.human_gate import record_agent_review_decision
from structural_screening_agent.bv_review.project_state import CalculationRun, EngineerApproval
from structural_screening_agent.bv_review.state_repository import JsonProjectReviewStateRepository


def test_local_agent_workflow_stops_at_first_engineer_review_gate() -> None:
    state = ProjectReviewState(project_id="pv-001", intake=_sample_intake())

    final_state = run_local_agent_workflow_until_blocked(state)

    assert final_state.current_phase == "document_check"
    assert final_state.phase_statuses["document_check"] == "waiting_for_engineer"
    assert final_state.phase_statuses["basis_build"] == "pending"
    assert final_state.phase_statuses["review_plan"] == "pending"
    assert final_state.basis_references == []
    assert final_state.review_plan == []
    assert final_state.review_paths == []
    assert final_state.calculation_runs == []
    assert [event.agent_role for event in final_state.agent_events] == ["document_intake"]
    assert final_state.agent_events[-1].target_phase == "document_check"


def test_local_agent_workflow_applies_calculation_risk_and_report_after_locked_gate() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "engineer_data_lock": "approved",
        },
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

    assert final_state.current_phase == "calculation_check"
    assert final_state.phase_statuses["calculation_check"] == "waiting_for_engineer"
    assert final_state.phase_statuses["risk_register"] == "pending"
    assert final_state.phase_statuses["report_draft"] == "pending"
    assert final_state.risks == []
    assert final_state.report_sections == []
    assert final_state.rfi_items == []
    assert [event.agent_role for event in final_state.agent_events] == ["calculation_check"]


def test_local_agent_workflow_resumes_after_each_engineer_review_gate() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "engineer_data_lock": "approved",
        },
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

    with_calculation_event = run_local_agent_workflow_until_blocked(state)
    with_calculation_approved = record_agent_review_decision(
        with_calculation_event,
        event_id="agent-event-001",
        decision="approved",
        reviewer="Engineer A",
    )
    with_risk_event = run_local_agent_workflow_until_blocked(with_calculation_approved)
    with_risk_approved = record_agent_review_decision(
        with_risk_event,
        event_id="agent-event-002",
        decision="approved",
        reviewer="Engineer A",
    )
    final_state = run_local_agent_workflow_until_blocked(with_risk_approved)

    assert final_state.current_phase == "report_draft"
    assert final_state.phase_statuses["report_draft"] == "waiting_for_engineer"
    assert final_state.risks
    assert final_state.report_sections
    assert final_state.rfi_items
    assert [event.agent_role for event in final_state.agent_events] == [
        "calculation_check",
        "risk_ncr",
        "report_composer",
    ]


def test_resume_local_agent_workflow_after_review_decisions_applies_review_and_runs_next_segment() -> None:
    state = run_local_agent_workflow_until_blocked(
        ProjectReviewState(project_id="pv-001", intake=_sample_intake())
    )

    resumed = resume_local_agent_workflow_after_review_decisions(
        state,
        {
            "agent-event-001": {
                "decision": "approved",
                "comment": "Document intake evidence reviewed.",
            }
        },
        reviewer="Engineer A",
    )

    assert resumed.current_phase == "basis_build"
    assert resumed.phase_statuses["document_check"] == "approved"
    assert resumed.phase_statuses["basis_build"] == "waiting_for_engineer"
    assert [event.agent_role for event in resumed.agent_events] == [
        "document_intake",
        "basis_code",
    ]
    assert resumed.approvals[-1].target_type == "agent_event"
    assert resumed.approvals[-1].target_id == "agent-event-001"
    assert resumed.approvals[-1].reviewer == "Engineer A"
    assert resumed.approvals[-1].comment == "Document intake evidence reviewed."


def test_resume_local_agent_workflow_after_review_decisions_does_not_consume_future_decisions() -> None:
    state = run_local_agent_workflow_until_blocked(
        ProjectReviewState(project_id="pv-001", intake=_sample_intake())
    )

    resumed = resume_local_agent_workflow_after_review_decisions(
        state,
        {
            "agent-event-001": {"decision": "approved"},
            "agent-event-002": {"decision": "approved"},
        },
        reviewer="Engineer A",
    )

    assert resumed.current_phase == "basis_build"
    assert resumed.phase_statuses["basis_build"] == "waiting_for_engineer"
    assert [approval.target_id for approval in resumed.approvals] == ["agent-event-001"]
    assert [event.agent_role for event in resumed.agent_events] == [
        "document_intake",
        "basis_code",
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

    assert final_state.current_phase == "document_check"
    assert persisted_state.current_phase == "document_check"
    assert persisted_state.basis_references == []
    assert persisted_state.review_plan == []
    assert persisted_state.review_paths == []
    assert [event.agent_role for event in persisted_state.agent_events] == ["document_intake"]


def test_persisted_local_agent_workflow_resumes_locked_calculation_gate_state(tmp_path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    repository.save(
        ProjectReviewState(
            project_id="pv-locked",
            intake=_sample_intake(),
            current_phase="engineer_data_lock",
            phase_statuses={
                **ProjectReviewState(project_id="pv-locked", intake=_sample_intake()).phase_statuses,
                "engineer_data_lock": "approved",
            },
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

    assert final_state.current_phase == "calculation_check"
    assert persisted_state.current_phase == "calculation_check"
    assert persisted_state.risks == []
    assert persisted_state.report_sections == []
    assert persisted_state.rfi_items == []
    assert [event.agent_role for event in persisted_state.agent_events] == ["calculation_check"]


def test_persisted_local_agent_workflow_summary_records_resume_audit_trail(tmp_path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    repository.save(ProjectReviewState(project_id="pv-001", intake=_sample_intake()))

    result = run_persisted_local_agent_workflow_with_summary(repository, "pv-001")

    assert result.state.current_phase == "document_check"
    assert result.summary.project_id == "pv-001"
    assert result.summary.start_phase == "intake"
    assert result.summary.final_phase == "document_check"
    assert result.summary.saved is True
    assert result.summary.applied_agent_roles == ["document_intake"]
    assert result.summary.applied_agent_event_ids == ["agent-event-001"]
    assert result.summary.artifact_counts["document_versions"] == len(
        result.state.document_versions
    )
    assert result.summary.artifact_counts["review_plan"] == len(result.state.review_plan)
    assert result.summary.artifact_counts["review_paths"] == len(result.state.review_paths)


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
