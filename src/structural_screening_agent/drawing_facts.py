from typing import List

from structural_screening_agent.localization import Language, translate, translate_option
from structural_screening_agent.models import BuildingIntake


def build_drawing_facts_summary(intake: BuildingIntake, language: Language) -> List[str]:
    items = [
        f"{translate(language, 'drawing_availability')}: "
        f"{translate_option(language, 'drawing_availability', intake.drawing_availability)}",
        f"{translate(language, 'structural_system')}: {intake.structural_system}",
        f"{translate(language, 'roof_type')}: {intake.roof_type}",
    ]
    if intake.project_type == "rooftop_pv":
        items.extend(
            [
                f"{translate(language, 'existing_member_schedule_status')}: "
                f"{translate_option(language, 'document_status', intake.existing_member_schedule_status)}",
                f"{translate(language, 'connection_detail_status')}: "
                f"{translate_option(language, 'document_status', intake.connection_detail_status)}",
                f"{translate(language, 'roof_vendor_data_status')}: "
                f"{translate_option(language, 'document_status', intake.roof_vendor_data_status)}",
            ]
        )
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
                f"{translate(language, 'roof_panel_type')}: "
                f"{translate_option(language, 'roof_panel_type', intake.roof_panel_type)}"
            )
        if intake.roof_panel_thickness_mm is not None:
            items.append(f"{translate(language, 'roof_panel_thickness')}: {intake.roof_panel_thickness_mm:.1f} mm")
        if intake.roof_rib_height_mm is not None:
            items.append(f"{translate(language, 'roof_rib_height')}: {intake.roof_rib_height_mm:.1f} mm")
    return items
