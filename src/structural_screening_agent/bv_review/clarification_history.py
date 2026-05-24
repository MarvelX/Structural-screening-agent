from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.project_state import (
    ProjectReviewState,
    RFIItem,
    ReportRevision,
)


ClarificationHistoryLanguage = Literal["zh", "en"]
ClarificationNextAction = Literal[
    "collect_client_response",
    "close_rfi_after_engineer_review",
    "record_report_reissue_revision",
    "ready",
]


class ClarificationHistorySummary(BaseModel):
    total_rfi_count: int = Field(ge=0)
    open_rfi_count: int = Field(ge=0)
    responded_rfi_count: int = Field(ge=0)
    closed_rfi_count: int = Field(ge=0)
    reopened_rfi_count: int = Field(ge=0)
    incremental_recheck_rfi_count: int = Field(ge=0)
    pending_recheck_rfi_ids: list[str] = Field(default_factory=list)
    closed_uncovered_rfi_ids: list[str] = Field(default_factory=list)
    latest_report_revision_id: Optional[str] = None
    next_clarification_action: ClarificationNextAction = "ready"


def build_clarification_history_summary(
    state: ProjectReviewState,
) -> ClarificationHistorySummary:
    latest_revision = _latest_revision(state.report_revisions)
    covered_rfi_ids = set(latest_revision.related_rfi_ids) if latest_revision else set()
    pending_recheck_rfi_ids = [
        rfi.rfi_id
        for rfi in state.rfi_items
        if rfi.status == "responded"
        and rfi.triggers_incremental_recheck
        and not _rfi_recheck_is_complete(rfi)
    ]
    closed_uncovered_rfi_ids = [
        rfi.rfi_id
        for rfi in state.rfi_items
        if rfi.status == "closed" and rfi.rfi_id not in covered_rfi_ids
    ]
    return ClarificationHistorySummary(
        total_rfi_count=len(state.rfi_items),
        open_rfi_count=sum(1 for rfi in state.rfi_items if rfi.status == "open"),
        responded_rfi_count=sum(
            1 for rfi in state.rfi_items if rfi.status == "responded"
        ),
        closed_rfi_count=sum(1 for rfi in state.rfi_items if rfi.status == "closed"),
        reopened_rfi_count=sum(1 for rfi in state.rfi_items if rfi.status == "reopened"),
        incremental_recheck_rfi_count=sum(
            1 for rfi in state.rfi_items if rfi.triggers_incremental_recheck
        ),
        pending_recheck_rfi_ids=pending_recheck_rfi_ids,
        closed_uncovered_rfi_ids=closed_uncovered_rfi_ids,
        latest_report_revision_id=latest_revision.revision_id if latest_revision else None,
        next_clarification_action=_next_summary_action(
            state.rfi_items,
            closed_uncovered_rfi_ids,
        ),
    )


def build_clarification_history_rows(
    state: ProjectReviewState,
    language: ClarificationHistoryLanguage,
) -> list[dict[str, object]]:
    latest_revision = _latest_revision(state.report_revisions)
    covered_rfi_ids = set(latest_revision.related_rfi_ids) if latest_revision else set()
    return [
        _row_zh(rfi, covered_rfi_ids) if language == "zh" else _row_en(rfi, covered_rfi_ids)
        for rfi in sorted(state.rfi_items, key=_rfi_sort_key)
    ]


def _row_zh(rfi: RFIItem, covered_rfi_ids: set[str]) -> dict[str, object]:
    return {
        "澄清 ID": rfi.rfi_id,
        "状态": _status_label(rfi.status, "zh"),
        "责任方": _owner_label(rfi.responsible_party, "zh"),
        "打开日期": rfi.opened_at or "未记录",
        "所需资料/字段": rfi.required_document_or_field,
        "需要增量复核": "是" if rfi.triggers_incremental_recheck else "否",
        "复核状态": _recheck_status_label(rfi, "zh"),
        "最新报告已覆盖": "是" if rfi.rfi_id in covered_rfi_ids else "否",
        "下一步": _action_label(_next_rfi_action(rfi, covered_rfi_ids), "zh"),
    }


def _row_en(rfi: RFIItem, covered_rfi_ids: set[str]) -> dict[str, object]:
    return {
        "Clarification ID": rfi.rfi_id,
        "Status": _status_label(rfi.status, "en"),
        "Owner": _owner_label(rfi.responsible_party, "en"),
        "Opened At": rfi.opened_at or "Not Recorded",
        "Required Document / Field": rfi.required_document_or_field,
        "Requires Incremental Recheck": "Yes" if rfi.triggers_incremental_recheck else "No",
        "Recheck Status": _recheck_status_label(rfi, "en"),
        "Latest Report Coverage": (
            "Covered" if rfi.rfi_id in covered_rfi_ids else "Not Covered"
        ),
        "Next Action": _action_label(_next_rfi_action(rfi, covered_rfi_ids), "en"),
    }


def _latest_revision(revisions: list[ReportRevision]) -> Optional[ReportRevision]:
    return max(
        revisions,
        key=lambda revision: (revision.created_at or "", revision.revision_id),
        default=None,
    )


def _rfi_sort_key(rfi: RFIItem) -> tuple[int, str, str]:
    status_rank = {"open": 0, "reopened": 0, "responded": 1, "closed": 2}
    return status_rank[rfi.status], rfi.opened_at or "", rfi.rfi_id


def _rfi_recheck_is_complete(rfi: RFIItem) -> bool:
    return set(rfi.reopen_review_items).issubset(set(rfi.completed_recheck_items))


def _next_summary_action(
    rfi_items: list[RFIItem],
    closed_uncovered_rfi_ids: list[str],
) -> ClarificationNextAction:
    if any(rfi.status in {"open", "reopened"} for rfi in rfi_items):
        return "collect_client_response"
    if any(rfi.status == "responded" for rfi in rfi_items):
        return "close_rfi_after_engineer_review"
    if closed_uncovered_rfi_ids:
        return "record_report_reissue_revision"
    return "ready"


def _next_rfi_action(
    rfi: RFIItem,
    covered_rfi_ids: set[str],
) -> ClarificationNextAction:
    if rfi.status in {"open", "reopened"}:
        return "collect_client_response"
    if rfi.status == "responded":
        return "close_rfi_after_engineer_review"
    if rfi.status == "closed" and rfi.rfi_id not in covered_rfi_ids:
        return "record_report_reissue_revision"
    return "ready"


def _status_label(status: str, language: ClarificationHistoryLanguage) -> str:
    labels = {
        "open": {"zh": "待回复", "en": "Open"},
        "responded": {"zh": "已回复", "en": "Responded"},
        "closed": {"zh": "已关闭", "en": "Closed"},
        "reopened": {"zh": "重新打开", "en": "Reopened"},
    }
    return labels.get(status, {}).get(language, status)


def _owner_label(owner: str, language: ClarificationHistoryLanguage) -> str:
    labels = {
        "client / designer": {"zh": "客户 / 设计院", "en": "Client / Designer"},
        "BV structural review engineer": {
            "zh": "BV 结构审核工程师",
            "en": "BV Structural Review Engineer",
        },
        "BV project review lead": {
            "zh": "BV 项目审核负责人",
            "en": "BV Project Review Lead",
        },
    }
    return labels.get(owner, {}).get(language, owner)


def _recheck_status_label(
    rfi: RFIItem,
    language: ClarificationHistoryLanguage,
) -> str:
    if not rfi.triggers_incremental_recheck:
        return "不需要" if language == "zh" else "Not Required"
    if _rfi_recheck_is_complete(rfi):
        return "已完成" if language == "zh" else "Complete"
    return "待复核" if language == "zh" else "Pending"


def _action_label(
    action: ClarificationNextAction,
    language: ClarificationHistoryLanguage,
) -> str:
    labels = {
        "collect_client_response": {
            "zh": "跟进客户 / 设计院回复",
            "en": "Collect client / designer response",
        },
        "close_rfi_after_engineer_review": {
            "zh": "工程师复核并关闭",
            "en": "Engineer review and closeout",
        },
        "record_report_reissue_revision": {
            "zh": "记录报告再签发修订",
            "en": "Record report reissue revision",
        },
        "ready": {
            "zh": "无需澄清动作",
            "en": "No clarification action",
        },
    }
    return labels[action][language]
