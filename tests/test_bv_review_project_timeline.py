from structural_screening_agent.bv_review.models import BVRiskItem
from structural_screening_agent.bv_review.project_state import (
    AgentWorkflowEvent,
    CommunicationRecord,
    EngineerApproval,
    ProjectReviewState,
    RFIItem,
    ReportRevision,
)
from structural_screening_agent.bv_review.project_timeline import (
    build_project_timeline_events,
)
from structural_screening_agent.bv_review.ui_state import default_bv_review_intake


def test_project_timeline_events_combine_project_state_milestones() -> None:
    state = ProjectReviewState(
        project_id="pv-project-timeline",
        intake=default_bv_review_intake(),
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-input",
                question="Please confirm foundation input.",
                responsible_party="client / designer",
                trigger_basis="Foundation input changed in Rev B.",
                required_document_or_field="pile_length_m",
                status="closed",
                client_response="Designer confirmed Rev B pile length.",
                reopen_review_items=["pile_length_m"],
                completed_recheck_items=["pile_length_m"],
                triggers_incremental_recheck=True,
            )
        ],
        risks=[
            BVRiskItem(
                risk_id="risk-open",
                title="Open finding remains under review",
                severity="medium",
                trigger_basis="Pending designer answer.",
                impact_scope="Foundation review",
                recommendation="Wait for closeout evidence.",
                blocks_report_issue=True,
                category="risk",
                status="open",
            ),
            BVRiskItem(
                risk_id="risk-foundation-input",
                title="Foundation input closed",
                severity="high",
                trigger_basis="Engineer reviewed Rev B input.",
                impact_scope="Foundation review",
                recommendation="Keep closeout evidence.",
                blocks_report_issue=True,
                category="nonconformity",
                status="closed",
                closeout_note="Engineer accepted Rev B input for screening report.",
            ),
        ],
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=12,
                rfi_count=1,
                calculation_run_ids=["foundation-run-001"],
                created_by="Engineer A",
                note="Ready for internal review.",
            )
        ],
    )

    events = build_project_timeline_events(state)

    assert [event.sort_key for event in events] == [
        "01-RFI-rfi-foundation-input",
        "02-FINDING-risk-foundation-input",
        "03-REPORT-report-rev-001",
    ]
    assert events[0].event_type == "rfi"
    assert events[0].item_id == "rfi-foundation-input"
    assert events[0].status == "closed"
    assert events[0].owner == "client / designer"
    assert events[0].linked_object == "pile_length_m"
    assert events[0].description == "Foundation input changed in Rev B."
    assert events[0].evidence == "Designer confirmed Rev B pile length."
    assert events[0].suggested_action == "rfi_closeout_review"

    assert events[1].event_type == "finding"
    assert events[1].item_id == "risk-foundation-input"
    assert events[1].status == "closed"
    assert events[1].owner == "engineer"
    assert events[1].linked_object == "Foundation review"
    assert events[1].description == "Foundation input closed"
    assert events[1].evidence == "Engineer accepted Rev B input for screening report."
    assert events[1].suggested_action == "finding_closeout_record"

    assert events[2].event_type == "report_revision"
    assert events[2].item_id == "report-rev-001"
    assert events[2].status == "report_draft"
    assert events[2].owner == "Engineer A"
    assert events[2].linked_object == "foundation-run-001"
    assert events[2].description == "BV 光伏结构设计审查报告"
    assert events[2].evidence == "Ready for internal review."
    assert events[2].suggested_action == "report_revision_review"


def test_project_timeline_events_are_empty_without_milestones() -> None:
    state = ProjectReviewState(
        project_id="pv-project-timeline-empty",
        intake=default_bv_review_intake(),
    )

    assert build_project_timeline_events(state) == []


def test_project_timeline_events_include_agent_and_engineer_gate_records() -> None:
    state = ProjectReviewState(
        project_id="pv-project-agent-timeline",
        intake=default_bv_review_intake(),
        agent_events=[
            AgentWorkflowEvent(
                event_id="agent-event-001",
                agent_role="document_intake",
                target_phase="document_check",
                status="applied",
                output_schema_version="bv-agent-output/v1",
                requires_engineer_review=True,
                summary_counts={"document_versions": 2, "extracted_fields": 4},
            )
        ],
        approvals=[
            EngineerApproval(
                approval_id="approval-agent-event-001",
                target_type="agent_event",
                target_id="agent-event-001",
                status="approved",
                reviewer="Engineer A",
                approved_at="2026-05-21T11:00:00+08:00",
                comment="Agent extraction checked against submitted package.",
                locked=True,
            ),
            EngineerApproval(
                approval_id="approval-calculation-gate",
                target_type="gate",
                target_id="calculation",
                status="approved",
                reviewer="Engineer B",
                approved_at="2026-05-21T11:30:00+08:00",
                comment="Calculation inputs locked for deterministic screening.",
                locked=True,
            ),
        ],
    )

    events = build_project_timeline_events(state)

    assert [event.sort_key for event in events] == [
        "00-AGENT-agent-event-001",
        "04-APPROVAL-approval-agent-event-001",
        "04-APPROVAL-approval-calculation-gate",
    ]
    assert events[0].event_type == "agent_event"
    assert events[0].item_id == "agent-event-001"
    assert events[0].status == "applied"
    assert events[0].owner == "document_intake"
    assert events[0].linked_object == "document_check"
    assert events[0].description == "bv-agent-output/v1"
    assert events[0].evidence == "document_versions=2; extracted_fields=4"
    assert events[0].suggested_action == "agent_event_review"

    assert events[1].event_type == "engineer_approval"
    assert events[1].item_id == "approval-agent-event-001"
    assert events[1].status == "approved"
    assert events[1].owner == "Engineer A"
    assert events[1].linked_object == "agent_event:agent-event-001"
    assert events[1].description == "Agent extraction checked against submitted package."
    assert events[1].evidence == "2026-05-21T11:00:00+08:00; locked=True"
    assert events[1].suggested_action == "engineer_approval_record"

    assert events[2].event_type == "engineer_approval"
    assert events[2].linked_object == "gate:calculation"


def test_project_timeline_events_include_project_communication_records() -> None:
    state = ProjectReviewState(
        project_id="pv-project-communication-timeline",
        intake=default_bv_review_intake(),
        communication_records=[
            CommunicationRecord(
                communication_id="comm-design-meeting-001",
                communication_type="meeting",
                occurred_at="2026-05-24T10:00:00+08:00",
                participants=[
                    "BV structural review engineer",
                    "client / designer",
                ],
                subject="Foundation evidence closeout meeting",
                summary="Designer agreed to submit Rev B geotechnical note.",
                linked_rfi_ids=["rfi-foundation-input"],
                linked_risk_ids=["risk-foundation-input"],
                action_items=["Client to submit Rev B note before report issue."],
            )
        ],
    )

    events = build_project_timeline_events(state)

    assert [event.sort_key for event in events] == [
        "05-COMM-comm-design-meeting-001"
    ]
    assert events[0].event_type == "communication"
    assert events[0].item_id == "comm-design-meeting-001"
    assert events[0].status == "meeting"
    assert events[0].owner == "BV structural review engineer, client / designer"
    assert events[0].linked_object == "RFI: rfi-foundation-input; Risk: risk-foundation-input"
    assert events[0].description == "Foundation evidence closeout meeting"
    assert events[0].evidence == "Designer agreed to submit Rev B geotechnical note."
    assert events[0].suggested_action == "communication_follow_up"
