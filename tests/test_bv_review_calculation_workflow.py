from structural_screening_agent.bv_review.calculation_workflow import (
    build_calculation_runs_from_locked_fields,
)
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.project_state import (
    EngineerApproval,
    ExtractedField,
    ProjectReviewState,
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
