from __future__ import annotations

from datetime import date
from typing import Optional

from structural_screening_agent.bv_review.models import (
    BVReportPreview,
    BVReportSection,
    BVReviewIntake,
    BVReviewResult,
    BVRiskItem,
)
from structural_screening_agent.bv_review.field_diff import (
    build_incremental_recheck_plan_from_closed_rfis,
)
from structural_screening_agent.bv_review.project_state import ProjectReviewState, RFIItem
from structural_screening_agent.bv_review.project_timeline import build_project_timeline_events
from structural_screening_agent.bv_review.service_scope import (
    build_service_scope_recommendations,
)


def build_bv_report_preview(
    intake: BVReviewIntake,
    result: BVReviewResult,
    *,
    project_state: Optional[ProjectReviewState] = None,
) -> BVReportPreview:
    blocking_items = [item for item in result.risks if item.blocks_report_issue]
    sections = [
        BVReportSection(
            heading="项目与审核范围",
            items=[
                f"项目名称: {intake.project_name}",
                f"国家/地区: {intake.country_or_region}",
                f"设计阶段: {intake.design_stage}",
                f"审核对象: {', '.join(intake.review_objects)}",
                f"当前审核结论: {result.decision}",
            ],
        ),
        BVReportSection(
            heading="审核依据",
            items=[f"{item.title}: {'; '.join(item.review_actions)}" for item in result.basis_references],
        ),
        BVReportSection(
            heading="提交资料清单与完整性状态",
            items=[f"{item.title}: {item.status} | {item.required_action}" for item in result.checklist_items],
        ),
        BVReportSection(
            heading="审核路径与方法",
            items=[f"{item.title}: {item.status} | {item.method}" for item in result.review_paths],
        ),
        BVReportSection(
            heading="主要发现",
            items=[
                f"阻塞项数量: {len(blocking_items)}",
                f"风险与不符合项数量: {len(result.risks)}",
                f"审核计划条目数量: {len(result.review_plan)}",
            ],
        ),
        BVReportSection(
            heading="不符合项与阻塞项",
            items=[
                f"{item.title}: {item.recommendation}"
                for item in result.risks
                if item.category == "nonconformity" or item.blocks_report_issue
            ]
            or ["当前未识别阻塞报告签发的不符合项。"],
        ),
        BVReportSection(
            heading="技术风险与优化建议",
            items=[
                f"{item.title}: {item.recommendation}"
                for item in result.risks
                if item.category in {"risk", "optimization"}
            ]
            or ["当前未识别需要单独列示的优化建议。"],
        ),
        BVReportSection(
            heading="后续行动",
            items=[f"{item.phase}: {item.method} | 交付物: {item.deliverable}" for item in result.review_plan[:8]],
        ),
        BVReportSection(
            heading="审核边界声明",
            items=[
                "本工具用于设计审核前期组织、资料完整性判断、风险识别和 screening-level 技术路径梳理。",
                "输出不替代正式设计、法定审批、有限元计算、施工图审查，也不代表 BV 官方签发流程。",
                "所有自动生成的不符合项、技术风险和优化建议均需由合格工程师复核。",
            ],
        ),
    ]
    active_rfi_section = build_bv_active_rfi_register_section(project_state)
    if active_rfi_section is not None:
        sections.insert(-1, active_rfi_section)
    rfi_closeout_section = build_bv_rfi_closeout_evidence_section(project_state)
    if rfi_closeout_section is not None:
        sections.insert(-1, rfi_closeout_section)
    finding_closeout_section = build_bv_finding_closeout_evidence_section(project_state)
    if finding_closeout_section is not None:
        sections.insert(-1, finding_closeout_section)
    report_revision_section = build_bv_report_revision_history_section(project_state)
    if report_revision_section is not None:
        sections.insert(-1, report_revision_section)
    project_timeline_section = build_bv_project_timeline_section(project_state)
    if project_timeline_section is not None:
        sections.insert(-1, project_timeline_section)
    service_scope_section = build_bv_service_scope_section(
        intake,
        result,
        project_state=project_state,
    )
    if service_scope_section is not None:
        sections.insert(-1, service_scope_section)
    return BVReportPreview(title="BV 光伏结构设计审查报告", sections=sections)


def build_bv_open_rfi_items(risks: list[BVRiskItem]) -> list[RFIItem]:
    rfi_items: list[RFIItem] = []
    for risk in risks:
        if not risk.blocks_report_issue:
            continue
        reopen_items = list(risk.linked_field_ids) or [risk.risk_id]
        rfi_items.append(
            RFIItem(
                rfi_id=f"rfi-{risk.risk_id}",
                question=_build_rfi_question_from_risk(risk),
                responsible_party="client / designer",
                trigger_basis=risk.trigger_basis,
                required_document_or_field=", ".join(reopen_items),
                status="open",
                reopen_review_items=reopen_items,
                triggers_incremental_recheck=True,
            )
        )
    return rfi_items


def _build_rfi_question_from_risk(risk: BVRiskItem) -> str:
    if risk.risk_id.startswith("calculation_blocked_"):
        return (
            f"请针对筛查级发现“{risk.title}”关闭确定性计算输入缺口，"
            "确认相关输入值、单位、资料版本和设计方处置意见；"
            "工程师复核后需重新运行筛查级计算，再进入报告结论。"
        )

    return (
        f"请针对筛查级发现“{risk.title}”提供澄清、补充资料或设计方处置意见；"
        "该问题需工程师复核后再进入报告结论。"
    )


def build_bv_active_rfi_register_section(
    project_state: Optional[ProjectReviewState],
) -> Optional[BVReportSection]:
    if project_state is None:
        return None

    active_rfis = [
        item
        for item in project_state.rfi_items
        if item.status in {"open", "responded", "reopened"}
    ]
    if not active_rfis:
        return None

    return BVReportSection(
        heading="未关闭 RFI 与客户澄清项",
        items=[
            (
                f"RFI {item.rfi_id} | "
                f"状态: {item.status} | "
                f"责任方: {item.responsible_party} | "
                f"触发依据: {item.trigger_basis} | "
                f"要求资料/字段: {item.required_document_or_field} | "
                f"增量复核: {'是' if item.triggers_incremental_recheck else '否'} | "
                f"问题: {item.question}"
            )
            for item in active_rfis
        ],
    )


def build_bv_rfi_closeout_evidence_section(
    project_state: Optional[ProjectReviewState],
) -> Optional[BVReportSection]:
    if project_state is None:
        return None

    plan = build_incremental_recheck_plan_from_closed_rfis(
        project_state.rfi_items,
        calculation_runs=project_state.calculation_runs,
    )
    if not plan.affected_items:
        return None

    item_to_rfi_id = {
        review_item_id: rfi.rfi_id
        for rfi in plan.rfi_items
        for review_item_id in rfi.reopen_review_items
    }
    return BVReportSection(
        heading="RFI 关闭与增量复核证据",
        items=[
            (
                f"RFI {item_to_rfi_id.get(item.item_id, '')} | "
                f"复核项: {item.item_id} | "
                f"字段: {', '.join(item.field_ids) or 'N/A'} | "
                f"计算运行: {', '.join(item.calculation_run_ids) or 'N/A'} | "
                "关闭证据: 已完成增量复核"
            )
            for item in plan.affected_items
        ],
    )


def build_bv_finding_closeout_evidence_section(
    project_state: Optional[ProjectReviewState],
) -> Optional[BVReportSection]:
    if project_state is None:
        return None

    closed_findings = [
        item
        for item in project_state.risks
        if item.status in {"closed", "accepted_with_comment"}
    ]
    if not closed_findings:
        return None

    return BVReportSection(
        heading="发现项关闭证据",
        items=[
            (
                f"发现项 {item.risk_id} | "
                f"标题: {item.title} | "
                f"状态: {item.status} | "
                f"影响范围: {item.impact_scope} | "
                f"关闭说明: {item.closeout_note or 'N/A'}"
            )
            for item in closed_findings
        ],
    )


def build_bv_report_revision_history_section(
    project_state: Optional[ProjectReviewState],
) -> Optional[BVReportSection]:
    if project_state is None or not project_state.report_revisions:
        return None

    return BVReportSection(
        heading="报告版本历史",
        items=[
            (
                f"报告版本 {revision.revision_id} | "
                f"来源阶段: {revision.source_phase} | "
                f"标题: {revision.report_title} | "
                f"章节数: {revision.section_count} | "
                f"RFI 数量: {revision.rfi_count} | "
                f"阻塞发现项: {', '.join(revision.blocking_risk_ids) or 'N/A'} | "
                f"计算运行: {', '.join(revision.calculation_run_ids) or 'N/A'} | "
                f"创建人: {revision.created_by} | "
                f"创建时间: {revision.created_at or 'N/A'} | "
                f"备注: {revision.note or 'N/A'}"
            )
            for revision in project_state.report_revisions
        ],
    )


def build_bv_project_timeline_section(
    project_state: Optional[ProjectReviewState],
) -> Optional[BVReportSection]:
    if project_state is None:
        return None

    items = [
        (
            f"排序: {event.sort_key} | "
            f"类型: {_timeline_event_type_label(event.event_type)} | "
            f"项目 ID: {event.item_id} | "
            f"状态: {_timeline_status_label(event.event_type, event.status)} | "
            f"责任方: {_timeline_owner_label(event.owner)} | "
            f"关联对象: {event.linked_object or 'N/A'} | "
            f"说明: {event.description} | "
            f"证据: {event.evidence or 'N/A'} | "
            f"建议动作: {_timeline_suggested_action_label(event.suggested_action)}"
        )
        for event in build_project_timeline_events(project_state)
    ]
    if not items:
        return None
    return BVReportSection(heading="项目时间线", items=items)


def _timeline_event_type_label(event_type: str) -> str:
    labels = {
        "rfi": "RFI",
        "finding": "发现项",
        "report_revision": "报告版本",
    }
    return labels.get(event_type, event_type)


def _timeline_status_label(event_type: str, status: str) -> str:
    if event_type == "rfi":
        return _rfi_status_label(status)
    if event_type == "finding":
        return _finding_status_label(status)
    if event_type == "report_revision":
        return _review_phase_label(status)
    return status


def _timeline_owner_label(owner: str) -> str:
    if owner == "engineer":
        return "工程师"
    return owner


def _timeline_suggested_action_label(suggested_action: str) -> str:
    labels = {
        "rfi_closeout_review": "工程师复核客户回复并保留关闭证据",
        "finding_closeout_record": "保留发现项关闭证据并进入报告",
        "report_revision_review": "按报告版本记录继续内部复核",
    }
    return labels.get(suggested_action, suggested_action)


def _rfi_status_label(status: str) -> str:
    labels = {
        "open": "待回复",
        "responded": "已回复",
        "closed": "已关闭",
        "reopened": "重新打开",
    }
    return labels.get(status, status)


def _finding_status_label(status: str) -> str:
    labels = {
        "open": "未关闭",
        "under_review": "复核中",
        "closed": "已关闭",
        "accepted_with_comment": "带意见接受",
    }
    return labels.get(status, status)


def _review_phase_label(phase: str) -> str:
    labels = {
        "intake": "项目录入",
        "document_check": "资料检查",
        "basis_build": "审核依据",
        "review_plan": "审核计划",
        "engineer_data_lock": "工程师数据锁定",
        "calculation_check": "计算校核",
        "risk_register": "风险登记",
        "report_draft": "报告草稿",
        "engineer_approval": "工程师批准",
        "issue_rfi_closeout": "签发 / RFI 关闭",
    }
    return labels.get(phase, phase)


def build_bv_service_scope_section(
    intake: BVReviewIntake,
    result: BVReviewResult,
    *,
    project_state: Optional[ProjectReviewState] = None,
) -> Optional[BVReportSection]:
    recommendations = build_service_scope_recommendations(
        intake,
        result,
        project_state=project_state,
    )
    if not recommendations:
        return None

    return BVReportSection(
        heading="BV 服务范围建议",
        items=[
            (
                f"{item.title} | 优先级: {item.priority} | "
                f"触发证据: {', '.join(item.trigger_evidence_ids)} | "
                f"客户价值: {item.client_value} | "
                f"边界: {item.boundary_statement}"
            )
            for item in recommendations
        ],
    )


def build_bv_markdown_report(
    intake: BVReviewIntake,
    result: BVReviewResult,
    *,
    project_state: Optional[ProjectReviewState] = None,
) -> str:
    preview = (
        build_bv_report_preview(intake, result, project_state=project_state)
        if project_state is not None
        else result.report_preview or build_bv_report_preview(intake, result)
    )
    lines = [f"# {preview.title}", ""]
    for section in preview.sections:
        lines.append(f"## {section.heading}")
        for item in section.items:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_bv_report_filename(scope_key: str, report_date: Optional[date] = None) -> str:
    current_date = report_date or date.today()
    return f"{current_date.isoformat()}-{scope_key}-bv-review-report.md"
