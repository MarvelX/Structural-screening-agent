from structural_screening_agent.core.calculators import get_portal_frame_calculator
from structural_screening_agent.core.calculators.base import PortalFrameScreeningResult
from structural_screening_agent.core.domain import PortalFrameScreeningCase


def run_portal_frame_screening(case: PortalFrameScreeningCase) -> PortalFrameScreeningResult:
    if case.evidence.screening_level == "level_c":
        return PortalFrameScreeningResult(
            conclusion_status="insufficient_evidence",
            screening_level=case.evidence.screening_level,
            code_path=case.code_context.standard,
            calculation_summary="Evidence is insufficient for portal-frame calculation.",
            calculation_rows=[],
        )

    calculator = get_portal_frame_calculator(case.code_context.standard)
    result = calculator.calculate(case)
    return result.model_copy(
        update={
            "screening_level": case.evidence.screening_level,
            "code_path": case.code_context.standard,
        }
    )
