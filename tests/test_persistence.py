import sqlite3
from pathlib import Path

import pytest

from structural_screening_agent.core.domain import PortalFrameScreeningCase, from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.core.persistence import ScreeningRepository
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


def test_repository_persists_case_and_kernel_outcome(tmp_path) -> None:
    repository = ScreeningRepository(tmp_path / "screening.db")
    case = from_building_intake(main_demo_case())
    outcome = evaluate_screening_case(case)

    run_id = repository.save_run(case, outcome)
    stored = repository.load_run(run_id)

    assert stored.run_id == run_id
    assert stored.case.building.project_type == "rooftop_pv"
    assert stored.outcome.decision.status == "conditional_go"


def test_repository_round_trip_preserves_portal_frame_case(tmp_path) -> None:
    repository = ScreeningRepository(tmp_path / "screening.db")
    case = from_building_intake(main_demo_case())
    outcome = evaluate_screening_case(case)

    run_id = repository.save_run(case, outcome)
    stored = repository.load_run(run_id)

    assert isinstance(stored.case, PortalFrameScreeningCase)
    assert stored.case.code_context.standard == "gb"
    assert stored.case.primary_frame.rafter_section == "310x150x8x12 welded rafter"
    assert stored.case.secondary_members.purlin_spacing_m == 1.5
    assert stored.case.pv_load.added_dead_load_kpa == 0.18
    assert stored.case.evidence.screening_level == "level_b"


def test_repository_persists_normalized_screening_records_and_basis_registry(tmp_path) -> None:
    repository = ScreeningRepository(tmp_path / "screening.db")
    case = from_building_intake(main_demo_case())
    outcome = evaluate_screening_case(case)

    result_id = repository.save_evaluation(
        case=case,
        outcome=outcome,
        report_markdown="# report",
        explanation_payload={"summary": "demo"},
        language="zh",
    )

    stored = repository.load_evaluation(result_id)

    assert stored.case.building.project_type == "rooftop_pv"
    assert stored.outcome.decision.status == "conditional_go"
    assert stored.report_markdown == "# report"
    assert stored.language == "zh"

    with sqlite3.connect(tmp_path / "screening.db") as connection:
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "cases",
                "evidence_snapshots",
                "screening_results",
                "screening_result_calculations",
                "screening_result_actions",
                "screening_result_rules",
                "screening_result_basis_links",
                "exported_reports",
                "standards_basis_records",
            )
        }
        basis_row = connection.execute(
            """
            SELECT applicable_standards, trigger_conditions, review_requirements, evidence_requirements
            FROM standards_basis_records
            WHERE basis_id = ?
            """,
            ("gb_portal_frame_purlin_screening",),
        ).fetchone()
        result_rule_row = connection.execute(
            """
            SELECT rule_id, severity, basis_ids_json, traces_json
            FROM screening_result_rules
            WHERE screening_result_id = ?
            ORDER BY rule_id
            LIMIT 1
            """,
            (result_id,),
        ).fetchone()
        basis_link_row = connection.execute(
            """
            SELECT basis_id
            FROM screening_result_basis_links
            WHERE screening_result_id = ?
            ORDER BY basis_id
            LIMIT 1
            """,
            (result_id,),
        ).fetchone()
        calc_row = connection.execute(
            """
            SELECT calc_id, category, value_text, numeric_value
            FROM screening_result_calculations
            WHERE screening_result_id = ? AND calc_id = ?
            """,
            (result_id, "verification_readiness_score"),
        ).fetchone()
        action_row = connection.execute(
            """
            SELECT title_en, phase
            FROM screening_result_actions
            WHERE screening_result_id = ?
            ORDER BY id
            LIMIT 1
            """,
            (result_id,),
        ).fetchone()

    assert counts["cases"] == 1
    assert counts["evidence_snapshots"] == 1
    assert counts["screening_results"] == 1
    assert counts["screening_result_calculations"] >= 1
    assert counts["screening_result_actions"] >= 1
    assert counts["screening_result_rules"] >= 1
    assert counts["screening_result_basis_links"] >= 1
    assert counts["exported_reports"] == 1
    assert counts["standards_basis_records"] >= 3
    assert basis_row is not None
    assert "gb" in basis_row[0]
    assert "drawings" in basis_row[3]
    assert result_rule_row is not None
    assert result_rule_row[0] == "gb_portal_frame_purlin_screening"
    assert "gb_portal_frame_purlin_screening" in result_rule_row[2]
    assert "portal_frame.purlin_strength_ratio" in result_rule_row[3]
    assert basis_link_row is not None
    assert basis_link_row[0] == "gb_portal_frame_purlin_screening"
    assert calc_row is not None
    assert calc_row[0] == "verification_readiness_score"
    assert calc_row[1] == "readiness"
    assert calc_row[2] == "55"
    assert calc_row[3] == 55
    assert action_row is not None
    assert action_row[1] in {"must_do", "parallel", "later"}


def test_repository_persists_portal_frame_purlin_strength_ratio(tmp_path) -> None:
    repository = ScreeningRepository(tmp_path / "screening.db")
    case = from_building_intake(_level_b_portal_frame_intake())
    outcome = evaluate_screening_case(case)

    result_id = repository.save_evaluation(
        case=case,
        outcome=outcome,
        report_markdown="# report",
        explanation_payload={"summary": "demo"},
        language="zh",
    )

    with sqlite3.connect(tmp_path / "screening.db") as connection:
        calc_row = connection.execute(
            """
            SELECT calc_id, category, value_text, numeric_value
            FROM screening_result_calculations
            WHERE screening_result_id = ? AND calc_id = ?
            """,
            (result_id, "purlin_strength_ratio"),
        ).fetchone()

    assert calc_row is not None
    assert calc_row[0] == "purlin_strength_ratio"
    assert calc_row[1] == "reserve"
    assert calc_row[2]
    assert calc_row[3] is not None


def test_repository_persists_portal_frame_snapshot_payload(tmp_path) -> None:
    repository = ScreeningRepository(tmp_path / "screening.db")
    case = from_building_intake(main_demo_case())
    outcome = evaluate_screening_case(case)

    result_id = repository.save_evaluation(
        case=case,
        outcome=outcome,
        report_markdown="# report",
        explanation_payload={"summary": "demo"},
        language="zh",
    )

    with sqlite3.connect(tmp_path / "screening.db") as connection:
        snapshot_json = connection.execute(
            """
            SELECT snapshot_json
            FROM evidence_snapshots
            WHERE case_id = (
                SELECT case_id
                FROM screening_results
                WHERE id = ?
            )
            """,
            (result_id,),
        ).fetchone()[0]

    snapshot = __import__("json").loads(snapshot_json)

    assert snapshot["evidence"]["screening_level"] == "level_b"
    assert snapshot["evidence"]["missing_critical_data"]
    assert "original_drawings_available" in snapshot["evidence"]
    assert snapshot["geometry"]["span_m"] == 30.0
    assert snapshot["primary_frame"]["rafter_section"] == "310x150x8x12 welded rafter"
    assert snapshot["secondary_members"]["purlin_type"] == "cold_formed_z"
    assert snapshot["pv_load"]["added_dead_load_kpa"] == 0.18


def test_repository_connection_enforces_foreign_keys(tmp_path) -> None:
    repository = ScreeningRepository(tmp_path / "screening.db")

    with repository._connect() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO screening_result_basis_links(screening_result_id, basis_id)
                VALUES (?, ?)
                """,
                (999, "gb_50017_general"),
            )


def test_repository_atomic_save_does_not_leave_partial_rows_on_failure(tmp_path) -> None:
    class FailingScreeningRepository(ScreeningRepository):
        def _insert_exported_report(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("report export failed")

    repository = FailingScreeningRepository(tmp_path / "screening.db")
    case = from_building_intake(_level_b_portal_frame_intake())
    outcome = evaluate_screening_case(case)

    try:
        repository.save_run_and_evaluation(
            case=case,
            outcome=outcome,
            report_markdown="# report",
            explanation_payload={"summary": "demo"},
            language="zh",
        )
    except RuntimeError as error:
        assert str(error) == "report export failed"
    else:
        raise AssertionError("expected save_run_and_evaluation to fail")

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


def test_repository_migrates_legacy_basis_table_and_resyncs_registry(tmp_path: Path) -> None:
    database_path = tmp_path / "screening.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE standards_basis_records (
                basis_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                title_en TEXT NOT NULL,
                title_zh TEXT NOT NULL,
                citation_en TEXT NOT NULL,
                citation_zh TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO standards_basis_records(
                basis_id, source_type, title_en, title_zh, citation_en, citation_zh
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "gb_50017_general",
                "legacy",
                "legacy title",
                "旧标题",
                "legacy citation",
                "旧说明",
            ),
        )

    ScreeningRepository(database_path)

    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(standards_basis_records)"
            ).fetchall()
        }
        migrated_row = connection.execute(
            """
            SELECT
                source_type,
                applicable_standards,
                trigger_conditions,
                review_requirements,
                evidence_requirements
            FROM standards_basis_records
            WHERE basis_id = ?
            """,
            ("gb_50017_general",),
        ).fetchone()

    assert "applicable_standards" in columns
    assert "trigger_conditions" in columns
    assert "review_requirements" in columns
    assert "evidence_requirements" in columns
    assert migrated_row is not None
    assert migrated_row[0] == "standard"
    assert "gb" in migrated_row[1]
    assert "connection review" in migrated_row[2]
    assert "member schedule" in migrated_row[4]
