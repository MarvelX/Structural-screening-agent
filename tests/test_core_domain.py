from structural_screening_agent.core.domain import (
    Building,
    ConnectionEvidence,
    LoadAssumptions,
    MemberEvidence,
    ReviewTask,
    RoofSystem,
    ScreeningCase,
    StandardsContext,
    from_building_intake,
)
from structural_screening_agent.demo_data import main_demo_case


def test_screening_case_groups_inputs_into_engineering_domain_objects() -> None:
    case = from_building_intake(main_demo_case())

    assert case.building.project_type == "rooftop_pv"
    assert case.building.building_type == "existing warehouse"
    assert case.building.building_span_m == 30.0
    assert case.geometry.eave_height_m == 8.0
    assert case.roof_system.attachment_preference == "clamp_based"
    assert case.member_evidence.member_schedule_status == "available"
    assert case.connection_evidence.available_verification_path == "drawings_only"
    assert case.load_assumptions.estimated_added_load_kpa == 0.18
    assert case.standards_context.design_standard == "gb"
    assert any(task.task_type == "site_survey" for task in case.review_tasks)
    assert any(task.task_type == "connection_review" for task in case.review_tasks)


def test_screening_case_requires_explicit_engineering_sections() -> None:
    case = ScreeningCase(
        building=Building(
            project_type="retrofit",
            building_type="plant",
            structural_system="steel",
            roof_type="metal roof",
            building_span_m=24.0,
            column_spacing_m=8.0,
            purlin_type="z",
        ),
        roof_system=RoofSystem(
            panel_type="profiled_sheet",
            panel_thickness_mm=0.7,
            rib_height_mm=76.0,
            attachment_preference="clamp_based",
            waterproofing_sensitivity="medium",
            restricted_installation_zones="",
        ),
        member_evidence=MemberEvidence(
            drawing_availability="complete",
            survey_available=True,
            member_schedule_status="available",
            corrosion_condition="low",
        ),
        connection_evidence=ConnectionEvidence(
            connection_detail_status="available",
            roof_vendor_data_status="available",
            available_verification_path="drawings_plus_survey",
        ),
        load_assumptions=LoadAssumptions(
            intended_modification="equipment upgrade",
            estimated_added_load_kpa=0.22,
        ),
        standards_context=StandardsContext(
            design_standard="gb",
            shutdown_constraint="none",
        ),
        review_tasks=[
            ReviewTask(
                task_id="member_review",
                task_type="member_review",
                objective="Confirm governing members",
                required_evidence=["member schedule"],
                status="pending",
            )
        ],
    )

    assert case.standards_context.design_standard == "gb"
    assert case.member_evidence.survey_available is True
    assert case.review_tasks[0].task_type == "member_review"
