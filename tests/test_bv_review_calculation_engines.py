import pytest

from structural_screening_agent.bv_review.calculation_engines import (
    FoundationEngineInput,
    SuperstructureEngineInput,
    build_foundation_calculation_run,
    build_superstructure_calculation_run,
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
        ),
        input_field_ids=[
            "pile_diameter_mm",
            "pile_length_m",
            "side_resistance_standard_kpa",
            "bearing_capacity_characteristic_kpa",
            "uplift_force_kn",
            "compression_force_kn",
        ],
    )

    assert run.engine_name == "foundation"
    assert run.status == "completed"
    assert run.input_locked is True
    assert run.structured_errors == []
    assert run.result_summary["screening_boundary"] == "screening-level review support only"
    assert run.result_summary["overturning_check_note"] == "not covered; engineer review required"
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
