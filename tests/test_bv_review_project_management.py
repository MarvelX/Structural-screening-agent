from structural_screening_agent.bv_review.project_management import (
    build_project_management_action_rows,
    build_project_management_actions,
)
from structural_screening_agent.bv_review.project_state import (
    AgentWorkflowEvent,
    CalculationRun,
    EngineerApproval,
    ProjectReviewState,
    RFIItem,
    ReportRevision,
)
from structural_screening_agent.bv_review.models import BVReviewIntake


def test_project_management_actions_prioritize_rfi_agent_and_calculation_work() -> None:
    state = ProjectReviewState(
        project_id="pv-management-actions",
        intake=_sample_intake(),
        current_phase="issue_rfi_closeout",
        phase_statuses={
            "intake": "approved",
            "document_check": "approved",
            "basis_build": "approved",
            "review_plan": "approved",
            "engineer_data_lock": "approved",
            "calculation_check": "waiting_for_engineer",
            "risk_register": "approved",
            "report_draft": "pending",
            "engineer_approval": "pending",
            "issue_rfi_closeout": "waiting_for_client",
        },
        agent_events=[
            AgentWorkflowEvent(
                event_id="calculation-check-agent-001",
                agent_role="calculation_check",
                target_phase="calculation_check",
                status="applied",
                output_schema_version="phase1.local",
                requires_engineer_review=True,
            )
        ],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_locked=True,
                status="failed",
                structured_errors=["Missing geotechnical side resistance."],
            )
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-001",
                question="Please provide geotechnical side resistance.",
                responsible_party="client / designer",
                trigger_basis="Foundation calculation missing side resistance.",
                required_document_or_field="side_resistance_standard_kpa",
                status="open",
                reopen_review_items=["side_resistance_standard_kpa"],
                triggers_incremental_recheck=True,
            ),
            RFIItem(
                rfi_id="rfi-load-001",
                question="Please confirm updated load table.",
                responsible_party="client / designer",
                trigger_basis="Client replied with Rev B load table.",
                required_document_or_field="uplift_force_kn",
                status="responded",
                client_response="Rev B load table submitted.",
                reopen_review_items=["uplift_force_kn"],
                triggers_incremental_recheck=True,
            ),
        ],
    )

    actions = build_project_management_actions(state)

    action_ids = [item.action_id for item in actions]
    assert action_ids[:4] == [
        "rfi-client-response-rfi-foundation-001",
        "rfi-engineer-closeout-rfi-load-001",
        "agent-review-calculation-check-agent-001",
        "calculation-follow-up-foundation-run-001",
    ]
    assert all(item.trigger_evidence_ids for item in actions)
    assert actions[0].owner_role == "client / designer"
    assert actions[1].owner_role == "BV structural review engineer"
    assert actions[2].blocks_report_issue is True


def test_project_management_actions_include_report_revision_after_report_gate_approval() -> None:
    state = ProjectReviewState(
        project_id="pv-report-ready-management",
        intake=_sample_intake(),
        approvals=[
            EngineerApproval(
                approval_id="report-gate-approval-001",
                target_type="report",
                target_id="report",
                status="approved",
                reviewer="Engineer A",
                locked=True,
            )
        ],
    )

    actions = build_project_management_actions(state)

    assert [item.action_id for item in actions] == ["record-report-revision-snapshot"]
    assert actions[0].owner_role == "BV project review lead"
    assert actions[0].priority == "medium"


def test_project_management_actions_ignore_closed_completed_and_already_recorded_work() -> None:
    state = ProjectReviewState(
        project_id="pv-management-closed-items",
        intake=_sample_intake(),
        phase_statuses={
            "intake": "approved",
            "document_check": "approved",
            "basis_build": "approved",
            "review_plan": "approved",
            "engineer_data_lock": "approved",
            "calculation_check": "approved",
            "risk_register": "approved",
            "report_draft": "approved",
            "engineer_approval": "approved",
            "issue_rfi_closeout": "approved",
        },
        agent_events=[
            AgentWorkflowEvent(
                event_id="risk-agent-001",
                agent_role="risk_ncr",
                target_phase="risk_register",
                status="applied",
                output_schema_version="phase1.local",
                requires_engineer_review=True,
            )
        ],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_locked=True,
                status="completed",
            )
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-closed-001",
                question="Please confirm updated foundation reaction table.",
                responsible_party="client / designer",
                trigger_basis="Closed RFI evidence.",
                required_document_or_field="uplift_force_kn",
                status="closed",
                client_response="Rev B table confirmed.",
                reopen_review_items=["uplift_force_kn"],
                completed_recheck_items=["uplift_force_kn"],
                triggers_incremental_recheck=True,
            )
        ],
        approvals=[
            EngineerApproval(
                approval_id="report-gate-approval-001",
                target_type="report",
                target_id="report",
                status="approved",
                reviewer="Engineer A",
                locked=True,
            )
        ],
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=9,
                rfi_count=1,
                created_by="Engineer A",
            )
        ],
    )

    assert build_project_management_actions(state) == []


def test_project_management_actions_cover_reopened_rfi_and_blocked_calculation() -> None:
    state = ProjectReviewState(
        project_id="pv-management-reopened-blocked",
        intake=_sample_intake(),
        rfi_items=[
            RFIItem(
                rfi_id="rfi-reopened-001",
                question="Please confirm revised pile length.",
                responsible_party="client / designer",
                trigger_basis="Closed evidence was superseded by Rev C.",
                required_document_or_field="pile_length_m",
                status="reopened",
                reopen_review_items=["pile_length_m"],
                triggers_incremental_recheck=True,
            )
        ],
        calculation_runs=[
            CalculationRun(
                run_id="superstructure-run-001",
                engine_name="superstructure",
                engine_version="phase1-deterministic-screening",
                input_locked=False,
                status="blocked",
                structured_errors=["Missing steel grade."],
            )
        ],
    )

    action_ids = {item.action_id for item in build_project_management_actions(state)}

    assert "rfi-client-response-rfi-reopened-001" in action_ids
    assert "calculation-follow-up-superstructure-run-001" in action_ids


def test_project_management_action_rows_are_localized_for_dashboard() -> None:
    actions = build_project_management_actions(
        ProjectReviewState(
            project_id="pv-localized-management",
            intake=_sample_intake(),
            rfi_items=[
                RFIItem(
                    rfi_id="rfi-load-001",
                    question="Please confirm updated load table.",
                    responsible_party="client / designer",
                    trigger_basis="Client replied with Rev B load table.",
                    required_document_or_field="uplift_force_kn",
                    status="responded",
                    client_response="Rev B load table submitted.",
                    reopen_review_items=["uplift_force_kn"],
                    triggers_incremental_recheck=True,
                )
            ],
        )
    )

    zh_rows = build_project_management_action_rows(actions, "zh")
    en_rows = build_project_management_action_rows(actions, "en")

    assert zh_rows[0]["行动类型"] == "RFI 工程师关闭"
    assert zh_rows[0]["优先级"] == "高"
    assert en_rows[0]["Action Type"] == "RFI Engineer Closeout"
    assert en_rows[0]["Priority"] == "High"
    assert "Close RFI" in en_rows[0]["Recommended Action"]


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV management demo",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation"],
    )
