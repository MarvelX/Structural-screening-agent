from datetime import date

from structural_screening_agent.bv_review.models import BVReviewIntake, BVRiskItem
from structural_screening_agent.bv_review.report import (
    build_bv_open_rfi_items,
    build_bv_markdown_report,
    build_bv_report_filename,
    build_bv_report_preview,
)
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    ProjectReviewState,
    ReportRevision,
    RFIItem,
)
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Hebei rooftop PV design review",
        country_or_region="China",
        project_type="rooftop_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "existing_rooftop_added_load"],
        client_requirements=["Client requires independent structural design review."],
        documents={
            "structural_drawings": "partial",
            "calculation_report": "missing",
            "technical_specification": "available",
            "geotechnical_report": "missing",
            "vendor_datasheets": "partial",
            "contract_requirements": "available",
        },
    )


def test_bv_report_preview_contains_required_design_review_sections() -> None:
    result = evaluate_bv_review(_sample_intake())
    preview = build_bv_report_preview(_sample_intake(), result)

    headings = [section.heading for section in preview.sections]
    assert preview.title == "BV 光伏结构设计审查报告"
    assert "项目与审核范围" in headings
    assert "审核依据" in headings
    assert "提交资料清单与完整性状态" in headings
    assert "审核路径与方法" in headings
    assert "主要发现" in headings
    assert "不符合项与阻塞项" in headings
    assert "技术风险与优化建议" in headings
    assert "后续行动" in headings
    assert "审核边界声明" in headings


def test_bv_report_boundary_statement_does_not_claim_formal_design_or_bv_official_issue() -> None:
    result = evaluate_bv_review(_sample_intake())
    preview = build_bv_report_preview(_sample_intake(), result)

    boundary = next(section for section in preview.sections if section.heading == "审核边界声明")
    text = "\n".join(boundary.items)
    assert "不替代正式设计" in text
    assert "不代表 BV 官方签发流程" in text
    assert "合格工程师复核" in text


def test_bv_markdown_report_contains_required_sections_and_boundary_statement() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)

    report = build_bv_markdown_report(intake, result)

    assert report.startswith("# BV 光伏结构设计审查报告")
    assert "## 项目与审核范围" in report
    assert "## 审核依据" in report
    assert "## 提交资料清单与完整性状态" in report
    assert "## 审核路径与方法" in report
    assert "## 不符合项与阻塞项" in report
    assert "## 技术风险与优化建议" in report
    assert "## 后续行动" in report
    assert "## 审核边界声明" in report
    assert "不替代正式设计" in report
    assert "不代表 BV 官方签发流程" in report


def test_bv_markdown_report_includes_traceable_service_scope_recommendations() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)

    report = build_bv_markdown_report(intake, result)

    assert "## BV 服务范围建议" in report
    assert "资料完整性与 RFI 关闭支持" in report
    assert "触发证据:" in report
    assert "不替代正式设计" in report


def test_bv_report_preview_includes_traceable_service_scope_recommendations() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)

    preview = build_bv_report_preview(intake, result)
    section = next(section for section in preview.sections if section.heading == "BV 服务范围建议")
    text = "\n".join(section.items)

    assert "资料完整性与 RFI 关闭支持" in text
    assert "触发证据:" in text
    assert "不替代正式设计" in text


def test_bv_report_preview_includes_closed_rfi_recheck_evidence_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-rfi-closeout",
        intake=intake,
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-human-gate",
                input_field_ids=["pile_length_m"],
                input_locked=True,
                status="completed",
            )
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-pile_length_m",
                question="Please confirm updated input for Pile Length M.",
                responsible_party="client",
                trigger_basis="Field pile_length_m changed from '3.5' to '4.0'.",
                required_document_or_field="pile_length_m",
                status="closed",
                client_response="Confirmed Rev B pile length is 4.0 m.",
                reopen_review_items=["calculation-recheck-pile_length_m"],
                completed_recheck_items=["calculation-recheck-pile_length_m"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(section for section in preview.sections if section.heading == "RFI 关闭与增量复核证据")

    assert section.items == [
        (
            "RFI rfi-pile_length_m | 复核项: calculation-recheck-pile_length_m | "
            "字段: pile_length_m | 计算运行: foundation-run-001 | 关闭证据: 已完成增量复核"
        )
    ]


def test_bv_report_preview_prefers_latest_incremental_recheck_evidence() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-rfi-closeout",
        intake=intake,
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["uplift_force_kn"],
                input_locked=True,
                status="completed",
            ),
            CalculationRun(
                run_id="incremental-recheck-rfi-foundation-run-001-foundation-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["uplift_force_kn"],
                input_locked=True,
                status="completed",
            ),
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-run-001",
                question="Please confirm foundation reaction updates.",
                responsible_party="client / designer",
                trigger_basis="Foundation run requires clarification.",
                required_document_or_field="uplift_force_kn",
                status="closed",
                client_response="Designer submitted Rev B reaction table.",
                reopen_review_items=["uplift_force_kn"],
                completed_recheck_items=["uplift_force_kn"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(
        section
        for section in preview.sections
        if section.heading == "RFI 关闭与增量复核证据"
    )
    text = "\n".join(section.items)

    assert "incremental-recheck-rfi-foundation-run-001-foundation-001" in text
    assert "计算运行: foundation-run-001" not in text


def test_bv_markdown_report_includes_closed_rfi_recheck_evidence_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-rfi-closeout",
        intake=intake,
        rfi_items=[
            RFIItem(
                rfi_id="rfi-direct-field",
                question="请确认基础反力。",
                responsible_party="client",
                trigger_basis="基础反力发生变化。",
                required_document_or_field="uplift_force_kn",
                status="closed",
                client_response="设计院已提交 Rev B 反力表。",
                reopen_review_items=["uplift_force_kn"],
                completed_recheck_items=["uplift_force_kn"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    report = build_bv_markdown_report(intake, result, project_state=state)

    assert "## RFI 关闭与增量复核证据" in report
    assert "RFI rfi-direct-field" in report
    assert "关闭证据: 已完成增量复核" in report


def test_bv_report_preview_includes_finding_closeout_evidence_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-finding-closeout",
        intake=intake,
        risks=[
            BVRiskItem(
                risk_id="foundation-bearing-capacity-closed",
                title="基础承载力澄清已关闭",
                severity="high",
                trigger_basis="工程师复核 Rev B 地勘资料。",
                impact_scope="基础审核",
                recommendation="保留关闭证据。",
                blocks_report_issue=True,
                category="nonconformity",
                status="closed",
                closeout_note="工程师确认 Rev B 地勘承载力参数可用于筛查级报告。",
            ),
            BVRiskItem(
                risk_id="layout-residual-accepted",
                title="支架排布残余优化意见",
                severity="medium",
                trigger_basis="工程师接受残余优化意见。",
                impact_scope="支架布置",
                recommendation="在报告中保留残余意见。",
                blocks_report_issue=True,
                category="optimization",
                status="accepted_with_comment",
                closeout_note="工程师接受该项作为残余优化建议，不阻塞报告草稿。",
            ),
            BVRiskItem(
                risk_id="open-finding-not-closeout-evidence",
                title="未关闭发现项",
                severity="critical",
                trigger_basis="仍缺少资料。",
                impact_scope="基础审核",
                recommendation="继续跟进。",
                blocks_report_issue=True,
                category="nonconformity",
            ),
        ],
    )

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(section for section in preview.sections if section.heading == "发现项关闭证据")
    text = "\n".join(section.items)

    assert "foundation-bearing-capacity-closed" in text
    assert "状态: closed" in text
    assert "工程师确认 Rev B 地勘承载力参数可用于筛查级报告。" in text
    assert "layout-residual-accepted" in text
    assert "状态: accepted_with_comment" in text
    assert "open-finding-not-closeout-evidence" not in text


def test_bv_markdown_report_includes_finding_closeout_evidence_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-finding-closeout",
        intake=intake,
        risks=[
            BVRiskItem(
                risk_id="foundation-bearing-capacity-closed",
                title="基础承载力澄清已关闭",
                severity="high",
                trigger_basis="工程师复核 Rev B 地勘资料。",
                impact_scope="基础审核",
                recommendation="保留关闭证据。",
                blocks_report_issue=True,
                category="nonconformity",
                status="closed",
                closeout_note="工程师确认 Rev B 地勘承载力参数可用于筛查级报告。",
            )
        ],
    )

    report = build_bv_markdown_report(intake, result, project_state=state)

    assert "## 发现项关闭证据" in report
    assert "foundation-bearing-capacity-closed" in report
    assert "关闭说明: 工程师确认 Rev B 地勘承载力参数可用于筛查级报告。" in report


def test_bv_report_preview_includes_report_revision_history_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-revision-history",
        intake=intake,
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=10,
                rfi_count=1,
                blocking_risk_ids=["risk-foundation-input"],
                calculation_run_ids=["foundation-run-001"],
                created_by="Engineer A",
                created_at="2026-05-21T10:00:00+08:00",
                note="Issued for internal technical review.",
            )
        ],
    )

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(section for section in preview.sections if section.heading == "报告版本历史")
    text = "\n".join(section.items)

    assert "report-rev-001" in text
    assert "来源阶段: report_draft" in text
    assert "章节数: 10" in text
    assert "RFI 数量: 1" in text
    assert "阻塞发现项: risk-foundation-input" in text
    assert "计算运行: foundation-run-001" in text
    assert "创建人: Engineer A" in text
    assert "Issued for internal technical review." in text


def test_bv_markdown_report_includes_report_revision_history_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-revision-history",
        intake=intake,
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=10,
                rfi_count=0,
                blocking_risk_ids=[],
                calculation_run_ids=["foundation-run-001"],
                created_by="Engineer A",
            )
        ],
    )

    report = build_bv_markdown_report(intake, result, project_state=state)

    assert "## 报告版本历史" in report
    assert "report-rev-001" in report
    assert "计算运行: foundation-run-001" in report


def test_bv_report_preview_includes_active_rfi_register_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-active-rfi",
        intake=intake,
        rfi_items=[
            RFIItem(
                rfi_id="rfi-calculation-blocked-foundation",
                question="请补充基础抗拔计算输入并确认单位。",
                responsible_party="client / designer",
                trigger_basis="基础确定性计算输入阻塞。",
                required_document_or_field="pile_length_m, uplift_force_kn",
                status="open",
                reopen_review_items=["pile_length_m", "uplift_force_kn"],
                triggers_incremental_recheck=True,
            ),
            RFIItem(
                rfi_id="rfi-closed-reference",
                question="已关闭 RFI 不应进入未关闭台账。",
                responsible_party="client",
                trigger_basis="已关闭。",
                required_document_or_field="technical_specification",
                status="closed",
                client_response="Rev B 已补充。",
            ),
        ],
    )

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(
        section
        for section in preview.sections
        if section.heading == "未关闭 RFI 与客户澄清项"
    )
    text = "\n".join(section.items)

    assert "rfi-calculation-blocked-foundation" in text
    assert "状态: open" in text
    assert "触发依据: 基础确定性计算输入阻塞。" in text
    assert "pile_length_m, uplift_force_kn" in text
    assert "增量复核: 是" in text
    assert "rfi-closed-reference" not in text


def test_bv_markdown_report_includes_active_rfi_register_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-active-rfi",
        intake=intake,
        rfi_items=[
            RFIItem(
                rfi_id="rfi-calculation-blocked-superstructure",
                question="请确认支架立柱截面和最不利弯矩。",
                responsible_party="client / designer",
                trigger_basis="上部支架构件确定性计算输入阻塞。",
                required_document_or_field="post_section, worst_bending_moment_knm",
                status="reopened",
                reopen_review_items=["post_section", "worst_bending_moment_knm"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    report = build_bv_markdown_report(intake, result, project_state=state)

    assert "## 未关闭 RFI 与客户澄清项" in report
    assert "rfi-calculation-blocked-superstructure" in report
    assert "post_section, worst_bending_moment_knm" in report


def test_bv_report_filename_uses_date_and_scope_key() -> None:
    filename = build_bv_report_filename("rooftop_pv_review", report_date=date(2026, 5, 9))

    assert filename == "2026-05-09-rooftop_pv_review-bv-review-report.md"


def test_bv_open_rfi_items_are_created_from_blocking_risks_only() -> None:
    result = evaluate_bv_review(_sample_intake())

    rfi_items = build_bv_open_rfi_items(result.risks)

    assert rfi_items
    assert all(item.status == "open" for item in rfi_items)
    assert all(item.triggers_incremental_recheck for item in rfi_items)
    assert all(item.reopen_review_items for item in rfi_items)
    assert not any("正式签发" in item.question for item in rfi_items)
    assert {
        item.rfi_id.replace("rfi-", "", 1)
        for item in rfi_items
    } <= {risk.risk_id for risk in result.risks if risk.blocks_report_issue}


def test_bv_open_rfi_item_preserves_risk_traceability_and_screening_boundary() -> None:
    result = evaluate_bv_review(_sample_intake())
    blocking_risk = next(risk for risk in result.risks if risk.blocks_report_issue)

    rfi_item = next(
        item
        for item in build_bv_open_rfi_items(result.risks)
        if item.rfi_id == f"rfi-{blocking_risk.risk_id}"
    )

    assert blocking_risk.title in rfi_item.question
    assert "筛查级" in rfi_item.question
    assert rfi_item.trigger_basis == blocking_risk.trigger_basis
    assert rfi_item.required_document_or_field == ", ".join(blocking_risk.linked_field_ids)
    assert rfi_item.reopen_review_items == blocking_risk.linked_field_ids


def test_bv_open_rfi_item_for_blocked_calculation_names_deterministic_input_closeout() -> None:
    risk = BVRiskItem(
        risk_id="calculation_blocked_superstructure_run_post_p1_001",
        title="上部支架构件确定性计算输入阻塞",
        severity="critical",
        trigger_basis="确定性筛查计算 superstructure-run-post-P1-001: 状态=blocked。",
        linked_field_ids=["post_section", "worst_bending_moment_knm"],
        impact_scope="上部支架构件强度、稳定和相关 RFI/NCR 判断",
        recommendation="先关闭确定性计算输入缺口。",
        blocks_report_issue=True,
        category="nonconformity",
    )

    rfi_item = build_bv_open_rfi_items([risk])[0]

    assert "确定性计算输入缺口" in rfi_item.question
    assert "单位" in rfi_item.question
    assert "资料版本" in rfi_item.question
    assert "重新运行筛查级计算" in rfi_item.question
    assert "筛查级" in rfi_item.question
    assert rfi_item.required_document_or_field == "post_section, worst_bending_moment_knm"
