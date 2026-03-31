from typing import List

from structural_screening_agent.localization import Language, translate, translate_option
from structural_screening_agent.models import BuildingIntake


def build_screening_snapshot(intake: BuildingIntake, language: Language) -> List[str]:
    if intake.project_type != "rooftop_pv":
        return []

    items = []
    if intake.building_span_m is not None:
        items.append(f"{translate(language, 'building_span')}: {intake.building_span_m:.1f} m")
    if intake.column_spacing_m is not None:
        items.append(f"{translate(language, 'column_spacing')}: {intake.column_spacing_m:.1f} m")
    if intake.purlin_type:
        items.append(
            f"{translate(language, 'purlin_type')}: {translate_option(language, 'purlin_type', intake.purlin_type)}"
        )
    if intake.roof_panel_type:
        items.append(
            f"{translate(language, 'roof_panel_type')}: {translate_option(language, 'roof_panel_type', intake.roof_panel_type)}"
        )
    if intake.corrosion_condition:
        items.append(
            f"{translate(language, 'corrosion_condition')}: "
            f"{translate_option(language, 'corrosion_condition', intake.corrosion_condition)}"
        )
    items.append(
        f"{translate(language, 'verification_path')}: "
        f"{translate_option(language, 'available_verification_path', intake.available_verification_path)}"
    )
    return items
