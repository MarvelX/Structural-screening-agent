from typing import List

from structural_screening_agent.localization import Language
from structural_screening_agent.models import ScreeningResult


def build_review_progression_summary(result: ScreeningResult, language: Language) -> List[str]:
    must_do = next((item for item in result.recommended_actions if item.phase == "must_do"), None)
    default_action_zh = must_do.title_zh if must_do else "补齐针对性复核动作"
    default_action_en = must_do.title_en if must_do else "close the targeted verification action"

    path_configs = [
        ("member", "Reserve Capacity Screening", "构件复核路径", "Member Review Path"),
        ("connection", "Attachment Feasibility Screening", "连接复核路径", "Connection Review Path"),
    ]

    lines: List[str] = []
    for category, check_title_en, label_zh, label_en in path_configs:
        trigger = next((item for item in result.review_triggers if item.category == category), None)
        check = next((item for item in result.engineering_checks if item.title_en == check_title_en), None)
        if not trigger and not check:
            continue

        if language == "zh":
            trigger_text = trigger.title_zh if trigger else "当前暂无额外触发项"
            status_text = "当前不可判定"
            if check:
                status_text = (
                    "可初步放行"
                    if check.status == "screen_pass"
                    else ("需专项复核" if check.status == "review" else "当前不可判定")
                )
            lines.append(
                f"{label_zh}：由“{trigger_text}”触发；当前检查状态为“{status_text}”；下一步应先做：{default_action_zh}。"
            )
        else:
            trigger_text = trigger.title_en if trigger else "No additional trigger is active"
            status_text = "Undetermined"
            if check:
                status_text = (
                    "Screen Pass" if check.status == "screen_pass" else ("Review Needed" if check.status == "review" else "Undetermined")
                )
            lines.append(
                f"{label_en}: triggered by '{trigger_text}'; current check status is '{status_text}'; next step should be {default_action_en}."
            )

    return lines
