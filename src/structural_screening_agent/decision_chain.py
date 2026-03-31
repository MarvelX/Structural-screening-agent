from typing import List

from structural_screening_agent.localization import Language
from structural_screening_agent.models import ScreeningResult


def build_decision_chain(result: ScreeningResult, language: Language) -> List[str]:
    top_risk = result.risks[0] if result.risks else None
    must_do = next((item for item in result.recommended_actions if item.phase == "must_do"), None)
    primary_option = result.options[0] if result.options else None
    review_needed = result.review_required[0] if result.review_required else None

    if language == "zh":
        lines = []
        if top_risk:
            lines.append(f"当前首先受限于：{top_risk.title_zh}。")
        if must_do:
            lines.append(f"因此必须先做：{must_do.title_zh}。")
        if primary_option:
            rationale = primary_option.priority_rationale_zh or primary_option.recommendation_note_zh
            lines.append(f"因此当前优先路径是：{primary_option.title_zh}。{rationale}")
        if review_needed:
            lines.append(f"后续规范复核应进入：{review_needed.title_zh}")
        return lines

    lines = []
    if top_risk:
        lines.append(f"The current decision is mainly constrained by: {top_risk.title_en}.")
    if must_do:
        lines.append(f"So the team should first: {must_do.title_en}.")
    if primary_option:
        rationale = primary_option.priority_rationale_en or primary_option.recommendation_note_en
        lines.append(f"Therefore the current preferred path is: {primary_option.title_en}. {rationale}")
    if review_needed:
        lines.append(f"The next code review path should proceed under: {review_needed.title_en}")
    return lines
