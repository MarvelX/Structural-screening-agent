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
    translate,
    translate_option,
)
from structural_screening_agent.management_summary import build_management_summary
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


def build_workbench_view(evaluation: Dict[str, Any], language: Language = "zh") -> WorkbenchView:
    intake = evaluation["intake"]
    result: ScreeningResult = evaluation["result"]
    explanation: LLMExplanation = evaluation["explanation"]
    questions: List[str] = evaluation["questions"]

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
        management_summary=build_management_summary(result, language),
        screening_snapshot=build_screening_snapshot(intake, language),
        drawing_facts=build_drawing_facts_summary(intake, language),
        assumptions_limitations=build_assumptions_and_limitations(intake, result, language),
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
