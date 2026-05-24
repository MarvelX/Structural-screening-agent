from __future__ import annotations

import json
from pathlib import Path
from re import fullmatch
from typing import Literal, Optional, Union

from pydantic import BaseModel, ValidationError

from structural_screening_agent.bv_review.field_diff import (
    IncrementalRecheckPlan,
    build_incremental_recheck_plan_from_closed_rfis,
)
from structural_screening_agent.bv_review.project_management import (
    build_project_management_actions,
    build_project_management_sla_summary,
)
from structural_screening_agent.bv_review.project_state import ProjectReviewState, ReviewPhase
from structural_screening_agent.bv_review.project_timeline import build_project_timeline_events


ProjectInventoryWorkflowStatus = Literal["blocked", "action_required", "ready"]


class ProjectReviewStateSummary(BaseModel):
    project_id: str
    project_name: str
    current_phase: ReviewPhase
    agent_event_count: int
    pending_agent_review_count: int
    active_rfi_count: int
    open_finding_count: int = 0
    report_revision_count: int
    timeline_event_count: int = 0
    locked_gate_count: int = 0
    locked_quality_gate_ids: list[str] = []
    open_quality_gate_ids: list[str] = []
    management_action_count: int = 0
    blocking_action_count: int = 0
    overdue_action_count: int = 0
    earliest_due_date: Optional[str] = None
    next_due_action_id: Optional[str] = None
    workflow_status: ProjectInventoryWorkflowStatus = "ready"
    next_action_ids: list[str] = []
    next_action_categories: list[str] = []
    next_action_owner_roles: list[str] = []


class ProjectReviewStateInventory(BaseModel):
    summaries: list[ProjectReviewStateSummary]
    invalid_project_ids: list[str]

    @property
    def invalid_project_count(self) -> int:
        return len(self.invalid_project_ids)


class JsonProjectReviewStateRepository:
    def __init__(self, root: Union[Path, str]):
        self.root = Path(root)

    def _path_for(self, project_id: str) -> Path:
        if fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", project_id) is None:
            raise ValueError("Project id must be a safe file name.")
        return self.root / f"{project_id}.json"

    def save(self, state: ProjectReviewState) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._path_for(state.project_id)
        path.write_text(
            json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load(self, project_id: str) -> ProjectReviewState:
        path = self._path_for(project_id)
        if not path.exists():
            raise FileNotFoundError(f"No project review state found for {project_id!r}.")
        return ProjectReviewState.model_validate_json(path.read_text(encoding="utf-8"))

    def load_closed_rfi_recheck_plan(self, project_id: str) -> IncrementalRecheckPlan:
        state = self.load(project_id)
        return build_incremental_recheck_plan_from_closed_rfis(
            state.rfi_items,
            calculation_runs=state.calculation_runs,
        )

    def list_project_ids(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(path.stem for path in self.root.glob("*.json") if path.is_file())

    def list_project_summaries(self) -> list[ProjectReviewStateSummary]:
        return self.list_project_inventory().summaries

    def list_project_inventory(self) -> ProjectReviewStateInventory:
        summaries: list[ProjectReviewStateSummary] = []
        invalid_project_ids: list[str] = []
        for project_id in self.list_project_ids():
            try:
                summaries.append(_summarize_project_state(self.load(project_id)))
            except (FileNotFoundError, OSError, ValueError, ValidationError):
                invalid_project_ids.append(project_id)
        return ProjectReviewStateInventory(
            summaries=summaries,
            invalid_project_ids=invalid_project_ids,
        )


def _summarize_project_state(state: ProjectReviewState) -> ProjectReviewStateSummary:
    pending_agent_review_count = sum(
        1
        for event in state.agent_events
        if event.requires_engineer_review
        and state.phase_statuses.get(event.target_phase) == "waiting_for_engineer"
    )
    active_rfi_count = sum(
        1 for item in state.rfi_items if item.status in {"open", "reopened", "responded"}
    )
    open_finding_count = sum(
        1 for item in state.risks if item.status in {"open", "under_review"}
    )
    management_actions = build_project_management_actions(state)
    sla_summary = build_project_management_sla_summary(management_actions)
    blocking_action_count = sum(
        1 for action in management_actions if action.blocks_report_issue
    )
    locked_quality_gate_ids = _locked_quality_gate_ids(state)
    open_quality_gate_ids = _open_quality_gate_ids(state, locked_quality_gate_ids)
    return ProjectReviewStateSummary(
        project_id=state.project_id,
        project_name=state.intake.project_name,
        current_phase=state.current_phase,
        agent_event_count=len(state.agent_events),
        pending_agent_review_count=pending_agent_review_count,
        active_rfi_count=active_rfi_count,
        open_finding_count=open_finding_count,
        report_revision_count=len(state.report_revisions),
        timeline_event_count=len(build_project_timeline_events(state)),
        locked_gate_count=sum(
            1
            for approval in state.approvals
            if approval.target_type == "gate"
            and approval.status == "approved"
            and approval.locked
        ),
        locked_quality_gate_ids=locked_quality_gate_ids,
        open_quality_gate_ids=open_quality_gate_ids,
        management_action_count=len(management_actions),
        blocking_action_count=blocking_action_count,
        overdue_action_count=sla_summary.overdue_action_count,
        earliest_due_date=sla_summary.earliest_due_date,
        next_due_action_id=sla_summary.next_due_action_id,
        workflow_status=_project_inventory_workflow_status(
            management_action_count=len(management_actions),
            blocking_action_count=blocking_action_count,
            open_quality_gate_count=len(open_quality_gate_ids),
        ),
        next_action_ids=[action.action_id for action in management_actions[:3]],
        next_action_categories=[action.category for action in management_actions[:3]],
        next_action_owner_roles=[
            action.owner_role for action in management_actions[:3]
        ],
    )


def _project_inventory_workflow_status(
    *,
    management_action_count: int,
    blocking_action_count: int,
    open_quality_gate_count: int,
) -> ProjectInventoryWorkflowStatus:
    if blocking_action_count:
        return "blocked"
    if management_action_count or open_quality_gate_count:
        return "action_required"
    return "ready"


def _locked_quality_gate_ids(state: ProjectReviewState) -> list[str]:
    return [
        approval.target_id
        for approval in state.approvals
        if approval.target_type == "gate"
        and approval.status == "approved"
        and approval.locked
        and approval.target_id in _QUALITY_GATE_IDS
    ]


def _open_quality_gate_ids(
    state: ProjectReviewState,
    locked_quality_gate_ids: list[str],
) -> list[str]:
    open_gate_ids: list[str] = []
    if any(status == "missing" for status in state.intake.documents.values()):
        open_gate_ids.append("document")
    if not state.basis_references:
        open_gate_ids.append("basis")
    if "calculation" not in locked_quality_gate_ids:
        open_gate_ids.append("calculation")
    if "report" not in locked_quality_gate_ids:
        open_gate_ids.append("report")
    return open_gate_ids


_QUALITY_GATE_IDS = {"document", "basis", "calculation", "report"}
