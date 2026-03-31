from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.rule_engine import evaluate_screening


def test_partial_drawings_and_no_survey_yield_conditional_go() -> None:
    result = evaluate_screening(main_demo_case())
    assert result.status.value == "conditional_go"
    assert result.confidence == "medium"
    assert result.traceability
    assert any("gb_50017_general" in item.basis_ids for item in result.traceability)
    assert any(
        trace.input_path == "roof.panel_thickness_mm"
        for item in result.traceability
        for trace in item.traces
    )
    assert result.verification_readiness.level == "partial"
    assert result.engineering_checks[0].title_en == "Reserve Capacity Screening"
    assert result.engineering_checks[0].status == "review"
    assert result.engineering_checks[1].title_en == "Attachment Feasibility Screening"
    assert result.engineering_checks[1].status == "undetermined"
    assert len(result.attachment_pathways) == 4
    assert any("clamp-based" in item.title_en.lower() for item in result.attachment_pathways)
    assert any("penetrating" in item.title_en.lower() for item in result.attachment_pathways)
    assert any("vendor-confirmed" in item.title_en.lower() for item in result.attachment_pathways)
    assert any(item.status == "undetermined" for item in result.attachment_pathways)
    assert any(item.category == "member" for item in result.review_triggers)
    assert any(item.category == "connection" for item in result.review_triggers)
    assert any("added load" in item.summary_en.lower() for item in result.review_triggers if item.category == "member")
    assert any("rib height" in item.summary_en.lower() for item in result.review_triggers if item.category == "connection")
    assert any("reserve capacity" in risk.title_en.lower() for risk in result.risks)
    assert any("gb 50017" in item.title_en.lower() for item in result.review_required)
    assert any("survey" in item.title_en.lower() for item in result.missing_data)
    assert any("member schedule" in item.title_en.lower() for item in result.verification_readiness.blockers)
    assert any("connection detail" in item.title_en.lower() for item in result.verification_readiness.blockers)
    assert len(result.member_reserve_uncertainties) >= 4
    assert any(item.severity == "high" for item in result.member_reserve_uncertainties)
    assert any("load demand" in item.title_en.lower() for item in result.member_reserve_uncertainties)
    assert any("evidence completeness" in item.title_en.lower() for item in result.member_reserve_uncertainties)
    assert any("framing module" in item.title_en.lower() for item in result.member_reserve_uncertainties)
    assert any("condition state" in item.title_en.lower() for item in result.member_reserve_uncertainties)
    assert any("structural verification" in item.title_en.lower() for item in result.recommended_actions)
    assert any(item.phase == "must_do" for item in result.recommended_actions)
    assert any(item.phase == "parallel" for item in result.recommended_actions)
    assert any(item.phase == "later" for item in result.recommended_actions)
    assert len(result.resource_recommendations) >= 3
    assert any("structural engineer" in item.title_en.lower() for item in result.resource_recommendations)
    assert any("roof system" in item.title_en.lower() for item in result.resource_recommendations)
    assert any("site survey" in item.title_en.lower() for item in result.resource_recommendations)
    assert len(result.options) >= 2


def test_aisc_context_generates_review_needed_note() -> None:
    intake = main_demo_case().model_copy(update={"design_standard_context": "aisc"})
    result = evaluate_screening(intake)
    assert any("aisc 360" in item.title_en.lower() for item in result.review_required)


def test_missing_drawings_and_strict_shutdown_can_trigger_no_go() -> None:
    intake = main_demo_case().model_copy(
        update={"drawing_availability": "missing", "shutdown_constraint": "strict"}
    )
    result = evaluate_screening(intake)
    assert result.status.value == "no_go"


def test_no_viable_verification_path_for_main_demo_triggers_no_go() -> None:
    intake = main_demo_case().model_copy(
        update={
            "available_verification_path": "no_viable_path_yet",
            "drawing_availability": "missing",
            "survey_available": False,
        }
    )
    result = evaluate_screening(intake)
    assert result.status.value == "no_go"
    assert result.confidence == "low"
    assert result.verification_readiness.level == "not_ready"
    assert any("verification path" in risk.title_en.lower() for risk in result.risks)
    assert any("verification route" in item.title_en.lower() for item in result.recommended_actions)


def test_main_demo_flags_roof_attachment_uncertainty_when_panel_details_missing() -> None:
    intake = main_demo_case().model_copy(
        update={
            "roof_panel_type": "profiled_sheet",
            "roof_attachment_preference": "clamp_based",
            "waterproofing_sensitivity": "high",
            "roof_panel_thickness_mm": None,
            "roof_rib_height_mm": None,
        }
    )
    result = evaluate_screening(intake)
    assert result.status.value == "conditional_go"
    attachment_risk = next(risk for risk in result.risks if "attachment path" in risk.title_en.lower())
    clamp_path = next(item for item in result.attachment_pathways if "clamp-based" in item.title_en.lower())
    assert "rib height" in attachment_risk.detail_en.lower()
    assert "板厚" in attachment_risk.detail_zh
    assert clamp_path.status == "undetermined"
    assert any("roof panel thickness" in item.title_en.lower() for item in result.missing_data)
    assert any("rib height" in item.title_en.lower() for item in result.missing_data)


def test_main_demo_options_include_structured_tradeoffs() -> None:
    result = evaluate_screening(main_demo_case())
    assert len(result.options) >= 3
    assert result.options[0].title_en == "Restricted-Zone Installation"
    assert "limited shutdown" in result.options[0].priority_rationale_en.lower()
    assert "phased" in result.options[0].fit_when_en.lower()
    assert result.options[0].cost_level_en == "Medium"
    assert result.options[1].schedule_impact_en == "High"
    assert "pause" in result.options[2].recommendation_note_en.lower()


def test_long_span_partial_data_increases_reserve_uncertainty() -> None:
    intake = main_demo_case().model_copy(
        update={
            "building_span_m": 36.0,
            "column_spacing_m": 9.0,
            "drawing_availability": "partial",
            "corrosion_condition": "moderate",
        }
    )
    result = evaluate_screening(intake)
    long_span_risk = next(risk for risk in result.risks if "long-span" in risk.title_en.lower())
    assert "36.0 m" in long_span_risk.detail_en
    assert "9.0 m" in long_span_risk.detail_en
    assert any("framing module" in item.title_en.lower() for item in result.recommended_actions)


def test_limited_shutdown_without_zone_strategy_adds_operational_risk() -> None:
    intake = main_demo_case().model_copy(
        update={
            "shutdown_constraint": "limited",
            "restricted_installation_zones": "",
        }
    )
    result = evaluate_screening(intake)
    assert any("operational disruption" in risk.title_en.lower() for risk in result.risks)
    assert any("restricted-zone" in item.title_en.lower() for item in result.recommended_actions)


def test_complete_data_can_screen_reserve_and_attachment_more_favorably() -> None:
    intake = main_demo_case().model_copy(
        update={
            "estimated_added_load_kpa": 0.10,
            "drawing_availability": "complete",
            "survey_available": True,
            "existing_member_schedule_status": "available",
            "connection_detail_status": "available",
            "roof_vendor_data_status": "available",
            "corrosion_condition": "low",
            "available_verification_path": "drawings_plus_survey",
            "roof_panel_thickness_mm": 0.7,
            "roof_rib_height_mm": 76.0,
            "waterproofing_sensitivity": "medium",
            "shutdown_constraint": "none",
        }
    )
    result = evaluate_screening(intake)
    reserve_check = next(item for item in result.engineering_checks if item.title_en == "Reserve Capacity Screening")
    connection_check = next(item for item in result.engineering_checks if item.title_en == "Attachment Feasibility Screening")
    clamp_path = next(item for item in result.attachment_pathways if "clamp-based" in item.title_en.lower())
    evidence_uncertainty = next(
        item for item in result.member_reserve_uncertainties if item.title_en == "Member Reserve Uncertainty: Evidence Completeness"
    )
    assert reserve_check.status == "screen_pass"
    assert connection_check.status == "screen_pass"
    assert clamp_path.status == "screen_pass"
    assert evidence_uncertainty.severity == "low"
    assert not any("site survey" in item.title_en.lower() for item in result.resource_recommendations)
    assert len(result.review_triggers) <= 1
