from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.ui_state import (
    BV_DOCUMENT_LABELS,
    BV_REVIEW_OBJECT_LABELS,
    build_bv_review_intake,
    default_bv_review_intake,
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
