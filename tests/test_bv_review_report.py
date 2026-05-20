from datetime import date

from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.report import (
    build_bv_open_rfi_items,
    build_bv_markdown_report,
    build_bv_report_filename,
    build_bv_report_preview,
)
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Hebei rooftop PV design review",
        country_or_region="China",
        project_type="rooftop_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "existing_rooftop_added_load"],
        client_requirements=["Client requires independent structural design review."],
        documents={
            "structural_drawings": "partial",
            "calculation_report": "missing",
            "technical_specification": "available",
            "geotechnical_report": "missing",
            "vendor_datasheets": "partial",
            "contract_requirements": "available",
        },
    )


def test_bv_report_preview_contains_required_design_review_sections() -> None:
    result = evaluate_bv_review(_sample_intake())
    preview = build_bv_report_preview(_sample_intake(), result)

    headings = [section.heading for section in preview.sections]
    assert preview.title == "BV 光伏结构设计审查报告"
    assert "项目与审核范围" in headings
    assert "审核依据" in headings
    assert "提交资料清单与完整性状态" in headings
    assert "审核路径与方法" in headings
    assert "主要发现" in headings
    assert "不符合项与阻塞项" in headings
    assert "技术风险与优化建议" in headings
    assert "后续行动" in headings
    assert "审核边界声明" in headings


def test_bv_report_boundary_statement_does_not_claim_formal_design_or_bv_official_issue() -> None:
    result = evaluate_bv_review(_sample_intake())
    preview = build_bv_report_preview(_sample_intake(), result)

    boundary = next(section for section in preview.sections if section.heading == "审核边界声明")
    text = "\n".join(boundary.items)
    assert "不替代正式设计" in text
    assert "不代表 BV 官方签发流程" in text
    assert "合格工程师复核" in text


def test_bv_markdown_report_contains_required_sections_and_boundary_statement() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)

    report = build_bv_markdown_report(intake, result)

    assert report.startswith("# BV 光伏结构设计审查报告")
    assert "## 项目与审核范围" in report
    assert "## 审核依据" in report
    assert "## 提交资料清单与完整性状态" in report
    assert "## 审核路径与方法" in report
    assert "## 不符合项与阻塞项" in report
    assert "## 技术风险与优化建议" in report
    assert "## 后续行动" in report
    assert "## 审核边界声明" in report
    assert "不替代正式设计" in report
    assert "不代表 BV 官方签发流程" in report


def test_bv_report_filename_uses_date_and_scope_key() -> None:
    filename = build_bv_report_filename("rooftop_pv_review", report_date=date(2026, 5, 9))

    assert filename == "2026-05-09-rooftop_pv_review-bv-review-report.md"


def test_bv_open_rfi_items_are_created_from_blocking_risks_only() -> None:
    result = evaluate_bv_review(_sample_intake())

    rfi_items = build_bv_open_rfi_items(result.risks)

    assert rfi_items
    assert all(item.status == "open" for item in rfi_items)
    assert all(item.triggers_incremental_recheck for item in rfi_items)
    assert all(item.reopen_review_items for item in rfi_items)
    assert not any("正式签发" in item.question for item in rfi_items)
    assert {
        item.rfi_id.replace("rfi-", "", 1)
        for item in rfi_items
    } <= {risk.risk_id for risk in result.risks if risk.blocks_report_issue}


def test_bv_open_rfi_item_preserves_risk_traceability_and_screening_boundary() -> None:
    result = evaluate_bv_review(_sample_intake())
    blocking_risk = next(risk for risk in result.risks if risk.blocks_report_issue)

    rfi_item = next(
        item
        for item in build_bv_open_rfi_items(result.risks)
        if item.rfi_id == f"rfi-{blocking_risk.risk_id}"
    )

    assert blocking_risk.title in rfi_item.question
    assert "筛查级" in rfi_item.question
    assert rfi_item.trigger_basis == blocking_risk.trigger_basis
    assert rfi_item.required_document_or_field == ", ".join(blocking_risk.linked_field_ids)
    assert rfi_item.reopen_review_items == blocking_risk.linked_field_ids
