from structural_screening_agent.bv_review.calculation_workflow import (
    build_calculation_runs_from_locked_fields,
    build_incremental_calculation_recheck_runs_for_rfi,
    run_incremental_calculation_recheck_for_rfi,
)
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    EngineerApproval,
    ExtractedField,
    ProjectReviewState,
    RFIItem,
)


def test_calculation_workflow_does_not_run_before_calculation_gate_is_locked() -> None:
    state = ProjectReviewState(
        project_id="pv-calculation-workflow",
        intake=_sample_intake(),
        extracted_fields=_locked_calculation_fields(),
    )

    runs = build_calculation_runs_from_locked_fields(state)

    assert runs == []


def test_calculation_workflow_builds_foundation_and_superstructure_runs_from_locked_fields() -> None:
    state = ProjectReviewState(
        project_id="pv-calculation-workflow",
        intake=_sample_intake(),
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

    runs = build_calculation_runs_from_locked_fields(state)

    assert [run.run_id for run in runs] == [
        "foundation-run-001",
        "superstructure-run-post-P1-001",
    ]
    assert [run.engine_name for run in runs] == ["foundation", "superstructure"]
    assert all(run.status == "completed" for run in runs)
    assert runs[0].result_summary["screening_status"] == "review_required"
    assert runs[1].result_summary["member_id"] == "post-P1"
    assert runs[1].result_summary["screening_status"] == "pass"
    assert state.calculation_runs == []


def test_incremental_recheck_for_responded_rfi_runs_deterministic_engine_and_marks_recheck_complete() -> None:
    state = ProjectReviewState(
        project_id="pv-calculation-workflow",
        intake=_sample_intake(),
        current_phase="issue_rfi_closeout",
        extracted_fields=_locked_calculation_fields(),
        approvals=[_calculation_gate_approval()],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["pile_length_m", "uplift_force_kn"],
                input_locked=True,
                status="completed",
            )
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-run-001",
                question="Please confirm foundation reaction updates.",
                responsible_party="client / designer",
                trigger_basis="Foundation screening run requires clarification.",
                required_document_or_field="uplift_force_kn",
                status="responded",
                client_response="Designer submitted Rev B reaction table.",
                reopen_review_items=["uplift_force_kn"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    updated = run_incremental_calculation_recheck_for_rfi(
        state,
        rfi_id="rfi-foundation-run-001",
    )

    assert updated.current_phase == "issue_rfi_closeout"
    assert updated.phase_statuses["calculation_check"] == "waiting_for_engineer"
    assert updated.phase_statuses["issue_rfi_closeout"] == "waiting_for_engineer"
    assert updated.rfi_items[0].completed_recheck_items == ["uplift_force_kn"]
    assert [run.run_id for run in updated.calculation_runs] == [
        "foundation-run-001",
        "incremental-recheck-rfi-foundation-run-001-foundation-001",
    ]
    recheck_run = updated.calculation_runs[-1]
    assert recheck_run.engine_name == "foundation"
    assert recheck_run.status == "completed"
    assert recheck_run.input_locked is True
    assert recheck_run.result_summary["screening_boundary"] == (
        "screening-level review support only"
    )
    assert state.rfi_items[0].completed_recheck_items == []


def test_incremental_recheck_keeps_rfi_incomplete_when_deterministic_engine_blocks() -> None:
    state = ProjectReviewState(
        project_id="pv-calculation-workflow",
        intake=_sample_intake(),
        current_phase="issue_rfi_closeout",
        extracted_fields=[_locked_field("pile_length_m", "3.5", "m")],
        approvals=[_calculation_gate_approval()],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["pile_length_m"],
                input_locked=True,
                status="completed",
            )
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-run-001",
                question="Please confirm foundation input updates.",
                responsible_party="client / designer",
                trigger_basis="Foundation input changed.",
                required_document_or_field="pile_length_m",
                status="responded",
                client_response="Designer confirmed Rev B pile length.",
                reopen_review_items=["pile_length_m"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    updated = run_incremental_calculation_recheck_for_rfi(
        state,
        rfi_id="rfi-foundation-run-001",
    )

    assert updated.phase_statuses["calculation_check"] == "blocked"
    assert updated.rfi_items[0].completed_recheck_items == []
    recheck_run = updated.calculation_runs[-1]
    assert recheck_run.status == "blocked"
    assert "pile_diameter_mm is required." in recheck_run.structured_errors


def test_incremental_recheck_preview_requires_locked_calculation_gate() -> None:
    state = ProjectReviewState(
        project_id="pv-calculation-workflow",
        intake=_sample_intake(),
        extracted_fields=_locked_calculation_fields(),
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-run-001",
                question="Please confirm foundation reaction updates.",
                responsible_party="client / designer",
                trigger_basis="Foundation input changed.",
                required_document_or_field="uplift_force_kn",
                status="responded",
                client_response="Designer submitted Rev B reaction table.",
                reopen_review_items=["uplift_force_kn"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    assert (
        build_incremental_calculation_recheck_runs_for_rfi(
            state,
            rfi_id="rfi-foundation-run-001",
        )
        == []
    )


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV calculation workflow",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents={"calculation_report": "available"},
    )


def _calculation_gate_approval() -> EngineerApproval:
    return EngineerApproval(
        approval_id="approval-calculation",
        target_type="gate",
        target_id="calculation",
        status="approved",
        locked=True,
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
