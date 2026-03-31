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
