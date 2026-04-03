import pytest

from structural_screening_agent.core.domain import PortalFrameScreeningCase, from_building_intake
from structural_screening_agent.demo_data import main_demo_case


def test_portal_frame_case_collects_engineering_inputs() -> None:
    case = from_building_intake(main_demo_case())

    assert isinstance(case, PortalFrameScreeningCase)
    assert case.code_context.standard == "gb"
    assert case.geometry.span_m == 30.0
    assert case.geometry.bay_spacing_m == 8.0
    assert case.primary_frame.rafter_section
    assert case.secondary_members.purlin_type == "cold_formed_z"
    assert case.secondary_members.purlin_spacing_m is not None
    assert case.pv_load.added_dead_load_kpa == 0.18
    assert case.evidence.original_drawings_available is True


def test_portal_frame_case_tracks_screening_level_from_evidence() -> None:
    intake = main_demo_case().model_copy(
        update={
            "drawing_availability": "missing",
            "existing_member_schedule_status": "missing",
            "survey_available": False,
        }
    )

    case = from_building_intake(intake)

    assert case.evidence.screening_level == "level_c"
    assert "original structural drawings" in case.evidence.missing_critical_data[0].lower()


def test_portal_frame_case_projects_compatibility_views_from_evidence() -> None:
    case = from_building_intake(main_demo_case())
    updated = case.model_copy(
        update={
            "evidence": case.evidence.model_copy(
                update={
                    "drawing_availability": "complete",
                    "screening_level": "level_a",
                }
            )
        }
    )

    assert updated.member_evidence.drawing_availability == "complete"
    assert updated.connection_evidence.available_verification_path == "drawings_only"


def test_secondary_member_profile_uses_purlin_type_not_section() -> None:
    case = from_building_intake(main_demo_case())

    assert case.secondary_members.purlin_type == "cold_formed_z"
    with pytest.raises(AttributeError):
        _ = case.secondary_members.purlin_section
