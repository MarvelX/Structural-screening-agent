from datetime import date
from typing import Optional

from structural_screening_agent.bv_review.models import (
    BVReportPreview,
    BVReportSection,
    BVReviewIntake,
    BVReviewResult,
)


def build_bv_report_preview(intake: BVReviewIntake, result: BVReviewResult) -> BVReportPreview:
    blocking_items = [item for item in result.risks if item.blocks_report_issue]
    sections = [
        BVReportSection(
            heading="项目与审核范围",
            items=[
                f"项目名称: {intake.project_name}",
                f"国家/地区: {intake.country_or_region}",
                f"设计阶段: {intake.design_stage}",
                f"审核对象: {', '.join(intake.review_objects)}",
                f"当前审核结论: {result.decision}",
            ],
        ),
        BVReportSection(
            heading="审核依据",
            items=[f"{item.title}: {'; '.join(item.review_actions)}" for item in result.basis_references],
        ),
        BVReportSection(
            heading="提交资料清单与完整性状态",
            items=[f"{item.title}: {item.status} | {item.required_action}" for item in result.checklist_items],
        ),
        BVReportSection(
            heading="审核路径与方法",
            items=[f"{item.title}: {item.status} | {item.method}" for item in result.review_paths],
        ),
        BVReportSection(
            heading="主要发现",
            items=[
                f"阻塞项数量: {len(blocking_items)}",
                f"风险与不符合项数量: {len(result.risks)}",
                f"审核计划条目数量: {len(result.review_plan)}",
            ],
        ),
        BVReportSection(
            heading="不符合项与阻塞项",
            items=[
                f"{item.title}: {item.recommendation}"
                for item in result.risks
                if item.category == "nonconformity" or item.blocks_report_issue
            ]
            or ["当前未识别阻塞报告签发的不符合项。"],
        ),
        BVReportSection(
            heading="技术风险与优化建议",
            items=[
                f"{item.title}: {item.recommendation}"
                for item in result.risks
                if item.category in {"risk", "optimization"}
            ]
            or ["当前未识别需要单独列示的优化建议。"],
        ),
        BVReportSection(
            heading="后续行动",
            items=[f"{item.phase}: {item.method} | 交付物: {item.deliverable}" for item in result.review_plan[:8]],
        ),
        BVReportSection(
            heading="审核边界声明",
            items=[
                "本工具用于设计审核前期组织、资料完整性判断、风险识别和 screening-level 技术路径梳理。",
                "输出不替代正式设计、第三方签章、有限元计算、施工图审查，也不代表 BV 官方签发流程。",
                "所有自动生成的不符合项、技术风险和优化建议均需由合格工程师复核。",
            ],
        ),
    ]
    return BVReportPreview(title="BV 光伏结构设计审查报告", sections=sections)


def build_bv_markdown_report(intake: BVReviewIntake, result: BVReviewResult) -> str:
    preview = result.report_preview or build_bv_report_preview(intake, result)
    lines = [f"# {preview.title}", ""]
    for section in preview.sections:
        lines.append(f"## {section.heading}")
        for item in section.items:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_bv_report_filename(scope_key: str, report_date: Optional[date] = None) -> str:
    current_date = report_date or date.today()
    return f"{current_date.isoformat()}-{scope_key}-bv-review-report.md"
