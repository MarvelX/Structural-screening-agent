import sqlite3

import pytest

from structural_screening_agent.core.persistence import ScreeningRepository
from structural_screening_agent.app_state import build_intake, evaluate_case
from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.models import BuildingIntake


def _level_b_portal_frame_intake() -> BuildingIntake:
    return BuildingIntake(
        project_type="rooftop_pv",
        design_standard_context="gb",
        building_type="test warehouse",
        structural_system="steel portal frame",
        roof_type="metal roof",
        intended_modification="distributed rooftop pv",
        estimated_added_load_kpa=0.18,
        building_span_m=30.0,
        column_spacing_m=8.0,
        rafter_section="310x150x8x12 welded rafter",
        column_section="305x305x10x15 welded column",
        purlin_spacing_m=1.5,
        purlin_type="cold_formed_z",
        roof_panel_type="profiled_sheet",
        roof_panel_thickness_mm=None,
        roof_rib_height_mm=None,
        roof_attachment_preference="clamp_based",
        existing_member_schedule_status="available",
        connection_detail_status="partial",
        roof_vendor_data_status="missing",
        corrosion_condition="moderate",
        waterproofing_sensitivity="high",
        restricted_installation_zones="maintenance corridor",
        available_verification_path="drawings_only",
        shutdown_constraint="limited",
        drawing_availability="complete",
        survey_available=False,
    )


def test_evaluate_case_exposes_kernel_case_and_outcome() -> None:
    evaluation = evaluate_case(main_demo_case().model_dump(), language="zh")

    assert evaluation["kernel_case"].building.project_type == "rooftop_pv"
    assert evaluation["kernel_outcome"].decision.status == "conditional_go"
    assert evaluation["kernel_outcome"].findings
    assert "Assessment Basis and Screening Calculations | 评估依据与筛查计算" in evaluation["report"]
    assert "Verification Readiness Score | 复核准备度分数: 55" in evaluation["report"]


def test_evaluate_case_can_persist_run_when_repository_is_provided(tmp_path) -> None:
    repository = ScreeningRepository(tmp_path / "screening.db")

    evaluation = evaluate_case(main_demo_case().model_dump(), language="zh", repository=repository)

    with sqlite3.connect(tmp_path / "screening.db") as connection:
        run_id = connection.execute(
            "SELECT run_id FROM screening_results WHERE id = ?",
            (evaluation["persistence"]["result_id"],),
        ).fetchone()[0]

    assert evaluation["persistence"]["result_id"] >= 1
    assert evaluation["persistence"]["run_id"] >= 1
    assert run_id == evaluation["persistence"]["run_id"]


def test_evaluate_case_level_b_portal_frame_report_includes_memo_sections() -> None:
    evaluation = evaluate_case(_level_b_portal_frame_intake().model_dump(), language="zh")

    assert "Review Scope and Boundary | 复核范围与边界" in evaluation["report"]
    assert "Simplified Calculation Results | 简化计算结果" in evaluation["report"]
    assert "Preliminary Structural Conclusion | 初步结构结论" in evaluation["report"]
    assert "Recommended Next-Step Review Actions | 后续复核建议" in evaluation["report"]
    assert "Purlin Strength Ratio | 檩条强度比" in evaluation["report"]
    assert "Purlin Deflection Ratio | 檩条挠度比" in evaluation["report"]


def test_evaluate_case_uses_kernel_driven_follow_up_questions() -> None:
    evaluation = evaluate_case(_level_b_portal_frame_intake().model_dump(), language="zh")

    assert any("为什么问这个" in question for question in evaluation["questions"])
    assert any("锁边" in question or "夹具" in question for question in evaluation["questions"])


def test_build_intake_can_apply_default_package_without_overwriting_known_inputs() -> None:
    intake = build_intake(
        {
            "default_package_key": "portal_frame_conservative",
            "project_type": "rooftop_pv",
            "design_standard_context": "gb",
            "building_type": "rough warehouse",
            "structural_system": "steel portal frame",
            "roof_type": "metal roof",
            "intended_modification": "distributed rooftop pv",
            "estimated_added_load_kpa": 0.16,
            "building_span_m": 28.0,
            "column_spacing_m": 8.0,
            "shutdown_constraint": "limited",
            "drawing_availability": "partial",
            "survey_available": False,
            "steel_grade": None,
            "purlin_type": None,
            "roof_panel_type": None,
        }
    )

    assert intake.building_type == "rough warehouse"
    assert intake.estimated_added_load_kpa == 0.16
    assert intake.steel_grade == "Q235"
    assert intake.purlin_type == "cold_formed_z"
    assert intake.roof_panel_type == "profiled_sheet"


def test_evaluate_case_does_not_leave_orphan_run_when_atomic_persistence_fails(tmp_path) -> None:
    class FailingAtomicRepository(ScreeningRepository):
        def _insert_exported_report(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("atomic save failed")

    repository = FailingAtomicRepository(tmp_path / "screening.db")

    with pytest.raises(RuntimeError, match="atomic save failed"):
        evaluate_case(
            _level_b_portal_frame_intake().model_dump(),
            language="zh",
            repository=repository,
        )

    with sqlite3.connect(tmp_path / "screening.db") as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "screening_runs",
                "cases",
                "evidence_snapshots",
                "screening_results",
                "screening_result_calculations",
                "screening_result_actions",
                "screening_result_rules",
                "screening_result_basis_links",
                "exported_reports",
            )
        }

    assert counts == {
        "screening_runs": 0,
        "cases": 0,
        "evidence_snapshots": 0,
        "screening_results": 0,
        "screening_result_calculations": 0,
        "screening_result_actions": 0,
        "screening_result_rules": 0,
        "screening_result_basis_links": 0,
        "exported_reports": 0,
    }
