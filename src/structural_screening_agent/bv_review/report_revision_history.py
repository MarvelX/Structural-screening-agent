from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.project_state import (
    ProjectReviewState,
    ReportRevision,
)


ReportRevisionHistoryLanguage = Literal["zh", "en"]


class ReportRevisionHistorySummary(BaseModel):
    total_revision_count: int = Field(ge=0)
    latest_revision_id: Optional[str] = None
    latest_revision_status: Optional[str] = None
    open_revision_count: int = Field(ge=0)
    superseded_revision_count: int = Field(ge=0)
    next_revision_action: Optional[str] = None


def build_report_revision_history_summary(
    state: ProjectReviewState,
) -> ReportRevisionHistorySummary:
    revisions = _sorted_revisions(state.report_revisions)
    latest = revisions[-1] if revisions else None
    return ReportRevisionHistorySummary(
        total_revision_count=len(revisions),
        latest_revision_id=latest.revision_id if latest else None,
        latest_revision_status=latest.revision_status if latest else None,
        open_revision_count=sum(
            1
            for revision in revisions
            if revision.revision_status
            in {"draft", "issued_for_review", "issued_for_client_response"}
        ),
        superseded_revision_count=sum(
            1 for revision in revisions if revision.revision_status == "superseded"
        ),
        next_revision_action=_next_revision_action(latest),
    )


def build_report_revision_history_rows(
    state: ProjectReviewState,
    language: ReportRevisionHistoryLanguage,
) -> list[dict[str, object]]:
    return [
        _revision_row_zh(revision) if language == "zh" else _revision_row_en(revision)
        for revision in _sorted_revisions(state.report_revisions)
    ]


def _sorted_revisions(revisions: list[ReportRevision]) -> list[ReportRevision]:
    return sorted(
        revisions,
        key=lambda revision: (
            revision.created_at or "",
            revision.revision_id,
        ),
    )


def _next_revision_action(revision: Optional[ReportRevision]) -> Optional[str]:
    if revision is None:
        return "record_first_revision"
    if revision.revision_status == "draft":
        return "complete_engineer_review"
    if revision.revision_status == "issued_for_review":
        return "collect_reviewer_decision"
    if revision.revision_status == "issued_for_client_response":
        return "track_client_response"
    if revision.revision_status == "superseded":
        return "confirm_active_revision"
    if revision.revision_status == "finalized":
        return None
    return None


def _revision_row_zh(revision: ReportRevision) -> dict[str, object]:
    return {
        "修订 ID": revision.revision_id,
        "状态": _status_label(revision.revision_status, "zh"),
        "生成阶段": revision.source_phase,
        "生成时间": revision.created_at or "未记录",
        "生成者": revision.created_by,
        "替代版本": revision.supersedes_revision_id or "无",
        "关联 RFI": ", ".join(revision.related_rfi_ids) or "无",
        "用途": revision.issue_purpose or "未记录",
    }


def _revision_row_en(revision: ReportRevision) -> dict[str, object]:
    return {
        "Revision ID": revision.revision_id,
        "Status": _status_label(revision.revision_status, "en"),
        "Source Phase": revision.source_phase,
        "Created At": revision.created_at or "Not Recorded",
        "Created By": revision.created_by,
        "Supersedes": revision.supersedes_revision_id or "None",
        "Related RFIs": ", ".join(revision.related_rfi_ids) or "None",
        "Purpose": revision.issue_purpose or "Not Recorded",
    }


def _status_label(status: str, language: ReportRevisionHistoryLanguage) -> str:
    labels = {
        "draft": {"zh": "草稿", "en": "Draft"},
        "issued_for_review": {"zh": "发给复核", "en": "Issued for Review"},
        "issued_for_client_response": {
            "zh": "发给客户回复",
            "en": "Issued for Client Response",
        },
        "superseded": {"zh": "已被替代", "en": "Superseded"},
        "finalized": {"zh": "已定稿", "en": "Finalized"},
    }
    return labels.get(status, {}).get(language, status)
