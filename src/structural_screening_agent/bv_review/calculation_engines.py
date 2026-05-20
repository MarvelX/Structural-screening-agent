from __future__ import annotations

from math import pi
from typing import Literal

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.project_state import CalculationRun, FieldValue


ENGINE_VERSION = "phase1-deterministic-screening"
SCREENING_BOUNDARY = "screening-level review support only"


class FoundationEngineInput(BaseModel):
    pile_diameter_mm: float | None = None
    pile_length_m: float | None = None
    side_resistance_standard_kpa: float | None = None
    bearing_capacity_characteristic_kpa: float | None = None
    uplift_force_kn: float | None = None
    compression_force_kn: float | None = None


class SuperstructureEngineInput(BaseModel):
    member_id: str = Field(min_length=1)
    member_type: Literal["post", "beam", "purlin", "brace"]
    section_area_mm2: float | None = None
    section_modulus_mm3: float | None = None
    radius_of_gyration_mm: float | None = None
    effective_length_m: float | None = None
    steel_yield_strength_mpa: float | None = None
    axial_force_kn: float | None = None
    bending_moment_knm: float | None = None


def build_foundation_calculation_run(
    *,
    run_id: str,
    input_data: FoundationEngineInput,
    input_field_ids: list[str],
) -> CalculationRun:
    errors = _validate_positive_inputs(
        input_data,
        [
            "pile_diameter_mm",
            "pile_length_m",
            "side_resistance_standard_kpa",
            "bearing_capacity_characteristic_kpa",
            "uplift_force_kn",
            "compression_force_kn",
        ],
    )
    if errors:
        return _blocked_run(run_id, "foundation", input_field_ids, errors)

    pile_diameter_m = _as_float(input_data.pile_diameter_mm) / 1000
    pile_length_m = _as_float(input_data.pile_length_m)
    side_area_m2 = pi * pile_diameter_m * pile_length_m
    base_area_m2 = pi * pile_diameter_m**2 / 4
    uplift_capacity_kn = side_area_m2 * _as_float(input_data.side_resistance_standard_kpa)
    bearing_capacity_kn = (
        base_area_m2 * _as_float(input_data.bearing_capacity_characteristic_kpa)
    )
    uplift_utilization_ratio = _as_float(input_data.uplift_force_kn) / uplift_capacity_kn
    bearing_utilization_ratio = (
        _as_float(input_data.compression_force_kn) / bearing_capacity_kn
    )
    controlling_ratio = max(uplift_utilization_ratio, bearing_utilization_ratio)

    return _completed_run(
        run_id,
        "foundation",
        input_field_ids,
        {
            "screening_boundary": SCREENING_BOUNDARY,
            "overturning_check_note": "not covered; engineer review required",
            "uplift_capacity_kn": _rounded(uplift_capacity_kn),
            "bearing_capacity_kn": _rounded(bearing_capacity_kn),
            "uplift_utilization_ratio": _rounded(uplift_utilization_ratio),
            "bearing_utilization_ratio": _rounded(bearing_utilization_ratio),
            "controlling_utilization_ratio": _rounded(controlling_ratio),
            "screening_status": _screening_status(controlling_ratio),
        },
    )


def build_superstructure_calculation_run(
    *,
    run_id: str,
    input_data: SuperstructureEngineInput,
    input_field_ids: list[str],
) -> CalculationRun:
    errors = _validate_positive_inputs(
        input_data,
        [
            "section_area_mm2",
            "section_modulus_mm3",
            "radius_of_gyration_mm",
            "effective_length_m",
            "steel_yield_strength_mpa",
            "axial_force_kn",
            "bending_moment_knm",
        ],
    )
    if errors:
        return _blocked_run(run_id, "superstructure", input_field_ids, errors)

    axial_stress_mpa = abs(_as_float(input_data.axial_force_kn)) * 1000 / _as_float(
        input_data.section_area_mm2
    )
    bending_stress_mpa = abs(_as_float(input_data.bending_moment_knm)) * 1_000_000 / _as_float(
        input_data.section_modulus_mm3
    )
    strength_utilization_ratio = (
        axial_stress_mpa + bending_stress_mpa
    ) / _as_float(input_data.steel_yield_strength_mpa)
    slenderness_ratio = (
        _as_float(input_data.effective_length_m) * 1000 / _as_float(input_data.radius_of_gyration_mm)
    )
    slenderness_utilization_ratio = slenderness_ratio / 150
    stability_utilization_ratio = strength_utilization_ratio * max(
        1.0, slenderness_utilization_ratio
    )
    controlling_ratio = max(
        strength_utilization_ratio,
        stability_utilization_ratio,
        slenderness_utilization_ratio,
    )

    return _completed_run(
        run_id,
        "superstructure",
        input_field_ids,
        {
            "screening_boundary": SCREENING_BOUNDARY,
            "member_id": input_data.member_id,
            "member_type": input_data.member_type,
            "axial_stress_mpa": _rounded(axial_stress_mpa),
            "bending_stress_mpa": _rounded(bending_stress_mpa),
            "strength_utilization_ratio": _rounded(strength_utilization_ratio),
            "slenderness_ratio": _rounded(slenderness_ratio),
            "slenderness_utilization_ratio": _rounded(slenderness_utilization_ratio),
            "stability_utilization_ratio": _rounded(stability_utilization_ratio),
            "controlling_utilization_ratio": _rounded(controlling_ratio),
            "screening_status": _screening_status(controlling_ratio),
        },
    )


def _validate_positive_inputs(input_data: BaseModel, field_names: list[str]) -> list[str]:
    errors: list[str] = []
    for field_name in field_names:
        value = getattr(input_data, field_name)
        if value is None:
            errors.append(f"{field_name} is required.")
        elif value <= 0:
            errors.append(f"{field_name} must be greater than zero.")
    return errors


def _blocked_run(
    run_id: str,
    engine_name: Literal["foundation", "superstructure"],
    input_field_ids: list[str],
    errors: list[str],
) -> CalculationRun:
    return CalculationRun(
        run_id=run_id,
        engine_name=engine_name,
        engine_version=ENGINE_VERSION,
        input_field_ids=input_field_ids,
        input_locked=False,
        status="blocked",
        structured_errors=errors,
    )


def _completed_run(
    run_id: str,
    engine_name: Literal["foundation", "superstructure"],
    input_field_ids: list[str],
    result_summary: dict[str, FieldValue],
) -> CalculationRun:
    return CalculationRun(
        run_id=run_id,
        engine_name=engine_name,
        engine_version=ENGINE_VERSION,
        input_field_ids=input_field_ids,
        input_locked=True,
        status="completed",
        result_summary=result_summary,
    )


def _as_float(value: float | None) -> float:
    if value is None:
        raise ValueError("Validated numeric input unexpectedly became None.")
    return float(value)


def _rounded(value: float) -> float:
    return round(value, 2)


def _screening_status(controlling_ratio: float) -> str:
    return "pass" if controlling_ratio <= 1.0 else "review_required"
