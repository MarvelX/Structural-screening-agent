from structural_screening_agent.bv_review.project_management import (
    build_finding_lifecycle_summary,
    build_finding_lifecycle_summary_rows,
    build_project_management_action_summary,
    build_project_management_action_summary_rows,
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
from structural_screening_agent.bv_review.models import (
    BVBasisReference,
    BVRiskItem,
    BVReviewIntake,
)


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


def test_project_management_actions_include_open_blocking_finding_closeout() -> None:
    state = ProjectReviewState(
        project_id="pv-finding-closeout-actions",
        intake=_sample_intake(),
        risks=[
            BVRiskItem(
                risk_id="foundation-bearing-capacity-open",
                title="Foundation bearing capacity evidence remains open",
                severity="critical",
                trigger_basis="Missing geotechnical confirmation.",
                impact_scope="Foundation review",
                recommendation="Close the finding after engineer review of evidence.",
                blocks_report_issue=True,
                category="nonconformity",
            ),
            BVRiskItem(
                risk_id="layout-optimization-closed",
                title="Layout optimization comment closed",
                severity="medium",
                trigger_basis="Engineer accepted residual comment.",
                impact_scope="PV layout review",
                recommendation="Keep comment in workpaper.",
                blocks_report_issue=True,
                category="optimization",
                status="closed",
                closeout_note="Closed after engineer review.",
            ),
        ],
    )

    actions = build_project_management_actions(state)

    assert [item.action_id for item in actions] == [
        "finding-closeout-foundation-bearing-capacity-open"
    ]
    assert actions[0].category == "finding_closeout"
    assert actions[0].owner_role == "BV structural review engineer"
    assert actions[0].blocks_report_issue is True


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


def test_project_management_actions_include_open_quality_gate_follow_up() -> None:
    state = ProjectReviewState(
        project_id="pv-quality-gate-follow-up",
        intake=_sample_intake(),
        current_phase="report_draft",
        phase_statuses={
            "intake": "approved",
            "document_check": "approved",
            "basis_build": "approved",
            "review_plan": "approved",
            "engineer_data_lock": "approved",
            "calculation_check": "approved",
            "risk_register": "approved",
            "report_draft": "running",
            "engineer_approval": "pending",
            "issue_rfi_closeout": "pending",
        },
    )

    actions = build_project_management_actions(state)
    action_ids = [item.action_id for item in actions]

    assert action_ids == [
        "quality-gate-follow-up-basis",
        "quality-gate-follow-up-calculation",
        "quality-gate-follow-up-report",
    ]
    assert [item.category for item in actions] == ["quality_gate_follow_up"] * 3
    assert all(item.owner_role == "BV project review lead" for item in actions)
    assert all(item.blocks_report_issue for item in actions)


def test_project_management_action_rows_are_localized_for_dashboard() -> None:
    actions = [
        *build_project_management_actions(
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
        ),
        build_project_management_actions(
            ProjectReviewState(
                project_id="pv-localized-quality-gates",
                intake=_sample_intake(),
                current_phase="report_draft",
            )
        )[0],
    ]

    zh_rows = build_project_management_action_rows(actions, "zh")
    en_rows = build_project_management_action_rows(actions, "en")

    assert zh_rows[0]["行动类型"] == "RFI 工程师关闭"
    assert zh_rows[0]["优先级"] == "高"
    assert zh_rows[-1]["行动类型"] == "质量门禁跟进"
    assert zh_rows[-1]["建议动作"] == "跟进未通过的质量门禁，补齐证据并记录工程师判断后再进入报告签发。"
    assert en_rows[0]["Action Type"] == "RFI Engineer Closeout"
    assert en_rows[0]["Priority"] == "High"
    assert en_rows[-1]["Action Type"] == "Quality Gate Follow-up"
    assert en_rows[-1]["Owner Role"] == "BV Project Review Lead"
    assert "Resolve the open quality gate" in en_rows[-1]["Recommended Action"]


def test_project_management_action_summary_counts_blockers_priorities_and_owners() -> None:
    actions = [
        *build_project_management_actions(
            ProjectReviewState(
                project_id="pv-summary-management",
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
                risks=[
                    BVRiskItem(
                        risk_id="foundation-bearing-capacity-open",
                        title="Foundation bearing capacity evidence remains open",
                        severity="critical",
                        trigger_basis="Missing geotechnical confirmation.",
                        impact_scope="Foundation review",
                        recommendation="Close the finding after engineer review.",
                        blocks_report_issue=True,
                        category="nonconformity",
                    )
                ],
            )
        ),
        build_project_management_actions(
            ProjectReviewState(
                project_id="pv-summary-quality-gates",
                intake=_sample_intake(),
                current_phase="report_draft",
            )
        )[0],
    ]

    summary = build_project_management_action_summary(actions)
    zh_rows = build_project_management_action_summary_rows(summary, "zh")
    en_rows = build_project_management_action_summary_rows(summary, "en")

    assert summary.total_action_count == 3
    assert summary.blocking_action_count == 3
    assert summary.high_priority_count == 2
    assert summary.medium_priority_count == 1
    assert summary.owner_roles == [
        "BV structural review engineer",
        "BV project review lead",
    ]
    assert summary.next_blocking_action_id == "rfi-engineer-closeout-rfi-load-001"
    assert zh_rows == [
        {"指标": "项目待办", "数值": 3},
        {"指标": "阻塞报告待办", "数值": 3},
        {"指标": "高优先级", "数值": 2},
        {"指标": "中优先级", "数值": 1},
        {"指标": "低优先级", "数值": 0},
        {"指标": "责任方", "数值": "BV 结构审核工程师, BV 项目审核负责人"},
        {"指标": "下一项阻塞行动", "数值": "rfi-engineer-closeout-rfi-load-001"},
    ]
    assert en_rows == [
        {"Metric": "Project Actions", "Value": 3},
        {"Metric": "Blocking Actions", "Value": 3},
        {"Metric": "High Priority", "Value": 2},
        {"Metric": "Medium Priority", "Value": 1},
        {"Metric": "Low Priority", "Value": 0},
        {
            "Metric": "Owner Roles",
            "Value": "BV Structural Review Engineer, BV Project Review Lead",
        },
        {"Metric": "Next Blocking Action", "Value": "rfi-engineer-closeout-rfi-load-001"},
    ]


def test_finding_lifecycle_summary_tracks_findings_rfis_and_next_action() -> None:
    state = ProjectReviewState(
        project_id="pv-lifecycle-summary",
        intake=_sample_intake(),
        risks=[
            BVRiskItem(
                risk_id="foundation-open",
                title="Foundation evidence remains open",
                severity="critical",
                trigger_basis="Missing geotechnical report.",
                impact_scope="Foundation review",
                recommendation="Request evidence.",
                blocks_report_issue=True,
                category="nonconformity",
            ),
            BVRiskItem(
                risk_id="layout-under-review",
                title="Layout optimization under review",
                severity="medium",
                trigger_basis="O&M access route unclear.",
                impact_scope="Layout review",
                recommendation="Confirm access route.",
                blocks_report_issue=False,
                category="optimization",
                status="under_review",
            ),
            BVRiskItem(
                risk_id="connection-accepted",
                title="Connection residual comment accepted",
                severity="low",
                trigger_basis="Engineer accepted residual issue.",
                impact_scope="Connection review",
                recommendation="Keep in report.",
                blocks_report_issue=True,
                category="risk",
                status="accepted_with_comment",
            ),
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-geotech",
                question="Provide geotechnical report.",
                responsible_party="client / designer",
                trigger_basis="Foundation evidence gap.",
                required_document_or_field="geotechnical_report",
                status="open",
            ),
            RFIItem(
                rfi_id="rfi-load-table",
                question="Confirm load table.",
                responsible_party="client / designer",
                trigger_basis="Revised reaction table submitted.",
                required_document_or_field="uplift_force_kn",
                status="responded",
                client_response="Rev B table submitted.",
            ),
            RFIItem(
                rfi_id="rfi-closed",
                question="Confirm pile length.",
                responsible_party="client / designer",
                trigger_basis="Closed after engineer review.",
                required_document_or_field="pile_length_m",
                status="closed",
                client_response="Pile length confirmed.",
            ),
            RFIItem(
                rfi_id="rfi-reopened",
                question="Confirm revised pile spacing.",
                responsible_party="client / designer",
                trigger_basis="Rev C superseded previous closeout.",
                required_document_or_field="pile_spacing_m",
                status="reopened",
            ),
        ],
    )

    summary = build_finding_lifecycle_summary(state)
    zh_rows = build_finding_lifecycle_summary_rows(summary, "zh")
    en_rows = build_finding_lifecycle_summary_rows(summary, "en")

    assert summary.open_finding_count == 2
    assert summary.blocking_open_finding_count == 1
    assert summary.closed_or_accepted_finding_count == 1
    assert summary.open_rfi_count == 2
    assert summary.responded_rfi_count == 1
    assert summary.closed_rfi_count == 1
    assert summary.next_lifecycle_action_id == "rfi-client-response-rfi-geotech"
    assert zh_rows[0] == {"指标": "待关闭发现项", "数值": 2}
    assert zh_rows[4] == {"指标": "待工程师关闭澄清", "数值": 1}
    assert "RFI" not in str(zh_rows)
    assert en_rows[0] == {"Metric": "Open Findings", "Value": 2}
    assert en_rows[4] == {"Metric": "RFIs Awaiting Engineer Closeout", "Value": 1}


def test_project_management_actions_skip_quality_gate_follow_up_at_intake() -> None:
    state = ProjectReviewState(
        project_id="pv-intake-not-ready-for-gate-follow-up",
        intake=_sample_intake(),
    )

    assert build_project_management_actions(state) == []


def test_project_management_actions_ignore_locked_quality_gates() -> None:
    state = ProjectReviewState(
        project_id="pv-locked-quality-gates",
        intake=_sample_intake(),
        current_phase="report_draft",
        basis_references=[
            BVBasisReference(
                basis_id="gb-50797",
                title="PV station design basis",
                source_type="code",
                review_actions=["Use as review basis."],
            )
        ],
        approvals=[
            EngineerApproval(
                approval_id="calculation-gate-approval",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            ),
            EngineerApproval(
                approval_id="report-gate-approval",
                target_type="gate",
                target_id="report",
                status="approved",
                locked=True,
            ),
        ],
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=9,
                rfi_count=0,
                created_by="Engineer A",
            )
        ],
    )

    assert build_project_management_actions(state) == []


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV management demo",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation"],
    )
