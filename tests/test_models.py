import pytest
from pydantic import ValidationError

from structural_screening_agent.models import BuildingIntake, DecisionStatus


def test_building_intake_requires_project_type() -> None:
    with pytest.raises(ValidationError) as exc_info:
        BuildingIntake(
            building_type="warehouse",
            structural_system="steel",
            roof_type="metal deck",
            intended_modification="rooftop_pv",
            estimated_added_load_kpa=0.18,
            shutdown_constraint="limited",
            drawing_availability="partial",
        )

    assert "project_type" in str(exc_info.value)


def test_demo_case_uses_conditional_go_target() -> None:
    from structural_screening_agent.demo_data import main_demo_case

    intake = main_demo_case()
    assert intake.project_type == "rooftop_pv"
    assert intake.building_span_m == 30.0
    assert intake.column_spacing_m == 8.0
    assert intake.roof_panel_type == "profiled_sheet"
    assert intake.available_verification_path == "drawings_only"
    assert DecisionStatus.CONDITIONAL_GO.value == "conditional_go"
