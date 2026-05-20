import pytest

from structural_screening_agent.bv_review.calculation_engines import (
    FoundationEngineInput,
    SuperstructureEngineInput,
    build_foundation_calculation_run,
    build_foundation_calculation_run_from_fields,
    build_superstructure_calculation_run,
    build_superstructure_calculation_run_from_fields,
)
from structural_screening_agent.bv_review.project_state import ExtractedField


def _confirmed_field(field_id: str, value: str, *, unit: str | None = None) -> ExtractedField:
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


def _confirmed_but_excluded_field(
    field_id: str, value: str, *, unit: str | None = None
) -> ExtractedField:
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
        include_in_calculation=False,
    )


def test_foundation_engine_returns_completed_screening_run_with_traceable_ratios() -> None:
    run = build_foundation_calculation_run(
        run_id="foundation-run-001",
        input_data=FoundationEngineInput(
            pile_diameter_mm=300,
            pile_length_m=3.5,
            side_resistance_standard_kpa=35,
            bearing_capacity_characteristic_kpa=180,
            uplift_force_kn=140,
            compression_force_kn=10,
            horizontal_force_kn=12,
        ),
        input_field_ids=[
            "pile_diameter_mm",
            "pile_length_m",
            "side_resistance_standard_kpa",
            "bearing_capacity_characteristic_kpa",
            "uplift_force_kn",
            "compression_force_kn",
            "horizontal_force_kn",
        ],
    )

    assert run.engine_name == "foundation"
    assert run.status == "completed"
    assert run.input_locked is True
    assert run.structured_errors == []
    assert run.result_summary["screening_boundary"] == "screening-level review support only"
    assert (
        run.result_summary["lateral_and_overturning_check_note"]
        == "horizontal force captured for engineer review; lateral and overturning checks are not covered"
    )
    assert run.result_summary["horizontal_force_kn"] == pytest.approx(12, abs=0.01)
    assert run.result_summary["uplift_utilization_ratio"] == pytest.approx(1.21, abs=0.01)
    assert run.result_summary["bearing_utilization_ratio"] == pytest.approx(0.79, abs=0.01)
    assert run.result_summary["screening_status"] == "review_required"


def test_foundation_engine_blocks_with_structured_errors_for_missing_or_invalid_inputs() -> None:
    run = build_foundation_calculation_run(
        run_id="foundation-run-002",
        input_data=FoundationEngineInput(
            pile_diameter_mm=0,
            pile_length_m=None,
            side_resistance_standard_kpa=35,
            bearing_capacity_characteristic_kpa=None,
            uplift_force_kn=45,
            compression_force_kn=10,
        ),
        input_field_ids=["pile_diameter_mm", "pile_length_m"],
    )

    assert run.status == "blocked"
    assert run.input_locked is False
    assert "pile_diameter_mm must be greater than zero." in run.structured_errors
    assert "pile_length_m is required." in run.structured_errors
    assert "bearing_capacity_characteristic_kpa is required." in run.structured_errors
    assert run.result_summary == {}


def test_foundation_engine_runs_from_engineer_confirmed_fields() -> None:
    run = build_foundation_calculation_run_from_fields(
        run_id="foundation-run-from-fields",
        fields=[
            _confirmed_field("pile_diameter_mm", "300", unit="mm"),
            _confirmed_field("pile_length_m", "3.5", unit="m"),
            _confirmed_field("side_resistance_standard_kpa", "35", unit="kPa"),
            _confirmed_field("bearing_capacity_characteristic_kpa", "180", unit="kPa"),
            _confirmed_field("uplift_force_kn", "140", unit="kN"),
            _confirmed_field("compression_force_kn", "10", unit="kN"),
            _confirmed_field("horizontal_force_kn", "12", unit="kN"),
        ],
    )

    assert run.status == "completed"
    assert run.input_field_ids == [
        "pile_diameter_mm",
        "pile_length_m",
        "side_resistance_standard_kpa",
        "bearing_capacity_characteristic_kpa",
        "uplift_force_kn",
        "compression_force_kn",
        "horizontal_force_kn",
    ]
    assert run.result_summary["horizontal_force_kn"] == pytest.approx(12, abs=0.01)
    assert run.result_summary["screening_status"] == "review_required"


def test_foundation_engine_from_fields_blocks_missing_horizontal_force_evidence() -> None:
    run = build_foundation_calculation_run_from_fields(
        run_id="foundation-run-from-fields-missing-horizontal",
        fields=[
            _confirmed_field("pile_diameter_mm", "300", unit="mm"),
            _confirmed_field("pile_length_m", "3.5", unit="m"),
            _confirmed_field("side_resistance_standard_kpa", "35", unit="kPa"),
            _confirmed_field("bearing_capacity_characteristic_kpa", "180", unit="kPa"),
            _confirmed_field("uplift_force_kn", "140", unit="kN"),
            _confirmed_field("compression_force_kn", "10", unit="kN"),
        ],
    )

    assert run.status == "blocked"
    assert "horizontal_force_kn is required." in run.structured_errors


def test_foundation_engine_from_fields_blocks_unconfirmed_or_non_numeric_values() -> None:
    unconfirmed_force = ExtractedField(
        field_id="uplift_force_kn",
        name="Uplift Force",
        candidate_value="140",
        unit="kN",
        source_document_id="calculation-report-c001",
        page_or_section="Calculation input table",
        quote="uplift_force_kn = 140",
        confidence=0.92,
        is_confirmed=False,
        include_in_calculation=False,
    )
    run = build_foundation_calculation_run_from_fields(
        run_id="foundation-run-from-fields-blocked",
        fields=[
            _confirmed_field("pile_diameter_mm", "not-a-number", unit="mm"),
            _confirmed_field("pile_length_m", "3.5", unit="m"),
            _confirmed_field("side_resistance_standard_kpa", "35", unit="kPa"),
            _confirmed_field("bearing_capacity_characteristic_kpa", "180", unit="kPa"),
            unconfirmed_force,
            _confirmed_field("compression_force_kn", "10", unit="kN"),
            _confirmed_field("horizontal_force_kn", "12", unit="kN"),
        ],
    )

    assert run.status == "blocked"
    assert run.input_locked is False
    assert "pile_diameter_mm confirmed value must be numeric." in run.structured_errors
    assert (
        "uplift_force_kn must be engineer-confirmed and marked for calculation."
        in run.structured_errors
    )


def test_foundation_engine_from_fields_blocks_confirmed_fields_excluded_from_calculation() -> None:
    run = build_foundation_calculation_run_from_fields(
        run_id="foundation-run-from-fields-excluded",
        fields=[
            _confirmed_but_excluded_field("pile_diameter_mm", "300", unit="mm"),
            _confirmed_field("pile_length_m", "3.5", unit="m"),
            _confirmed_field("side_resistance_standard_kpa", "35", unit="kPa"),
            _confirmed_field("bearing_capacity_characteristic_kpa", "180", unit="kPa"),
            _confirmed_field("uplift_force_kn", "140", unit="kN"),
            _confirmed_field("compression_force_kn", "10", unit="kN"),
            _confirmed_field("horizontal_force_kn", "12", unit="kN"),
        ],
    )

    assert run.status == "blocked"
    assert (
        "pile_diameter_mm must be engineer-confirmed and marked for calculation."
        in run.structured_errors
    )


def test_superstructure_engine_returns_strength_stability_and_slenderness_ratios() -> None:
    run = build_superstructure_calculation_run(
        run_id="superstructure-run-001",
        input_data=SuperstructureEngineInput(
            member_id="post-P1",
            member_type="post",
            section_area_mm2=2400,
            section_modulus_mm3=180000,
            radius_of_gyration_mm=32,
            effective_length_m=3.2,
            steel_yield_strength_mpa=235,
            axial_force_kn=60,
            bending_moment_knm=18,
        ),
        input_field_ids=[
            "post_section_area_mm2",
            "post_section_modulus_mm3",
            "post_effective_length_m",
            "steel_yield_strength_mpa",
            "worst_axial_force_kn",
            "worst_bending_moment_knm",
        ],
    )

    assert run.engine_name == "superstructure"
    assert run.status == "completed"
    assert run.result_summary["screening_boundary"] == "screening-level review support only"
    assert run.result_summary["member_id"] == "post-P1"
    assert run.result_summary["strength_utilization_ratio"] == pytest.approx(0.53, abs=0.01)
    assert run.result_summary["slenderness_ratio"] == pytest.approx(100.0, abs=0.01)
    assert run.result_summary["stability_utilization_ratio"] == pytest.approx(0.53, abs=0.01)
    assert run.result_summary["screening_status"] == "pass"


def test_superstructure_engine_blocks_without_complete_section_and_material_data() -> None:
    run = build_superstructure_calculation_run(
        run_id="superstructure-run-002",
        input_data=SuperstructureEngineInput(
            member_id="beam-B1",
            member_type="beam",
            section_area_mm2=None,
            section_modulus_mm3=0,
            radius_of_gyration_mm=30,
            effective_length_m=4.0,
            steel_yield_strength_mpa=None,
            axial_force_kn=25,
            bending_moment_knm=15,
        ),
        input_field_ids=["beam_section_area_mm2", "beam_section_modulus_mm3"],
    )

    assert run.status == "blocked"
    assert run.input_locked is False
    assert "section_area_mm2 is required." in run.structured_errors
    assert "section_modulus_mm3 must be greater than zero." in run.structured_errors
    assert "steel_yield_strength_mpa is required." in run.structured_errors


def test_superstructure_engine_runs_from_engineer_confirmed_fields() -> None:
    run = build_superstructure_calculation_run_from_fields(
        run_id="superstructure-run-from-fields",
        fields=[
            _confirmed_field("section_area_mm2", "2400", unit="mm2"),
            _confirmed_field("section_modulus_mm3", "180000", unit="mm3"),
            _confirmed_field("radius_of_gyration_mm", "32", unit="mm"),
            _confirmed_field("effective_length_m", "3.2", unit="m"),
            _confirmed_field("steel_yield_strength_mpa", "235", unit="MPa"),
            _confirmed_field("axial_force_kn", "60", unit="kN"),
            _confirmed_field("bending_moment_knm", "18", unit="kN*m"),
        ],
        member_id="post-P1",
        member_type="post",
    )

    assert run.status == "completed"
    assert run.result_summary["member_id"] == "post-P1"
    assert run.result_summary["screening_status"] == "pass"


def test_superstructure_engine_from_fields_blocks_unconfirmed_member_data() -> None:
    unconfirmed_area = ExtractedField(
        field_id="section_area_mm2",
        name="Section Area",
        candidate_value="2400",
        unit="mm2",
        source_document_id="calculation-report-c001",
        page_or_section="Calculation input table",
        quote="section_area_mm2 = 2400",
        confidence=0.92,
        is_confirmed=False,
        include_in_calculation=False,
    )
    run = build_superstructure_calculation_run_from_fields(
        run_id="superstructure-run-from-fields-blocked",
        fields=[
            unconfirmed_area,
            _confirmed_field("section_modulus_mm3", "180000", unit="mm3"),
            _confirmed_field("radius_of_gyration_mm", "32", unit="mm"),
            _confirmed_field("effective_length_m", "3.2", unit="m"),
            _confirmed_field("steel_yield_strength_mpa", "235", unit="MPa"),
            _confirmed_field("axial_force_kn", "60", unit="kN"),
            _confirmed_field("bending_moment_knm", "18", unit="kN*m"),
        ],
        member_id="post-P1",
        member_type="post",
    )

    assert run.status == "blocked"
    assert (
        "section_area_mm2 must be engineer-confirmed and marked for calculation."
        in run.structured_errors
    )


def test_superstructure_engine_from_fields_blocks_missing_required_member_data() -> None:
    run = build_superstructure_calculation_run_from_fields(
        run_id="superstructure-run-from-fields-missing",
        fields=[
            _confirmed_field("section_area_mm2", "2400", unit="mm2"),
            _confirmed_field("section_modulus_mm3", "180000", unit="mm3"),
            _confirmed_field("radius_of_gyration_mm", "32", unit="mm"),
            _confirmed_field("effective_length_m", "3.2", unit="m"),
            _confirmed_field("steel_yield_strength_mpa", "235", unit="MPa"),
            _confirmed_field("axial_force_kn", "60", unit="kN"),
        ],
        member_id="post-P1",
        member_type="post",
    )

    assert run.status == "blocked"
    assert "bending_moment_knm is required." in run.structured_errors
