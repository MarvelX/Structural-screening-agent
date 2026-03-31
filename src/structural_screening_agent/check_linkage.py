from typing import List

from structural_screening_agent.localization import Language, format_bilingual_item
from structural_screening_agent.models import ScreeningResult


def build_check_action_links(result: ScreeningResult, language: Language) -> List[str]:
    primary_option = result.options[0] if result.options else None
    must_do = next((item for item in result.recommended_actions if item.phase == "must_do"), None)
    if not primary_option:
        return []

    lines = []
    for check in result.engineering_checks:
        if language == "zh":
            action_text = must_do.title_zh if must_do else "补齐针对性复核动作"
            lines.append(
                f"{check.title_zh}为“{'可初步放行' if check.status == 'screen_pass' else ('需专项复核' if check.status == 'review' else '当前不可判定')}”，"
                f"因此必须先做：{action_text}；当前优先路径保持为：{primary_option.title_zh}。"
            )
        else:
            action_text = must_do.title_en if must_do else "close the targeted verification action"
            status_text = {
                "screen_pass": "Screen Pass",
                "review": "Review Needed",
                "undetermined": "Undetermined",
            }[check.status]
            lines.append(
                f"{check.title_en} is currently '{status_text}', so the team should first {action_text}; "
                f"the preferred path remains {primary_option.title_en}."
            )
    return lines
