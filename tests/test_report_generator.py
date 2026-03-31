from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.models import LLMExplanation
from structural_screening_agent.report_generator import build_markdown_report
from structural_screening_agent.rule_engine import evaluate_screening


def test_report_contains_bilingual_headings_and_decision() -> None:
    intake = main_demo_case()
    result = evaluate_screening(intake)
    explanation = LLMExplanation(
        provider="mock",
        model="demo-mock",
        mode="fallback",
        summary="Decision: Conditional Go | 有条件推进",
    )
    report = build_markdown_report(intake, result, explanation)
    assert "Executive Summary | 执行摘要" in report
    assert "Decision Snapshot | 决策快照" in report
    assert "Immediate Actions | 即刻动作" in report
    assert "Review Paths and Resources | 复核路径与资源" in report
    assert report.index("## Executive Summary | 执行摘要") < report.index("## Project Summary | 项目概况")
    assert report.index("## Immediate Actions | 即刻动作") < report.index("## Project Summary | 项目概况")
    assert "Decision | 决策结论" in report
    assert "Conditional Go | 有条件推进" in report
    assert "Top Risks | 关键风险" in report
    assert "Agent Explanation | Agent 说明" in report
    assert "Project Type | 项目类型: Rooftop PV | 屋面光伏" in report
    assert "Design Standard Context | 规范体系" in report
    assert "Management Summary | 管理层摘要" in report
    assert "Current Decision" in report
    assert "Next Step" in report
    assert "Preferred Path" in report
    assert "Therefore the current preferred path is" in report
    assert "Main-Case Screening Inputs | 主案例筛查项" in report
    assert "Drawing Facts Summary | 图纸关键信息摘录" in report
    assert "Existing Member Schedule" in report
    assert "Connection Detail Record" in report
    assert "Roof Vendor Data" in report
    assert "Verification Readiness | 结构复核准备度" in report
    assert "Engineering Screening Checks | 工程筛查检查" in report
    assert "Member Reserve Uncertainty Matrix | 构件承载储备不确定性矩阵" in report
    assert "High Uncertainty" in report
    assert "高不确定性" in report
    assert "Load Demand" in report
    assert "Roof Attachment Pathway Matrix | 屋面连接路径矩阵" in report
    assert "Clamp-Based Roof Connection" in report
    assert "当前不可判定" in report
    assert "Review Trigger Matrix | 专项复核触发项" in report
    assert "Review Progression | 复核推进链" in report
    assert "Recommended Resources | 建议配置资源" in report
    assert "Structural Engineer for Member Review" in report
    assert "Roof System" in report
    assert "Member Review Trigger" in report
    assert "Connection Review Trigger" in report
    assert "Check-to-Action Linkage | 检查联动摘要" in report
    assert "Reserve Capacity Screening" in report
    assert "承载储备筛查" in report
    assert "Attachment Feasibility Screening" in report
    assert "连接可行性筛查" in report
    assert "Assumptions and Limits | 假设与边界" in report
    assert "Partial Ready | 部分具备" in report
    assert "Decision Chain | 决策链摘要" not in report
    assert "Building Span (m): 30.0 m | 建筑跨度 (m): 30.0 m" in report
    assert "Basis | 依据" in report
    assert "Review Needed | 后续规范复核提示" in report
    assert "GB 50017" in report
    assert "Must Do | 必须先做" in report
    assert "Parallel Track | 建议并行做" in report
    assert "Later Step | 可后续做" in report
    assert "Priority Rationale | 当前优先原因" in report
    assert "Fit When | 适用情形" in report
    assert "Recommendation Note | 推荐说明" in report
