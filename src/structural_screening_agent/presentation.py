from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel

from structural_screening_agent.assumptions import build_assumptions_and_limitations
from structural_screening_agent.check_linkage import build_check_action_links
from structural_screening_agent.decision_chain import build_decision_chain
from structural_screening_agent.drawing_facts import build_drawing_facts_summary
from structural_screening_agent.intake_snapshot import build_screening_snapshot
from structural_screening_agent.localization import (
    Language,
    format_bilingual_detail,
    format_bilingual_item,
    format_confidence,
    format_decision_localized,
    format_attachment_pathway,
    format_engineering_check,
    format_option_detail,
    format_resource_recommendation,
    format_reserve_uncertainty,
    format_review_trigger,
    format_verification_readiness,
    localize_calc_unit,
    localize_basis_term,
    localize_input_path,
    translate,
    translate_option,
)
from structural_screening_agent.management_summary import build_management_summary
from structural_screening_agent.core.kernel import BasisReferenceOutput, CalculationOutput, KernelOutcome
from structural_screening_agent.models import DecisionStatus, LLMExplanation, ScreeningOption, ScreeningResult
from structural_screening_agent.review_path_summary import build_review_progression_summary


class ContentCard(BaseModel):
    title: str
    detail: str
    tone: Literal["neutral", "amber", "red", "blue", "green"] = "neutral"


class OptionCard(BaseModel):
    title: str
    details: List[str]
    emphasis: Literal["primary", "secondary"] = "secondary"


class AgentPanel(BaseModel):
    provider_label: str
    summary: str
    notice: Optional[str] = None


class ActionGroup(BaseModel):
    title: str
    cards: List[ContentCard]


class WorkbenchView(BaseModel):
    hero_decision: str
    hero_tone: Literal["green", "amber", "red"]
    confidence_label: str
    scenario_label: str
    standards_context_label: str
    conclusion_overview_card: Optional[ContentCard]
    assessment_metric_cards: List[ContentCard]
    assessment_scope_cards: List[ContentCard]
    evidence_overview_cards: List[ContentCard]
    evidence_status_cards: List[ContentCard]
    calc_summary_cards: List[ContentCard]
    load_combination_sensitivity_cards: List[ContentCard]
    basis_reference_cards: List[ContentCard]
    preliminary_conclusion_cards: List[ContentCard]
    next_step_cards: List[ContentCard]
    management_summary: List[str]
    screening_snapshot: List[str]
    drawing_facts: List[str]
    assumptions_limitations: List[str]
    decision_chain: List[str]
    verification_readiness_title: str
    verification_readiness_summary: str
    verification_blockers: List[ContentCard]
    engineering_check_cards: List[ContentCard]
    member_reserve_uncertainty_cards: List[ContentCard]
    attachment_pathway_cards: List[ContentCard]
    resource_recommendation_cards: List[ContentCard]
    review_trigger_cards: List[ContentCard]
    traceability_cards: List[ContentCard]
    review_progression_summary: List[str]
    check_action_links: List[ContentCard]
    risk_cards: List[ContentCard]
    missing_data_cards: List[ContentCard]
    action_cards: List[ContentCard]
    action_groups: List[ActionGroup]
    question_cards: List[ContentCard]
    review_needed_cards: List[ContentCard]
    options: List[OptionCard]
    agent: AgentPanel
    report_title: str


def _decision_tone(status: DecisionStatus) -> Literal["green", "amber", "red"]:
    if status == DecisionStatus.GO:
        return "green"
    if status == DecisionStatus.NO_GO:
        return "red"
    return "amber"


def _option_details(option: ScreeningOption, language: Language) -> List[str]:
    details = []
    rationale = getattr(option, f"priority_rationale_{language}")
    if rationale:
        details.append(f"{translate(language, 'priority_rationale')}: {rationale}")
    details.extend([
        format_option_detail(option, "fit_when", language),
        format_option_detail(option, "main_constraint", language),
        format_option_detail(option, "operational_impact", language),
        format_option_detail(option, "cost_level", language),
        format_option_detail(option, "screening_cost_range", language),
        (
            "成本区间说明: 仅供初筛阶段方案比较，不替代正式报价或预算。"
            if language == "zh"
            else "Cost Range Note: For screening-stage option comparison only; not a formal quotation or budget."
        ),
        format_option_detail(option, "schedule_impact", language),
        format_option_detail(option, "recommendation_note", language),
    ])
    return details


def _build_action_groups(result: ScreeningResult, language: Language) -> List[ActionGroup]:
    grouped_cards = {"must_do": [], "parallel": [], "later": []}
    for item in result.recommended_actions:
        grouped_cards[item.phase].append(
            ContentCard(title=format_bilingual_item(item, language), detail="", tone="green")
        )

    ordered_phases = ["must_do", "parallel", "later"]
    return [
        ActionGroup(title=translate(language, phase), cards=grouped_cards[phase])
        for phase in ordered_phases
        if grouped_cards[phase]
    ]


def _build_traceability_cards(result: ScreeningResult, language: Language) -> List[ContentCard]:
    cards: List[ContentCard] = []
    for item in result.traceability:
        traces = ", ".join(
            f"{localize_input_path(language, trace.input_path)}={trace.observed_value}"
            for trace in item.traces
        ) or translate(language, "none")
        detail = f"{translate(language, 'input_traces')}: {traces}"
        cards.append(
            ContentCard(
                title=item.summary_zh if language == "zh" else item.summary_en,
                detail=detail,
                tone="red" if item.severity == "blocking" else ("amber" if item.severity == "caution" else "blue"),
            )
        )
    return cards


def _find_calc_output(kernel_outcome: Optional[KernelOutcome], calc_id: str) -> Optional[CalculationOutput]:
    if kernel_outcome is None:
        return None
    return next((item for item in kernel_outcome.calc_outputs if item.calc_id == calc_id), None)


def _controlling_factor_detail(kernel_outcome: Optional[KernelOutcome], language: Language) -> Optional[str]:
    if kernel_outcome is None:
        return None
    if kernel_outcome.controlling_path is not None:
        return (
            kernel_outcome.controlling_path.summary_zh
            if language == "zh"
            else kernel_outcome.controlling_path.summary_en
        )
    candidates = [
        ("purlin_strength_ratio", "Purlin strength check", "檩条强度筛查"),
        ("purlin_deflection_ratio", "Purlin deflection check", "檩条挠度筛查"),
        ("primary_frame_rafter_screening_ratio", "Primary-frame rafter added-moment screening", "主门架梁附加弯矩筛查"),
        ("primary_frame_column_screening_ratio", "Primary-frame column added-moment screening", "主门架柱附加弯矩筛查"),
        ("primary_frame_screening_ratio", "Primary-frame added-moment screening", "主门架附加弯矩筛查"),
    ]
    best: tuple[str, float] | None = None
    best_labels: tuple[str, str] | None = None
    for calc_id, label_en, label_zh in candidates:
        item = _find_calc_output(kernel_outcome, calc_id)
        if item is None or item.numeric_value is None:
            continue
        value = float(item.numeric_value)
        if best is None or value > best[1]:
            best = (calc_id, value)
            best_labels = (label_en, label_zh)
    if best is None or best_labels is None:
        return None
    label_en, label_zh = best_labels
    return (
        f"当前控制因素主要落在{label_zh}。"
        if language == "zh"
        else f"Current controlling factor is the {label_en}."
    )


def _build_assessment_scope_cards(evaluation: Dict[str, Any], language: Language) -> List[ContentCard]:
    intake = evaluation["intake"]
    kernel_case = evaluation.get("kernel_case")
    screening_level = getattr(getattr(kernel_case, "evidence", None), "screening_level", None)
    cards = [
        ContentCard(
            title="复核范围" if language == "zh" else "Review Scope",
            detail=(
                "既有单层门式刚架建筑屋面光伏增载初筛。"
                if language == "zh"
                else "Screening review for rooftop PV added load on an existing single-story portal-frame building."
            ),
            tone="blue",
        ),
        ContentCard(
            title="规范路径" if language == "zh" else "Code Path",
            detail=translate_option(language, "design_standard_context", intake.design_standard_context),
            tone="blue",
        ),
    ]
    if screening_level:
        cards.append(
            ContentCard(
                title="资料等级" if language == "zh" else "Evidence Level",
                detail=screening_level,
                tone="amber" if screening_level != "level_a" else "green",
            )
        )
    return cards


def _build_evidence_status_cards(kernel_outcome: Optional[KernelOutcome], language: Language) -> List[ContentCard]:
    if kernel_outcome is None:
        return []
    tone_map = {"available": "green", "partial": "amber", "missing": "red", "undetermined": "amber"}
    return [
        ContentCard(
            title=item.summary_zh if language == "zh" else item.summary_en,
            detail=", ".join(localize_input_path(language, path) for path in item.source_paths),
            tone=tone_map.get(item.status, "amber"),
        )
        for item in kernel_outcome.evidence_snapshot
    ]


def _build_evidence_overview_cards(kernel_outcome: Optional[KernelOutcome], language: Language) -> List[ContentCard]:
    if kernel_outcome is None or not kernel_outcome.evidence_snapshot:
        return []
    counts = {"available": 0, "partial": 0, "missing": 0, "undetermined": 0}
    for item in kernel_outcome.evidence_snapshot:
        counts[item.status] = counts.get(item.status, 0) + 1
    detail = (
        f"已掌握 {counts['available']} 项，部分掌握 {counts['partial']} 项，缺失 {counts['missing']} 项。"
        if language == "zh"
        else f"{counts['available']} available, {counts['partial']} partial, {counts['missing']} missing."
    )
    tone = "red" if counts["missing"] else ("amber" if counts["partial"] else "green")
    return [
        ContentCard(
            title="证据摘要" if language == "zh" else "Evidence Overview",
            detail=detail,
            tone=tone,
        )
    ]


def _build_calc_summary_cards(
    kernel_outcome: Optional[KernelOutcome],
    screening_level: Optional[str],
    language: Language,
) -> List[ContentCard]:
    if kernel_outcome is None:
        return []
    ordered_calc_ids = [
        "added_load_kpa",
        "purlin_strength_ratio",
        "purlin_deflection_ratio",
        "critical_added_load_kpa",
        "remaining_added_load_margin_kpa",
        "primary_frame_line_load",
        "primary_frame_added_moment_proxy",
        "primary_frame_column_added_moment_proxy",
        "primary_frame_rafter_screening_ratio",
        "primary_frame_rafter_deflection_sensitivity",
        "primary_frame_column_screening_ratio",
        "primary_frame_column_stability_sensitivity",
        "primary_frame_screening_ratio",
        "verification_readiness_score",
        "uncertainty_score",
    ]
    title_map = {
        "added_load_kpa": ("新增屋面恒载", "Added Roof Load"),
        "purlin_strength_ratio": ("檩条强度比", "Purlin Strength Ratio"),
        "purlin_deflection_ratio": ("檩条挠度比", "Purlin Deflection Ratio"),
        "critical_added_load_kpa": ("临界新增荷载估算", "Estimated Critical Added Load"),
        "remaining_added_load_margin_kpa": ("剩余新增荷载余量", "Remaining Added-Load Margin"),
        "primary_frame_line_load": ("主门架附加线荷载", "Primary Frame Line Load"),
        "primary_frame_added_moment_proxy": ("主门架附加弯矩代理值", "Primary Frame Added Moment Proxy"),
        "primary_frame_column_added_moment_proxy": ("主门架柱附加弯矩代理值", "Primary Frame Column Added Moment Proxy"),
        "primary_frame_rafter_screening_ratio": ("主门架梁筛查比值", "Primary Frame Rafter Screening Ratio"),
        "primary_frame_rafter_deflection_sensitivity": ("主门架梁挠度敏感性", "Primary Frame Rafter Deflection Sensitivity"),
        "primary_frame_column_screening_ratio": ("主门架柱筛查比值", "Primary Frame Column Screening Ratio"),
        "primary_frame_column_stability_sensitivity": ("主门架柱稳定敏感性", "Primary Frame Column Stability Sensitivity"),
        "primary_frame_screening_ratio": ("主门架筛查比值", "Primary Frame Screening Ratio"),
        "verification_readiness_score": ("复核准备度分数", "Verification Readiness Score"),
        "uncertainty_score": ("不确定性分数", "Uncertainty Score"),
    }
    cards: List[ContentCard] = []

    def format_calc_value(item: CalculationOutput) -> str:
        if not item.unit:
            return item.value_text
        unit_text = localize_calc_unit(language, item.unit)
        if item.unit == "dimensionless":
            return f"{item.value_text} ({unit_text})"
        return f"{item.value_text} {unit_text}"

    for calc_id in ordered_calc_ids:
        item = _find_calc_output(kernel_outcome, calc_id)
        if item is None:
            continue
        title_zh, title_en = title_map[calc_id]
        detail_lines = [
            f"{format_calc_value(item)} | {item.summary_zh if language == 'zh' else item.summary_en}"
        ]
        formula_text = item.formula_zh if language == "zh" else item.formula_en
        if formula_text:
            detail_lines.append(f"{'计算式' if language == 'zh' else 'Formula'}: {formula_text}")
        if item.unit:
            detail_lines.append(
                f"{translate(language, 'result_unit')}: {localize_calc_unit(language, item.unit)}"
            )
        cards.append(
            ContentCard(
                title=title_zh if language == "zh" else title_en,
                detail="\n".join(detail_lines),
                tone="green" if calc_id in {"added_load_kpa", "verification_readiness_score"} else "amber",
            )
        )
    if not any(card.title in {"檩条强度比", "Purlin Strength Ratio"} for card in cards) and screening_level == "level_c":
        cards.append(
            ContentCard(
                title="当前未进入檩条简化验算" if language == "zh" else "Purlin Check Not Yet Available",
                detail=(
                    "当前资料等级为 level_c，系统仅能给出荷载与证据链判断，不能形成可辩护的檩条强度/挠度筛查结果。"
                    if language == "zh"
                    else "Current evidence remains at level_c, so the system can only provide load and evidence judgments, not a defendable purlin strength/deflection screening result."
                ),
                tone="red",
            )
        )
    return cards


def _build_basis_reference_cards(kernel_outcome: Optional[KernelOutcome], language: Language) -> List[ContentCard]:
    if kernel_outcome is None:
        return []
    cards: List[ContentCard] = []
    for item in kernel_outcome.basis_references:
        title = item.title_zh if language == "zh" else item.title_en
        citation = item.citation_zh if language == "zh" else item.citation_en
        standards = ", ".join(
            translate_option(language, "design_standard_context", standard)
            for standard in item.applicable_standards
        ) or translate(language, "none")
        trigger_conditions = "; ".join(
            localize_basis_term(language, condition) for condition in item.trigger_conditions
        ) or translate(language, "none")
        evidence_requirements = "; ".join(
            localize_basis_term(language, requirement) for requirement in item.evidence_requirements
        ) or translate(language, "none")
        review_requirements = "; ".join(
            localize_basis_term(language, requirement) for requirement in item.review_requirements
        ) or translate(language, "none")
        detail = "\n".join(
            [
                f"{translate(language, 'engineering_meaning')}: {citation}",
                f"{translate(language, 'applicable_standards')}: {standards}",
                f"{translate(language, 'trigger_conditions')}: {trigger_conditions}",
                f"{translate(language, 'evidence_requirements')}: {evidence_requirements}",
                f"{translate(language, 'follow_up_review')}: {review_requirements}",
            ]
        )
        cards.append(ContentCard(title=title, detail=detail, tone="blue"))
    return cards


def _build_load_combination_sensitivity_cards(
    kernel_outcome: Optional[KernelOutcome],
    language: Language,
) -> List[ContentCard]:
    if kernel_outcome is None:
        return []
    return [
        ContentCard(
            title=item.title_zh if language == "zh" else item.title_en,
            detail=item.summary_zh if language == "zh" else item.summary_en,
            tone="amber",
        )
        for item in kernel_outcome.load_combination_sensitivities
    ]


def _build_preliminary_conclusion_cards(
    result: ScreeningResult,
    kernel_outcome: Optional[KernelOutcome],
    language: Language,
) -> List[ContentCard]:
    cards = [
        ContentCard(
            title="初步结论" if language == "zh" else "Preliminary Conclusion",
            detail=format_decision_localized(result.status, language),
            tone=_decision_tone(result.status),
        )
    ]
    controlling_factor = _controlling_factor_detail(kernel_outcome, language)
    if controlling_factor:
        cards.append(
            ContentCard(
                title="当前控制因素" if language == "zh" else "Current Controlling Factor",
                detail=controlling_factor,
                tone="amber",
            )
        )
    if kernel_outcome is not None and kernel_outcome.triggered_rules:
        for item in kernel_outcome.triggered_rules[:3]:
            cards.append(
                ContentCard(
                    title=item.summary_zh if language == "zh" else item.summary_en,
                    detail=", ".join(item.basis_ids) or translate(language, "none"),
                    tone="red" if item.severity == "blocking" else ("amber" if item.severity == "caution" else "blue"),
                )
            )
    return cards


def _build_next_step_cards(result: ScreeningResult, language: Language) -> List[ContentCard]:
    cards: List[ContentCard] = []
    for item in result.recommended_actions[:5]:
        cards.append(
            ContentCard(
                title=format_bilingual_item(item, language),
                detail=translate(language, item.phase),
                tone="green" if item.phase == "must_do" else ("blue" if item.phase == "parallel" else "neutral"),
            )
        )
    return cards


def _build_assessment_metric_cards(
    result: ScreeningResult,
    kernel_outcome: Optional[KernelOutcome],
    language: Language,
) -> List[ContentCard]:
    cards = [
        ContentCard(
            title="当前结论" if language == "zh" else "Current Decision",
            detail=format_decision_localized(result.status, language),
            tone=_decision_tone(result.status),
        )
    ]
    controlling_factor = _controlling_factor_detail(kernel_outcome, language)
    if controlling_factor:
        cards.append(
            ContentCard(
                title="控制因素" if language == "zh" else "Controlling Factor",
                detail=controlling_factor,
                tone="amber",
            )
        )
    ratio_candidates = [
        _find_calc_output(kernel_outcome, "purlin_strength_ratio"),
        _find_calc_output(kernel_outcome, "purlin_deflection_ratio"),
        _find_calc_output(kernel_outcome, "primary_frame_rafter_screening_ratio"),
        _find_calc_output(kernel_outcome, "primary_frame_column_screening_ratio"),
        _find_calc_output(kernel_outcome, "primary_frame_screening_ratio"),
    ]
    numeric_items = [item for item in ratio_candidates if item is not None and item.numeric_value is not None]
    if numeric_items:
        governing_item = max(numeric_items, key=lambda item: float(item.numeric_value or 0))
        cards.append(
            ContentCard(
                title="控制比值" if language == "zh" else "Governing Ratio",
                detail=f"{governing_item.value_text} | {governing_item.summary_zh if language == 'zh' else governing_item.summary_en}",
                tone="amber",
            )
        )
    return cards


def _build_conclusion_overview_card(
    result: ScreeningResult,
    kernel_outcome: Optional[KernelOutcome],
    language: Language,
) -> ContentCard:
    lines = [
        (
            f"当前结论：{format_decision_localized(result.status, language)}"
            if language == "zh"
            else f"Current decision: {format_decision_localized(result.status, language)}"
        )
    ]
    controlling_factor = _controlling_factor_detail(kernel_outcome, language)
    if controlling_factor:
        lines.append(
            (
                f"控制因素：{controlling_factor.replace('当前控制因素主要落在', '').rstrip('。')}"
                if language == "zh"
                else f"Controlling factor: {controlling_factor.replace('Current controlling factor is the ', '').rstrip('.')}"
            )
        )
    ratio_candidates = [
        _find_calc_output(kernel_outcome, "purlin_strength_ratio"),
        _find_calc_output(kernel_outcome, "purlin_deflection_ratio"),
        _find_calc_output(kernel_outcome, "primary_frame_rafter_screening_ratio"),
        _find_calc_output(kernel_outcome, "primary_frame_column_screening_ratio"),
        _find_calc_output(kernel_outcome, "primary_frame_screening_ratio"),
    ]
    numeric_items = [item for item in ratio_candidates if item is not None and item.numeric_value is not None]
    if numeric_items:
        governing_item = max(numeric_items, key=lambda item: float(item.numeric_value or 0))
        lines.append(
            (
                f"控制比值：{governing_item.value_text}"
                if language == "zh"
                else f"Governing ratio: {governing_item.value_text}"
            )
        )
    return ContentCard(
        title="结论摘要" if language == "zh" else "Conclusion Overview",
        detail="\n".join(lines),
        tone=_decision_tone(result.status),
    )


def build_workbench_view(evaluation: Dict[str, Any], language: Language = "zh") -> WorkbenchView:
    intake = evaluation["intake"]
    result: ScreeningResult = evaluation["result"]
    explanation: LLMExplanation = evaluation["explanation"]
    questions: List[str] = evaluation["questions"]
    kernel_outcome: Optional[KernelOutcome] = evaluation.get("kernel_outcome")
    screening_level = getattr(getattr(evaluation.get("kernel_case"), "evidence", None), "screening_level", None)

    option_cards = [
        OptionCard(
            title=format_bilingual_item(option, language),
            details=_option_details(option, language),
            emphasis="primary" if index == 0 else "secondary",
        )
        for index, option in enumerate(result.options)
    ]

    question_cards = [
        ContentCard(title=f"Q{index + 1}", detail=question, tone="blue")
        for index, question in enumerate(questions)
    ]
    action_groups = _build_action_groups(result, language)

    return WorkbenchView(
        hero_decision=format_decision_localized(result.status, language),
        hero_tone=_decision_tone(result.status),
        confidence_label=f"{translate(language, 'confidence')}: {format_confidence(result.confidence, language)}",
        scenario_label=f"{translate(language, 'scenario')}: {translate_option(language, 'project_type', intake.project_type)}",
        standards_context_label=(
            f"{translate(language, 'design_standard_context')}: "
            f"{translate_option(language, 'design_standard_context', intake.design_standard_context)}"
        ),
        conclusion_overview_card=_build_conclusion_overview_card(result, kernel_outcome, language),
        assessment_metric_cards=_build_assessment_metric_cards(result, kernel_outcome, language),
        assessment_scope_cards=_build_assessment_scope_cards(evaluation, language),
        evidence_overview_cards=_build_evidence_overview_cards(kernel_outcome, language),
        evidence_status_cards=_build_evidence_status_cards(kernel_outcome, language),
        calc_summary_cards=_build_calc_summary_cards(kernel_outcome, screening_level, language),
        load_combination_sensitivity_cards=_build_load_combination_sensitivity_cards(kernel_outcome, language),
        basis_reference_cards=_build_basis_reference_cards(kernel_outcome, language),
        preliminary_conclusion_cards=_build_preliminary_conclusion_cards(result, kernel_outcome, language),
        next_step_cards=_build_next_step_cards(result, language),
        management_summary=build_management_summary(result, language),
        screening_snapshot=build_screening_snapshot(intake, language),
        drawing_facts=build_drawing_facts_summary(intake, language),
        assumptions_limitations=build_assumptions_and_limitations(intake, result, language, kernel_outcome),
        decision_chain=build_decision_chain(result, language),
        verification_readiness_title=(
            f"{translate(language, 'verification_readiness')}: "
            f"{format_verification_readiness(result.verification_readiness.level, language)}"
        ),
        verification_readiness_summary=(
            result.verification_readiness.summary_zh
            if language == "zh"
            else result.verification_readiness.summary_en
        ),
        verification_blockers=[
            ContentCard(title=format_bilingual_item(item, language), detail="", tone="amber")
            for item in result.verification_readiness.blockers
        ],
        engineering_check_cards=[
            ContentCard(
                title=format_engineering_check(item, language),
                detail=item.summary_zh if language == "zh" else item.summary_en,
                tone="green" if item.status == "screen_pass" else ("red" if item.status == "undetermined" else "amber"),
            )
            for item in result.engineering_checks
        ],
        member_reserve_uncertainty_cards=[
            ContentCard(
                title=format_reserve_uncertainty(item, language),
                detail=item.summary_zh if language == "zh" else item.summary_en,
                tone="red" if item.severity == "high" else ("amber" if item.severity == "medium" else "green"),
            )
            for item in result.member_reserve_uncertainties
        ],
        attachment_pathway_cards=[
            ContentCard(
                title=format_attachment_pathway(item, language),
                detail=item.summary_zh if language == "zh" else item.summary_en,
                tone="green" if item.status == "screen_pass" else ("red" if item.status == "undetermined" else "amber"),
            )
            for item in result.attachment_pathways
        ],
        resource_recommendation_cards=[
            ContentCard(
                title=format_resource_recommendation(item, language),
                detail=item.summary_zh if language == "zh" else item.summary_en,
                tone="blue",
            )
            for item in result.resource_recommendations
        ],
        review_trigger_cards=[
            ContentCard(
                title=format_review_trigger(item, language),
                detail=item.summary_zh if language == "zh" else item.summary_en,
                tone="amber",
            )
            for item in result.review_triggers
        ],
        traceability_cards=_build_traceability_cards(result, language),
        review_progression_summary=build_review_progression_summary(result, language),
        check_action_links=[
            ContentCard(title=link.split("，", 1)[0] if language == "zh" else link.split(" is currently", 1)[0], detail=link, tone="blue")
            for link in build_check_action_links(result, language)
        ],
        risk_cards=[
            ContentCard(title=format_bilingual_item(item, language), detail=format_bilingual_detail(item, language), tone="red")
            for item in result.risks
        ],
        missing_data_cards=[
            ContentCard(title=format_bilingual_item(item, language), detail="", tone="amber")
            for item in result.missing_data
        ],
        action_cards=[
            ContentCard(title=format_bilingual_item(item, language), detail="", tone="green")
            for item in result.recommended_actions
        ],
        action_groups=action_groups,
        question_cards=question_cards,
        review_needed_cards=[
            ContentCard(title=format_bilingual_item(item, language), detail="", tone="amber")
            for item in result.review_required
        ],
        options=option_cards,
        agent=AgentPanel(
            provider_label=(
                translate(language, "mock_fallback")
                if explanation.mode == "fallback"
                else translate(language, "live_model")
            ),
            summary=explanation.summary,
            notice=(
                f"{translate(language, 'fallback_active')}: {explanation.requested_provider} -> mock ({explanation.fallback_reason})"
                if explanation.mode == "fallback" and explanation.requested_provider not in (None, "mock")
                else None
            ),
        ),
        report_title=translate(language, "decision_memo"),
    )
