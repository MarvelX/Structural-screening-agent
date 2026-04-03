from datetime import date
from typing import Optional

from pydantic import BaseModel

from structural_screening_agent.assumptions import build_assumptions_and_limitations
from structural_screening_agent.bilingual import same_line
from structural_screening_agent.check_linkage import build_check_action_links
from structural_screening_agent.core.kernel import KernelOutcome
from structural_screening_agent.decision_chain import build_decision_chain
from structural_screening_agent.drawing_facts import build_drawing_facts_summary
from structural_screening_agent.intake_snapshot import build_screening_snapshot
from structural_screening_agent.localization import (
    Language,
    format_attachment_pathway,
    format_bilingual_detail,
    format_bilingual_item,
    format_confidence,
    format_decision_localized,
    format_engineering_check,
    format_option_detail,
    format_resource_recommendation,
    format_reserve_uncertainty,
    format_review_trigger,
    format_verification_readiness,
    localize_calc_unit,
    localize_basis_term,
    localize_input_path,
    localize_preset_text,
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


def _build_traceability_lines(result: ScreeningResult) -> str:
    if not result.traceability:
        return "None | 无"

    blocks = []
    for item in result.traceability:
        trace_summary = ", ".join(
            same_line(
                localize_input_path("en", trace.input_path),
                localize_input_path("zh", trace.input_path),
            )
            + f"={trace.observed_value}"
            for trace in item.traces
        ) or "None"
        blocks.extend(
            [
                f"- {same_line(item.summary_en, item.summary_zh)}",
                f"  - {same_line('Input Traces', '输入追踪')}: {trace_summary}",
            ]
        )
    return "\n".join(blocks)


def _calc_label(calc_id: str) -> str:
    mapping = {
        "added_load_kpa": same_line("Added Load Assumption", "新增荷载假定"),
        "reserve_screening_status": same_line("Reserve Screening Status", "承载储备筛查状态"),
        "attachment_screening_status": same_line("Attachment Screening Status", "连接路径筛查状态"),
        "verification_readiness_score": same_line("Verification Readiness Score", "复核准备度分数"),
        "uncertainty_score": same_line("Uncertainty Score", "不确定性分数"),
        "purlin_strength_ratio": same_line("Purlin Strength Ratio", "檩条强度比"),
        "purlin_deflection_ratio": same_line("Purlin Deflection Ratio", "檩条挠度比"),
        "critical_added_load_kpa": same_line("Estimated Critical Added Load", "临界新增荷载估算"),
        "remaining_added_load_margin_kpa": same_line("Remaining Added-Load Margin", "剩余新增荷载余量"),
        "primary_frame_line_load": same_line("Primary Frame Line Load", "主门架附加线荷载"),
        "primary_frame_added_moment_proxy": same_line("Primary Frame Added Moment Proxy", "主门架附加弯矩代理值"),
        "primary_frame_column_added_moment_proxy": same_line("Primary Frame Column Added Moment Proxy", "主门架柱附加弯矩代理值"),
        "primary_frame_reference_moment_proxy": same_line("Primary Frame Reference Moment Proxy", "主门架参考弯矩代理值"),
        "primary_frame_rafter_reference_moment_proxy": same_line("Primary Frame Rafter Reference Moment Proxy", "主门架梁参考弯矩代理值"),
        "primary_frame_rafter_screening_ratio": same_line("Primary Frame Rafter Screening Ratio", "主门架梁筛查比值"),
        "primary_frame_rafter_deflection_sensitivity": same_line("Primary Frame Rafter Deflection Sensitivity", "主门架梁挠度敏感性"),
        "primary_frame_column_reference_moment_proxy": same_line("Primary Frame Column Reference Moment Proxy", "主门架柱参考弯矩代理值"),
        "primary_frame_column_screening_ratio": same_line("Primary Frame Column Screening Ratio", "主门架柱筛查比值"),
        "primary_frame_column_stability_sensitivity": same_line("Primary Frame Column Stability Sensitivity", "主门架柱稳定敏感性"),
        "primary_frame_screening_ratio": same_line("Primary Frame Screening Ratio", "主门架筛查比值"),
    }
    return mapping.get(calc_id, calc_id)


def _find_kernel_calc_output(kernel_outcome: Optional[KernelOutcome], calc_id: str):
    if kernel_outcome is None:
        return None
    return next((item for item in kernel_outcome.calc_outputs if item.calc_id == calc_id), None)


def _format_bilingual_unit(unit: Optional[str]) -> Optional[str]:
    if not unit:
        return None
    unit_en = localize_calc_unit("en", unit)
    unit_zh = localize_calc_unit("zh", unit)
    if unit_en == unit_zh:
        return unit_en
    return same_line(unit_en, unit_zh)


def _format_calc_value_bilingual(item) -> str:
    unit_text = _format_bilingual_unit(item.unit)
    if not unit_text:
        return item.value_text
    if item.unit == "dimensionless":
        return f"{item.value_text} ({unit_text})"
    return f"{item.value_text} {unit_text}"


def _controlling_factor_line(kernel_outcome: Optional[KernelOutcome]) -> Optional[str]:
    if kernel_outcome is None:
        return None
    if kernel_outcome.controlling_path is not None:
        return same_line(
            kernel_outcome.controlling_path.summary_en,
            kernel_outcome.controlling_path.summary_zh,
        )
    candidates = [
        ("purlin_strength_ratio", "purlin strength screening", "檩条强度筛查"),
        ("purlin_deflection_ratio", "purlin deflection screening", "檩条挠度筛查"),
        ("primary_frame_rafter_screening_ratio", "primary-frame rafter added-moment screening", "主门架梁的附加弯矩筛查"),
        ("primary_frame_column_screening_ratio", "primary-frame column added-moment screening", "主门架柱的附加弯矩筛查"),
        ("primary_frame_screening_ratio", "primary-frame added-moment screening", "主门架附加弯矩筛查"),
    ]
    best: tuple[float, str, str] | None = None
    for calc_id, label_en, label_zh in candidates:
        item = _find_kernel_calc_output(kernel_outcome, calc_id)
        if item is None or item.numeric_value is None:
            continue
        value = float(item.numeric_value)
        if best is None or value > best[0]:
            best = (value, label_en, label_zh)
    if best is None:
        return None
    _, label_en, label_zh = best
    return same_line(
        f"Current controlling factor is the {label_en}.",
        f"当前控制因素主要落在{label_zh}。",
    )


def _build_assessment_basis_and_calc_lines(kernel_outcome: Optional[KernelOutcome]) -> str:
    if kernel_outcome is None:
        return "None | 无"

    blocks: list[str] = []
    if kernel_outcome.load_combination_sensitivities:
        blocks.append(f"### {same_line('Load Combination Sensitivity', '荷载组合敏感性')}")
        for item in kernel_outcome.load_combination_sensitivities:
            blocks.append(f"- {same_line(item.title_en, item.title_zh)}")
            blocks.append(f"  - {same_line(item.summary_en, item.summary_zh)}")
        blocks.append("")
    if kernel_outcome.basis_references:
        blocks.append(f"### {same_line('Basis References', '依据条目')}")
        for item in kernel_outcome.basis_references:
            blocks.append(f"- {same_line(item.title_en, item.title_zh)}")
            standards_en = ", ".join(item.applicable_standards) or "None"
            standards_zh = ", ".join(
                translate_option("zh", "design_standard_context", standard)
                for standard in item.applicable_standards
            ) or "无"
            blocks.append(
                f"  - {same_line('Engineering Meaning', '工程含义')}: "
                f"{same_line(item.citation_en, item.citation_zh)}"
            )
            blocks.append(
                f"  - {same_line('Applicable Standards', '适用规范体系')}: "
                f"{same_line(standards_en, standards_zh)}"
            )
            trigger_conditions_en = "; ".join(item.trigger_conditions) or "None"
            trigger_conditions_zh = "; ".join(
                localize_basis_term("zh", condition) for condition in item.trigger_conditions
            ) or "无"
            blocks.append(
                f"  - {same_line('Trigger Conditions', '触发条件')}: "
                f"{same_line(trigger_conditions_en, trigger_conditions_zh)}"
            )
            evidence_requirements_en = "; ".join(item.evidence_requirements) or "None"
            evidence_requirements_zh = "; ".join(
                localize_basis_term("zh", requirement) for requirement in item.evidence_requirements
            ) or "无"
            blocks.append(
                f"  - {same_line('Evidence Requirements', '证据需求')}: "
                f"{same_line(evidence_requirements_en, evidence_requirements_zh)}"
            )
            review_requirements_en = "; ".join(item.review_requirements) or "None"
            review_requirements_zh = "; ".join(
                localize_basis_term("zh", requirement) for requirement in item.review_requirements
            ) or "无"
            blocks.append(
                f"  - {same_line('Follow-up Review', '后续复核要求')}: "
                f"{same_line(review_requirements_en, review_requirements_zh)}"
            )

    key_calc_ids = {
        "added_load_kpa",
        "verification_readiness_score",
        "uncertainty_score",
        "purlin_strength_ratio",
        "purlin_deflection_ratio",
        "critical_added_load_kpa",
        "remaining_added_load_margin_kpa",
        "primary_frame_column_added_moment_proxy",
        "primary_frame_rafter_screening_ratio",
        "primary_frame_rafter_deflection_sensitivity",
        "primary_frame_column_screening_ratio",
        "primary_frame_column_stability_sensitivity",
        "primary_frame_screening_ratio",
    }
    calc_items = [item for item in kernel_outcome.calc_outputs if item.calc_id in key_calc_ids]
    if calc_items:
        if blocks:
            blocks.append("")
        blocks.append(f"### {same_line('Screening Calculations', '筛查计算')}")
        for item in calc_items:
            blocks.append(f"- {_calc_label(item.calc_id)}: {_format_calc_value_bilingual(item)}")
            if item.formula_en or item.formula_zh:
                blocks.append(
                    f"  - {same_line('Formula', '计算式')}: "
                    f"{same_line(item.formula_en or '-', item.formula_zh or '-')}"
                )
            if item.unit:
                blocks.append(
                    f"  - {same_line('Result Unit', '结果单位')}: {_format_bilingual_unit(item.unit)}"
                )

    return "\n".join(blocks) if blocks else "None | 无"


def _build_structural_memo_sections(
    intake: BuildingIntake,
    result: ScreeningResult,
    kernel_outcome: Optional[KernelOutcome],
) -> list[str]:
    def format_calc_value(item) -> str:
        return _format_calc_value_bilingual(item)

    scope_lines = [
        f"- {same_line('Screening review summary for rooftop PV added-load review on an existing portal-frame building', '既有门式刚架建筑屋面光伏增载初筛复核摘要')}",
        f"- {same_line('Boundary: not a final design deliverable or signed code review', '边界：本输出不替代正式设计成果，也不构成签章规范复核')}",
        f"- {same_line('Code path', '规范路径')}: {same_line(translate_option('en', 'design_standard_context', intake.design_standard_context), translate_option('zh', 'design_standard_context', intake.design_standard_context))}",
        (
            f"- {same_line('Known structural system', '当前已知结构体系')}: "
            f"{same_line(localize_preset_text('en', 'structural_system', intake.structural_system), localize_preset_text('zh', 'structural_system', intake.structural_system))}"
        ),
        (
            f"- {same_line('Steel Grade', '钢材标号')}: "
            f"{same_line(intake.steel_grade or 'Not confirmed', intake.steel_grade or '尚未确认')}"
        ),
    ]

    strength_ratio = _find_kernel_calc_output(kernel_outcome, "purlin_strength_ratio")
    deflection_ratio = _find_kernel_calc_output(kernel_outcome, "purlin_deflection_ratio")
    added_load = _find_kernel_calc_output(kernel_outcome, "added_load_kpa")
    memo_calc_lines: list[str] = []
    if strength_ratio is not None and deflection_ratio is not None and kernel_outcome is not None:
        memo_calc_lines.extend(
            [
                f"- {same_line('Added roof dead load', '新增屋面恒载')}: {(format_calc_value(added_load) if added_load is not None else 'N/A')}",
                f"- {same_line('Purlin Strength Ratio', '檩条强度比')}: {format_calc_value(strength_ratio)}",
                f"- {same_line('Purlin Deflection Ratio', '檩条挠度比')}: {format_calc_value(deflection_ratio)}",
            ]
        )
        critical_added_load = _find_kernel_calc_output(kernel_outcome, "critical_added_load_kpa")
        if critical_added_load is not None:
            memo_calc_lines.append(
                f"- {same_line('Estimated Critical Added Load', '临界新增荷载估算')}: {format_calc_value(critical_added_load)}"
            )
        remaining_margin = _find_kernel_calc_output(kernel_outcome, "remaining_added_load_margin_kpa")
        if remaining_margin is not None:
            memo_calc_lines.append(
                f"- {same_line('Remaining Added-Load Margin', '剩余新增荷载余量')}: {format_calc_value(remaining_margin)}"
            )
        primary_frame_ratio = _find_kernel_calc_output(kernel_outcome, "primary_frame_screening_ratio")
        if primary_frame_ratio is not None:
            memo_calc_lines.append(
                f"- {same_line('Primary Frame Screening Ratio', '主门架筛查比值')}: {format_calc_value(primary_frame_ratio)}"
            )
        primary_frame_column_added_moment = _find_kernel_calc_output(kernel_outcome, "primary_frame_column_added_moment_proxy")
        if primary_frame_column_added_moment is not None:
            memo_calc_lines.append(
                f"- {same_line('Primary Frame Column Added Moment Proxy', '主门架柱附加弯矩代理值')}: {format_calc_value(primary_frame_column_added_moment)}"
            )
        primary_frame_rafter_ratio = _find_kernel_calc_output(kernel_outcome, "primary_frame_rafter_screening_ratio")
        if primary_frame_rafter_ratio is not None:
            memo_calc_lines.append(
                f"- {same_line('Primary Frame Rafter Screening Ratio', '主门架梁筛查比值')}: {format_calc_value(primary_frame_rafter_ratio)}"
            )
        primary_frame_column_ratio = _find_kernel_calc_output(kernel_outcome, "primary_frame_column_screening_ratio")
        if primary_frame_column_ratio is not None:
            memo_calc_lines.append(
                f"- {same_line('Primary Frame Column Screening Ratio', '主门架柱筛查比值')}: {format_calc_value(primary_frame_column_ratio)}"
            )
        for calc_id in (
            "purlin_strength_ratio",
            "purlin_deflection_ratio",
            "critical_added_load_kpa",
            "remaining_added_load_margin_kpa",
            "primary_frame_column_added_moment_proxy",
            "primary_frame_rafter_screening_ratio",
            "primary_frame_column_screening_ratio",
            "primary_frame_screening_ratio",
        ):
            calc_item = _find_kernel_calc_output(kernel_outcome, calc_id)
            if calc_item is not None and (calc_item.formula_en or calc_item.formula_zh):
                memo_calc_lines.append(
                    f"  - {same_line('Formula', '计算式')}: {same_line(calc_item.formula_en or '-', calc_item.formula_zh or '-')}"
                )
            if calc_item is not None and calc_item.unit:
                memo_calc_lines.append(
                    f"  - {same_line('Result Unit', '结果单位')}: {_format_bilingual_unit(calc_item.unit)}"
                )
    else:
        memo_calc_lines.append(
            f"- {same_line('Evidence remains insufficient for defendable simplified calculations', '当前证据条件仍不足以形成可辩护的简化计算结果')}"
        )

    if kernel_outcome is not None:
        kernel_status_label = {
            "go": same_line("Go", "可推进"),
            "conditional_go": same_line("Conditional Go", "有条件推进"),
            "no_go": same_line("No-Go", "暂不建议推进"),
        }.get(
            kernel_outcome.decision.status,
            same_line(kernel_outcome.decision.status, kernel_outcome.decision.status),
        )
        memo_calc_lines.append(
            f"- {same_line('Current screening decision', '当前筛查结论')}: "
            f"{kernel_status_label}"
        )

    if result.status == DecisionStatus.CONDITIONAL_GO:
        conclusion_text = same_line(
            "The case is conditionally supportable for continued review, but it is not yet a final go decision.",
            "该案例可作为有条件继续复核的对象，但尚不足以形成最终放行结论。",
        )
    elif result.status == DecisionStatus.GO:
        conclusion_text = same_line(
            "The screening result supports progression, subject to the listed review actions.",
            "当前筛查结果支持推进，但仍需完成所列复核动作。",
        )
    else:
        conclusion_text = same_line(
            "The screening result does not support progression at this stage.",
            "当前筛查结果不支持继续推进。",
        )

    preliminary_conclusion_lines = [
        f"- {conclusion_text}",
    ]
    controlling_factor_line = _controlling_factor_line(kernel_outcome)
    if controlling_factor_line is not None:
        preliminary_conclusion_lines.append(f"- {controlling_factor_line}")
    if result.recommended_actions:
        preliminary_conclusion_lines.append(
            f"- {same_line('Open review item still governing the next stage', '当前主导下一阶段的未闭合复核项')}: "
            f"{same_line(result.recommended_actions[0].title_en, result.recommended_actions[0].title_zh)}"
        )

    recommended_action_lines: list[str] = []
    if result.missing_data:
        recommended_action_lines.append(f"### {same_line(translate('en', 'must_do'), translate('zh', 'must_do'))}")
        recommended_action_lines.extend(
            f"- {same_line(item.title_en, item.title_zh)}"
            for item in result.missing_data
        )
    if result.review_required:
        recommended_action_lines.append(f"### {same_line(translate('en', 'parallel'), translate('zh', 'parallel'))}")
        recommended_action_lines.extend(
            f"- {same_line(item.title_en, item.title_zh)}"
            for item in result.review_required
        )
    for phase in ["must_do", "parallel", "later"]:
        items = [item for item in result.recommended_actions if item.phase == phase]
        if not items:
            continue
        heading = f"### {same_line(translate('en', phase), translate('zh', phase))}"
        if heading not in recommended_action_lines:
            recommended_action_lines.append(heading)
        recommended_action_lines.extend(f"- {same_line(item.title_en, item.title_zh)}" for item in items)

    return [
        "\n".join(scope_lines),
        "\n".join(memo_calc_lines),
        "\n".join(preliminary_conclusion_lines),
        "\n".join(recommended_action_lines),
    ]


def build_report_filename(case_key: str, report_date: Optional[date] = None) -> str:
    current_date = report_date or date.today()
    return f"{current_date.isoformat()}-{case_key}-screening-report.md"


def _build_report_preview_title(
    intake: BuildingIntake,
    language: Language,
    kernel_outcome: Optional[KernelOutcome],
) -> str:
    if kernel_outcome is not None and intake.project_type == "rooftop_pv":
        return (
            "门式刚架屋面光伏增载初筛复核摘要"
            if language == "zh"
            else "Portal-Frame Rooftop PV Screening Review Summary"
        )
    return translate(language, "decision_memo")


def build_report_preview(
    intake: BuildingIntake,
    result: ScreeningResult,
    explanation: LLMExplanation,
    language: Language = "zh",
    kernel_outcome: Optional[KernelOutcome] = None,
) -> ReportPreview:
    screening_snapshot_items = build_screening_snapshot(intake, language)
    management_summary_items = build_management_summary(result, language)
    drawing_facts_items = build_drawing_facts_summary(intake, language)
    assumptions_items = build_assumptions_and_limitations(intake, result, language, kernel_outcome)
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
                format_option_detail(option, "screening_cost_range", language),
                (
                    f"{translate(language, 'screening_cost_note')}: "
                    f"{'仅供初筛阶段方案比较，不替代正式报价或预算。' if language == 'zh' else 'For screening-stage option comparison only; not a formal quotation or budget.'}"
                ),
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

    sections = []
    if kernel_outcome is not None:
        memo_scope_block, memo_calc_block, memo_conclusion_block, memo_actions_block = _build_structural_memo_sections(
            intake,
            result,
            kernel_outcome,
        )
        sections.extend(
            [
                ReportPreviewSection(
                    heading=translate(language, "assessment_scope"),
                    items=memo_scope_block.splitlines() or [translate(language, "none")],
                ),
                ReportPreviewSection(
                    heading=translate(language, "simplified_calculation_results"),
                    items=memo_calc_block.splitlines() or [translate(language, "none")],
                ),
                ReportPreviewSection(
                    heading=translate(language, "preliminary_structural_conclusion"),
                    items=memo_conclusion_block.splitlines() or [translate(language, "none")],
                ),
                ReportPreviewSection(
                    heading=translate(language, "next_step_review_actions"),
                    items=memo_actions_block.splitlines() or [translate(language, "none")],
                ),
            ]
        )

    sections.extend([
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
                    f"{translate(language, 'building_type')}: {localize_preset_text(language, 'building_type', intake.building_type)}",
                    f"{translate(language, 'structural_system')}: {localize_preset_text(language, 'structural_system', intake.structural_system)}",
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
        ])

    return ReportPreview(
        title=_build_report_preview_title(intake, language, kernel_outcome),
        sections=sections,
    )


def build_markdown_report(
    intake: BuildingIntake,
    result: ScreeningResult,
    explanation: LLMExplanation,
    kernel_outcome: Optional[KernelOutcome] = None,
) -> str:
    screening_snapshot_lines = build_screening_snapshot(intake, "en")
    screening_snapshot_lines_zh = build_screening_snapshot(intake, "zh")
    management_summary_en = build_management_summary(result, "en")
    management_summary_zh = build_management_summary(result, "zh")
    drawing_facts_en = build_drawing_facts_summary(intake, "en")
    drawing_facts_zh = build_drawing_facts_summary(intake, "zh")
    assumptions_en = build_assumptions_and_limitations(intake, result, "en", kernel_outcome)
    assumptions_zh = build_assumptions_and_limitations(intake, result, "zh", kernel_outcome)
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
                        f"- {same_line('Screening Cost Range', '初筛成本区间')}: "
                        f"{same_line(option.screening_cost_range_en, option.screening_cost_range_zh)}"
                    ),
                    (
                        f"- {same_line('Cost Range Note', '成本区间说明')}: "
                        f"{same_line('For screening-stage option comparison only; not a formal quotation or budget.', '仅供初筛阶段方案比较，不替代正式报价或预算。')}"
                    ),
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
    traceability_block = _build_traceability_lines(result)
    assessment_basis_and_calc_block = _build_assessment_basis_and_calc_lines(kernel_outcome)
    memo_sections = None
    if kernel_outcome is not None:
        memo_sections = _build_structural_memo_sections(
            intake,
            result,
            kernel_outcome,
        )

    title = (
        "# Portal-Frame Rooftop PV Screening Review Summary | 门式刚架屋面光伏增载初筛复核摘要"
        if kernel_outcome is not None
        else "# Structural Screening Review | 结构初筛复核"
    )
    sections = [title, ""]
    if memo_sections is not None:
        memo_scope_block, memo_calc_block, memo_conclusion_block, memo_actions_block = memo_sections
        sections.extend(
            [
                "## Review Scope and Boundary | 复核范围与边界",
                memo_scope_block,
                "",
                "## Simplified Calculation Results | 简化计算结果",
                memo_calc_block,
                "",
                "## Preliminary Structural Conclusion | 初步结构结论",
                memo_conclusion_block,
                "",
                "## Recommended Next-Step Review Actions | 后续复核建议",
                memo_actions_block or "None | 无",
                "",
            ]
        )
    sections.extend(
        [
        "## Project Summary | 项目概况",
        f"- {same_line('Project Type', '项目类型')}: {same_line(translate_option('en', 'project_type', intake.project_type), translate_option('zh', 'project_type', intake.project_type))}",
        f"- {same_line('Design Standard Context', '规范体系')}: {same_line(translate_option('en', 'design_standard_context', intake.design_standard_context), translate_option('zh', 'design_standard_context', intake.design_standard_context))}",
        f"- {same_line('Building Type', '建筑类型')}: {same_line(localize_preset_text('en', 'building_type', intake.building_type), localize_preset_text('zh', 'building_type', intake.building_type))}",
        f"- {same_line('Structural System', '结构体系')}: {same_line(localize_preset_text('en', 'structural_system', intake.structural_system), localize_preset_text('zh', 'structural_system', intake.structural_system))}",
        f"- {same_line('Steel Grade', '钢材标号')}: {same_line(intake.steel_grade or 'Not confirmed', intake.steel_grade or '尚未确认')}",
        (
            f"- {same_line('Available Verification Path', '可用复核路径')}: "
            f"{same_line(translate_option('en', 'available_verification_path', intake.available_verification_path), translate_option('zh', 'available_verification_path', intake.available_verification_path))}"
        ),
        "",
        "## Assessment Basis and Screening Calculations | 评估依据与筛查计算",
        assessment_basis_and_calc_block,
        "",
        "## Verification Readiness | 结构复核准备度",
        verification_readiness_block,
        "",
        "## Engineering Screening Checks | 工程筛查检查",
        engineering_check_block,
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
        "## Main-Case Screening Inputs | 主案例筛查项",
        screening_snapshot_block,
        "",
        "## Drawing Facts Summary | 图纸关键信息摘录",
        drawing_facts_block,
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
    ])
    sections.extend(
        [
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
        "## Traceability and Basis | 可追溯性与依据",
        traceability_block,
        "",
        "## Review Note | 复核说明",
        explanation.summary,
        "",
        "## Options | 方案选项",
        option_lines,
        ]
    )
    return "\n".join(sections)
