from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.blocked_calculation_draft import (
    build_blocked_calculation_review_draft,
)
from structural_screening_agent.bv_review.field_diff import (
    rfi_incremental_recheck_is_complete,
    select_latest_calculation_evidence_runs,
)
from structural_screening_agent.bv_review.models import BVReportPreview, BVReviewResult
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    EngineerApproval,
    ExtractedField,
    ProjectReviewState,
    RFIItem,
    ReportRevision,
)


def fields_ready_for_calculation(fields: list[ExtractedField]) -> bool:
    calculation_fields = [field for field in fields if field.include_in_calculation]
    if not calculation_fields:
        return False

    return all(
        field.is_confirmed and field.confirmed_value not in (None, "")
        for field in calculation_fields
    )


def build_engineer_approval(
    approval_id: str, target_id: str, reviewer: str, comment: str = ""
) -> EngineerApproval:
    return EngineerApproval(
        approval_id=approval_id,
        target_type="gate",
        target_id=target_id,
        status="approved",
        reviewer=reviewer,
        comment=comment,
        locked=True,
    )


def record_agent_review_decision(
    state: ProjectReviewState,
    *,
    event_id: str,
    decision: Literal["approved", "rejected"],
    reviewer: str,
    comment: str = "",
) -> ProjectReviewState:
    event = next(
        (item for item in state.agent_events if item.event_id == event_id),
        None,
    )
    if event is None:
        raise ValueError(f"Agent event {event_id!r} does not exist.")
    if not event.requires_engineer_review:
        raise ValueError(f"Agent event {event_id!r} does not require engineer review.")
    if any(
        approval.target_type == "agent_event" and approval.target_id == event_id
        for approval in state.approvals
    ):
        raise ValueError(
            f"Agent event {event_id!r} already has an engineer review decision."
        )
    if state.phase_statuses.get(event.target_phase) != "waiting_for_engineer":
        raise ValueError(f"Agent event {event_id!r} is not pending engineer review.")

    approval = EngineerApproval(
        approval_id=f"agent-review-{event_id}",
        target_type="agent_event",
        target_id=event_id,
        status=decision,
        reviewer=reviewer,
        comment=comment,
        locked=decision == "approved",
    )
    phase_statuses = dict(state.phase_statuses)
    phase_statuses[event.target_phase] = decision
    return state.model_copy(
        update={
            "phase_statuses": phase_statuses,
            "approvals": [*state.approvals, approval],
        }
    )


def record_rfi_client_response(
    state: ProjectReviewState,
    *,
    rfi_id: str,
    client_response: str,
) -> ProjectReviewState:
    if not client_response.strip():
        raise ValueError("RFI client response must not be empty.")

    rfi = _find_unique_rfi(state, rfi_id)
    if rfi.status not in {"open", "reopened"}:
        raise ValueError("Only open or reopened RFI items can record a client response.")

    updated_rfi = rfi.model_copy(
        update={
            "status": "responded",
            "client_response": client_response,
        }
    )
    return _copy_with_rfi_update(
        state,
        updated_rfi,
        phase_status="waiting_for_engineer",
    )


def close_rfi_after_engineer_review(
    state: ProjectReviewState,
    *,
    rfi_id: str,
    closeout_note: str,
    completed_recheck_item_ids: Optional[list[str]] = None,
) -> ProjectReviewState:
    if not closeout_note.strip():
        raise ValueError("RFI closeout note must not be empty.")

    rfi = _find_unique_rfi(state, rfi_id)
    if rfi.status != "responded":
        raise ValueError("Only responded RFI items can be closed after engineer review.")
    completed_items = _validate_completed_recheck_items(
        rfi,
        completed_recheck_item_ids,
    )

    response_with_closeout = f"{rfi.client_response}\nCloseout: {closeout_note}"
    updated_rfi = rfi.model_copy(
        update={
            "status": "closed",
            "client_response": response_with_closeout,
            "completed_recheck_items": completed_items,
        }
    )
    updated_items = _replace_rfi(state.rfi_items, updated_rfi)
    phase_status = (
        "approved"
        if _all_incremental_rfis_closed(updated_items)
        else "waiting_for_engineer"
    )
    return _copy_with_rfi_items(
        state,
        updated_items,
        phase_status=phase_status,
    )


def issue_blocked_calculation_draft_rfi(
    state: ProjectReviewState,
    *,
    rfi_id: str,
    reviewer: str,
    comment: str = "",
    approved_at: Optional[str] = None,
) -> ProjectReviewState:
    if not reviewer.strip():
        raise ValueError("RFI issue reviewer must not be empty.")
    if any(item.rfi_id == rfi_id for item in state.rfi_items):
        raise ValueError(f"RFI item {rfi_id!r} already exists.")

    draft = build_blocked_calculation_review_draft(state)
    draft_rfi = next((item for item in draft.rfi_items if item.rfi_id == rfi_id), None)
    if draft_rfi is None:
        raise ValueError(
            f"RFI item {rfi_id!r} does not match a blocked calculation draft."
        )

    approval = EngineerApproval(
        approval_id=f"rfi-issue-{rfi_id}",
        target_type="rfi",
        target_id=rfi_id,
        status="approved",
        reviewer=reviewer,
        approved_at=approved_at,
        comment=comment,
        locked=True,
    )
    statuses = dict(state.phase_statuses)
    statuses["issue_rfi_closeout"] = "waiting_for_client"
    return state.model_copy(
        update={
            "current_phase": "issue_rfi_closeout",
            "phase_statuses": statuses,
            "rfi_items": [*state.rfi_items, draft_rfi],
            "approvals": [*state.approvals, approval],
        }
    )


def build_calculation_gate_run(
    run_id: str,
    engine_name: str,
    fields: list[ExtractedField],
) -> CalculationRun:
    calculation_fields = [field for field in fields if field.include_in_calculation]
    if not fields_ready_for_calculation(fields):
        return CalculationRun(
            run_id=run_id,
            engine_name=engine_name,
            engine_version="phase1-human-gate",
            input_field_ids=[field.field_id for field in calculation_fields],
            input_locked=False,
            status="blocked",
            structured_errors=[
                "Calculation gate requires at least one engineer-confirmed field marked for calculation."
            ],
        )

    return CalculationRun(
        run_id=run_id,
        engine_name=engine_name,
        engine_version="phase1-human-gate",
        input_field_ids=[field.field_id for field in calculation_fields],
        input_locked=True,
        status="ready",
    )


def _find_unique_rfi(state: ProjectReviewState, rfi_id: str) -> RFIItem:
    matches = [item for item in state.rfi_items if item.rfi_id == rfi_id]
    if not matches:
        raise ValueError(f"RFI item {rfi_id!r} does not exist.")
    if len(matches) > 1:
        raise ValueError(f"RFI item {rfi_id!r} is duplicated in project state.")
    return matches[0]


def _copy_with_rfi_update(
    state: ProjectReviewState,
    updated_rfi: RFIItem,
    *,
    phase_status: str,
) -> ProjectReviewState:
    return _copy_with_rfi_items(
        state,
        _replace_rfi(state.rfi_items, updated_rfi),
        phase_status=phase_status,
    )


def _copy_with_rfi_items(
    state: ProjectReviewState,
    rfi_items: list[RFIItem],
    *,
    phase_status: str,
) -> ProjectReviewState:
    statuses = dict(state.phase_statuses)
    statuses["issue_rfi_closeout"] = phase_status
    return state.model_copy(
        update={
            "current_phase": "issue_rfi_closeout",
            "phase_statuses": statuses,
            "rfi_items": rfi_items,
        }
    )


def _replace_rfi(rfi_items: list[RFIItem], updated_rfi: RFIItem) -> list[RFIItem]:
    return [
        updated_rfi if item.rfi_id == updated_rfi.rfi_id else item
        for item in rfi_items
    ]


def _all_incremental_rfis_closed(rfi_items: list[RFIItem]) -> bool:
    return all(
        rfi_incremental_recheck_is_complete(item)
        for item in rfi_items
        if item.triggers_incremental_recheck
    )


def _validate_completed_recheck_items(
    rfi: RFIItem,
    completed_recheck_item_ids: Optional[list[str]],
) -> list[str]:
    if not rfi.triggers_incremental_recheck:
        return list(completed_recheck_item_ids or [])

    if not completed_recheck_item_ids:
        raise ValueError("Incremental RFI closeout requires completed recheck items.")

    required_items = set(rfi.reopen_review_items)
    completed_items = set(completed_recheck_item_ids)
    missing_items = sorted(required_items - completed_items)
    unknown_items = sorted(completed_items - required_items)
    if missing_items:
        raise ValueError(
            "Incremental RFI closeout is missing completed recheck items: "
            + ", ".join(missing_items)
        )
    if unknown_items:
        raise ValueError(
            "Incremental RFI closeout includes unknown completed recheck items: "
            + ", ".join(unknown_items)
        )
    return list(completed_recheck_item_ids)


class ReportDraftGateResult(BaseModel):
    status: Literal["ready", "blocked"]
    reasons: list[str] = Field(default_factory=list)
    blocking_risk_ids: list[str] = Field(default_factory=list)
    incremental_recheck_rfi_ids: list[str] = Field(default_factory=list)
    pending_agent_review_event_ids: list[str] = Field(default_factory=list)
    rejected_agent_review_event_ids: list[str] = Field(default_factory=list)
    calculation_run_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def build_report_draft_gate_result(
    state: ProjectReviewState,
    result: BVReviewResult,
) -> ReportDraftGateResult:
    reasons: list[str] = []
    notes: list[str] = []

    if not result.basis_references:
        reasons.append("Review basis is missing; report draft input is blocked.")

    missing_documents = [
        item.document_key for item in result.checklist_items if item.status == "missing"
    ]
    if missing_documents:
        reasons.append(
            "Missing required document inputs block report draft input: "
            + ", ".join(missing_documents)
        )

    blocking_risk_ids = [
        item.risk_id for item in result.risks if item.blocks_report_issue
    ]
    if blocking_risk_ids:
        reasons.append(
            "Blocking risks or nonconformities remain open: "
            + ", ".join(blocking_risk_ids)
        )

    incremental_rfi_ids = [
        item.rfi_id
        for item in state.rfi_items
        if item.triggers_incremental_recheck
        and not rfi_incremental_recheck_is_complete(item)
    ]
    if incremental_rfi_ids:
        reasons.append(
            "Open RFI items trigger incremental recheck: "
            + ", ".join(incremental_rfi_ids)
        )

    pending_agent_review_event_ids = [
        event.event_id
        for event in state.agent_events
        if event.requires_engineer_review
        and state.phase_statuses.get(event.target_phase) == "waiting_for_engineer"
    ]
    if pending_agent_review_event_ids:
        reasons.append(
            "Pending agent engineer review blocks report draft input: "
            + ", ".join(pending_agent_review_event_ids)
        )
    rejected_agent_review_event_ids = [
        event.event_id
        for event in state.agent_events
        if event.requires_engineer_review
        and state.phase_statuses.get(event.target_phase) == "rejected"
    ]
    if rejected_agent_review_event_ids:
        reasons.append(
            "Rejected agent engineer review blocks report draft input: "
            + ", ".join(rejected_agent_review_event_ids)
        )

    executable_runs = select_latest_calculation_evidence_runs(
        [
            run
            for run in state.calculation_runs
            if run.input_locked and run.status in {"ready", "completed"}
        ]
    )
    if not state.is_gate_locked("calculation"):
        reasons.append("Calculation gate is not locked by an engineer.")
    if not executable_runs:
        reasons.append("No locked calculation interface run is ready for report drafting.")

    calculation_run_ids = [run.run_id for run in executable_runs]
    if any(run.status == "ready" for run in executable_runs):
        notes.append(
            "Calculation interface input is ready but not completed; report draft must not claim structural verification."
        )

    return ReportDraftGateResult(
        status="blocked" if reasons else "ready",
        reasons=reasons,
        blocking_risk_ids=blocking_risk_ids,
        incremental_recheck_rfi_ids=incremental_rfi_ids,
        pending_agent_review_event_ids=pending_agent_review_event_ids,
        rejected_agent_review_event_ids=rejected_agent_review_event_ids,
        calculation_run_ids=calculation_run_ids,
        notes=notes,
    )


def record_report_revision(
    state: ProjectReviewState,
    *,
    revision_id: str,
    report_preview: BVReportPreview,
    gate_result: ReportDraftGateResult,
    reviewer: str,
    note: str = "",
    created_at: Optional[str] = None,
) -> ProjectReviewState:
    if gate_result.status != "ready":
        raise ValueError(
            "Cannot record report revision while report draft gate is blocked."
        )
    if not state.is_gate_locked("report"):
        raise ValueError(
            "Report gate must be approved by an engineer before recording a report revision."
        )
    if any(revision.revision_id == revision_id for revision in state.report_revisions):
        raise ValueError(f"Report revision {revision_id!r} already exists.")

    revision = ReportRevision(
        revision_id=revision_id,
        source_phase=state.current_phase,
        report_title=report_preview.title,
        section_count=len(report_preview.sections),
        rfi_count=len(state.rfi_items),
        blocking_risk_ids=list(gate_result.blocking_risk_ids),
        calculation_run_ids=list(gate_result.calculation_run_ids),
        created_by=reviewer,
        created_at=created_at,
        note=note or None,
    )
    return state.model_copy(
        update={"report_revisions": [*state.report_revisions, revision]}
    )
