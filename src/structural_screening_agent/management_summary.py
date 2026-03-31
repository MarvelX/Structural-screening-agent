from typing import List

from structural_screening_agent.localization import Language, format_decision_localized
from structural_screening_agent.models import ScreeningResult


def build_management_summary(result: ScreeningResult, language: Language) -> List[str]:
    top_risk = result.risks[0] if result.risks else None
    must_do = next((item for item in result.recommended_actions if item.phase == "must_do"), None)
    primary_option = result.options[0] if result.options else None
    review_needed = result.review_required[0] if result.review_required else None

    if language == "zh":
        lines = [f"当前结论：{format_decision_localized(result.status, 'zh')}。"]
        if top_risk:
            lines.append(f"主要约束：{top_risk.title_zh}。")
        if must_do:
            lines.append(f"下一步：{must_do.title_zh}。")
        if primary_option:
            lines.append(f"优先路径：{primary_option.title_zh}。")
        if review_needed:
            lines.append(f"规范复核：{review_needed.title_zh}")
        return lines

    lines = [f"Current Decision: {format_decision_localized(result.status, 'en')}."]
    if top_risk:
        lines.append(f"Primary Constraint: {top_risk.title_en}.")
    if must_do:
        lines.append(f"Next Step: {must_do.title_en}.")
    if primary_option:
        lines.append(f"Preferred Path: {primary_option.title_en}.")
    if review_needed:
        lines.append(f"Code Review Path: {review_needed.title_en}")
    return lines
