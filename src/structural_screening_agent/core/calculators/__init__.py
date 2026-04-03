from typing import Literal

from structural_screening_agent.core.calculators.aisc_portal_frame import AISCPortalFrameCalculator
from structural_screening_agent.core.calculators.base import PortalFrameCalculator
from structural_screening_agent.core.calculators.eurocode_portal_frame import EurocodePortalFrameCalculator
from structural_screening_agent.core.calculators.gb_portal_frame import GBPortalFrameCalculator


_CALCULATOR_BY_STANDARD = {
    "gb": GBPortalFrameCalculator(),
    "aisc": AISCPortalFrameCalculator(),
    "eurocode": EurocodePortalFrameCalculator(),
}


def get_portal_frame_calculator(standard: Literal["gb", "aisc", "eurocode"]) -> PortalFrameCalculator:
    try:
        return _CALCULATOR_BY_STANDARD[standard]
    except KeyError as exc:
        raise ValueError(f"Unsupported portal-frame design standard: {standard}") from exc
