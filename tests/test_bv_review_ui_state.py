import pytest
from pydantic import ValidationError

from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.ui_state import (
    BV_DOCUMENT_LABELS,
    BV_REVIEW_OBJECT_LABELS,
    build_extracted_fields_from_human_gate_rows,
    build_bv_review_intake,
    build_field_diff_summary_rows,
    build_ground_fixed_human_gate_rows,
    build_incremental_recheck_summary_rows,
    default_bv_review_intake,
    localize_report_gate_reason,
)
from structural_screening_agent.bv_review.field_diff import (
    build_incremental_recheck_plan,
    diff_extracted_fields,
)
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def test_default_bv_review_intake_runs_through_workflow() -> None:
    intake = default_bv_review_intake()
    result = evaluate_bv_review(intake)

    assert isinstance(intake, BVReviewIntake)
    assert intake.project_name == "BV rooftop PV design review demo"
    assert "gb" in intake.standards_systems
    assert "iec" in intake.standards_systems
    assert "mounting_structure" in intake.review_objects
    assert result.report_preview is not None
    assert result.report_preview.title == "BV 光伏结构设计审查报告"


def test_bv_ui_labels_cover_default_documents_and_review_objects() -> None:
    intake = default_bv_review_intake()

    assert set(intake.documents) <= set(BV_DOCUMENT_LABELS)
    assert set(intake.review_objects) <= set(BV_REVIEW_OBJECT_LABELS)
    assert BV_DOCUMENT_LABELS["calculation_report"]["zh"] == "结构计算书"
    assert BV_REVIEW_OBJECT_LABELS["existing_rooftop_added_load"]["zh"] == "既有屋面增载"


def test_build_bv_review_intake_preserves_user_selected_scope_and_documents() -> None:
    intake = build_bv_review_intake(
        project_name="Owner review package",
        country_or_region="Australia",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["iec", "as_nzs"],
        review_objects=["foundation", "load_calculation"],
        client_requirements_text="Independent review before IFC release",
        documents={
            "technical_specification": "available",
            "geotechnical_report": "partial",
            "calculation_report": "missing",
        },
    )

    assert intake.project_name == "Owner review package"
    assert intake.country_or_region == "Australia"
    assert intake.standards_systems == ["iec", "as_nzs"]
    assert intake.review_objects == ["foundation", "load_calculation"]
    assert intake.client_requirements == ["Independent review before IFC release"]
    assert intake.documents["geotechnical_report"] == "partial"


def test_build_bv_review_intake_rejects_empty_user_selected_scope() -> None:
    with pytest.raises(ValidationError):
        build_bv_review_intake(
            project_name="Scope removed",
            country_or_region="China",
            project_type="rooftop_pv",
            design_stage="construction_drawing",
            standards_systems=[],
            review_objects=["foundation"],
            client_requirements_text="",
            documents={},
        )

    with pytest.raises(ValidationError):
        build_bv_review_intake(
            project_name="Scope removed",
            country_or_region="China",
            project_type="rooftop_pv",
            design_stage="construction_drawing",
            standards_systems=["gb"],
            review_objects=[],
            client_requirements_text="",
            documents={},
        )


def test_ground_fixed_human_gate_rows_follow_selected_language_and_traceability() -> None:
    zh_rows = build_ground_fixed_human_gate_rows("zh")
    en_rows = build_ground_fixed_human_gate_rows("en")

    assert zh_rows[0]["field_name"] == "支架倾角"
    assert en_rows[0]["field_name"] == "Rack tilt angle"
    assert "支架" not in str(en_rows[0]["field_name"])
    assert all(row["source_document_id"] for row in zh_rows)
    assert all(row["page_or_section"] for row in zh_rows)
    assert all(row["quote"] for row in zh_rows)


def test_human_gate_rows_convert_to_traceable_extracted_fields() -> None:
    fields = build_extracted_fields_from_human_gate_rows(
        build_ground_fixed_human_gate_rows("en")
    )

    assert fields[0].field_id == "tilt_angle_deg"
    assert fields[0].source_document_id == "structural-drawing-s101"
    assert fields[0].include_in_calculation is True
    assert fields[0].is_confirmed is True
    assert fields[2].include_in_calculation is False


def test_build_incremental_recheck_summary_returns_review_items_without_running_diff() -> None:
    old_fields = build_extracted_fields_from_human_gate_rows(
        build_ground_fixed_human_gate_rows("en")
    )
    new_rows = build_ground_fixed_human_gate_rows("en")
    new_rows[1]["candidate_value"] = "4.0"
    new_fields = build_extracted_fields_from_human_gate_rows(new_rows)
    plan = build_incremental_recheck_plan(diff_extracted_fields(old_fields, new_fields))

    rows = build_incremental_recheck_summary_rows(plan, "en")

    assert rows
    assert rows[0]["Type"] == "Calculation Recheck"
    assert "Pile length" in str(rows[0]["Reason"])


def test_bv_diff_and_recheck_summary_rows_are_localized_for_chinese_ui() -> None:
    old_fields = build_extracted_fields_from_human_gate_rows(
        build_ground_fixed_human_gate_rows("zh")
    )
    new_rows = build_ground_fixed_human_gate_rows("zh")
    new_rows[1]["candidate_value"] = "4.0"
    new_fields = build_extracted_fields_from_human_gate_rows(new_rows)
    diffs = diff_extracted_fields(old_fields, new_fields)
    plan = build_incremental_recheck_plan(diffs)

    diff_rows = build_field_diff_summary_rows(diffs, "zh")
    recheck_rows = build_incremental_recheck_summary_rows(plan, "zh")

    assert "差分类型" in diff_rows[0]
    assert diff_rows[0]["差分类型"] == "修改"
    assert diff_rows[0]["影响已锁定计算"] == "是"
    assert "类型" in recheck_rows[0]
    assert recheck_rows[0]["类型"] == "计算复核"
    assert "changed and affects" not in str(recheck_rows[0]["原因"])


def test_report_gate_incremental_rfi_reason_localizes_to_chinese() -> None:
    reason = "Open RFI items trigger incremental recheck: rfi-pile_length_m"

    localized = localize_report_gate_reason(reason, "zh")

    assert localized == "未关闭的 RFI 触发增量复核：rfi-pile_length_m"
