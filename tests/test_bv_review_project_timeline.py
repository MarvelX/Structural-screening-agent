from structural_screening_agent.bv_review.models import BVRiskItem
from structural_screening_agent.bv_review.project_state import (
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
