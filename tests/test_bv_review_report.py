from datetime import date

from structural_screening_agent.bv_review.models import BVReviewIntake, BVRiskItem
from structural_screening_agent.bv_review.report import (
    build_bv_open_rfi_items,
    build_bv_markdown_report,
    build_bv_report_filename,
    build_bv_report_preview,
)
from structural_screening_agent.bv_review.project_state import (
    AgentWorkflowEvent,
    CalculationRun,
    DocumentVersion,
    EngineerApproval,
    ExtractedField,
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


def test_bv_report_preview_includes_project_timeline_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-project-timeline",
        intake=intake,
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-input",
                question="Please confirm foundation input.",
                responsible_party="client / designer",
                trigger_basis="Foundation input changed in Rev B.",
                required_document_or_field="pile_length_m",
                status="closed",
                client_response="Designer confirmed Rev B pile length.",
                reopen_review_items=["pile_length_m"],
                completed_recheck_items=["pile_length_m"],
                triggers_incremental_recheck=True,
            )
        ],
        risks=[
            BVRiskItem(
                risk_id="risk-foundation-input",
                title="Foundation input closed",
                severity="high",
                trigger_basis="Engineer reviewed Rev B input.",
                impact_scope="Foundation review",
                recommendation="Keep closeout evidence.",
                blocks_report_issue=True,
                category="nonconformity",
                status="closed",
                closeout_note="Engineer accepted Rev B input for screening report.",
            )
        ],
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=12,
                rfi_count=1,
                blocking_risk_ids=[],
                calculation_run_ids=["foundation-run-001"],
                created_by="Engineer A",
                created_at="2026-05-21T10:00:00+08:00",
                note="Ready for internal review.",
            )
        ],
    )

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(section for section in preview.sections if section.heading == "项目时间线")
    text = "\n".join(section.items)

    assert "01-RFI-rfi-foundation-input" in text
    assert "类型: RFI" in text
    assert "责任方: client / designer" in text
    assert "建议动作: 工程师复核客户回复并保留关闭证据" in text
    assert "02-FINDING-risk-foundation-input" in text
    assert "类型: 发现项" in text
    assert "责任方: 工程师" in text
    assert "03-REPORT-report-rev-001" in text
    assert "类型: 报告版本" in text
    assert "责任方: Engineer A" in text


def test_bv_markdown_report_includes_project_timeline_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-project-timeline",
        intake=intake,
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=12,
                rfi_count=0,
                calculation_run_ids=["foundation-run-001"],
                created_by="Engineer A",
            )
        ],
    )

    report = build_bv_markdown_report(intake, result, project_state=state)

    assert "## 项目时间线" in report
    assert "03-REPORT-report-rev-001" in report
    assert "建议动作: 按报告版本记录继续内部复核" in report


def test_bv_report_project_timeline_includes_agent_and_engineer_gate_events() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-agent-timeline",
        intake=intake,
        agent_events=[
            AgentWorkflowEvent(
                event_id="agent-event-001",
                agent_role="document_intake",
                target_phase="document_check",
                status="applied",
                output_schema_version="bv-agent-output/v1",
                requires_engineer_review=True,
                summary_counts={"document_versions": 2},
            )
        ],
        approvals=[
            EngineerApproval(
                approval_id="approval-calculation-gate",
                target_type="gate",
                target_id="calculation",
                status="approved",
                reviewer="Engineer B",
                approved_at="2026-05-21T11:30:00+08:00",
                comment="Calculation inputs locked for deterministic screening.",
                locked=True,
            )
        ],
    )

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(section for section in preview.sections if section.heading == "项目时间线")
    text = "\n".join(section.items)

    assert "00-AGENT-agent-event-001" in text
    assert "类型: Agent 事件" in text
    assert "状态: 已应用" in text
    assert "责任方: 资料接收 Agent" in text
    assert "关联对象: 资料检查" in text
    assert "建议动作: 复核 Agent 产物并记录工程师判断" in text
    assert "04-APPROVAL-approval-calculation-gate" in text
    assert "类型: 工程师审批" in text
    assert "状态: 已批准" in text
    assert "关联对象: 门禁: calculation" in text
    assert "证据: 2026-05-21T11:30:00+08:00; 已锁定" in text


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


def test_bv_report_preview_includes_project_management_actions_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-management-actions",
        intake=intake,
        current_phase="issue_rfi_closeout",
        phase_statuses={
            "intake": "approved",
            "document_check": "approved",
            "basis_build": "approved",
            "review_plan": "approved",
            "engineer_data_lock": "approved",
            "calculation_check": "waiting_for_engineer",
            "risk_register": "approved",
            "report_draft": "pending",
            "engineer_approval": "pending",
            "issue_rfi_closeout": "waiting_for_client",
        },
        agent_events=[
            AgentWorkflowEvent(
                event_id="calculation-check-agent-001",
                agent_role="calculation_check",
                target_phase="calculation_check",
                status="applied",
                output_schema_version="phase1.local",
                requires_engineer_review=True,
            )
        ],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_locked=True,
                status="failed",
                structured_errors=["Missing geotechnical side resistance."],
            )
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-001",
                question="Please provide geotechnical side resistance.",
                responsible_party="client / designer",
                trigger_basis="Foundation calculation missing side resistance.",
                required_document_or_field="side_resistance_standard_kpa",
                status="open",
                reopen_review_items=["side_resistance_standard_kpa"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(section for section in preview.sections if section.heading == "项目管理待办")
    text = "\n".join(section.items)

    assert "摘要 | 项目待办: 7 | 阻塞报告待办: 7 | 高优先级: 3" in text
    assert "中优先级: 4 | 低优先级: 0" in text
    assert "责任方: 客户 / 设计院, BV 结构审核工程师, BV 项目审核负责人" in text
    assert "rfi-client-response-rfi-foundation-001" in text
    assert "行动类型: RFI 客户回复" in text
    assert "责任角色: 客户 / 设计院" in text
    assert "触发证据: rfi-foundation-001" in text
    assert "阻塞报告: 是" in text
    assert "agent-review-calculation-check-agent-001" in text
    assert "calculation-follow-up-foundation-run-001" in text


def test_bv_report_preview_includes_foundation_evidence_path_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-foundation-evidence",
        intake=intake,
        extracted_fields=[
            ExtractedField(
                field_id="pile_diameter_mm",
                name="Pile diameter",
                candidate_value="300",
                unit="mm",
                source_document_id="calculation-report-c001",
                page_or_section="Foundation input table",
                quote="pile_diameter_mm = 300",
                confidence=0.9,
                is_confirmed=True,
                confirmed_value="300",
                confirmed_unit="mm",
                include_in_calculation=True,
            ),
            ExtractedField(
                field_id="bearing_capacity_characteristic_kpa",
                name="Bearing capacity characteristic",
                candidate_value="180",
                unit="kPa",
                source_document_id="geotechnical-report-g001",
                page_or_section="Geotechnical parameter table",
                quote="fak = 180 kPa",
                confidence=0.88,
                is_confirmed=False,
                include_in_calculation=False,
            ),
        ],
    )

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(section for section in preview.sections if section.heading == "基础证据路径")
    text = "\n".join(section.items)

    assert "地勘参数证据 | 状态: 缺失" in text
    assert "缺失资料: 地勘报告" in text
    assert "未确认字段: bearing_capacity_characteristic_kpa" in text
    assert "缺失字段: side_resistance_standard_kpa" in text
    assert "阻塞基础计算: 是" in text
    assert "基础最不利反力证据" in text


def test_bv_markdown_report_includes_foundation_evidence_path_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(project_id="pv-report-foundation-evidence", intake=intake)

    report = build_bv_markdown_report(intake, result, project_state=state)

    assert "## 基础证据路径" in report
    assert "地勘参数证据 | 状态: 缺失" in report
    assert "阻塞基础计算: 是" in report


def test_bv_report_preview_includes_evidence_matrix_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    risk = BVRiskItem(
        risk_id="risk-geotechnical-evidence",
        title="地勘参数证据不足",
        severity="critical",
        trigger_basis="地勘参数证据不足。",
        linked_field_ids=[
            "bearing_capacity_characteristic_kpa",
            "geotechnical_report",
            "side_resistance_standard_kpa",
        ],
        impact_scope="基础筛查级计算",
        recommendation="补充地勘参数。",
        blocks_report_issue=True,
        category="nonconformity",
    )
    state = ProjectReviewState(
        project_id="pv-report-evidence-matrix",
        intake=intake,
        document_versions=[
            DocumentVersion(
                document_id="geo-r1",
                document_type="geotechnical_report",
                revision="R1",
                source_name="Geotechnical report package",
                status="available",
            )
        ],
        extracted_fields=[
            ExtractedField(
                field_id="bearing_capacity_characteristic_kpa",
                name="Bearing capacity characteristic",
                candidate_value="180",
                unit="kPa",
                source_document_id="geo-r1",
                page_or_section="Section 4.2",
                quote="fak = 180 kPa",
                confidence=0.91,
                is_confirmed=True,
                confirmed_value="180",
                include_in_calculation=True,
            )
        ],
        risks=[risk],
    )
    result = result.model_copy(update={"risks": [*result.risks, risk]})

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(section for section in preview.sections if section.heading == "发现项证据矩阵")
    text = "\n".join(section.items)

    assert "发现项 risk-geotechnical-evidence" in text
    assert "关联项: bearing_capacity_characteristic_kpa" in text
    assert "证据类型: 字段证据" in text
    assert "来源: geo-r1" in text
    assert "位置: Section 4.2" in text
    assert "摘录: fak = 180 kPa" in text
    assert "状态: 已确认" in text
    assert "置信度: 0.91" in text
    assert "关联项: geotechnical_report" in text
    assert "证据类型: 资料证据" in text
    assert "位置: Revision R1" in text
    assert "关联项: side_resistance_standard_kpa" in text
    assert "证据类型: 缺失证据" in text


def test_bv_markdown_report_includes_evidence_matrix_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-evidence-matrix",
        intake=intake,
        risks=[
            BVRiskItem(
                risk_id="risk-missing-side-resistance",
                title="侧阻力参数缺失",
                severity="critical",
                trigger_basis="侧阻力参数缺失。",
                linked_field_ids=["side_resistance_standard_kpa"],
                impact_scope="基础筛查级计算",
                recommendation="补充侧阻力参数。",
                blocks_report_issue=True,
                category="nonconformity",
            )
        ],
    )

    report = build_bv_markdown_report(intake, result, project_state=state)

    assert "## 发现项证据矩阵" in report
    assert "发现项 risk-missing-side-resistance" in report
    assert "证据类型: 缺失证据" in report


def test_bv_markdown_report_includes_project_management_actions_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-management-actions",
        intake=intake,
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-001",
                question="Please provide geotechnical side resistance.",
                responsible_party="client / designer",
                trigger_basis="Foundation calculation missing side resistance.",
                required_document_or_field="side_resistance_standard_kpa",
                status="open",
                reopen_review_items=["side_resistance_standard_kpa"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    report = build_bv_markdown_report(intake, result, project_state=state)

    assert "## 项目管理待办" in report
    assert "摘要 | 项目待办: 1 | 阻塞报告待办: 1" in report
    assert "rfi-client-response-rfi-foundation-001" in report
    assert "建议动作: 跟进客户 / 设计院回复" in report


def test_bv_report_preview_includes_quality_gate_status_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-quality-gates",
        intake=intake,
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-001",
                question="Please provide geotechnical side resistance.",
                responsible_party="client / designer",
                trigger_basis="Foundation calculation missing side resistance.",
                required_document_or_field="side_resistance_standard_kpa",
                status="open",
                reopen_review_items=["side_resistance_standard_kpa"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    preview = build_bv_report_preview(intake, result, project_state=state)
    section = next(section for section in preview.sections if section.heading == "质量门禁状态")
    text = "\n".join(section.items)

    assert "资料门禁: 阻塞" in text
    assert "依据门禁: 通过" in text
    assert "计算门禁: 未锁定" in text
    assert "签发门禁: 阻塞" in text
    assert "缺失必要资料" in text
    assert "结构计算书" in text
    assert "地勘报告" in text
    assert "RFI 触发增量复核" in text
    assert "rfi-foundation-001" in text
    assert "Missing required document inputs" not in text


def test_bv_markdown_report_includes_quality_gate_status_when_state_is_provided() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-quality-gates",
        intake=intake,
        approvals=[
            EngineerApproval(
                approval_id="calculation-gate-approval",
                target_type="gate",
                target_id="calculation",
                status="approved",
                reviewer="Engineer A",
                locked=True,
            )
        ],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_locked=True,
                status="ready",
            )
        ],
    )

    report = build_bv_markdown_report(intake, result, project_state=state)

    assert "## 质量门禁状态" in report
    assert "计算门禁: 已锁定" in report
    assert "可用计算: foundation-run-001" in report
    assert "签发门禁: 阻塞" in report


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
