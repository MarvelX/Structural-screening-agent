from datetime import date

from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.decision_agent import build_bilingual_explanation
from structural_screening_agent.report_generator import build_markdown_report, build_report_preview, build_report_filename
from structural_screening_agent.rule_engine import evaluate_screening


def test_report_preview_follows_ui_language_but_not_export_language() -> None:
    intake = main_demo_case()
    result = evaluate_screening(intake)
    kernel_outcome = evaluate_screening_case(from_building_intake(intake))
    explanation = build_bilingual_explanation(intake, result, language="zh")

    preview = build_report_preview(intake, result, explanation, language="zh", kernel_outcome=kernel_outcome)
    report = build_markdown_report(intake, result, explanation)

    assert preview.title == "门式刚架屋面光伏增载初筛复核摘要"
    assert preview.sections[0].heading == "评估范围"
    assert any("门式刚架建筑屋面光伏增载初筛复核摘要" in item for item in preview.sections[0].items)
    assert preview.sections[1].heading == "简化计算结果"
    assert any("檩条强度比" in item for item in preview.sections[1].items)
    assert any("檩条挠度比" in item for item in preview.sections[1].items)
    assert preview.sections[2].heading == "初步结构结论"
    assert any("当前控制因素主要落在檩条" in item for item in preview.sections[2].items)
    assert preview.sections[3].heading == "后续复核建议"
    assert any("针对性现场调查" in item or "GB 门式刚架檩条筛查依据" in item for item in preview.sections[3].items)
    assert preview.sections[4].heading == "执行摘要"
    assert any("当前结论" in item for item in preview.sections[4].items)
    assert any("优先路径" in item for item in preview.sections[4].items)
    assert preview.sections[8].heading == "项目概况"
    assert preview.sections[8].items[0] == "项目类型: 屋面光伏"
    assert "rooftop_pv" not in preview.sections[8].items[0]
    assert any("建筑类型: 既有仓库" in item for item in preview.sections[8].items)
    assert any("结构体系: 门式刚架钢结构" in item for item in preview.sections[8].items)
    assert "Project Summary | 项目概况" in report
    assert "Decision | 决策结论" in report


def test_report_preview_updates_controlling_factor_when_primary_frame_governs() -> None:
    intake = main_demo_case().model_copy(update={"rafter_section": "250x125x6x8 welded rafter"})
    result = evaluate_screening(intake)
    kernel_outcome = evaluate_screening_case(from_building_intake(intake))
    explanation = build_bilingual_explanation(intake, result, language="zh")

    preview = build_report_preview(intake, result, explanation, language="zh", kernel_outcome=kernel_outcome)

    assert any("当前控制因素主要落在主门架梁的附加弯矩筛查" in item for item in preview.sections[2].items)


def test_report_filename_matches_main_demo_and_current_date() -> None:
    filename = build_report_filename("main_warehouse_pv", report_date=date(2026, 3, 31))
    assert filename.startswith("2026-03-31-main_warehouse_pv")
    assert filename.endswith(".md")
