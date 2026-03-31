from structural_screening_agent.models import BuildingIntake


def main_demo_case() -> BuildingIntake:
    return BuildingIntake(
        project_type="rooftop_pv",
        building_type="existing warehouse",
        structural_system="steel portal frame",
        roof_type="metal roof",
        intended_modification="distributed rooftop pv",
        estimated_added_load_kpa=0.18,
        building_span_m=30.0,
        column_spacing_m=8.0,
        purlin_type="cold_formed_z",
        roof_panel_type="profiled_sheet",
        roof_panel_thickness_mm=None,
        roof_rib_height_mm=None,
        roof_attachment_preference="clamp_based",
        existing_member_schedule_status="missing",
        connection_detail_status="partial",
        roof_vendor_data_status="missing",
        corrosion_condition="moderate",
        waterproofing_sensitivity="high",
        restricted_installation_zones="skylights, smoke vents, and maintenance corridors",
        available_verification_path="drawings_only",
        shutdown_constraint="limited",
        drawing_availability="partial",
        survey_available=False,
    )


def warehouse_upgrade_case() -> BuildingIntake:
    return BuildingIntake(
        project_type="load_upgrade",
        building_type="existing logistics warehouse",
        structural_system="steel frame",
        roof_type="metal roof",
        intended_modification="add conveyor and mezzanine support load",
        estimated_added_load_kpa=0.12,
        building_span_m=24.0,
        column_spacing_m=8.0,
        purlin_type="cold_formed_z",
        roof_panel_type="profiled_sheet",
        roof_panel_thickness_mm=None,
        roof_rib_height_mm=None,
        roof_attachment_preference="undecided",
        existing_member_schedule_status="available",
        connection_detail_status="partial",
        roof_vendor_data_status="available",
        corrosion_condition="low",
        waterproofing_sensitivity="medium",
        restricted_installation_zones="existing conveyor clear zones",
        available_verification_path="drawings_plus_survey",
        shutdown_constraint="limited",
        drawing_availability="complete",
        survey_available=True,
    )


def industrial_retrofit_case() -> BuildingIntake:
    return BuildingIntake(
        project_type="retrofit",
        building_type="industrial production building",
        structural_system="steel-concrete composite",
        roof_type="insulated panel roof",
        intended_modification="partial line retrofit and use change",
        estimated_added_load_kpa=0.28,
        building_span_m=27.0,
        column_spacing_m=9.0,
        purlin_type=None,
        roof_panel_type="sandwich_panel",
        roof_panel_thickness_mm=None,
        roof_rib_height_mm=None,
        roof_attachment_preference="undecided",
        existing_member_schedule_status="missing",
        connection_detail_status="missing",
        roof_vendor_data_status="missing",
        corrosion_condition="unknown",
        waterproofing_sensitivity="medium",
        restricted_installation_zones="process equipment support zones",
        available_verification_path="no_viable_path_yet",
        shutdown_constraint="strict",
        drawing_availability="missing",
        survey_available=False,
    )


def all_demo_cases() -> dict[str, BuildingIntake]:
    return {
        "main_warehouse_pv": main_demo_case(),
        "warehouse_upgrade": warehouse_upgrade_case(),
        "industrial_retrofit": industrial_retrofit_case(),
    }
