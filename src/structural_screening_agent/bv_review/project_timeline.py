from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.project_state import ProjectReviewState


TimelineEventType = Literal["rfi", "finding", "report_revision"]
TimelineSuggestedAction = Literal[
    "rfi_closeout_review",
    "finding_closeout_record",
    "report_revision_review",
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
    return events
