from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.decision_agent import build_follow_up_questions
from structural_screening_agent.models import BuildingIntake, DecisionStatus, ScreeningResult, VerificationReadiness


def test_metal_roof_pv_case_requests_rib_height_and_panel_thickness() -> None:
    intake = BuildingIntake(
        project_type="rooftop_pv",
        building_type="existing warehouse",
        structural_system="steel portal frame",
        roof_type="profiled steel sheet",
        intended_modification="distributed rooftop pv",
        estimated_added_load_kpa=0.18,
        shutdown_constraint="limited",
        drawing_availability="partial",
        survey_available=False,
        roof_panel_thickness_mm=None,
        roof_rib_height_mm=None,
    )
    result = ScreeningResult(
        status=DecisionStatus.CONDITIONAL_GO,
        confidence="medium",
        risks=[],
        missing_data=[],
        recommended_actions=[],
        options=[],
        verification_readiness=VerificationReadiness(
            level="partial",
            summary_en="Partial readiness",
            summary_zh="部分具备",
        ),
    )

    questions = build_follow_up_questions(intake, result, language="zh")

    assert any("波峰高度" in question for question in questions)
    assert any("板厚" in question for question in questions)


def test_follow_up_questions_escalate_when_verification_route_and_purlin_are_unknown() -> None:
    intake = BuildingIntake(
        project_type="rooftop_pv",
        building_type="existing warehouse",
        structural_system="steel portal frame",
        roof_type="profiled steel sheet",
        intended_modification="distributed rooftop pv",
        estimated_added_load_kpa=0.18,
        purlin_type="unknown",
        available_verification_path="no_viable_path_yet",
        shutdown_constraint="limited",
        drawing_availability="partial",
        survey_available=False,
        roof_panel_thickness_mm=0.6,
        roof_rib_height_mm=76.0,
    )
    result = ScreeningResult(
        status=DecisionStatus.NO_GO,
        confidence="low",
        risks=[],
        missing_data=[],
        recommended_actions=[],
        options=[],
        verification_readiness=VerificationReadiness(
            level="not_ready",
            summary_en="Not ready",
            summary_zh="尚不具备",
        ),
    )

    questions = build_follow_up_questions(intake, result, language="zh")

    assert any("复核路径" in question for question in questions)
    assert any("檩条形式" in question for question in questions)


def test_follow_up_questions_explain_why_connection_questions_are_asked() -> None:
    intake = BuildingIntake(
        project_type="rooftop_pv",
        design_standard_context="gb",
        building_type="existing warehouse",
        structural_system="steel portal frame",
        roof_type="metal roof",
        intended_modification="distributed rooftop pv",
        estimated_added_load_kpa=0.18,
        roof_panel_type="profiled_sheet",
        roof_panel_thickness_mm=None,
        roof_rib_height_mm=None,
        roof_attachment_preference="clamp_based",
        connection_detail_status="missing",
        roof_vendor_data_status="missing",
        shutdown_constraint="limited",
        drawing_availability="complete",
        survey_available=False,
    )
    result = ScreeningResult(
        status=DecisionStatus.CONDITIONAL_GO,
        confidence="medium",
        risks=[],
        missing_data=[],
        recommended_actions=[],
        options=[],
        verification_readiness=VerificationReadiness(
            level="partial",
            summary_en="Partial readiness",
            summary_zh="部分具备",
        ),
    )
    kernel_outcome = evaluate_screening_case(from_building_intake(intake))

    questions = build_follow_up_questions(intake, result, language="zh", kernel_outcome=kernel_outcome)

    assert any("锁边" in question or "夹具" in question for question in questions)
    assert any("为什么问这个" in question for question in questions)


def test_follow_up_questions_shift_to_primary_frame_sensitive_inputs_when_rafter_governs() -> None:
    intake = BuildingIntake(
        project_type="rooftop_pv",
        design_standard_context="gb",
        building_type="existing warehouse",
        structural_system="steel portal frame",
        roof_type="metal roof",
        intended_modification="distributed rooftop pv",
        estimated_added_load_kpa=0.18,
        building_span_m=30.0,
        column_spacing_m=8.0,
        eave_height_m=8.0,
        rafter_section="250x125x6x8 welded rafter",
        column_section="305x305x10x15 welded column",
        steel_grade="Q355",
        purlin_spacing_m=1.5,
        purlin_type="cold_formed_z",
        roof_panel_type="profiled_sheet",
        roof_panel_thickness_mm=0.6,
        roof_rib_height_mm=75.0,
        roof_attachment_preference="clamp_based",
        existing_member_schedule_status="available",
        connection_detail_status="available",
        roof_vendor_data_status="available",
        corrosion_condition="low",
        waterproofing_sensitivity="high",
        available_verification_path="drawings_plus_survey",
        shutdown_constraint="limited",
        drawing_availability="complete",
        survey_available=True,
    )
    result = ScreeningResult(
        status=DecisionStatus.CONDITIONAL_GO,
        confidence="medium",
        risks=[],
        missing_data=[],
        recommended_actions=[],
        options=[],
        verification_readiness=VerificationReadiness(
            level="partial",
            summary_en="Partial readiness",
            summary_zh="部分具备",
        ),
    )
    kernel_outcome = evaluate_screening_case(from_building_intake(intake))

    questions = build_follow_up_questions(intake, result, language="zh", kernel_outcome=kernel_outcome)

    assert any("门架梁截面" in question or "檐口高度" in question or "跨度" in question for question in questions)
    assert any("为什么问这个" in question and "主门架梁" in question for question in questions)
