from typing import List, Optional

from structural_screening_agent.core.kernel import KernelOutcome
from structural_screening_agent.localization import Language
from structural_screening_agent.models import BuildingIntake, ScreeningResult


def build_assumptions_and_limitations(
    intake: BuildingIntake,
    result: ScreeningResult,
    language: Language,
    kernel_outcome: Optional[KernelOutcome] = None,
) -> List[str]:
    if kernel_outcome is not None and kernel_outcome.assumption_ledger:
        return [
            item.summary_zh if language == "zh" else item.summary_en
            for item in kernel_outcome.assumption_ledger
        ]

    if language == "zh":
        items = ["当前输出仅用于前期结构筛查与路径判断，不替代正式结构设计、规范计算或签字结论。"]
        if intake.drawing_availability != "complete":
            items.append("当前判断默认缺失图纸信息可能在后续正式复核中改变构件、连接或整体稳定控制条件。")
        if not intake.survey_available:
            items.append("当前尚未通过现场调查验证腐蚀、节点做法与实际构造偏差。")
        if intake.existing_member_schedule_status != "available":
            items.append("既有构件表/截面表尚未完整掌握，正式复核时关键构件识别仍可能调整。")
        if intake.connection_detail_status != "available":
            items.append("节点连接做法资料尚未完整掌握，连接判断仍可能在后续详细复核中变化。")
        if intake.roof_vendor_data_status != "available":
            items.append("屋面系统厂家资料尚未完整掌握，屋面连接与防水构造边界仍需后续确认。")
        if intake.project_type == "rooftop_pv" and intake.roof_panel_type == "profiled_sheet":
            if intake.roof_panel_thickness_mm is None or intake.roof_rib_height_mm is None:
                items.append("压型钢板的连接可行性仍依赖板厚和波高等关键参数确认。")
        if result.verification_readiness.level != "ready":
            items.append("在结构复核准备度未达到“已具备”前，当前结论不应作为大范围铺开或施工承诺依据。")
        return items

    items = ["Current output is for early-stage structural screening and path selection only. It does not replace formal design, code calculations, or signed conclusions."]
    if intake.drawing_availability != "complete":
        items.append("The current decision assumes missing drawing information may still change the governing member, connection, or global stability checks in formal review.")
    if not intake.survey_available:
        items.append("Corrosion, connection detailing, and as-built deviations remain unverified until the site survey is completed.")
    if intake.existing_member_schedule_status != "available":
        items.append("The existing member schedule / section schedule is still incomplete, so the controlling members identified in formal review may change.")
    if intake.connection_detail_status != "available":
        items.append("Connection detailing records remain incomplete, so the current connection judgement may still shift during detailed review.")
    if intake.roof_vendor_data_status != "available":
        items.append("Roof-system vendor data is still incomplete, so attachment and waterproofing boundaries remain subject to later confirmation.")
    if intake.project_type == "rooftop_pv" and intake.roof_panel_type == "profiled_sheet":
        if intake.roof_panel_thickness_mm is None or intake.roof_rib_height_mm is None:
            items.append("Attachment feasibility for the profiled roof still depends on confirmation of key panel properties such as thickness and rib height.")
    if result.verification_readiness.level != "ready":
        items.append("Until verification readiness reaches 'Ready', the current conclusion should not be used for broad rollout or construction commitment.")
    return items
