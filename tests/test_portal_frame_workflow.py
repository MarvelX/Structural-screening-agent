import subprocess

from structural_screening_agent.core.calculators.base import CalculationRow, PortalFrameScreeningResult
from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.demo_data import main_demo_case


def test_portal_frame_module_imports_under_python_39() -> None:
    completed = subprocess.run(
        [
            "python3",
            "-c",
            "import structural_screening_agent.core.portal_frame as m; print(m.run_portal_frame_screening.__name__)",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "run_portal_frame_screening" in completed.stdout


def test_portal_frame_screening_routes_level_b_cases_to_standard_calculator() -> None:
    from structural_screening_agent.core import portal_frame

    class BadMetadataCalculator:
        standard = "aisc"

        def calculate(self, case):
            return PortalFrameScreeningResult(
                conclusion_status="calculator_result",
                screening_level="level_a",
                code_path="eurocode",
                calculation_summary="bad metadata from calculator",
                calculation_rows=[CalculationRow(label="source", value="calculator")],
            )

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
    original_router = portal_frame.get_portal_frame_calculator
    portal_frame.get_portal_frame_calculator = lambda standard: BadMetadataCalculator()
    try:
        result = portal_frame.run_portal_frame_screening(case)
    finally:
        portal_frame.get_portal_frame_calculator = original_router

    assert case.evidence.screening_level == "level_b"
    assert result.conclusion_status == "calculator_result"
    assert result.code_path == "gb"
    assert result.screening_level == "level_b"
    assert result.calculation_summary
    assert result.calculation_rows


def test_portal_frame_screening_stops_on_level_c_evidence_insufficiency() -> None:
    from structural_screening_agent.core.portal_frame import run_portal_frame_screening

    intake = main_demo_case().model_copy(
        update={
            "drawing_availability": "missing",
            "existing_member_schedule_status": "missing",
            "survey_available": False,
        }
    )

    case = from_building_intake(intake)
    result = run_portal_frame_screening(case)

    assert case.evidence.screening_level == "level_c"
    assert result.conclusion_status == "insufficient_evidence"
    assert result.code_path == case.code_context.standard
    assert result.screening_level == "level_c"
    assert result.calculation_rows == []
    assert "insufficient" in result.calculation_summary.lower()
