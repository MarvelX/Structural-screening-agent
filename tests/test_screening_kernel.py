from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.calculators.base import CalculationRow, PortalFrameScreeningResult
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.demo_data import main_demo_case


def test_kernel_returns_conditional_go_with_basis_ids_and_trace_refs() -> None:
    outcome = evaluate_screening_case(from_building_intake(main_demo_case()))

    assert outcome.decision.status == "conditional_go"
    assert outcome.decision.confidence == "medium"
    assert outcome.controlling_path is not None
    assert outcome.controlling_path.path_id == "purlin_deflection"
    assert outcome.controlling_path.category == "member"
    assert len(outcome.assumption_ledger) >= 3
    assert any(item.assumption_id == "screening_scope_boundary" for item in outcome.assumption_ledger)
    assert any(item.assumption_id == "site_survey_unverified" for item in outcome.assumption_ledger)
    assert any(item.evidence_id == "member_drawings" and item.status == "available" for item in outcome.evidence_snapshot)
    assert any(item.evidence_id == "site_survey" and item.status == "missing" for item in outcome.evidence_snapshot)
    assert any(item.calc_id == "verification_readiness_score" and item.numeric_value == 55 for item in outcome.calc_outputs)
    assert any(item.calc_id == "uncertainty_score" and item.numeric_value == 85 for item in outcome.calc_outputs)
    assert outcome.reserve_screening.status == "review"
    assert outcome.attachment_screening.status == "screen_pass"
    assert len(outcome.engineering_checks) == 2
    assert any(item.check_id == "reserve_screening" and item.status == "review" for item in outcome.engineering_checks)
    assert any(item.check_id == "attachment_screening" and item.status == "screen_pass" for item in outcome.engineering_checks)
    assert outcome.verification_readiness.level == "partial"
    assert any("connection detail" in blocker.title_en.lower() for blocker in outcome.verification_readiness.blockers)
    assert outcome.uncertainty_assessment.overall == "high"
    assert any(component.component == "evidence_completeness" for component in outcome.uncertainty_assessment.components)
    assert len(outcome.member_reserve_uncertainties) >= 4
    assert any(item.severity == "high" for item in outcome.member_reserve_uncertainties)
    assert len(outcome.attachment_pathways) == 4
    assert all(item.status == "review" for item in outcome.attachment_pathways)
    assert any(item.category == "connection" for item in outcome.review_triggers)
    assert any(item.phase == "later" for item in outcome.recommended_actions)
    assert len(outcome.resource_recommendations) >= 3
    assert any("structural engineer" in item.title_en.lower() for item in outcome.resource_recommendations)
    assert any("roof system" in item.title_en.lower() for item in outcome.resource_recommendations)
    assert any(item.rule_id == "gb_portal_frame_purlin_screening" for item in outcome.triggered_rules)
    assert any(item.rule_id == "gb_portal_frame_purlin_screening" and "gb_portal_frame_purlin_screening" in item.basis_ids for item in outcome.triggered_rules)
    assert any(item.basis_id == "gb_portal_frame_purlin_screening" and "gb" in item.applicable_standards for item in outcome.basis_references)
    assert outcome.load_combination_sensitivities
    assert any("风" in item.summary_zh or "雪" in item.summary_zh for item in outcome.load_combination_sensitivities)
    assert outcome.findings
    assert any(finding.basis_ids for finding in outcome.findings)
    assert any(
        trace.input_path == "portal_frame.purlin_strength_ratio"
        for finding in outcome.findings
        for trace in finding.traces
    )
    assert any(
        trace.input_path == "portal_frame.controlling_path"
        for finding in outcome.findings
        for trace in finding.traces
    )


def test_kernel_records_conservative_steel_grade_assumption_when_missing() -> None:
    intake = main_demo_case().model_copy(update={"steel_grade": None})

    outcome = evaluate_screening_case(from_building_intake(intake))

    assert any(item.assumption_id == "steel_grade_conservative_default" for item in outcome.assumption_ledger)
    assert any("Q235" in item.summary_zh for item in outcome.assumption_ledger if item.assumption_id == "steel_grade_conservative_default")


def test_kernel_returns_go_when_verification_path_and_roof_geometry_are_closed() -> None:
    intake = main_demo_case().model_copy(
        update={
            "estimated_added_load_kpa": 0.10,
            "roof_panel_thickness_mm": 0.7,
            "roof_rib_height_mm": 76.0,
                "drawing_availability": "complete",
                "survey_available": True,
                "available_verification_path": "drawings_plus_survey",
                "existing_member_schedule_status": "available",
                "connection_detail_status": "available",
                "roof_vendor_data_status": "available",
                "corrosion_condition": "low",
            }
        )

    outcome = evaluate_screening_case(from_building_intake(intake))

    assert outcome.decision.status == "go"
    assert outcome.decision.confidence == "high"
    assert any(item.evidence_id == "site_survey" and item.status == "available" for item in outcome.evidence_snapshot)
    assert any(item.calc_id == "verification_readiness_score" and item.numeric_value == 85 for item in outcome.calc_outputs)
    assert outcome.reserve_screening.status == "screen_pass"
    assert outcome.attachment_screening.status == "screen_pass"
    assert all(item.status == "screen_pass" for item in outcome.engineering_checks)
    assert outcome.verification_readiness.level == "ready"
    assert not outcome.verification_readiness.blockers
    assert outcome.uncertainty_assessment.overall == "low"
    assert any(item.severity == "low" for item in outcome.member_reserve_uncertainties if item.component == "evidence_completeness")
    assert any(item.status == "screen_pass" for item in outcome.attachment_pathways if item.pathway == "clamp_based")
    assert len(outcome.review_triggers) <= 1
    assert any(item.phase == "later" for item in outcome.recommended_actions)
    assert not any("site survey" in item.title_en.lower() for item in outcome.resource_recommendations)
    assert any(item.rule_id == "gb_portal_frame_purlin_screening" and item.severity == "info" for item in outcome.triggered_rules)
    assert any(item.basis_id == "gb_portal_frame_purlin_screening" for item in outcome.basis_references)
    assert not outcome.findings


def test_kernel_load_combination_sensitivity_mentions_wind_for_column_governing_case() -> None:
    intake = main_demo_case().model_copy(
        update={
            "eave_height_m": 12.0,
            "column_section": "200x100x6x8 welded column",
        }
    )

    outcome = evaluate_screening_case(from_building_intake(intake))

    assert outcome.controlling_path is not None
    assert outcome.controlling_path.path_id == "primary_frame_column"
    assert outcome.load_combination_sensitivities
    assert any("风" in item.summary_zh and "主门架柱" in item.summary_zh for item in outcome.load_combination_sensitivities)


def test_kernel_estimates_critical_added_load_and_remaining_margin() -> None:
    intake = main_demo_case().model_copy(
        update={
            "estimated_added_load_kpa": 0.10,
            "roof_panel_thickness_mm": 0.7,
            "roof_rib_height_mm": 76.0,
            "drawing_availability": "complete",
            "survey_available": True,
            "available_verification_path": "drawings_plus_survey",
            "existing_member_schedule_status": "available",
            "connection_detail_status": "available",
            "roof_vendor_data_status": "available",
            "corrosion_condition": "low",
        }
    )

    outcome = evaluate_screening_case(from_building_intake(intake))

    critical_load = next(item for item in outcome.calc_outputs if item.calc_id == "critical_added_load_kpa")
    remaining_margin = next(
        item for item in outcome.calc_outputs if item.calc_id == "remaining_added_load_margin_kpa"
    )

    assert critical_load.numeric_value == 0.16
    assert critical_load.unit == "kPa"
    assert critical_load.formula_en is not None and "q_crit" in critical_load.formula_en
    assert remaining_margin.numeric_value == 0.06
    assert remaining_margin.unit == "kPa"
    assert remaining_margin.formula_en is not None and "q_margin" in remaining_margin.formula_en


def test_kernel_load_combination_sensitivity_carries_standard_specific_route_labels() -> None:
    labels = {
        "gb": "国标 GB",
        "aisc": "AISC / ASCE",
        "eurocode": "Eurocode",
    }

    for standard, label in labels.items():
        intake = main_demo_case().model_copy(update={"design_standard_context": standard})

        outcome = evaluate_screening_case(from_building_intake(intake))

        assert outcome.load_combination_sensitivities
        assert any(label in item.summary_zh for item in outcome.load_combination_sensitivities)


def test_kernel_exposes_gb_portal_frame_purlin_screening_outputs_for_level_b_case() -> None:
    intake = main_demo_case().model_copy(
        update={
            "drawing_availability": "complete",
            "existing_member_schedule_status": "available",
            "survey_available": False,
            "connection_detail_status": "partial",
            "roof_vendor_data_status": "missing",
        }
    )
    case = from_building_intake(intake)

    assert case.evidence.screening_level == "level_b"

    outcome = evaluate_screening_case(case)

    assert outcome.controlling_path is not None
    assert outcome.controlling_path.path_id == "purlin_deflection"
    assert any(item.calc_id == "purlin_strength_ratio" and item.numeric_value is not None for item in outcome.calc_outputs)
    assert any(item.calc_id == "purlin_deflection_ratio" and item.numeric_value is not None for item in outcome.calc_outputs)
    assert any(item.rule_id == "gb_portal_frame_purlin_screening" for item in outcome.triggered_rules)
    assert any(item.basis_id == "gb_portal_frame_purlin_screening" for item in outcome.basis_references)
    assert any(finding.finding_id == "gb_portal_frame_purlin_screening" for finding in outcome.findings)


def test_framing_module_uncertainty_steps_up_at_33m_boundary() -> None:
    base_intake = main_demo_case().model_copy(
        update={
            "building_span_m": 30.0,
            "column_spacing_m": 8.0,
        }
    )
    boundary_intake = base_intake.model_copy(
        update={
            "building_span_m": 33.0,
            "column_spacing_m": 8.5,
        }
    )

    base_outcome = evaluate_screening_case(from_building_intake(base_intake))
    boundary_outcome = evaluate_screening_case(from_building_intake(boundary_intake))

    base_framing = next(
        item for item in base_outcome.member_reserve_uncertainties if item.component == "framing_module"
    )
    boundary_framing = next(
        item for item in boundary_outcome.member_reserve_uncertainties if item.component == "framing_module"
    )

    assert base_framing.severity == "medium"
    assert boundary_framing.severity == "high"


def test_large_span_parallel_action_only_appears_at_33m_and_8p5m_boundary() -> None:
    below_boundary = main_demo_case().model_copy(
        update={
            "building_span_m": 32.9,
            "column_spacing_m": 8.4,
            "drawing_availability": "partial",
        }
    )
    at_boundary = below_boundary.model_copy(
        update={
            "building_span_m": 33.0,
            "column_spacing_m": 8.5,
        }
    )

    below_outcome = evaluate_screening_case(from_building_intake(below_boundary))
    boundary_outcome = evaluate_screening_case(from_building_intake(at_boundary))

    assert not any("框架模数" in item.title_zh for item in below_outcome.recommended_actions)
    assert any("框架模数" in item.title_zh for item in boundary_outcome.recommended_actions)


def test_load_combination_sensitivity_uses_standard_specific_route_labels() -> None:
    aisc_outcome = evaluate_screening_case(
        from_building_intake(main_demo_case().model_copy(update={"design_standard_context": "aisc"}))
    )
    eurocode_outcome = evaluate_screening_case(
        from_building_intake(main_demo_case().model_copy(update={"design_standard_context": "eurocode"}))
    )

    assert any("AISC / ASCE" in item.summary_en for item in aisc_outcome.load_combination_sensitivities)
    assert any("Eurocode" in item.summary_en for item in eurocode_outcome.load_combination_sensitivities)


def test_kernel_skips_gb_purlin_finding_when_ratio_rows_are_missing(monkeypatch) -> None:
    from structural_screening_agent.core import kernel

    intake = main_demo_case().model_copy(
        update={
            "drawing_availability": "complete",
            "existing_member_schedule_status": "available",
            "survey_available": False,
            "connection_detail_status": "partial",
            "roof_vendor_data_status": "missing",
        }
    )
    case = from_building_intake(intake)

    def fake_run_portal_frame_screening(_case):
        return PortalFrameScreeningResult(
            conclusion_status="formal_review_required",
            screening_level="level_b",
            code_path="gb",
            calculation_summary="calculator result without ratio rows",
            calculation_rows=[
                CalculationRow(
                    row_id="tributary_load",
                    numeric_value=0.26,
                    value_text="0.26",
                    unit="kN/m",
                    label_en="Tributary line load",
                    label_zh="檩条分担线荷载",
                )
            ],
            controlling_component="purlin",
            controlling_path="purlin_strength",
            code_reference_ids=["gb_portal_frame_purlin_screening"],
        )

    monkeypatch.setattr(kernel, "run_portal_frame_screening", fake_run_portal_frame_screening)

    outcome = evaluate_screening_case(case)

    assert any(item.calc_id == "tributary_load" and item.numeric_value == 0.26 for item in outcome.calc_outputs)
    assert not any(item.rule_id == "gb_portal_frame_purlin_screening" for item in outcome.triggered_rules)
    assert not any(item.basis_id == "gb_portal_frame_purlin_screening" for item in outcome.basis_references)
    assert not any(finding.finding_id == "gb_portal_frame_purlin_screening" for finding in outcome.findings)
