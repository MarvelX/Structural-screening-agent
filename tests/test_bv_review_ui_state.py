import pytest
from pydantic import ValidationError

from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.ui_state import (
    BV_DOCUMENT_LABELS,
    BV_REVIEW_OBJECT_LABELS,
    build_agent_engineer_review_decision_rows,
    build_agent_workflow_artifact_rows,
    build_agent_engineer_review_queue_rows,
    build_agent_workflow_event_rows,
    build_agent_workflow_phase_rows,
    build_calculation_result_summary_rows,
    build_closed_rfi_incremental_recheck_rows,
    build_extracted_fields_from_human_gate_rows,
    build_bv_review_intake,
    build_field_diff_summary_rows,
    build_ground_fixed_human_gate_rows,
    build_incremental_recheck_summary_rows,
    build_persisted_workflow_run_summary_rows,
    build_project_review_state_summary_rows,
    build_report_gate_evidence_rows,
    default_bv_review_intake,
    localize_report_gate_reason,
)
from structural_screening_agent.bv_review.field_diff import (
    build_incremental_recheck_plan,
    diff_extracted_fields,
)
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    ProjectReviewState,
    RFIItem,
)
from structural_screening_agent.bv_review.human_gate import (
    ReportDraftGateResult,
    record_agent_review_decision,
)
from structural_screening_agent.bv_review.state_repository import ProjectReviewStateSummary
from structural_screening_agent.bv_review import (
    PersistedWorkflowRunSummary,
    run_local_agent_workflow_until_blocked,
)
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def test_default_bv_review_intake_runs_through_workflow() -> None:
    intake = default_bv_review_intake()
    result = evaluate_bv_review(intake)

    assert isinstance(intake, BVReviewIntake)
    assert intake.project_name == "BV rooftop PV design review demo"
    assert "gb" in intake.standards_systems
    assert "iec" in intake.standards_systems
    assert "mounting_structure" in intake.review_objects
    assert result.report_preview is not None
    assert result.report_preview.title == "BV 光伏结构设计审查报告"


def test_bv_ui_labels_cover_default_documents_and_review_objects() -> None:
    intake = default_bv_review_intake()

    assert set(intake.documents) <= set(BV_DOCUMENT_LABELS)
    assert set(intake.review_objects) <= set(BV_REVIEW_OBJECT_LABELS)
    assert BV_DOCUMENT_LABELS["calculation_report"]["zh"] == "结构计算书"
    assert BV_REVIEW_OBJECT_LABELS["existing_rooftop_added_load"]["zh"] == "既有屋面增载"


def test_build_bv_review_intake_preserves_user_selected_scope_and_documents() -> None:
    intake = build_bv_review_intake(
        project_name="Owner review package",
        country_or_region="Australia",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["iec", "as_nzs"],
        review_objects=["foundation", "load_calculation"],
        client_requirements_text="Independent review before IFC release",
        documents={
            "technical_specification": "available",
            "geotechnical_report": "partial",
            "calculation_report": "missing",
        },
    )

    assert intake.project_name == "Owner review package"
    assert intake.country_or_region == "Australia"
    assert intake.standards_systems == ["iec", "as_nzs"]
    assert intake.review_objects == ["foundation", "load_calculation"]
    assert intake.client_requirements == ["Independent review before IFC release"]
    assert intake.documents["geotechnical_report"] == "partial"


def test_build_bv_review_intake_rejects_empty_user_selected_scope() -> None:
    with pytest.raises(ValidationError):
        build_bv_review_intake(
            project_name="Scope removed",
            country_or_region="China",
            project_type="rooftop_pv",
            design_stage="construction_drawing",
            standards_systems=[],
            review_objects=["foundation"],
            client_requirements_text="",
            documents={},
        )

    with pytest.raises(ValidationError):
        build_bv_review_intake(
            project_name="Scope removed",
            country_or_region="China",
            project_type="rooftop_pv",
            design_stage="construction_drawing",
            standards_systems=["gb"],
            review_objects=[],
            client_requirements_text="",
            documents={},
        )


def test_ground_fixed_human_gate_rows_follow_selected_language_and_traceability() -> None:
    zh_rows = build_ground_fixed_human_gate_rows("zh")
    en_rows = build_ground_fixed_human_gate_rows("en")

    assert zh_rows[0]["field_name"] == "支架倾角"
    assert en_rows[0]["field_name"] == "Rack tilt angle"
    assert "支架" not in str(en_rows[0]["field_name"])
    assert all(row["source_document_id"] for row in zh_rows)
    assert all(row["page_or_section"] for row in zh_rows)
    assert all(row["quote"] for row in zh_rows)
    assert {
        "pile_diameter_mm",
        "side_resistance_standard_kpa",
        "uplift_force_kn",
        "compression_force_kn",
        "horizontal_force_kn",
    } <= {str(row["field_id"]) for row in zh_rows}
    assert {"section_area_mm2", "steel_yield_strength_mpa", "bending_moment_knm"} <= {
        str(row["field_id"]) for row in zh_rows
    }


def test_human_gate_rows_convert_to_traceable_extracted_fields() -> None:
    fields = build_extracted_fields_from_human_gate_rows(
        build_ground_fixed_human_gate_rows("en")
    )

    assert fields[0].field_id == "tilt_angle_deg"
    assert fields[0].source_document_id == "structural-drawing-s101"
    assert fields[0].include_in_calculation is False
    assert fields[0].is_confirmed is True
    foundation_field_ids = {
        "pile_diameter_mm",
        "pile_length_m",
        "side_resistance_standard_kpa",
        "bearing_capacity_characteristic_kpa",
        "uplift_force_kn",
        "compression_force_kn",
        "horizontal_force_kn",
    }
    superstructure_field_ids = {
        "section_area_mm2",
        "section_modulus_mm3",
        "radius_of_gyration_mm",
        "effective_length_m",
        "steel_yield_strength_mpa",
        "axial_force_kn",
        "bending_moment_knm",
    }
    calculation_field_ids = {
        field.field_id for field in fields if field.include_in_calculation
    }
    assert foundation_field_ids <= calculation_field_ids
    assert superstructure_field_ids <= calculation_field_ids


def test_build_incremental_recheck_summary_returns_review_items_without_running_diff() -> None:
    old_fields = build_extracted_fields_from_human_gate_rows(
        build_ground_fixed_human_gate_rows("en")
    )
    new_rows = build_ground_fixed_human_gate_rows("en")
    next(row for row in new_rows if row["field_id"] == "pile_length_m")[
        "candidate_value"
    ] = "4.0"
    new_fields = build_extracted_fields_from_human_gate_rows(new_rows)
    plan = build_incremental_recheck_plan(diff_extracted_fields(old_fields, new_fields))

    rows = build_incremental_recheck_summary_rows(plan, "en")

    assert rows
    assert rows[0]["Type"] == "Calculation Recheck"
    assert "Pile length" in str(rows[0]["Reason"])


def test_persisted_workflow_run_summary_rows_localize_resume_audit_trail() -> None:
    summary = PersistedWorkflowRunSummary(
        project_id="pv-001",
        start_phase="intake",
        final_phase="engineer_data_lock",
        applied_agent_event_ids=["agent-event-001", "agent-event-002"],
        applied_agent_roles=["document_intake", "basis_code"],
        artifact_counts={
            "basis_references": 4,
            "review_plan": 3,
            "review_paths": 2,
            "rfi_items": 1,
            "agent_events": 2,
            "risks": 0,
        },
        saved=True,
    )

    zh_rows = build_persisted_workflow_run_summary_rows(summary, "zh")
    en_rows = build_persisted_workflow_run_summary_rows(summary, "en")

    assert zh_rows == [
        {"项目": "项目 ID", "内容": "pv-001"},
        {"项目": "起始阶段", "内容": "项目录入"},
        {"项目": "结束阶段", "内容": "工程师数据锁定"},
        {"项目": "新增 Agent 事件", "内容": "agent-event-001, agent-event-002"},
        {"项目": "执行 Agent", "内容": "资料接收 Agent, 依据与标准 Agent"},
        {
            "项目": "产物摘要",
            "内容": "审核依据: 4; 审核计划: 3; 审核路径: 2; RFI: 1; Agent 事件: 2",
        },
        {"项目": "保存状态", "内容": "已保存"},
    ]
    assert en_rows == [
        {"Item": "Project ID", "Value": "pv-001"},
        {"Item": "Start Phase", "Value": "Intake"},
        {"Item": "Final Phase", "Value": "Engineer Data Lock"},
        {"Item": "New Agent Events", "Value": "agent-event-001, agent-event-002"},
        {"Item": "Executed Agents", "Value": "Document Intake Agent, Basis & Code Agent"},
        {
            "Item": "Artifact Summary",
            "Value": "Review Basis: 4; Review Plan: 3; Review Paths: 2; RFI: 1; Agent Events: 2",
        },
        {"Item": "Save Status", "Value": "Saved"},
    ]
    assert "Document Intake Agent" not in str(zh_rows)
    assert "资料接收 Agent" not in str(en_rows)


def test_project_review_state_summary_rows_localize_project_inventory() -> None:
    summaries = [
        ProjectReviewStateSummary(
            project_id="pv-001",
            project_name="Ground PV review",
            current_phase="document_check",
            agent_event_count=4,
            pending_agent_review_count=2,
            active_rfi_count=1,
            report_revision_count=1,
        )
    ]

    zh_rows = build_project_review_state_summary_rows(summaries, "zh")
    en_rows = build_project_review_state_summary_rows(summaries, "en")

    assert zh_rows == [
        {
            "项目 ID": "pv-001",
            "项目名称": "Ground PV review",
            "当前阶段": "资料检查",
            "Agent 事件": 4,
            "待工程师复核": 2,
            "未关闭 RFI": 1,
            "报告修订": 1,
        }
    ]
    assert en_rows == [
        {
            "Project ID": "pv-001",
            "Project Name": "Ground PV review",
            "Current Phase": "Document Check",
            "Agent Events": 4,
            "Pending Engineer Reviews": 2,
            "Active RFIs": 1,
            "Report Revisions": 1,
        }
    ]
    assert "Document Check" not in str(zh_rows)
    assert "资料检查" not in str(en_rows)


def test_closed_rfi_incremental_recheck_rows_show_completed_evidence_without_mixed_language() -> None:
    state = ProjectReviewState(
        project_id="pv-ui-rfi-closeout",
        intake=default_bv_review_intake(),
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

    zh_rows = build_closed_rfi_incremental_recheck_rows(state, "zh")
    en_rows = build_closed_rfi_incremental_recheck_rows(state, "en")

    assert zh_rows == [
        {
            "RFI ID": "rfi-pile_length_m",
            "复核项 ID": "calculation-recheck-pile_length_m",
            "类型": "计算复核",
            "字段 ID": "pile_length_m",
            "计算运行 ID": "foundation-run-001",
            "关闭证据": "已完成增量复核",
        }
    ]
    assert en_rows == [
        {
            "RFI ID": "rfi-pile_length_m",
            "Recheck Item ID": "calculation-recheck-pile_length_m",
            "Type": "Calculation Recheck",
            "Field IDs": "pile_length_m",
            "Calculation Run IDs": "foundation-run-001",
            "Closeout Evidence": "Incremental recheck completed",
        }
    ]
    assert "Calculation Recheck" not in str(zh_rows)
    assert "计算复核" not in str(en_rows)


def test_bv_diff_and_recheck_summary_rows_are_localized_for_chinese_ui() -> None:
    old_fields = build_extracted_fields_from_human_gate_rows(
        build_ground_fixed_human_gate_rows("zh")
    )
    new_rows = build_ground_fixed_human_gate_rows("zh")
    next(row for row in new_rows if row["field_id"] == "pile_length_m")[
        "candidate_value"
    ] = "4.0"
    new_fields = build_extracted_fields_from_human_gate_rows(new_rows)
    diffs = diff_extracted_fields(old_fields, new_fields)
    plan = build_incremental_recheck_plan(diffs)

    diff_rows = build_field_diff_summary_rows(diffs, "zh")
    recheck_rows = build_incremental_recheck_summary_rows(plan, "zh")

    assert "差分类型" in diff_rows[0]
    assert diff_rows[0]["差分类型"] == "修改"
    assert diff_rows[0]["影响已锁定计算"] == "是"
    assert "类型" in recheck_rows[0]
    assert recheck_rows[0]["类型"] == "计算复核"
    assert "changed and affects" not in str(recheck_rows[0]["原因"])


def test_report_gate_incremental_rfi_reason_localizes_to_chinese() -> None:
    reason = "Open RFI items trigger incremental recheck: rfi-pile_length_m"

    localized = localize_report_gate_reason(reason, "zh")

    assert localized == "未关闭的 RFI 触发增量复核：rfi-pile_length_m"


def test_report_gate_pending_agent_review_reason_localizes_to_chinese() -> None:
    reason = "Pending agent engineer review blocks report draft input: agent-event-001"

    localized = localize_report_gate_reason(reason, "zh")

    assert localized == "待工程师复核的 Agent 产物阻塞报告草稿输入：agent-event-001"


def test_report_gate_rejected_agent_review_reason_localizes_to_chinese() -> None:
    reason = "Rejected agent engineer review blocks report draft input: agent-event-001"

    localized = localize_report_gate_reason(reason, "zh")

    assert localized == "已驳回的 Agent 产物阻塞报告草稿输入：agent-event-001"


def test_report_gate_evidence_rows_localize_structured_gate_ids() -> None:
    gate = ReportDraftGateResult(
        status="blocked",
        blocking_risk_ids=["risk-001"],
        incremental_recheck_rfi_ids=["rfi-001"],
        pending_agent_review_event_ids=["agent-event-001"],
        rejected_agent_review_event_ids=["agent-event-002"],
        calculation_run_ids=["run-001"],
    )

    zh_rows = build_report_gate_evidence_rows(gate, "zh")
    en_rows = build_report_gate_evidence_rows(gate, "en")

    assert zh_rows == [
        {"证据类型": "阻塞风险", "ID": "risk-001", "门禁作用": "阻塞报告草稿"},
        {"证据类型": "增量复核 RFI", "ID": "rfi-001", "门禁作用": "阻塞报告草稿"},
        {"证据类型": "待复核 Agent 产物", "ID": "agent-event-001", "门禁作用": "阻塞报告草稿"},
        {"证据类型": "已驳回 Agent 产物", "ID": "agent-event-002", "门禁作用": "阻塞报告草稿"},
        {"证据类型": "可用计算运行", "ID": "run-001", "门禁作用": "支持报告草稿"},
    ]
    assert en_rows == [
        {"Evidence Type": "Blocking Risk", "ID": "risk-001", "Gate Role": "Blocks Report Draft"},
        {
            "Evidence Type": "Incremental Recheck RFI",
            "ID": "rfi-001",
            "Gate Role": "Blocks Report Draft",
        },
        {
            "Evidence Type": "Pending Agent Review",
            "ID": "agent-event-001",
            "Gate Role": "Blocks Report Draft",
        },
        {
            "Evidence Type": "Rejected Agent Review",
            "ID": "agent-event-002",
            "Gate Role": "Blocks Report Draft",
        },
        {
            "Evidence Type": "Available Calculation Run",
            "ID": "run-001",
            "Gate Role": "Supports Report Draft",
        },
    ]
    assert "Pending Agent Review" not in str(zh_rows)
    assert "待复核" not in str(en_rows)


def test_calculation_result_summary_rows_localize_internal_keys_for_chinese_ui() -> None:
    rows = build_calculation_result_summary_rows(
        {
            "screening_boundary": "screening-level review support only",
            "lateral_and_overturning_check_note": (
                "horizontal force captured for engineer review; "
                "lateral and overturning checks are not covered"
            ),
            "horizontal_force_kn": 12,
            "screening_status": "review_required",
            "uplift_utilization_ratio": 1.21,
            "member_type": "post",
            "strength_utilization_ratio": 0.53,
        },
        "zh",
    )

    assert rows[0] == {"项目": "筛查边界", "结果": "仅用于筛查级审核支持"}
    assert rows[1] == {
        "项目": "水平力与抗倾覆提示",
        "结果": "已记录水平力供工程师复核；侧向与抗倾覆验算未覆盖",
    }
    assert rows[2] == {"项目": "最不利水平力", "结果": 12}
    assert rows[3] == {"项目": "筛查状态", "结果": "需复核"}
    assert rows[4] == {"项目": "抗拔利用率", "结果": 1.21}
    assert rows[5] == {"项目": "构件类型", "结果": "立柱"}
    assert rows[6] == {"项目": "强度利用率", "结果": 0.53}


def test_agent_workflow_phase_rows_localize_state_for_chinese_ui() -> None:
    state = run_local_agent_workflow_until_blocked(
        ProjectReviewState(project_id="pv-ui-agent", intake=default_bv_review_intake())
    )

    rows = build_agent_workflow_phase_rows(state, "zh")

    assert rows[0] == {"阶段": "项目录入", "状态": "待处理", "当前": ""}
    assert any(row == {"阶段": "工程师数据锁定", "状态": "等待工程师", "当前": "是"} for row in rows)
    assert "waiting_for_engineer" not in str(rows)


def test_agent_workflow_artifact_rows_show_runner_outputs_without_mixed_language() -> None:
    state = run_local_agent_workflow_until_blocked(
        ProjectReviewState(project_id="pv-ui-agent", intake=default_bv_review_intake())
    )

    zh_rows = build_agent_workflow_artifact_rows(state, "zh")
    en_rows = build_agent_workflow_artifact_rows(state, "en")

    assert {"产物": "审核依据", "数量": len(state.basis_references)} in zh_rows
    assert {"产物": "Agent 事件", "数量": len(state.agent_events)} in zh_rows
    assert {"Artifact": "Review Basis", "Count": len(state.basis_references)} in en_rows
    assert {"Artifact": "Agent Events", "Count": len(state.agent_events)} in en_rows
    assert "Review Basis" not in str(zh_rows)
    assert "审核依据" not in str(en_rows)


def test_agent_workflow_event_rows_localize_trace_details_without_raw_state() -> None:
    state = run_local_agent_workflow_until_blocked(
        ProjectReviewState(project_id="pv-ui-agent", intake=default_bv_review_intake())
    )

    zh_rows = build_agent_workflow_event_rows(state, "zh")
    en_rows = build_agent_workflow_event_rows(state, "en")

    assert zh_rows[0]["事件 ID"] == "agent-event-001"
    assert zh_rows[0]["Agent"] == "资料接收 Agent"
    assert zh_rows[0]["目标阶段"] == "资料检查"
    assert zh_rows[0]["状态"] == "已应用"
    assert zh_rows[0]["需工程师复核"] == "是"
    assert "资料版本: 6" in str(zh_rows[0]["产物摘要"])
    assert "缺失资料键: 2" in str(zh_rows[0]["产物摘要"])
    assert "document_check" not in str(zh_rows)
    assert "applied" not in str(zh_rows)

    assert en_rows[0]["Event ID"] == "agent-event-001"
    assert en_rows[0]["Agent"] == "Document Intake Agent"
    assert en_rows[0]["Target Phase"] == "Document Check"
    assert en_rows[0]["Status"] == "Applied"
    assert en_rows[0]["Engineer Review"] == "Yes"
    assert "Document Versions: 6" in str(en_rows[0]["Output Summary"])
    assert "Missing Document Keys: 2" in str(en_rows[0]["Output Summary"])
    assert "资料检查" not in str(en_rows)


def test_agent_engineer_review_queue_rows_show_only_pending_human_reviews() -> None:
    state = run_local_agent_workflow_until_blocked(
        ProjectReviewState(project_id="pv-ui-agent", intake=default_bv_review_intake())
    )
    approved_state = state.model_copy(
        update={
            "phase_statuses": {
                **state.phase_statuses,
                "document_check": "approved",
            }
        }
    )

    zh_rows = build_agent_engineer_review_queue_rows(approved_state, "zh")
    en_rows = build_agent_engineer_review_queue_rows(approved_state, "en")

    assert zh_rows
    assert all(row["阶段"] != "资料检查" for row in zh_rows)
    assert zh_rows[0]["复核项"] == "agent-event-002"
    assert zh_rows[0]["Agent"] == "依据与标准 Agent"
    assert zh_rows[0]["待办状态"] == "待工程师复核"
    assert zh_rows[0]["建议动作"] == "复核 Agent 产物并记录工程师判断"
    assert f"审核依据: {len(approved_state.basis_references)}" in str(zh_rows[0]["产物摘要"])
    assert "basis_build" not in str(zh_rows)
    assert "waiting_for_engineer" not in str(zh_rows)
    assert "Review agent output" not in str(zh_rows)

    assert en_rows[0]["Review Item"] == "agent-event-002"
    assert en_rows[0]["Agent"] == "Basis & Code Agent"
    assert en_rows[0]["Todo Status"] == "Pending Engineer Review"
    assert en_rows[0]["Suggested Action"] == "Review agent output and record engineer decision"
    assert f"Review Basis: {len(approved_state.basis_references)}" in str(
        en_rows[0]["Output Summary"]
    )
    assert "等待工程师" not in str(en_rows)


def test_agent_engineer_review_decision_rows_localize_approval_ledger() -> None:
    state = run_local_agent_workflow_until_blocked(
        ProjectReviewState(project_id="pv-ui-agent", intake=default_bv_review_intake())
    )
    reviewed = record_agent_review_decision(
        state,
        event_id="agent-event-001",
        decision="approved",
        reviewer="Engineer A",
        comment="Document intake reviewed.",
    )

    zh_rows = build_agent_engineer_review_decision_rows(reviewed, "zh")
    en_rows = build_agent_engineer_review_decision_rows(reviewed, "en")

    assert zh_rows == [
        {
            "复核记录": "agent-review-agent-event-001",
            "复核项": "agent-event-001",
            "Agent": "资料接收 Agent",
            "阶段": "资料检查",
            "结论": "已批准",
            "锁定": "是",
            "复核人": "Engineer A",
            "意见": "Document intake reviewed.",
        }
    ]
    assert en_rows == [
        {
            "Decision Record": "agent-review-agent-event-001",
            "Review Item": "agent-event-001",
            "Agent": "Document Intake Agent",
            "Phase": "Document Check",
            "Decision": "Approved",
            "Locked": "Yes",
            "Reviewer": "Engineer A",
            "Comment": "Document intake reviewed.",
        }
    ]
    assert "document_check" not in str(zh_rows)
    assert "已批准" not in str(en_rows)
