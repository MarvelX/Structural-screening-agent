from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.decision_agent import build_bilingual_explanation
from structural_screening_agent.report_generator import build_markdown_report, build_report_preview, build_report_filename
from structural_screening_agent.rule_engine import evaluate_screening


def test_report_preview_follows_ui_language_but_not_export_language() -> None:
    intake = main_demo_case()
    result = evaluate_screening(intake)
    explanation = build_bilingual_explanation(intake, result, language="zh")

    preview = build_report_preview(intake, result, explanation, language="zh")
    report = build_markdown_report(intake, result, explanation)

    assert preview.title == "决策摘要"
    assert preview.sections[0].heading == "执行摘要"
    assert any("当前结论" in item for item in preview.sections[0].items)
    assert any("优先路径" in item for item in preview.sections[0].items)
    assert any("因此当前优先路径" in item for item in preview.sections[0].items)
    assert preview.sections[1].heading == "决策快照"
    assert any("决策结论" in item for item in preview.sections[1].items)
    assert any("置信度" in item for item in preview.sections[1].items)
    assert preview.sections[2].heading == "即刻动作"
    assert any("必须先做" in item for item in preview.sections[2].items)
    assert preview.sections[3].heading == "复核路径与资源"
    assert any("构件复核路径" in item for item in preview.sections[3].items)
    assert any("结构复核工程师" in item for item in preview.sections[3].items)
    assert any("GB 50017" in item for item in preview.sections[3].items)
    assert preview.sections[4].heading == "项目概况"
    assert preview.sections[4].items[0] == "项目类型: 屋面光伏"
    assert "rooftop_pv" not in preview.sections[4].items[0]
    assert any("规范体系" in item for item in preview.sections[4].items)
    assert preview.sections[5].heading == "主案例筛查项"
    assert any("建筑跨度" in item for item in preview.sections[5].items)
    assert preview.sections[6].heading == "图纸关键信息摘录"
    assert any("图纸完整性" in item for item in preview.sections[6].items)
    assert any("既有构件表" in item for item in preview.sections[6].items)
    assert any("节点连接做法" in item for item in preview.sections[6].items)
    assert any("屋面系统厂家资料" in item for item in preview.sections[6].items)
    assert preview.sections[7].heading == "结构复核准备度"
    assert any("部分具备" in item for item in preview.sections[7].items)
    assert any("构件表" in item for item in preview.sections[7].items)
    assert preview.sections[8].heading == "工程筛查检查"
    assert any("承载储备筛查" in item for item in preview.sections[8].items)
    assert any("连接可行性筛查" in item for item in preview.sections[8].items)
    assert preview.sections[9].heading == "构件承载储备不确定性矩阵"
    assert any("新增荷载需求" in item for item in preview.sections[9].items)
    assert any("高不确定性" in item for item in preview.sections[9].items)
    assert preview.sections[10].heading == "屋面连接路径矩阵"
    assert any("夹持式屋面连接" in item for item in preview.sections[10].items)
    assert any("当前不可判定" in item for item in preview.sections[10].items)
    assert preview.sections[11].heading == "专项复核触发项"
    assert any("构件复核触发项" in item for item in preview.sections[11].items)
    assert any("连接复核触发项" in item for item in preview.sections[11].items)
    assert preview.sections[12].heading == "检查联动摘要"
    assert any("承载储备筛查" in item for item in preview.sections[12].items)
    assert any("必须先做" in item for item in preview.sections[12].items)
    assert preview.sections[13].heading == "假设与边界"
    assert any("仅用于前期结构筛查" in item for item in preview.sections[13].items)
    assert any("依据" in item for item in preview.sections[14].items)
    assert any("当前优先原因" in item for item in preview.sections[17].items)
    assert any("适用情形" in item for item in preview.sections[17].items)
    assert "Project Summary | 项目概况" in report
    assert "Decision | 决策结论" in report


def test_report_filename_matches_main_demo_and_current_date() -> None:
    filename = build_report_filename("main_warehouse_pv")
    assert filename.startswith("2026-03-31-main_warehouse_pv")
    assert filename.endswith(".md")
