from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.portal_frame import run_portal_frame_screening
from structural_screening_agent.models import BuildingIntake


def _level_b_case(standard: str = "gb"):
    intake = BuildingIntake(
        project_type="rooftop_pv",
        design_standard_context=standard,
        building_type="test warehouse",
        structural_system="steel portal frame",
        roof_type="metal roof",
        intended_modification="distributed rooftop pv",
        estimated_added_load_kpa=0.18,
        building_span_m=30.0,
        column_spacing_m=8.0,
        eave_height_m=8.0,
        rafter_section="310x150x8x12 welded rafter",
        column_section="305x305x10x15 welded column",
        steel_grade="Q355",
        purlin_spacing_m=1.5,
        purlin_type="cold_formed_z",
        roof_panel_type="profiled_sheet",
        roof_panel_thickness_mm=None,
        roof_rib_height_mm=None,
        roof_attachment_preference="clamp_based",
        existing_member_schedule_status="available",
        connection_detail_status="partial",
        roof_vendor_data_status="missing",
        corrosion_condition="moderate",
        waterproofing_sensitivity="high",
        restricted_installation_zones="maintenance corridor",
        available_verification_path="drawings_only",
        shutdown_constraint="limited",
        drawing_availability="complete",
        survey_available=False,
    )
    case = from_building_intake(intake)
    assert case.evidence.screening_level == "level_b"
    assert case.code_context.standard == standard
    return case


def test_run_portal_frame_screening_uses_real_gb_calculator_for_level_b_case() -> None:
    result = run_portal_frame_screening(_level_b_case())

    assert result.code_path == "gb"
    assert result.screening_level == "level_b"
    assert result.controlling_component in {"purlin", "primary_frame"}
    assert "gb_portal_frame_purlin_screening" in result.code_reference_ids
    assert any(row.row_id == "purlin_strength_ratio" for row in result.calculation_rows)
    assert any(row.row_id == "purlin_deflection_ratio" for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_screening_ratio" for row in result.calculation_rows)
    assert any(row.row_id == "purlin_strength_ratio" and row.numeric_value is not None for row in result.calculation_rows)
    assert any(row.row_id == "purlin_deflection_ratio" and row.numeric_value is not None for row in result.calculation_rows)
    assert any(row.row_id == "purlin_strength_ratio" and row.formula_en for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_screening_ratio" and row.formula_zh for row in result.calculation_rows)


def test_run_portal_frame_screening_routes_level_b_aisc_case_to_aisc_calculator() -> None:
    result = run_portal_frame_screening(_level_b_case("aisc"))

    assert result.code_path == "aisc"
    assert result.screening_level == "level_b"
    assert result.controlling_component in {"purlin", "primary_frame"}
    assert "aisc" in result.code_reference_ids[0]
    assert any(row.row_id == "purlin_strength_ratio" for row in result.calculation_rows)
    assert any(row.row_id == "purlin_deflection_ratio" for row in result.calculation_rows)


def test_run_portal_frame_screening_routes_level_b_eurocode_case_to_eurocode_calculator() -> None:
    result = run_portal_frame_screening(_level_b_case("eurocode"))

    assert result.code_path == "eurocode"
    assert result.screening_level == "level_b"
    assert result.controlling_component in {"purlin", "primary_frame"}
    assert "eurocode" in result.code_reference_ids[0]
    assert any(row.row_id == "purlin_strength_ratio" for row in result.calculation_rows)
    assert any(row.row_id == "purlin_deflection_ratio" for row in result.calculation_rows)


def test_low_load_aisc_case_still_carries_portal_frame_basis_on_screening_pass() -> None:
    base_case = _level_b_case("aisc")
    case = base_case.model_copy(
        update={
            "pv_load": base_case.pv_load.model_copy(
                update={
                    "added_dead_load_kpa": 0.10,
                }
            )
        }
    )

    result = run_portal_frame_screening(case)

    assert result.conclusion_status == "screening_pass"
    assert "aisc_portal_frame_purlin_screening" in result.code_reference_ids


def test_formal_review_required_case_is_controlled_by_purlin() -> None:
    base_case = _level_b_case()
    case = base_case.model_copy(
        update={
            "pv_load": base_case.pv_load.model_copy(
                update={
                    "added_dead_load_kpa": 0.17,
                }
            )
        }
    )

    result = run_portal_frame_screening(case)

    assert result.conclusion_status == "formal_review_required"
    assert result.controlling_component == "purlin"
    assert result.controlling_path == "purlin_deflection"


def test_primary_frame_rows_expose_screening_formula_chain() -> None:
    result = run_portal_frame_screening(_level_b_case())

    assert any(row.row_id == "primary_frame_line_load" for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_added_moment_proxy" for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_column_added_moment_proxy" for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_rafter_reference_moment_proxy" for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_rafter_screening_ratio" for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_rafter_deflection_sensitivity" for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_column_reference_moment_proxy" for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_column_screening_ratio" for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_column_stability_sensitivity" for row in result.calculation_rows)
    assert any(row.row_id == "primary_frame_reference_moment_proxy" for row in result.calculation_rows)
    assert any(
        row.row_id == "primary_frame_screening_ratio"
        and "M_add / M_ref" in (row.formula_en or "")
        for row in result.calculation_rows
    )
    assert any(
        row.row_id == "primary_frame_column_added_moment_proxy"
        and "h_e" in (row.formula_en or "")
        for row in result.calculation_rows
    )


def test_longer_span_increases_rafter_deflection_sensitivity_proxy() -> None:
    base_case = _level_b_case()
    longer_span_case = base_case.model_copy(
        update={
            "geometry": base_case.geometry.model_copy(update={"span_m": 36.0}),
        }
    )

    base_result = run_portal_frame_screening(base_case)
    longer_result = run_portal_frame_screening(longer_span_case)

    base_proxy = next(
        row.numeric_value for row in base_result.calculation_rows if row.row_id == "primary_frame_rafter_deflection_sensitivity"
    )
    longer_proxy = next(
        row.numeric_value for row in longer_result.calculation_rows if row.row_id == "primary_frame_rafter_deflection_sensitivity"
    )

    assert (longer_proxy or 0) > (base_proxy or 0)


def test_taller_column_increases_column_stability_sensitivity_proxy() -> None:
    base_case = _level_b_case()
    taller_case = base_case.model_copy(
        update={
            "geometry": base_case.geometry.model_copy(update={"eave_height_m": 12.0}),
        }
    )

    base_result = run_portal_frame_screening(base_case)
    taller_result = run_portal_frame_screening(taller_case)

    base_proxy = next(
        row.numeric_value for row in base_result.calculation_rows if row.row_id == "primary_frame_column_stability_sensitivity"
    )
    taller_proxy = next(
        row.numeric_value for row in taller_result.calculation_rows if row.row_id == "primary_frame_column_stability_sensitivity"
    )

    assert (taller_proxy or 0) > (base_proxy or 0)


def test_33m_span_boundary_increases_rafter_deflection_sensitivity_against_30m_case() -> None:
    base_case = _level_b_case()
    boundary_case = base_case.model_copy(
        update={
            "geometry": base_case.geometry.model_copy(update={"span_m": 33.0}),
        }
    )

    base_result = run_portal_frame_screening(base_case)
    boundary_result = run_portal_frame_screening(boundary_case)

    base_proxy = next(
        row.numeric_value for row in base_result.calculation_rows if row.row_id == "primary_frame_rafter_deflection_sensitivity"
    )
    boundary_proxy = next(
        row.numeric_value for row in boundary_result.calculation_rows if row.row_id == "primary_frame_rafter_deflection_sensitivity"
    )

    assert (boundary_proxy or 0) > (base_proxy or 0)


def test_weak_rafter_case_is_controlled_by_primary_frame_member_proxy() -> None:
    base_case = _level_b_case()
    case = base_case.model_copy(
        update={
            "primary_frame": base_case.primary_frame.model_copy(
                update={
                    "rafter_section": "250x125x6x8 welded rafter",
                }
            )
        }
    )

    result = run_portal_frame_screening(case)

    assert result.controlling_component == "primary_frame"
    assert result.controlling_path == "primary_frame_rafter"
    assert any(
        row.row_id == "primary_frame_rafter_screening_ratio"
        and (row.numeric_value or 0) > 1.13
        for row in result.calculation_rows
    )


def test_tall_weak_column_case_surfaces_column_screening_proxy() -> None:
    base_case = _level_b_case()
    case = base_case.model_copy(
        update={
            "geometry": base_case.geometry.model_copy(update={"eave_height_m": 12.0}),
            "primary_frame": base_case.primary_frame.model_copy(
                update={
                    "column_section": "200x100x6x8 welded column",
                }
            ),
        }
    )

    result = run_portal_frame_screening(case)

    column_ratio = next(
        row.numeric_value for row in result.calculation_rows if row.row_id == "primary_frame_column_screening_ratio"
    )
    rafter_ratio = next(
        row.numeric_value for row in result.calculation_rows if row.row_id == "primary_frame_rafter_screening_ratio"
    )

    assert result.controlling_component == "primary_frame"
    assert result.controlling_path == "primary_frame_column"
    assert (column_ratio or 0) > (rafter_ratio or 0)


def test_lower_steel_grade_increases_primary_frame_screening_ratios() -> None:
    q355_case = _level_b_case()
    q235_case = q355_case.model_copy(
        update={
            "primary_frame": q355_case.primary_frame.model_copy(update={"steel_grade": "Q235"}),
        }
    )

    q355_result = run_portal_frame_screening(q355_case)
    q235_result = run_portal_frame_screening(q235_case)

    q355_rafter_ratio = next(
        row.numeric_value for row in q355_result.calculation_rows if row.row_id == "primary_frame_rafter_screening_ratio"
    )
    q235_rafter_ratio = next(
        row.numeric_value for row in q235_result.calculation_rows if row.row_id == "primary_frame_rafter_screening_ratio"
    )
    q355_column_ratio = next(
        row.numeric_value for row in q355_result.calculation_rows if row.row_id == "primary_frame_column_screening_ratio"
    )
    q235_column_ratio = next(
        row.numeric_value for row in q235_result.calculation_rows if row.row_id == "primary_frame_column_screening_ratio"
    )

    assert (q235_rafter_ratio or 0) > (q355_rafter_ratio or 0)
    assert (q235_column_ratio or 0) > (q355_column_ratio or 0)
