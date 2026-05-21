from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.project_state import (
    AgentWorkflowEvent,
    CalculationRun,
    ProjectReviewState,
)
from structural_screening_agent.bv_review.models import BVRiskItem


ProjectActionCategory = Literal[
    "rfi_client_response",
    "rfi_engineer_closeout",
    "finding_closeout",
    "agent_engineer_review",
    "calculation_follow_up",
    "report_revision",
]
ProjectActionPriority = Literal["high", "medium", "low"]
ProjectActionLanguage = Literal["zh", "en"]


class ProjectManagementAction(BaseModel):
    action_id: str = Field(min_length=1)
    category: ProjectActionCategory
    priority: ProjectActionPriority
    owner_role: str = Field(min_length=1)
    trigger_evidence_ids: list[str] = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    blocks_report_issue: bool = False


def build_project_management_actions(
    state: ProjectReviewState,
) -> list[ProjectManagementAction]:
    actions: list[ProjectManagementAction] = []
    actions.extend(_rfi_actions(state))
    actions.extend(_finding_actions(state))
    actions.extend(_agent_review_actions(state))
    actions.extend(_calculation_actions(state))
    report_revision_action = _report_revision_action(state)
    if report_revision_action is not None:
        actions.append(report_revision_action)
    return sorted(actions, key=_action_sort_key)


def build_project_management_action_rows(
    actions: list[ProjectManagementAction],
    language: ProjectActionLanguage,
) -> list[dict[str, object]]:
    if language == "zh":
        return [
            {
                "行动 ID": action.action_id,
                "行动类型": _category_label(action.category, "zh"),
                "优先级": _priority_label(action.priority, "zh"),
                "责任角色": _owner_label(action.owner_role, "zh"),
                "触发证据": ", ".join(action.trigger_evidence_ids),
                "建议动作": _localized_recommended_action(action, "zh"),
                "阻塞报告": "是" if action.blocks_report_issue else "否",
            }
            for action in actions
        ]
    return [
        {
            "Action ID": action.action_id,
            "Action Type": _category_label(action.category, "en"),
            "Priority": _priority_label(action.priority, "en"),
            "Owner Role": _owner_label(action.owner_role, "en"),
            "Trigger Evidence": ", ".join(action.trigger_evidence_ids),
            "Recommended Action": _localized_recommended_action(action, "en"),
            "Blocks Report": "Yes" if action.blocks_report_issue else "No",
        }
        for action in actions
    ]


def _rfi_actions(state: ProjectReviewState) -> list[ProjectManagementAction]:
    actions: list[ProjectManagementAction] = []
    for rfi in state.rfi_items:
        if rfi.status in {"open", "reopened"}:
            actions.append(
                ProjectManagementAction(
                    action_id=f"rfi-client-response-{rfi.rfi_id}",
                    category="rfi_client_response",
                    priority="high",
                    owner_role=rfi.responsible_party,
                    trigger_evidence_ids=[rfi.rfi_id],
                    recommended_action=(
                        "Request client/designer response and required evidence before "
                        "closing the RFI."
                    ),
                    blocks_report_issue=True,
                )
            )
        elif rfi.status == "responded":
            actions.append(
                ProjectManagementAction(
                    action_id=f"rfi-engineer-closeout-{rfi.rfi_id}",
                    category="rfi_engineer_closeout",
                    priority="high",
                    owner_role="BV structural review engineer",
                    trigger_evidence_ids=[rfi.rfi_id],
                    recommended_action=(
                        "Close RFI after engineer review and complete any incremental "
                        "recheck items."
                    ),
                    blocks_report_issue=True,
                )
            )
    return actions


def _agent_review_actions(state: ProjectReviewState) -> list[ProjectManagementAction]:
    return [
        ProjectManagementAction(
            action_id=f"agent-review-{event.event_id}",
            category="agent_engineer_review",
            priority="high",
            owner_role="BV structural review engineer",
            trigger_evidence_ids=[event.event_id],
            recommended_action=(
                "Review the agent output, approve or reject it, and record the "
                "engineering rationale."
            ),
            blocks_report_issue=True,
        )
        for event in state.agent_events
        if _agent_event_waits_for_engineer(state, event)
    ]


def _finding_actions(state: ProjectReviewState) -> list[ProjectManagementAction]:
    return [
        ProjectManagementAction(
            action_id=f"finding-closeout-{risk.risk_id}",
            category="finding_closeout",
            priority=_finding_action_priority(risk),
            owner_role="BV structural review engineer",
            trigger_evidence_ids=[risk.risk_id],
            recommended_action=(
                "Close the finding after engineer review of evidence, or record "
                "an accepted residual comment before report issue."
            ),
            blocks_report_issue=True,
        )
        for risk in state.risks
        if risk.blocks_report_issue and risk.status not in _CLOSED_FINDING_STATUSES
    ]


def _finding_action_priority(risk: BVRiskItem) -> ProjectActionPriority:
    if risk.severity in {"critical", "high"}:
        return "high"
    return "medium"


def _calculation_actions(state: ProjectReviewState) -> list[ProjectManagementAction]:
    return [
        ProjectManagementAction(
            action_id=f"calculation-follow-up-{run.run_id}",
            category="calculation_follow_up",
            priority="high",
            owner_role="BV structural review engineer",
            trigger_evidence_ids=[run.run_id],
            recommended_action=(
                "Resolve blocked or failed deterministic calculation input before "
                "using the result in report conclusions."
            ),
            blocks_report_issue=True,
        )
        for run in state.calculation_runs
        if _calculation_run_requires_follow_up(run)
    ]


def _report_revision_action(
    state: ProjectReviewState,
) -> Optional[ProjectManagementAction]:
    if not state.is_gate_locked("report") or state.report_revisions:
        return None
    return ProjectManagementAction(
        action_id="record-report-revision-snapshot",
        category="report_revision",
        priority="medium",
        owner_role="BV project review lead",
        trigger_evidence_ids=["report"],
        recommended_action=(
            "Record a traceable report revision snapshot after report gate approval."
        ),
        blocks_report_issue=False,
    )


def _agent_event_waits_for_engineer(
    state: ProjectReviewState,
    event: AgentWorkflowEvent,
) -> bool:
    return (
        event.requires_engineer_review
        and state.phase_statuses.get(event.target_phase) == "waiting_for_engineer"
    )


def _calculation_run_requires_follow_up(run: CalculationRun) -> bool:
    return run.status in {"blocked", "failed"}


def _action_sort_key(action: ProjectManagementAction) -> tuple[int, int, str]:
    priority_rank = {"high": 0, "medium": 1, "low": 2}[action.priority]
    category_rank = {
        "rfi_client_response": 0,
        "rfi_engineer_closeout": 1,
        "finding_closeout": 2,
        "agent_engineer_review": 3,
        "calculation_follow_up": 4,
        "report_revision": 5,
    }[action.category]
    return priority_rank, category_rank, action.action_id


def _category_label(
    category: ProjectActionCategory,
    language: ProjectActionLanguage,
) -> str:
    labels = {
        "rfi_client_response": {
            "zh": "RFI 客户回复",
            "en": "RFI Client Response",
        },
        "rfi_engineer_closeout": {
            "zh": "RFI 工程师关闭",
            "en": "RFI Engineer Closeout",
        },
        "finding_closeout": {
            "zh": "发现项关闭",
            "en": "Finding Closeout",
        },
        "agent_engineer_review": {
            "zh": "Agent 产物复核",
            "en": "Agent Output Review",
        },
        "calculation_follow_up": {
            "zh": "计算输入跟进",
            "en": "Calculation Follow-up",
        },
        "report_revision": {
            "zh": "报告修订记录",
            "en": "Report Revision Snapshot",
        },
    }
    return labels[category][language]


def _priority_label(
    priority: ProjectActionPriority,
    language: ProjectActionLanguage,
) -> str:
    if language == "zh":
        return {"high": "高", "medium": "中", "low": "低"}[priority]
    return {"high": "High", "medium": "Medium", "low": "Low"}[priority]


def _owner_label(owner_role: str, language: ProjectActionLanguage) -> str:
    if language == "zh":
        labels = {
            "BV structural review engineer": "BV 结构审核工程师",
            "BV project review lead": "BV 项目审核负责人",
            "client / designer": "客户 / 设计院",
        }
        return labels.get(owner_role, owner_role)
    labels = {
        "client / designer": "Client / Designer",
    }
    return labels.get(owner_role, owner_role)


def _localized_recommended_action(
    action: ProjectManagementAction,
    language: ProjectActionLanguage,
) -> str:
    if language == "en":
        return action.recommended_action
    labels = {
        "rfi_client_response": "跟进客户 / 设计院回复和所需证据，关闭前不得进入无保留报告结论。",
        "rfi_engineer_closeout": "工程师复核客户回复，并完成相关增量复核项后关闭 RFI。",
        "finding_closeout": "工程师复核证据后关闭发现项，或记录可接受的残余意见后再进入报告签发。",
        "agent_engineer_review": "复核 Agent 产物，记录批准或驳回决定及工程判断依据。",
        "calculation_follow_up": "补齐或修正确定性计算输入，避免将失败计算用于报告结论。",
        "report_revision": "报告门禁批准后记录可追踪的报告修订快照。",
    }
    return labels[action.category]


_CLOSED_FINDING_STATUSES = {"closed", "accepted_with_comment"}
