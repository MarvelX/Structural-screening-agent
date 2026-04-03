from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.models import LLMExplanation
from structural_screening_agent.report_generator import build_markdown_report
from structural_screening_agent.rule_engine import evaluate_screening
from structural_screening_agent.models import BuildingIntake


def _level_b_portal_frame_intake() -> BuildingIntake:
    return BuildingIntake(
        project_type="rooftop_pv",
        design_standard_context="gb",
        building_type="test warehouse",
        structural_system="steel portal frame",
        roof_type="metal roof",
        intended_modification="distributed rooftop pv",
        estimated_added_load_kpa=0.18,
        building_span_m=30.0,
        column_spacing_m=8.0,
        eave_height_m=8.0,
        rafter_section="310x150x8x12 welded rafter",
        column_section="305x305x10x15 welded column",
        steel_grade="Q355",
        purlin_spacing_m=1.5,
        purlin_type="cold_formed_z",
        roof_panel_type="profiled_sheet",
        roof_panel_thickness_mm=None,
        roof_rib_height_mm=None,
        roof_attachment_preference="clamp_based",
        existing_member_schedule_status="available",
        connection_detail_status="partial",
        roof_vendor_data_status="missing",
        corrosion_condition="moderate",
        waterproofing_sensitivity="high",
        restricted_installation_zones="maintenance corridor",
        available_verification_path="drawings_only",
        shutdown_constraint="limited",
        drawing_availability="complete",
        survey_available=False,
    )


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
    assert report.index("## Project Summary | 项目概况") < report.index("## Executive Summary | 执行摘要")
    assert "Decision | 决策结论" in report
    assert "Conditional Go | 有条件推进" in report
    assert "Top Risks | 关键风险" in report
    assert "Review Note | 复核说明" in report
    assert "Project Type | 项目类型: Rooftop PV | 屋面光伏" in report
    assert "Design Standard Context | 规范体系" in report
    assert "Current Decision" in report
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
    assert "需专项复核" in report
    assert "Review Trigger Matrix | 专项复核触发项" in report
    assert "Review Progression | 复核推进链" in report
    assert "Recommended Resources | 建议配置资源" in report
    assert "Structural Engineer for Member Review" in report
    assert "Roof System" in report
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
    assert "Review Needed | 后续规范复核提示" in report
    assert "Review Needed | 后续规范复核提示" in report
    assert "GB 门式刚架檩条筛查依据" in report
    assert "Traceability and Basis | 可追溯性与依据" in report
    assert "gb_portal_frame_purlin_screening" not in report
    assert "Purlin Strength Ratio | 檩条强度比" in report
    assert "Priority Rationale | 当前优先原因" in report
    assert "Fit When | 适用情形" in report
    assert "Screening Cost Range | 初筛成本区间" in report
    assert "仅供初筛阶段方案比较" in report
    assert "Recommendation Note | 推荐说明" in report


def test_report_can_include_kernel_basis_and_screening_calculations() -> None:
    intake = main_demo_case()
    result = evaluate_screening(intake)
    kernel_outcome = evaluate_screening_case(from_building_intake(intake))
    explanation = LLMExplanation(
        provider="mock",
        model="demo-mock",
        mode="fallback",
        summary="Decision: Conditional Go | 有条件推进",
    )

    report = build_markdown_report(
        intake,
        result,
        explanation,
        kernel_outcome=kernel_outcome,
    )

    assert "Assessment Basis and Screening Calculations | 评估依据与筛查计算" in report
    assert "Load Combination Sensitivity | 荷载组合敏感性" in report
    assert "GB Portal Frame Purlin Screening Basis" in report
    assert "Engineering Meaning | 工程含义" in report
    assert "Applicable Standards | 适用规范体系: gb | 国标 GB" in report
    assert "Trigger Conditions | 触发条件" in report
    assert "Evidence Requirements | 证据需求" in report
    assert "Follow-up Review | 后续复核要求" in report
    assert "Basis IDs | 依据 ID" not in report
    assert "Verification Readiness Score | 复核准备度分数: 55" in report
    assert "Uncertainty Score | 不确定性分数: 85" in report
    assert "Purlin Strength Ratio | 檩条强度比: 0.90 (dimensionless | 无量纲)" in report
    assert "Purlin Deflection Ratio | 檩条挠度比: 1.13 (dimensionless | 无量纲)" in report
    assert "Estimated Critical Added Load | 临界新增荷载估算" in report
    assert "Remaining Added-Load Margin | 剩余新增荷载余量" in report
    assert "Primary Frame Screening Ratio | 主门架筛查比值" in report
    assert "Formula | 计算式" in report
    assert "Result Unit | 结果单位" in report
    assert "wind" in report.lower() or "风" in report


def test_report_hides_basis_ids_from_traceability_and_basis_sections() -> None:
    intake = main_demo_case()
    result = evaluate_screening(intake)
    kernel_outcome = evaluate_screening_case(from_building_intake(intake))
    explanation = LLMExplanation(
        provider="mock",
        model="demo-mock",
        mode="fallback",
        summary="Decision: Conditional Go | 有条件推进",
    )

    report = build_markdown_report(
        intake,
        result,
        explanation,
        kernel_outcome=kernel_outcome,
    )

    assert "依据 ID" not in report
    assert "Basis IDs" not in report
    assert "gb_portal_frame_purlin_screening" not in report


def test_report_includes_engineer_memo_sections_for_level_b_portal_frame_case() -> None:
    intake = _level_b_portal_frame_intake()
    result = evaluate_screening(intake)
    kernel_outcome = evaluate_screening_case(from_building_intake(intake))
    explanation = LLMExplanation(
        provider="mock",
        model="demo-mock",
        mode="fallback",
        summary="Decision: Conditional Go | 有条件推进",
    )

    report = build_markdown_report(
        intake,
        result,
        explanation,
        kernel_outcome=kernel_outcome,
    )

    assert "Review Scope and Boundary | 复核范围与边界" in report
    assert "Simplified Calculation Results | 简化计算结果" in report
    assert "Preliminary Structural Conclusion | 初步结构结论" in report
    assert "Recommended Next-Step Review Actions | 后续复核建议" in report
    assert "Portal-Frame Rooftop PV Screening Review Summary | 门式刚架屋面光伏增载初筛复核摘要" in report
    assert "Steel Grade | 钢材标号" in report
    assert "Added roof dead load | 新增屋面恒载" in report
    assert "Purlin Strength Ratio | 檩条强度比" in report
    assert "Purlin Deflection Ratio | 檩条挠度比" in report
    assert "Primary Frame Column Added Moment Proxy | 主门架柱附加弯矩代理值" in report
    assert "Primary Frame Screening Ratio | 主门架筛查比值" in report
    assert "Primary Frame Rafter Screening Ratio | 主门架梁筛查比值" in report
    assert "Primary Frame Column Screening Ratio | 主门架柱筛查比值" in report
    assert "Primary Frame Rafter Deflection Sensitivity | 主门架梁挠度敏感性" in report
    assert "Primary Frame Column Stability Sensitivity | 主门架柱稳定敏感性" in report
    assert "Current controlling factor" in report or "当前控制因素" in report
    assert "Assumptions and Limits | 假设与边界" in report
    assert "site survey" in report.lower() or "现场调查" in report


def test_report_updates_controlling_factor_when_primary_frame_governs() -> None:
    intake = _level_b_portal_frame_intake().model_copy(
        update={
            "rafter_section": "250x125x6x8 welded rafter",
        }
    )
    result = evaluate_screening(intake)
    kernel_outcome = evaluate_screening_case(from_building_intake(intake))
    explanation = LLMExplanation(
        provider="mock",
        model="demo-mock",
        mode="fallback",
        summary="Decision: Conditional Go | 有条件推进",
    )

    report = build_markdown_report(
        intake,
        result,
        explanation,
        kernel_outcome=kernel_outcome,
    )

    assert "Current controlling factor is the primary-frame rafter added-moment screening." in report
    assert "当前控制因素主要落在主门架梁的附加弯矩筛查。" in report


def test_report_surfaces_conservative_steel_grade_assumption_when_missing() -> None:
    intake = _level_b_portal_frame_intake().model_copy(update={"steel_grade": None})
    result = evaluate_screening(intake)
    kernel_outcome = evaluate_screening_case(from_building_intake(intake))
    explanation = LLMExplanation(
        provider="mock",
        model="demo-mock",
        mode="fallback",
        summary="Decision: Conditional Go | 有条件推进",
    )

    report = build_markdown_report(
        intake,
        result,
        explanation,
        kernel_outcome=kernel_outcome,
    )

    assert "Q235" in report
    assert "conservative" in report.lower() or "保守" in report


def test_report_without_kernel_outcome_does_not_insert_memo_sections() -> None:
    intake = main_demo_case()
    result = evaluate_screening(intake)
    explanation = LLMExplanation(
        provider="mock",
        model="demo-mock",
        mode="fallback",
        summary="Decision: Conditional Go | 有条件推进",
    )

    report = build_markdown_report(intake, result, explanation)

    assert "Review Scope and Boundary | 复核范围与边界" not in report
    assert "Simplified Calculation Results | 简化计算结果" not in report
    assert "Preliminary Structural Conclusion | 初步结构结论" not in report
    assert "Recommended Next-Step Review Actions | 后续复核建议" not in report
