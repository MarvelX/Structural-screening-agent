from typing import List

from structural_screening_agent.llm_providers import MockProvider, resolve_provider
from structural_screening_agent.localization import Language
from structural_screening_agent.models import BuildingIntake, LLMExplanation, ScreeningResult


def build_follow_up_questions(intake: BuildingIntake, result: ScreeningResult, language: Language = "zh") -> List[str]:
    questions: List[str] = []

    if intake.drawing_availability != "complete":
        questions.append(
            "请补充原结构图纸、既有计算书或竣工修编资料。"
            if language == "zh"
            else "Please provide original structural drawings, previous calculations, or any as-built markups."
        )
    if not intake.survey_available:
        questions.append(
            "是否可以安排针对性现场调查，确认构件尺寸、连接、腐蚀情况和屋面构造？"
            if language == "zh"
            else "Can a targeted site survey confirm member sizes, connections, corrosion condition, and roof build-up?"
        )
    if intake.available_verification_path == "no_viable_path_yet":
        questions.append(
            "目前缺少可执行的复核路径。业主能否开放图纸、局部开口检查或专项调查窗口？"
            if language == "zh"
            else "There is no viable verification route yet. Can the owner unlock drawings, limited intrusive checks, or a targeted survey window?"
        )
    if result.status.value != "go" and intake.shutdown_constraint != "none":
        questions.append(
            "复核或加固期间，可接受的停工窗口或分阶段施工约束是什么？"
            if language == "zh"
            else "What shutdown window or phased construction tolerance is acceptable during verification or strengthening?"
        )
    metal_roof_keywords = ("metal", "steel sheet", "profiled", "压型钢板", "金属屋面")
    roof_text = f"{intake.roof_type} {intake.intended_modification}".lower()
    if any(keyword in roof_text for keyword in metal_roof_keywords):
        if intake.roof_rib_height_mm is None or intake.roof_panel_thickness_mm is None:
            questions.append(
                "请补充压型钢板的波峰高度和板厚，这会直接影响光伏支架连接与局部承压判断。"
                if language == "zh"
                else "Please confirm the profiled steel sheet rib height and panel thickness, since both directly affect PV mounting connection and local bearing checks."
            )
        if intake.purlin_type in (None, "", "unknown"):
            questions.append(
                "请确认檩条形式及其与屋面板的支承关系，这会影响连接可行性和局部受力判断。"
                if language == "zh"
                else "Please confirm the purlin type and its support relationship to the roof panel, since this affects attachment feasibility and local force transfer."
            )

    return questions


def build_bilingual_explanation(
    intake: BuildingIntake, result: ScreeningResult, language: Language = "zh"
) -> LLMExplanation:
    questions = build_follow_up_questions(intake, result, language=language)
    provider = resolve_provider()
    requested_provider = provider.provider_name
    fallback_reason = None
    try:
        summary = provider.generate_summary(intake, result, questions, language)
    except Exception as exc:
        provider = MockProvider(provider_name="mock", model_name="demo-mock", mode="fallback")
        summary = provider.generate_summary(intake, result, questions, language)
        fallback_reason = str(exc)
    return LLMExplanation(
        provider=provider.provider_name,
        model=provider.model_name,
        mode=provider.mode,
        requested_provider=requested_provider,
        fallback_reason=fallback_reason,
        summary=summary,
    )
