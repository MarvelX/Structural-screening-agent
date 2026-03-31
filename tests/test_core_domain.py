from structural_screening_agent.core.domain import (
    EvidenceProfile,
    GeometryProfile,
    ModificationScope,
    ProjectProfile,
    RoofProfile,
    ScreeningCase,
    VerificationContext,
    from_building_intake,
)
from structural_screening_agent.demo_data import main_demo_case


def test_screening_case_groups_inputs_into_stable_domain_sections() -> None:
    case = from_building_intake(main_demo_case())

    assert case.project.project_type == "rooftop_pv"
    assert case.project.building_type == "existing warehouse"
    assert case.modification.estimated_added_load_kpa == 0.18
    assert case.geometry.building_span_m == 30.0
    assert case.roof.attachment_preference == "clamp_based"
    assert case.evidence.member_schedule_status == "missing"
    assert case.verification.available_path == "drawings_only"


def test_screening_case_requires_explicit_nested_sections() -> None:
    case = ScreeningCase(
        project=ProjectProfile(
            project_type="retrofit",
            design_standard="gb",
            building_type="plant",
            structural_system="steel",
            roof_type="metal roof",
        ),
        modification=ModificationScope(
            intended_modification="equipment upgrade",
            estimated_added_load_kpa=0.22,
        ),
        geometry=GeometryProfile(building_span_m=24.0, column_spacing_m=8.0, purlin_type="z"),
        roof=RoofProfile(
            panel_type="profiled_sheet",
            panel_thickness_mm=0.7,
            rib_height_mm=76.0,
            attachment_preference="clamp_based",
            waterproofing_sensitivity="medium",
            restricted_installation_zones="",
        ),
        evidence=EvidenceProfile(
            drawing_availability="complete",
            survey_available=True,
            member_schedule_status="available",
            connection_detail_status="available",
            roof_vendor_data_status="available",
        ),
        verification=VerificationContext(
            corrosion_condition="low",
            shutdown_constraint="none",
            available_path="drawings_plus_survey",
        ),
    )

    assert case.project.design_standard == "gb"
    assert case.evidence.survey_available is True
