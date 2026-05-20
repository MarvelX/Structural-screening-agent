from typing import Literal

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.models import BVReviewResult
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    EngineerApproval,
    ExtractedField,
    ProjectReviewState,
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


class ReportDraftGateResult(BaseModel):
    status: Literal["ready", "blocked"]
    reasons: list[str] = Field(default_factory=list)
    blocking_risk_ids: list[str] = Field(default_factory=list)
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
        if item.triggers_incremental_recheck and item.status != "closed"
    ]
    if incremental_rfi_ids:
        reasons.append(
            "Open RFI items trigger incremental recheck: "
            + ", ".join(incremental_rfi_ids)
        )

    executable_runs = [
        run
        for run in state.calculation_runs
        if run.input_locked and run.status in {"ready", "completed"}
    ]
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
        calculation_run_ids=calculation_run_ids,
        notes=notes,
    )
