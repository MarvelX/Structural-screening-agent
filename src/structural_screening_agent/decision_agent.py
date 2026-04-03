from typing import List, Optional

from structural_screening_agent.core.kernel import KernelOutcome
from structural_screening_agent.llm_providers import MockProvider, resolve_provider
from structural_screening_agent.localization import Language
from structural_screening_agent.models import BuildingIntake, LLMExplanation, ScreeningResult


def _append_question(questions: List[str], question: str) -> None:
    if question not in questions:
        questions.append(question)


def build_follow_up_questions(
    intake: BuildingIntake,
    result: ScreeningResult,
    language: Language = "zh",
    kernel_outcome: Optional[KernelOutcome] = None,
) -> List[str]:
    questions: List[str] = []

    if intake.drawing_availability != "complete":
        _append_question(
            questions,
            "请补充原结构图纸、既有计算书或竣工修编资料。"
            if language == "zh"
            else "Please provide original structural drawings, previous calculations, or any as-built markups."
        )
    if not intake.survey_available:
        _append_question(
            questions,
            "是否可以安排针对性现场调查，确认构件尺寸、连接、腐蚀情况和屋面构造？"
            if language == "zh"
            else "Can a targeted site survey confirm member sizes, connections, corrosion condition, and roof build-up?"
        )
    if intake.available_verification_path == "no_viable_path_yet":
        _append_question(
            questions,
            "目前缺少可执行的复核路径。业主能否开放图纸、局部开口检查或专项调查窗口？"
            if language == "zh"
            else "There is no viable verification route yet. Can the owner unlock drawings, limited intrusive checks, or a targeted survey window?"
        )
    if result.status.value != "go" and intake.shutdown_constraint != "none":
        _append_question(
            questions,
            "复核或加固期间，可接受的停工窗口或分阶段施工约束是什么？"
            if language == "zh"
            else "What shutdown window or phased construction tolerance is acceptable during verification or strengthening?"
        )
    metal_roof_keywords = ("metal", "steel sheet", "profiled", "压型钢板", "金属屋面")
    roof_text = f"{intake.roof_type} {intake.intended_modification}".lower()
    if any(keyword in roof_text for keyword in metal_roof_keywords):
        if intake.roof_rib_height_mm is None or intake.roof_panel_thickness_mm is None:
            _append_question(
                questions,
                "请补充压型钢板的波峰高度和板厚，这会直接影响光伏支架连接与局部承压判断。"
                if language == "zh"
                else "Please confirm the profiled steel sheet rib height and panel thickness, since both directly affect PV mounting connection and local bearing checks."
            )
        if intake.purlin_type in (None, "", "unknown"):
            _append_question(
                questions,
                "请确认檩条形式及其与屋面板的支承关系，这会影响连接可行性和局部受力判断。"
                if language == "zh"
                else "Please confirm the purlin type and its support relationship to the roof panel, since this affects attachment feasibility and local force transfer."
            )

    controlling_path = getattr(kernel_outcome, "controlling_path", None)
    if controlling_path is not None:
        if controlling_path.path_id in {"purlin_strength", "purlin_deflection"}:
            _append_question(
                questions,
                (
                    "请确认檩条间距、形式及连续性。为什么问这个：当前控制因素主要落在檩条，以上信息会直接改变单根檩条的分担荷载与挠度判断。"
                    if language == "zh"
                    else "Please confirm purlin spacing, type, and continuity. Why this matters: the current controlling path sits at the purlin level, and these inputs directly change tributary load and deflection judgement."
                ),
            )
        if controlling_path.path_id == "primary_frame_rafter":
            _append_question(
                questions,
                (
                    "请确认门架梁截面、建筑跨度及檐口高度。为什么问这个：当前控制因素主要落在主门架梁，这些参数会直接影响梁的附加弯矩与挠度敏感性判断。"
                    if language == "zh"
                    else "Please confirm the portal-frame rafter section, building span, and eave height. Why this matters: the current controlling path sits at the primary-frame rafter, and these inputs directly affect added-moment and deflection sensitivity."
                ),
            )
        if controlling_path.path_id == "primary_frame_column":
            _append_question(
                questions,
                (
                    "请确认门架柱截面、檐口高度及柱脚约束。为什么问这个：当前控制因素主要落在主门架柱，这些参数会直接影响柱的附加弯矩与稳定敏感性判断。"
                    if language == "zh"
                    else "Please confirm the portal-frame column section, eave height, and base restraint. Why this matters: the current controlling path sits at the primary-frame column, and these inputs directly affect added-moment and stability sensitivity."
                ),
            )
    if kernel_outcome is not None and any(
        item.category == "connection" for item in kernel_outcome.review_triggers
    ):
        _append_question(
            questions,
            (
                "请确认屋面板锁边方式、夹具型号或厂家连接资料。为什么问这个：当前连接路径仍未闭合，上述信息决定夹持连接是否具有抗拔和防水可辩护性。"
                if language == "zh"
                else "Please confirm the roof seam type, clamp type, or vendor attachment data. Why this matters: the connection path remains open, and these inputs determine whether clamp-based attachment is defensible for uplift and waterproofing."
            ),
        )

    return questions


def build_bilingual_explanation(
    intake: BuildingIntake,
    result: ScreeningResult,
    language: Language = "zh",
    kernel_outcome: Optional[KernelOutcome] = None,
) -> LLMExplanation:
    questions = build_follow_up_questions(intake, result, language=language, kernel_outcome=kernel_outcome)
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
