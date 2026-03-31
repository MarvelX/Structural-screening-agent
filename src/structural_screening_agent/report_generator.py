from datetime import date
from typing import Optional

from pydantic import BaseModel

from structural_screening_agent.assumptions import build_assumptions_and_limitations
from structural_screening_agent.bilingual import same_line
from structural_screening_agent.check_linkage import build_check_action_links
from structural_screening_agent.decision_chain import build_decision_chain
from structural_screening_agent.drawing_facts import build_drawing_facts_summary
from structural_screening_agent.intake_snapshot import build_screening_snapshot
from structural_screening_agent.localization import (
    Language,
    format_bilingual_detail,
    format_bilingual_item,
    format_attachment_pathway,
    format_confidence,
    format_decision_localized,
    format_engineering_check,
    format_option_detail,
    format_resource_recommendation,
    format_reserve_uncertainty,
    format_review_trigger,
    format_verification_readiness,
    translate,
    translate_option,
)
from structural_screening_agent.management_summary import build_management_summary
from structural_screening_agent.models import BuildingIntake, DecisionStatus, LLMExplanation, ScreeningResult
from structural_screening_agent.review_path_summary import build_review_progression_summary


def format_decision(status: DecisionStatus) -> str:
    mapping = {
        DecisionStatus.GO: same_line("Go", "可推进"),
        DecisionStatus.CONDITIONAL_GO: same_line("Conditional Go", "有条件推进"),
        DecisionStatus.NO_GO: same_line("No-Go", "暂不建议推进"),
    }
    return mapping[status]


class ReportPreviewSection(BaseModel):
    heading: str
    items: list[str]


class ReportPreview(BaseModel):
    title: str
    sections: list[ReportPreviewSection]


def _group_recommended_actions(result: ScreeningResult, language: Language) -> list[str]:
    ordered_phases = ["must_do", "parallel", "later"]
    grouped_lines = []
    for phase in ordered_phases:
        items = [item for item in result.recommended_actions if item.phase == phase]
        if not items:
            continue
        grouped_lines.append(translate(language, phase))
        grouped_lines.extend(format_bilingual_item(item, language) for item in items)
    return grouped_lines


def build_report_filename(case_key: str, report_date: Optional[date] = None) -> str:
    current_date = report_date or date.today()
    return f"{current_date.isoformat()}-{case_key}-screening-report.md"


def build_report_preview(
    intake: BuildingIntake, result: ScreeningResult, explanation: LLMExplanation, language: Language = "zh"
) -> ReportPreview:
    screening_snapshot_items = build_screening_snapshot(intake, language)
    management_summary_items = build_management_summary(result, language)
    drawing_facts_items = build_drawing_facts_summary(intake, language)
    assumptions_items = build_assumptions_and_limitations(intake, result, language)
    linkage_items = build_check_action_links(result, language)
    review_progression_items = build_review_progression_summary(result, language)
    decision_chain_items = build_decision_chain(result, language)
    recommended_action_items = _group_recommended_actions(result, language)
    engineering_check_items = []
    for item in result.engineering_checks:
        engineering_check_items.append(format_engineering_check(item, language))
        engineering_check_items.append(item.summary_zh if language == "zh" else item.summary_en)
    member_reserve_uncertainty_items = []
    for item in result.member_reserve_uncertainties:
        member_reserve_uncertainty_items.append(format_reserve_uncertainty(item, language))
        member_reserve_uncertainty_items.append(item.summary_zh if language == "zh" else item.summary_en)
    attachment_pathway_items = []
    for item in result.attachment_pathways:
        attachment_pathway_items.append(format_attachment_pathway(item, language))
        attachment_pathway_items.append(item.summary_zh if language == "zh" else item.summary_en)
    resource_recommendation_items = []
    for item in result.resource_recommendations:
        resource_recommendation_items.append(format_resource_recommendation(item, language))
        resource_recommendation_items.append(item.summary_zh if language == "zh" else item.summary_en)
    review_path_resource_items = [
        *review_progression_items,
        *resource_recommendation_items,
        *[format_bilingual_item(item, language) for item in result.review_required],
    ]
    review_trigger_items = []
    for item in result.review_triggers:
        review_trigger_items.append(format_review_trigger(item, language))
        review_trigger_items.append(item.summary_zh if language == "zh" else item.summary_en)
    option_preview_items = []
    for option in result.options:
        rationale = getattr(option, f"priority_rationale_{language}")
        option_preview_items.extend(
            [
                format_bilingual_item(option, language),
                f"{translate(language, 'priority_rationale')}: {rationale}" if rationale else None,
                format_option_detail(option, "fit_when", language),
                format_option_detail(option, "main_constraint", language),
                format_option_detail(option, "operational_impact", language),
                format_option_detail(option, "cost_level", language),
                format_option_detail(option, "schedule_impact", language),
                format_option_detail(option, "recommendation_note", language),
            ]
        )
    option_preview_items = [item for item in option_preview_items if item]

    risk_preview_items = []
    for item in result.risks:
        risk_preview_items.append(format_bilingual_item(item, language))
        detail = format_bilingual_detail(item, language)
        if detail:
            risk_preview_items.append(detail)

    return ReportPreview(
        title=translate(language, "decision_memo"),
        sections=[
            ReportPreviewSection(
                heading=translate(language, "executive_summary"),
                items=[*management_summary_items, *decision_chain_items] or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "decision_snapshot"),
                items=[
                    f"{translate(language, 'decision')}: {format_decision_localized(result.status, language)}",
                    f"{translate(language, 'confidence')}: {format_confidence(result.confidence, language)}",
                ],
            ),
            ReportPreviewSection(
                heading=translate(language, "immediate_actions"),
                items=recommended_action_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "review_paths_resources"),
                items=review_path_resource_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "project_summary"),
                items=[
                    f"{translate(language, 'project_type')}: {translate_option(language, 'project_type', intake.project_type)}",
                    (
                        f"{translate(language, 'design_standard_context')}: "
                        f"{translate_option(language, 'design_standard_context', intake.design_standard_context)}"
                    ),
                    f"{translate(language, 'building_type')}: {intake.building_type}",
                    f"{translate(language, 'structural_system')}: {intake.structural_system}",
                    (
                        f"{translate(language, 'verification_path')}: "
                        f"{translate_option(language, 'available_verification_path', intake.available_verification_path)}"
                    ),
                ],
            ),
            ReportPreviewSection(
                heading=translate(language, "main_case_screening_inputs"),
                items=screening_snapshot_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "drawing_facts_summary"),
                items=drawing_facts_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "verification_readiness"),
                items=[
                    (
                        f"{translate(language, 'verification_readiness')}: "
                        f"{format_verification_readiness(result.verification_readiness.level, language)}"
                    ),
                    (
                        result.verification_readiness.summary_zh
                        if language == "zh"
                        else result.verification_readiness.summary_en
                    ),
                    *[format_bilingual_item(item, language) for item in result.verification_readiness.blockers],
                ],
            ),
            ReportPreviewSection(
                heading=translate(language, "engineering_checks"),
                items=engineering_check_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "member_reserve_uncertainty_matrix"),
                items=member_reserve_uncertainty_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "attachment_pathway_matrix"),
                items=attachment_pathway_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "review_trigger_matrix"),
                items=review_trigger_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "check_action_linkage"),
                items=linkage_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "assumptions_limitations"),
                items=assumptions_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "top_risks"),
                items=risk_preview_items or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "missing_data"),
                items=[format_bilingual_item(item, language) for item in result.missing_data]
                or [translate(language, "none")],
            ),
            ReportPreviewSection(
                heading=translate(language, "agent_explanation"),
                items=[explanation.summary],
            ),
            ReportPreviewSection(
                heading=translate(language, "options"),
                items=option_preview_items or [translate(language, "none")],
            ),
        ],
    )


def build_markdown_report(intake: BuildingIntake, result: ScreeningResult, explanation: LLMExplanation) -> str:
    screening_snapshot_lines = build_screening_snapshot(intake, "en")
    screening_snapshot_lines_zh = build_screening_snapshot(intake, "zh")
    management_summary_en = build_management_summary(result, "en")
    management_summary_zh = build_management_summary(result, "zh")
    drawing_facts_en = build_drawing_facts_summary(intake, "en")
    drawing_facts_zh = build_drawing_facts_summary(intake, "zh")
    assumptions_en = build_assumptions_and_limitations(intake, result, "en")
    assumptions_zh = build_assumptions_and_limitations(intake, result, "zh")
    linkage_en = build_check_action_links(result, "en")
    linkage_zh = build_check_action_links(result, "zh")
    review_progression_en = build_review_progression_summary(result, "en")
    review_progression_zh = build_review_progression_summary(result, "zh")
    decision_chain_lines_en = build_decision_chain(result, "en")
    decision_chain_lines_zh = build_decision_chain(result, "zh")
    if screening_snapshot_lines:
        snapshot_pairs = []
        for index, line_en in enumerate(screening_snapshot_lines):
            line_zh = screening_snapshot_lines_zh[index]
            snapshot_pairs.append(f"- {same_line(line_en, line_zh)}")
        screening_snapshot_block = "\n".join(snapshot_pairs)
    else:
        screening_snapshot_block = "None | 无"
    management_summary_block = (
        "\n".join(
            f"- {same_line(line_en, management_summary_zh[index])}"
            for index, line_en in enumerate(management_summary_en)
        )
        if management_summary_en
        else "None | 无"
    )
    decision_snapshot_block = "\n".join(
        [
            f"- {same_line('Decision', '决策结论')}: {format_decision(result.status)}",
            f"- {same_line('Confidence', '置信度')}: {same_line(format_confidence(result.confidence, 'en'), format_confidence(result.confidence, 'zh'))}",
        ]
    )
    if drawing_facts_en:
        drawing_facts_block = "\n".join(
            f"- {same_line(line_en, drawing_facts_zh[index])}" for index, line_en in enumerate(drawing_facts_en)
        )
    else:
        drawing_facts_block = "None | 无"
    assumptions_block = (
        "\n".join(f"- {same_line(line_en, assumptions_zh[index])}" for index, line_en in enumerate(assumptions_en))
        if assumptions_en
        else "None | 无"
    )
    linkage_block = (
        "\n".join(f"- {same_line(line_en, linkage_zh[index])}" for index, line_en in enumerate(linkage_en))
        if linkage_en
        else "None | 无"
    )
    review_progression_block = (
        "\n".join(
            f"- {same_line(line_en, review_progression_zh[index])}"
            for index, line_en in enumerate(review_progression_en)
        )
        if review_progression_en
        else "None | 无"
    )
    review_trigger_block = (
        "\n".join(
            [
                entry
                for trigger in result.review_triggers
                for entry in (
                    f"- {same_line(format_review_trigger(trigger, 'en'), format_review_trigger(trigger, 'zh'))}",
                    f"  - {same_line(trigger.summary_en, trigger.summary_zh)}",
                )
            ]
        )
        if result.review_triggers
        else "None | 无"
    )
    if decision_chain_lines_en:
        decision_chain_block = "\n".join(
            f"- {same_line(line_en, decision_chain_lines_zh[index])}"
            for index, line_en in enumerate(decision_chain_lines_en)
        )
    else:
        decision_chain_block = "None | 无"

    if result.risks:
        risk_blocks = []
        for item in result.risks:
            risk_blocks.append(f"- {same_line(item.title_en, item.title_zh)}")
            if item.detail_en or item.detail_zh:
                risk_blocks.append(
                    f"  - {same_line('Basis', '依据')}: {same_line(item.detail_en or '', item.detail_zh or '')}"
                )
        risk_lines = "\n".join(risk_blocks)
    else:
        risk_lines = "None | 无"
    missing_data_lines = (
        "\n".join(same_line(item.title_en, item.title_zh) for item in result.missing_data) or "None | 无"
    )
    if result.recommended_actions:
        action_blocks = []
        for phase in ["must_do", "parallel", "later"]:
            items = [item for item in result.recommended_actions if item.phase == phase]
            if not items:
                continue
            action_blocks.append(f"### {same_line(translate('en', phase), translate('zh', phase))}")
            action_blocks.extend(f"- {same_line(item.title_en, item.title_zh)}" for item in items)
            action_blocks.append("")
        recommended_action_lines = "\n".join(action_blocks).rstrip()
    else:
        recommended_action_lines = "None | 无"
    readiness_lines = [
        f"- {same_line('Verification Readiness', '结构复核准备度')}: "
        f"{same_line(format_verification_readiness(result.verification_readiness.level, 'en'), format_verification_readiness(result.verification_readiness.level, 'zh'))}",
        f"- {same_line(result.verification_readiness.summary_en, result.verification_readiness.summary_zh)}",
    ]
    readiness_lines.extend(
        f"- {same_line(item.title_en, item.title_zh)}" for item in result.verification_readiness.blockers
    )
    verification_readiness_block = "\n".join(readiness_lines)
    engineering_check_block = (
        "\n".join(
            [
                entry
                for check in result.engineering_checks
                for entry in (
                    f"- {same_line(format_engineering_check(check, 'en'), format_engineering_check(check, 'zh'))}",
                    f"  - {same_line(check.summary_en, check.summary_zh)}",
                )
            ]
        )
        if result.engineering_checks
        else "None | 无"
    )
    member_reserve_uncertainty_block = (
        "\n".join(
            [
                entry
                for item in result.member_reserve_uncertainties
                for entry in (
                    f"- {same_line(format_reserve_uncertainty(item, 'en'), format_reserve_uncertainty(item, 'zh'))}",
                    f"  - {same_line(item.summary_en, item.summary_zh)}",
                )
            ]
        )
        if result.member_reserve_uncertainties
        else "None | 无"
    )
    attachment_pathway_block = (
        "\n".join(
            [
                entry
                for item in result.attachment_pathways
                for entry in (
                    f"- {same_line(format_attachment_pathway(item, 'en'), format_attachment_pathway(item, 'zh'))}",
                    f"  - {same_line(item.summary_en, item.summary_zh)}",
                )
            ]
        )
        if result.attachment_pathways
        else "None | 无"
    )
    resource_recommendation_block = (
        "\n".join(
            [
                entry
                for item in result.resource_recommendations
                for entry in (
                    f"- {same_line(format_resource_recommendation(item, 'en'), format_resource_recommendation(item, 'zh'))}",
                    f"  - {same_line(item.summary_en, item.summary_zh)}",
                )
            ]
        )
        if result.resource_recommendations
        else "None | 无"
    )
    review_path_resource_block = "\n".join(
        block for block in [review_progression_block, resource_recommendation_block, "\n".join(same_line(item.title_en, item.title_zh) for item in result.review_required) or "None | 无"] if block
    )
    if result.options:
        option_blocks = []
        for option in result.options:
            rationale_line = (
                f"- {same_line('Priority Rationale', '当前优先原因')}: "
                f"{same_line(option.priority_rationale_en or '', option.priority_rationale_zh or '')}"
                if option.priority_rationale_en or option.priority_rationale_zh
                else None
            )
            option_blocks.extend(
                [
                    f"### {same_line(option.title_en, option.title_zh)}",
                    rationale_line,
                    f"- {same_line('Fit When', '适用情形')}: {same_line(option.fit_when_en, option.fit_when_zh)}",
                    (
                        f"- {same_line('Main Constraint', '主要约束')}: "
                        f"{same_line(option.main_constraint_en, option.main_constraint_zh)}"
                    ),
                    (
                        f"- {same_line('Operational Impact', '运营影响')}: "
                        f"{same_line(option.operational_impact_en, option.operational_impact_zh)}"
                    ),
                    f"- {same_line('Cost Level', '成本等级')}: {same_line(option.cost_level_en, option.cost_level_zh)}",
                    (
                        f"- {same_line('Schedule Impact', '工期影响')}: "
                        f"{same_line(option.schedule_impact_en, option.schedule_impact_zh)}"
                    ),
                    (
                        f"- {same_line('Recommendation Note', '推荐说明')}: "
                        f"{same_line(option.recommendation_note_en, option.recommendation_note_zh)}"
                    ),
                    "",
                ]
            )
        option_blocks = [item for item in option_blocks if item is not None]
        option_lines = "\n".join(option_blocks).rstrip()
    else:
        option_lines = "None | 无"

    sections = [
        "# Structural Feasibility Screening Agent | 结构可行性评估 Agent",
        "",
        "## Executive Summary | 执行摘要",
        management_summary_block,
        "",
        *([decision_chain_block, ""] if decision_chain_block != "None | 无" else []),
        "## Decision Snapshot | 决策快照",
        decision_snapshot_block,
        "",
        "## Immediate Actions | 即刻动作",
        recommended_action_lines,
        "",
        "## Review Paths and Resources | 复核路径与资源",
        review_path_resource_block,
        "",
        "## Project Summary | 项目概况",
        f"- {same_line('Project Type', '项目类型')}: {same_line(translate_option('en', 'project_type', intake.project_type), translate_option('zh', 'project_type', intake.project_type))}",
        f"- {same_line('Design Standard Context', '规范体系')}: {same_line(translate_option('en', 'design_standard_context', intake.design_standard_context), translate_option('zh', 'design_standard_context', intake.design_standard_context))}",
        f"- {same_line('Building Type', '建筑类型')}: {intake.building_type}",
        f"- {same_line('Structural System', '结构体系')}: {intake.structural_system}",
        (
            f"- {same_line('Available Verification Path', '可用复核路径')}: "
            f"{same_line(translate_option('en', 'available_verification_path', intake.available_verification_path), translate_option('zh', 'available_verification_path', intake.available_verification_path))}"
        ),
        "",
        "## Management Summary | 管理层摘要",
        management_summary_block,
        "",
        "## Main-Case Screening Inputs | 主案例筛查项",
        screening_snapshot_block,
        "",
        "## Drawing Facts Summary | 图纸关键信息摘录",
        drawing_facts_block,
        "",
        "## Verification Readiness | 结构复核准备度",
        verification_readiness_block,
        "",
        "## Engineering Screening Checks | 工程筛查检查",
        engineering_check_block,
        "",
        "## Member Reserve Uncertainty Matrix | 构件承载储备不确定性矩阵",
        member_reserve_uncertainty_block,
        "",
        "## Roof Attachment Pathway Matrix | 屋面连接路径矩阵",
        attachment_pathway_block,
        "",
        "## Review Trigger Matrix | 专项复核触发项",
        review_trigger_block,
        "",
        "## Review Progression | 复核推进链",
        review_progression_block,
        "",
        "## Recommended Resources | 建议配置资源",
        resource_recommendation_block,
        "",
        "## Check-to-Action Linkage | 检查联动摘要",
        linkage_block,
        "",
        "## Assumptions and Limits | 假设与边界",
        assumptions_block,
        "",
        "## Decision | 决策结论",
        format_decision(result.status),
        "",
        "## Confidence | 置信度",
        result.confidence,
        "",
        "## Top Risks | 关键风险",
        risk_lines,
        "",
        "## Missing Critical Data | 待补关键资料",
        missing_data_lines,
        "",
        "## Recommended Action | 建议动作",
        recommended_action_lines,
        "",
        "## Review Needed | 后续规范复核提示",
        "\n".join(same_line(item.title_en, item.title_zh) for item in result.review_required) or "None | 无",
        "",
        "## Agent Explanation | Agent 说明",
        explanation.summary,
        "",
        "## Options | 方案选项",
        option_lines,
    ]
    return "\n".join(sections)
