from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.localization import (
    canonicalize_preset_text,
    format_bilingual_item,
    language_label,
    localize_basis_term,
    localize_preset_text,
    translate,
    translate_option,
)
from structural_screening_agent.models import BilingualItem
from structural_screening_agent.presentation import build_workbench_view
from structural_screening_agent.rule_engine import evaluate_screening
from structural_screening_agent.decision_agent import build_bilingual_explanation


def test_translate_returns_default_chinese_labels() -> None:
    assert translate("zh", "project_intake") == "项目输入"
    assert translate("en", "project_intake") == "Project Intake"
    assert translate("zh", "demo_scenario") == "案例库"
    assert translate("zh", "demo_flow") == "查看顺序"
    assert translate("zh", "product_scope") == "当前适用边界"
    assert translate("en", "standards_context_note") == "Standards Context"
    assert translate("zh", "input_group_project_basics") == "基本项目条件"
    assert translate("zh", "input_group_structural_evidence") == "结构证据链"
    assert translate("zh", "input_group_roof_connection") == "屋面连接证据链"
    assert translate("zh", "input_group_execution_constraints") == "施工约束"
    assert translate("en", "input_group_verification_route") == "Verification Route"
    assert translate("zh", "traceability_basis") == "可追溯性与依据"
    assert translate("zh", "engineering_meaning") == "工程含义"
    assert translate("en", "assessment_scope") == "Assessment Scope"
    assert translate("zh", "portal_frame_screening_title") == "门式刚架屋面光伏增载初筛"
    assert translate("en", "next_step_review_actions") == "Next-Step Review Actions"
    assert translate("zh", "assessment_tab") == "评估结论"
    assert translate("zh", "project_input_tab") == "项目输入"
    assert translate("zh", "report_export_tab") == "报告导出"
    assert translate("zh", "applicable_standards") == "适用规范体系"
    assert translate("zh", "evidence_requirements") == "证据需求"
    assert translate("zh", "human_gate_heading") == "工程师数据确认门禁"
    assert translate("en", "calculation_gate_ready").startswith("Calculation gate ready")
    assert translate("zh", "report_draft_gate_heading") == "报告草稿输入门禁"


def test_format_bilingual_item_respects_selected_language() -> None:
    item = BilingualItem(title_en="Top Risk", title_zh="关键风险")
    assert format_bilingual_item(item, "zh") == "关键风险"
    assert format_bilingual_item(item, "en") == "Top Risk"


def test_workbench_view_uses_single_language_ui_labels() -> None:
    intake = main_demo_case()
    result = evaluate_screening(intake)
    explanation = build_bilingual_explanation(intake, result, language="zh")
    evaluation = {
        "intake": intake,
        "result": result,
        "questions": ["请补充原结构图纸。"],
        "explanation": explanation,
        "report": "report",
    }

    zh_view = build_workbench_view(evaluation, language="zh")
    en_view = build_workbench_view(evaluation, language="en")

    assert zh_view.report_title == "复核摘要"
    assert en_view.report_title == "Review Summary"
    assert zh_view.scenario_label.startswith("场景")
    assert en_view.scenario_label.startswith("Scenario")


def test_translate_option_localizes_internal_select_values() -> None:
    assert translate_option("zh", "project_type", "rooftop_pv") == "屋面光伏"
    assert translate_option("zh", "shutdown_constraint", "limited") == "有限停工"
    assert translate_option("en", "drawing_availability", "partial") == "Partial"
    assert translate("zh", "agent_explanation") == "复核说明"
    assert translate("zh", "mock_fallback") == "模拟降级模式"


def test_language_selector_labels_are_fully_localized() -> None:
    assert language_label("zh", "zh") == "中文"
    assert language_label("zh", "en") == "英文"
    assert language_label("en", "zh") == "Chinese"
    assert language_label("en", "en") == "English"


def test_localize_preset_text_localizes_demo_defaults_for_text_inputs() -> None:
    assert localize_preset_text("zh", "building_type", "existing warehouse") == "既有仓库"
    assert localize_preset_text("zh", "structural_system", "steel portal frame") == "门式刚架钢结构"
    assert localize_preset_text("zh", "roof_type", "metal roof") == "金属屋面"
    assert localize_preset_text("zh", "modification", "distributed rooftop pv") == "分布式屋面光伏"
    assert localize_preset_text("en", "building_type", "existing warehouse") == "existing warehouse"


def test_canonicalize_preset_text_maps_localized_defaults_back_to_canonical_values() -> None:
    assert canonicalize_preset_text("building_type", "既有仓库") == "existing warehouse"
    assert canonicalize_preset_text("structural_system", "门式刚架钢结构") == "steel portal frame"
    assert canonicalize_preset_text("roof_type", "金属屋面") == "metal roof"
    assert canonicalize_preset_text("modification", "分布式屋面光伏") == "distributed rooftop pv"
    assert canonicalize_preset_text("building_type", "自定义建筑") == "自定义建筑"


def test_localize_basis_term_maps_engineering_basis_phrases() -> None:
    assert localize_basis_term("zh", "structural drawings") == "结构图纸"
    assert localize_basis_term("zh", "roof photovoltaic load summary") == "屋面光伏荷载摘要"
