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
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    EngineerApproval,
    ExtractedField,
)
from structural_screening_agent.bv_review.report import build_bv_active_rfi_register_section
from structural_screening_agent.bv_review.blocked_calculation_draft import (
    build_blocked_calculation_review_draft,
)
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


def test_local_agent_workflow_builds_calculation_runs_after_locked_gate() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "engineer_data_lock": "approved",
        },
        extracted_fields=_locked_calculation_fields(),
        approvals=[
            EngineerApproval(
                approval_id="approval-calculation",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            )
        ],
    )

    final_state = run_local_agent_workflow_until_blocked(state)

    assert final_state.current_phase == "calculation_check"
    assert final_state.phase_statuses["calculation_check"] == "waiting_for_engineer"
    assert [run.run_id for run in final_state.calculation_runs] == [
        "foundation-run-001",
        "superstructure-run-post-P1-001",
    ]
    assert all(run.status == "completed" for run in final_state.calculation_runs)
    assert final_state.agent_events[-1].agent_role == "calculation_check"
    assert final_state.agent_events[-1].summary_counts == {"calculation_run_ids": 2}


def test_local_agent_workflow_preserves_existing_calculation_runs() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "engineer_data_lock": "approved",
        },
        extracted_fields=_locked_calculation_fields(),
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
                run_id="manual-foundation-run",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["uplift_force_kn"],
                input_locked=True,
                status="completed",
                result_summary={
                    "screening_boundary": "screening-level review support only",
                    "screening_status": "pass",
                },
            )
        ],
    )

    final_state = run_local_agent_workflow_until_blocked(state)

    assert [run.run_id for run in final_state.calculation_runs] == [
        "manual-foundation-run"
    ]
    assert final_state.agent_events[-1].summary_counts == {"calculation_run_ids": 1}


def test_local_agent_workflow_keeps_engineer_data_lock_when_any_generated_engine_run_is_blocked() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "engineer_data_lock": "approved",
        },
        extracted_fields=[
            field
            for field in _locked_calculation_fields()
            if field.field_id not in {"bending_moment_knm"}
        ],
        approvals=[
            EngineerApproval(
                approval_id="approval-calculation",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            )
        ],
    )

    final_state = run_local_agent_workflow_until_blocked(state)

    assert final_state.current_phase == "engineer_data_lock"
    assert final_state.agent_events == []
    assert final_state.risks == []
    assert final_state.rfi_items == []
    assert final_state.report_sections == []
    assert [run.run_id for run in final_state.calculation_runs] == [
        "foundation-run-001",
        "superstructure-run-post-P1-001",
    ]
    assert final_state.calculation_runs[0].status == "completed"
    assert final_state.calculation_runs[1].status == "blocked"
    assert "bending_moment_knm is required." in final_state.calculation_runs[1].structured_errors


def test_blocked_calculation_review_draft_builds_risk_and_rfi_without_mutating_state() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "engineer_data_lock": "approved",
        },
        extracted_fields=[
            field
            for field in _locked_calculation_fields()
            if field.field_id not in {"bending_moment_knm"}
        ],
        approvals=[
            EngineerApproval(
                approval_id="approval-calculation",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            )
        ],
    )

    final_state = run_local_agent_workflow_until_blocked(state)
    draft = build_blocked_calculation_review_draft(final_state)

    assert final_state.current_phase == "engineer_data_lock"
    assert final_state.phase_statuses["calculation_check"] == "pending"
    assert final_state.agent_events == []
    assert final_state.risks == []
    assert final_state.rfi_items == []
    assert final_state.report_sections == []
    blocked_risk = next(
        risk
        for risk in draft.risks
        if risk.risk_id == "calculation_blocked_superstructure_run_post_p1_001"
    )
    assert blocked_risk.category == "nonconformity"
    assert blocked_risk.blocks_report_issue is True
    rfi = next(
        item
        for item in draft.rfi_items
        if item.rfi_id == "rfi-calculation_blocked_superstructure_run_post_p1_001"
    )
    assert rfi.status == "open"
    assert rfi.reopen_review_items == [
        "section_area_mm2",
        "section_modulus_mm3",
        "radius_of_gyration_mm",
        "effective_length_m",
        "steel_yield_strength_mpa",
        "axial_force_kn",
        "bending_moment_knm",
    ]
    assert "重新运行筛查级计算" in rfi.question
    display_state = final_state.model_copy(update={"rfi_items": draft.rfi_items})
    active_rfi_section = build_bv_active_rfi_register_section(display_state)
    assert active_rfi_section is not None
    assert active_rfi_section.heading == "未关闭 RFI 与客户澄清项"
    assert rfi.rfi_id in active_rfi_section.items[0]
    rerun_state = run_local_agent_workflow_until_blocked(final_state)
    assert rerun_state.risks == []
    assert rerun_state.rfi_items == []


def test_blocked_calculation_review_draft_includes_failed_runs() -> None:
    blocked_run = CalculationRun(
        run_id="foundation-failed-001",
        engine_name="foundation",
        engine_version="phase1-deterministic-screening",
        input_field_ids=["pile_length_m"],
        input_locked=False,
        status="failed",
        structured_errors=["foundation calculation failed."],
    )
    state = ProjectReviewState(
        project_id="pv-001",
        intake=BVReviewIntake(
            project_name="Ground PV design review",
            country_or_region="China",
            project_type="utility_pv",
            design_stage="detailed_design",
            standards_systems=["gb"],
            review_objects=["mounting_structure"],
            documents={
                "structural_drawings": "available",
                "calculation_report": "partial",
            },
        ),
        current_phase="engineer_data_lock",
        calculation_runs=[blocked_run],
    )

    draft = build_blocked_calculation_review_draft(state)

    assert [risk.risk_id for risk in draft.risks] == [
        "calculation_blocked_foundation_failed_001"
    ]
    assert draft.risks[0].blocks_report_issue is True
    assert draft.rfi_items[0].status == "open"
    assert draft.rfi_items[0].trigger_basis == draft.risks[0].trigger_basis


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


def _locked_field(field_id: str, value: str, unit: str) -> ExtractedField:
    return ExtractedField(
        field_id=field_id,
        name=field_id.replace("_", " ").title(),
        candidate_value=value,
        unit=unit,
        source_document_id="calculation-report-c001",
        page_or_section="Calculation input table",
        quote=f"{field_id} = {value}",
        confidence=0.92,
        is_confirmed=True,
        confirmed_value=value,
        confirmed_unit=unit,
        include_in_calculation=True,
    )


def _locked_calculation_fields() -> list[ExtractedField]:
    return [
        _locked_field("pile_diameter_mm", "300", "mm"),
        _locked_field("pile_length_m", "3.5", "m"),
        _locked_field("side_resistance_standard_kpa", "35", "kPa"),
        _locked_field("bearing_capacity_characteristic_kpa", "180", "kPa"),
        _locked_field("uplift_force_kn", "140", "kN"),
        _locked_field("compression_force_kn", "10", "kN"),
        _locked_field("horizontal_force_kn", "12", "kN"),
        _locked_field("section_area_mm2", "2400", "mm2"),
        _locked_field("section_modulus_mm3", "180000", "mm3"),
        _locked_field("radius_of_gyration_mm", "32", "mm"),
        _locked_field("effective_length_m", "3.2", "m"),
        _locked_field("steel_yield_strength_mpa", "235", "MPa"),
        _locked_field("axial_force_kn", "60", "kN"),
        _locked_field("bending_moment_knm", "18", "kN*m"),
    ]
