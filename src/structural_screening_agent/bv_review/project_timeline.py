from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.project_state import ProjectReviewState


TimelineEventType = Literal[
    "agent_event",
    "rfi",
    "finding",
    "report_revision",
    "engineer_approval",
]
TimelineSuggestedAction = Literal[
    "agent_event_review",
    "rfi_closeout_review",
    "finding_closeout_record",
    "report_revision_review",
    "engineer_approval_record",
]


class ProjectTimelineEvent(BaseModel):
    sort_key: str = Field(min_length=1)
    event_type: TimelineEventType
    item_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    linked_object: str = ""
    description: str = Field(min_length=1)
    evidence: str = ""
    suggested_action: TimelineSuggestedAction


def build_project_timeline_events(
    state: ProjectReviewState,
) -> list[ProjectTimelineEvent]:
    events: list[ProjectTimelineEvent] = []
    for event in state.agent_events:
        events.append(
            ProjectTimelineEvent(
                sort_key=f"00-AGENT-{event.event_id}",
                event_type="agent_event",
                item_id=event.event_id,
                status=event.status,
                owner=event.agent_role,
                linked_object=event.target_phase,
                description=event.output_schema_version,
                evidence=_format_summary_counts(event.summary_counts),
                suggested_action="agent_event_review",
            )
        )

    for rfi in state.rfi_items:
        events.append(
            ProjectTimelineEvent(
                sort_key=f"01-RFI-{rfi.rfi_id}",
                event_type="rfi",
                item_id=rfi.rfi_id,
                status=rfi.status,
                owner=rfi.responsible_party,
                linked_object=rfi.required_document_or_field,
                description=rfi.trigger_basis,
                evidence=rfi.client_response or "",
                suggested_action="rfi_closeout_review",
            )
        )

    for risk in state.risks:
        if risk.status not in {"closed", "accepted_with_comment"}:
            continue
        events.append(
            ProjectTimelineEvent(
                sort_key=f"02-FINDING-{risk.risk_id}",
                event_type="finding",
                item_id=risk.risk_id,
                status=risk.status,
                owner="engineer",
                linked_object=risk.impact_scope,
                description=risk.title,
                evidence=risk.closeout_note or "",
                suggested_action="finding_closeout_record",
            )
        )

    for revision in state.report_revisions:
        events.append(
            ProjectTimelineEvent(
                sort_key=f"03-REPORT-{revision.revision_id}",
                event_type="report_revision",
                item_id=revision.revision_id,
                status=revision.source_phase,
                owner=revision.created_by,
                linked_object=", ".join(revision.calculation_run_ids),
                description=revision.report_title,
                evidence=revision.note or "",
                suggested_action="report_revision_review",
            )
        )

    for approval in state.approvals:
        events.append(
            ProjectTimelineEvent(
                sort_key=f"04-APPROVAL-{approval.approval_id}",
                event_type="engineer_approval",
                item_id=approval.approval_id,
                status=approval.status,
                owner=approval.reviewer or "engineer",
                linked_object=f"{approval.target_type}:{approval.target_id}",
                description=approval.comment or "engineer_decision_recorded",
                evidence=_format_approval_evidence(
                    approved_at=approval.approved_at,
                    locked=approval.locked,
                ),
                suggested_action="engineer_approval_record",
            )
        )
    return events


def _format_summary_counts(summary_counts: dict[str, int]) -> str:
    return "; ".join(f"{key}={value}" for key, value in summary_counts.items())


def _format_approval_evidence(*, approved_at: Optional[str], locked: bool) -> str:
    parts: list[str] = []
    if approved_at:
        parts.append(approved_at)
    parts.append(f"locked={locked}")
    return "; ".join(parts)
