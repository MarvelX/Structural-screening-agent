from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.project_state import (
    ProjectReviewState,
    RFIItem,
    ReportRevision,
)


ReportReissueGateStatus = Literal["blocked", "ready"]
ReportReissueNextAction = Literal[
    "collect_client_response",
    "close_rfi_after_engineer_review",
    "approve_report_gate",
    "record_reissue_revision",
    "ready",
]
ReportReissueLanguage = Literal["zh", "en"]


class ReportReissueGateSummary(BaseModel):
    status: ReportReissueGateStatus
    next_reissue_action: ReportReissueNextAction
    open_rfi_ids: list[str] = Field(default_factory=list)
    responded_rfi_ids: list[str] = Field(default_factory=list)
    pending_recheck_rfi_ids: list[str] = Field(default_factory=list)
    closed_rfi_ids: list[str] = Field(default_factory=list)
    report_gate_locked: bool = False
    latest_revision_id: Optional[str] = None
    covered_rfi_ids: list[str] = Field(default_factory=list)
    uncovered_closed_rfi_ids: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)


def build_report_reissue_gate_summary(
    state: ProjectReviewState,
) -> ReportReissueGateSummary:
    open_rfi_ids = [
        item.rfi_id for item in state.rfi_items if item.status in {"open", "reopened"}
    ]
    responded_rfi_ids = [
        item.rfi_id for item in state.rfi_items if item.status == "responded"
    ]
    closed_rfi_ids = [item.rfi_id for item in state.rfi_items if item.status == "closed"]
    pending_recheck_rfi_ids = [
        item.rfi_id
        for item in state.rfi_items
        if item.triggers_incremental_recheck
        and item.status == "responded"
        and not _rfi_recheck_is_complete(item)
    ]
    report_gate_locked = state.is_gate_locked("report")
    latest_revision = _latest_revision(state.report_revisions)
    covered_rfi_ids = list(latest_revision.related_rfi_ids) if latest_revision else []
    uncovered_closed_rfi_ids = [
        rfi_id for rfi_id in closed_rfi_ids if rfi_id not in set(covered_rfi_ids)
    ]

    blocking_reasons = _blocking_reasons(
        open_rfi_ids=open_rfi_ids,
        responded_rfi_ids=responded_rfi_ids,
        pending_recheck_rfi_ids=pending_recheck_rfi_ids,
        report_gate_locked=report_gate_locked,
    )
    return ReportReissueGateSummary(
        status="blocked" if blocking_reasons else "ready",
        next_reissue_action=_next_reissue_action(
            open_rfi_ids=open_rfi_ids,
            responded_rfi_ids=responded_rfi_ids,
            report_gate_locked=report_gate_locked,
            uncovered_closed_rfi_ids=uncovered_closed_rfi_ids,
        ),
        open_rfi_ids=open_rfi_ids,
        responded_rfi_ids=responded_rfi_ids,
        pending_recheck_rfi_ids=pending_recheck_rfi_ids,
        closed_rfi_ids=closed_rfi_ids,
        report_gate_locked=report_gate_locked,
        latest_revision_id=latest_revision.revision_id if latest_revision else None,
        covered_rfi_ids=covered_rfi_ids,
        uncovered_closed_rfi_ids=uncovered_closed_rfi_ids,
        blocking_reasons=blocking_reasons,
    )


def build_report_reissue_gate_rows(
    summary: ReportReissueGateSummary,
    language: ReportReissueLanguage,
) -> list[dict[str, object]]:
    if language == "zh":
        return [
            {"指标": "再签发状态", "数值": _status_label(summary, "zh")},
            {"指标": "下一步", "数值": _action_label(summary.next_reissue_action, "zh")},
            {"指标": "待客户回复澄清", "数值": _id_list(summary.open_rfi_ids, "zh")},
            {"指标": "待工程师关闭澄清", "数值": _id_list(summary.responded_rfi_ids, "zh")},
            {
                "指标": "待增量复核澄清",
                "数值": _id_list(summary.pending_recheck_rfi_ids, "zh"),
            },
            {"指标": "报告门禁已批准", "数值": "是" if summary.report_gate_locked else "否"},
            {"指标": "最新报告修订", "数值": summary.latest_revision_id or "无"},
            {
                "指标": "未纳入最新报告的已关闭澄清",
                "数值": _id_list(summary.uncovered_closed_rfi_ids, "zh"),
            },
        ]
    return [
        {"Metric": "Reissue Status", "Value": _status_label(summary, "en")},
        {
            "Metric": "Next Action",
            "Value": _action_label(summary.next_reissue_action, "en"),
        },
        {"Metric": "RFIs Awaiting Client Response", "Value": _id_list(summary.open_rfi_ids, "en")},
        {
            "Metric": "RFIs Awaiting Engineer Closeout",
            "Value": _id_list(summary.responded_rfi_ids, "en"),
        },
        {
            "Metric": "RFIs Awaiting Incremental Recheck",
            "Value": _id_list(summary.pending_recheck_rfi_ids, "en"),
        },
        {"Metric": "Report Gate Approved", "Value": "Yes" if summary.report_gate_locked else "No"},
        {"Metric": "Latest Report Revision", "Value": summary.latest_revision_id or "None"},
        {
            "Metric": "Closed RFIs Not Covered by Latest Revision",
            "Value": _id_list(summary.uncovered_closed_rfi_ids, "en"),
        },
    ]


def _rfi_recheck_is_complete(rfi: RFIItem) -> bool:
    return set(rfi.reopen_review_items).issubset(set(rfi.completed_recheck_items))


def _latest_revision(revisions: list[ReportRevision]) -> Optional[ReportRevision]:
    return max(
        revisions,
        key=lambda revision: (revision.created_at or "", revision.revision_id),
        default=None,
    )


def _blocking_reasons(
    *,
    open_rfi_ids: list[str],
    responded_rfi_ids: list[str],
    pending_recheck_rfi_ids: list[str],
    report_gate_locked: bool,
) -> list[str]:
    reasons: list[str] = []
    if open_rfi_ids:
        reasons.append(
            "Open or reopened RFI items require client/designer response: "
            + ", ".join(open_rfi_ids)
        )
    if responded_rfi_ids:
        reasons.append(
            "Responded RFI items require engineer closeout: "
            + ", ".join(responded_rfi_ids)
        )
    if pending_recheck_rfi_ids:
        reasons.append(
            "Incremental recheck evidence is incomplete for RFI items: "
            + ", ".join(pending_recheck_rfi_ids)
        )
    if not report_gate_locked:
        reasons.append("Report gate must be approved before reissue.")
    return reasons


def _next_reissue_action(
    *,
    open_rfi_ids: list[str],
    responded_rfi_ids: list[str],
    report_gate_locked: bool,
    uncovered_closed_rfi_ids: list[str],
) -> ReportReissueNextAction:
    if open_rfi_ids:
        return "collect_client_response"
    if responded_rfi_ids:
        return "close_rfi_after_engineer_review"
    if not report_gate_locked:
        return "approve_report_gate"
    if uncovered_closed_rfi_ids:
        return "record_reissue_revision"
    return "ready"


def _status_label(
    summary: ReportReissueGateSummary,
    language: ReportReissueLanguage,
) -> str:
    if language == "en":
        if summary.status == "blocked":
            return "Blocked"
        if summary.next_reissue_action == "record_reissue_revision":
            return "Ready to Record Reissue"
        return "Ready"
    if summary.status == "blocked":
        return "阻塞"
    if summary.next_reissue_action == "record_reissue_revision":
        return "可记录新版报告"
    return "就绪"


def _action_label(
    action: ReportReissueNextAction,
    language: ReportReissueLanguage,
) -> str:
    labels = {
        "collect_client_response": {
            "zh": "跟进客户 / 设计院回复",
            "en": "Collect Client / Designer Response",
        },
        "close_rfi_after_engineer_review": {
            "zh": "工程师复核后关闭澄清",
            "en": "Close RFI After Engineer Review",
        },
        "approve_report_gate": {
            "zh": "完成报告门禁批准",
            "en": "Approve Report Gate",
        },
        "record_reissue_revision": {
            "zh": "记录报告再签发修订",
            "en": "Record Report Reissue Revision",
        },
        "ready": {
            "zh": "无需新的再签发动作",
            "en": "No New Reissue Action",
        },
    }
    return labels[action][language]


def _id_list(values: list[str], language: ReportReissueLanguage) -> str:
    if values:
        return ", ".join(values)
    return "无" if language == "zh" else "None"
