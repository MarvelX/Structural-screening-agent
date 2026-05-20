from structural_screening_agent.bv_review.ui import (
    build_bv_basis_items,
    build_bv_report_preview_sections,
)
from structural_screening_agent.bv_review.ui_state import default_bv_review_intake
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def test_bv_ui_helpers_import_without_streamlit_runtime() -> None:
    intake = default_bv_review_intake()
    result = evaluate_bv_review(intake)

    zh_items = build_bv_basis_items(result, "zh")
    en_items = build_bv_basis_items(result, "en")

    assert zh_items
    assert en_items
    assert "Review Basis" not in str(zh_items)
    assert "objects:" in en_items[0]


def test_bv_report_preview_sections_support_chinese_and_english() -> None:
    intake = default_bv_review_intake()
    result = evaluate_bv_review(intake)

    zh_sections = build_bv_report_preview_sections(intake, result, "zh")
    en_sections = build_bv_report_preview_sections(intake, result, "en")

    assert zh_sections[0].heading == "项目与审核范围"
    assert en_sections[0].heading == "Project and Review Scope"
    assert "Project name:" in en_sections[0].items[0]
    assert "Project name:" not in str(zh_sections)
