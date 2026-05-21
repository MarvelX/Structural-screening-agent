from structural_screening_agent.bv_review.human_gate import build_report_draft_gate_result
from structural_screening_agent.bv_review.models import BVRiskItem, BVReviewIntake
from structural_screening_agent.bv_review.project_state import (
    AgentWorkflowEvent,
    CalculationRun,
    EngineerApproval,
    ProjectReviewState,
    RFIItem,
)
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def _sample_intake(documents: dict[str, str] | None = None) -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents=documents
        or {
            "structural_drawings": "available",
            "calculation_report": "available",
            "technical_specification": "available",
            "geotechnical_report": "available",
            "vendor_datasheets": "available",
            "contract_requirements": "available",
        },
    )


def _sample_state(intake: BVReviewIntake, *, calculation_status: str | None = "ready") -> ProjectReviewState:
    calculation_runs = []
    if calculation_status is not None:
        calculation_runs.append(
            CalculationRun(
                run_id="run-001",
                engine_name="foundation",
                engine_version="phase1-human-gate",
                input_field_ids=["tilt_angle_deg"],
                input_locked=True,
                status=calculation_status,
            )
        )

    return ProjectReviewState(
        project_id="pv-report-gate-001",
        intake=intake,
        approvals=[
            EngineerApproval(
                approval_id="approval-001",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            )
        ],
        calculation_runs=calculation_runs,
    )


def test_report_draft_gate_blocks_when_basis_references_are_missing() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake).model_copy(update={"basis_references": []})

    gate = build_report_draft_gate_result(_sample_state(intake), result)

    assert gate.status == "blocked"
    assert any("basis" in reason.lower() for reason in gate.reasons)


def test_report_draft_gate_blocks_when_required_documents_are_missing() -> None:
    intake = _sample_intake(
        documents={
            "structural_drawings": "available",
            "calculation_report": "missing",
            "technical_specification": "available",
            "geotechnical_report": "missing",
            "vendor_datasheets": "available",
            "contract_requirements": "available",
        }
    )
    result = evaluate_bv_review(intake)

    gate = build_report_draft_gate_result(_sample_state(intake), result)

    assert gate.status == "blocked"
    assert any("missing" in reason.lower() for reason in gate.reasons)


def test_report_draft_gate_blocks_when_blocking_risks_remain() -> None:
    intake = _sample_intake(
        documents={
            "structural_drawings": "available",
            "calculation_report": "missing",
            "technical_specification": "available",
            "geotechnical_report": "available",
            "vendor_datasheets": "available",
            "contract_requirements": "available",
        }
    )
    result = evaluate_bv_review(intake)

    gate = build_report_draft_gate_result(_sample_state(intake), result)

    assert gate.status == "blocked"
    assert gate.blocking_risk_ids


def test_report_draft_gate_does_not_block_closed_or_engineer_accepted_findings() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake).model_copy(
        update={
            "risks": [
                BVRiskItem(
                    risk_id="closed-foundation-finding",
                    title="Foundation evidence clarification closed",
                    severity="high",
                    trigger_basis="Engineer reviewed Rev B geotechnical response.",
                    impact_scope="Foundation review",
                    recommendation="Retain closeout evidence in the workpaper.",
                    blocks_report_issue=True,
                    category="nonconformity",
                    status="closed",
                    closeout_note="Rev B evidence accepted by engineer.",
                ),
                BVRiskItem(
                    risk_id="accepted-layout-finding",
                    title="Residual layout optimization accepted",
                    severity="medium",
                    trigger_basis="Engineer accepted residual optimization note.",
                    impact_scope="PV layout review",
                    recommendation="Track as residual optimization comment.",
                    blocks_report_issue=True,
                    category="optimization",
                    status="accepted_with_comment",
                    closeout_note="Accepted with residual comment in report.",
                ),
            ]
        }
    )

    gate = build_report_draft_gate_result(_sample_state(intake), result)

    assert gate.status == "ready"
    assert gate.blocking_risk_ids == []


def test_report_draft_gate_blocks_before_calculation_gate_is_locked() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(project_id="pv-report-gate-002", intake=intake)

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "blocked"
    assert any("calculation gate" in reason.lower() for reason in gate.reasons)


def test_report_draft_gate_allows_traceable_ready_inputs_without_blockers() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)

    gate = build_report_draft_gate_result(_sample_state(intake), result)

    assert gate.status == "ready"
    assert gate.reasons == []
    assert gate.calculation_run_ids == ["run-001"]
    assert any("not completed" in note.lower() for note in gate.notes)


def test_report_draft_gate_blocks_pending_agent_engineer_review() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = _sample_state(intake).model_copy(
        update={
            "phase_statuses": {
                **_sample_state(intake).phase_statuses,
                "document_check": "waiting_for_engineer",
            },
            "agent_events": [
                AgentWorkflowEvent(
                    event_id="agent-event-001",
                    agent_role="document_intake",
                    target_phase="document_check",
                    status="applied",
                    output_schema_version="phase2-agent-contracts-v1",
                    requires_engineer_review=True,
                    summary_counts={"document_versions": 1},
                )
            ],
        }
    )

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "blocked"
    assert gate.pending_agent_review_event_ids == ["agent-event-001"]
    assert gate.rejected_agent_review_event_ids == []
    assert any("pending agent engineer review" in reason.lower() for reason in gate.reasons)


def test_report_draft_gate_allows_approved_agent_engineer_review() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = _sample_state(intake).model_copy(
        update={
            "phase_statuses": {
                **_sample_state(intake).phase_statuses,
                "document_check": "approved",
            },
            "agent_events": [
                AgentWorkflowEvent(
                    event_id="agent-event-001",
                    agent_role="document_intake",
                    target_phase="document_check",
                    status="applied",
                    output_schema_version="phase2-agent-contracts-v1",
                    requires_engineer_review=True,
                    summary_counts={"document_versions": 1},
                )
            ],
            "approvals": [
                *_sample_state(intake).approvals,
                EngineerApproval(
                    approval_id="agent-review-agent-event-001",
                    target_type="agent_event",
                    target_id="agent-event-001",
                    status="approved",
                    reviewer="Engineer A",
                    locked=True,
                ),
            ],
        }
    )

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "ready"
    assert gate.pending_agent_review_event_ids == []
    assert gate.rejected_agent_review_event_ids == []
    assert not any("pending agent engineer review" in reason.lower() for reason in gate.reasons)


def test_report_draft_gate_blocks_rejected_agent_engineer_review() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = _sample_state(intake).model_copy(
        update={
            "phase_statuses": {
                **_sample_state(intake).phase_statuses,
                "document_check": "rejected",
            },
            "agent_events": [
                AgentWorkflowEvent(
                    event_id="agent-event-001",
                    agent_role="document_intake",
                    target_phase="document_check",
                    status="applied",
                    output_schema_version="phase2-agent-contracts-v1",
                    requires_engineer_review=True,
                    summary_counts={"document_versions": 1},
                )
            ],
            "approvals": [
                *_sample_state(intake).approvals,
                EngineerApproval(
                    approval_id="agent-review-agent-event-001",
                    target_type="agent_event",
                    target_id="agent-event-001",
                    status="rejected",
                    reviewer="Engineer A",
                    comment="Source evidence is incomplete.",
                ),
            ],
        }
    )

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "blocked"
    assert gate.pending_agent_review_event_ids == []
    assert gate.rejected_agent_review_event_ids == ["agent-event-001"]
    assert any("rejected agent engineer review" in reason.lower() for reason in gate.reasons)


def test_report_draft_gate_blocks_when_open_incremental_recheck_rfi_exists() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = _sample_state(intake).model_copy(
        update={
            "rfi_items": [
                RFIItem(
                    rfi_id="rfi-pile_length_m",
                    question="Please confirm updated input for Pile Length M.",
                    responsible_party="client",
                    trigger_basis="Field pile_length_m changed from '3.5' to '4.0'.",
                    required_document_or_field="pile_length_m",
                    status="reopened",
                    reopen_review_items=["calculation-recheck-pile_length_m"],
                    triggers_incremental_recheck=True,
                )
            ]
        }
    )

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "blocked"
    assert gate.incremental_recheck_rfi_ids == ["rfi-pile_length_m"]
    assert any("incremental recheck" in reason.lower() for reason in gate.reasons)


def test_report_draft_gate_allows_closed_incremental_recheck_rfi() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = _sample_state(intake).model_copy(
        update={
            "rfi_items": [
                RFIItem(
                    rfi_id="rfi-pile_length_m",
                    question="Please confirm updated input for Pile Length M.",
                    responsible_party="client",
                    trigger_basis="Field pile_length_m changed from '3.5' to '4.0'.",
                    required_document_or_field="pile_length_m",
                    status="closed",
                    client_response="Confirmed Rev B pile length is 4.0 m.",
                    reopen_review_items=["calculation-recheck-pile_length_m"],
                    completed_recheck_items=["calculation-recheck-pile_length_m"],
                    triggers_incremental_recheck=True,
                )
            ]
        }
    )

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "ready"
    assert gate.incremental_recheck_rfi_ids == []


def test_report_draft_gate_prefers_latest_incremental_recheck_calculation_evidence() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = _sample_state(intake).model_copy(
        update={
            "calculation_runs": [
                CalculationRun(
                    run_id="foundation-run-001",
                    engine_name="foundation",
                    engine_version="phase1-deterministic-screening",
                    input_field_ids=["pile_length_m", "uplift_force_kn"],
                    input_locked=True,
                    status="completed",
                ),
                CalculationRun(
                    run_id="incremental-recheck-rfi-foundation-run-001-foundation-001",
                    engine_name="foundation",
                    engine_version="phase1-deterministic-screening",
                    input_field_ids=["pile_length_m", "uplift_force_kn"],
                    input_locked=True,
                    status="completed",
                ),
            ],
            "rfi_items": [
                RFIItem(
                    rfi_id="rfi-foundation-run-001",
                    question="Please confirm foundation reaction updates.",
                    responsible_party="client / designer",
                    trigger_basis="Foundation run requires clarification.",
                    required_document_or_field="uplift_force_kn",
                    status="closed",
                    client_response="Designer submitted Rev B reaction table.",
                    reopen_review_items=["uplift_force_kn"],
                    completed_recheck_items=["uplift_force_kn"],
                    triggers_incremental_recheck=True,
                )
            ],
        }
    )

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "ready"
    assert gate.calculation_run_ids == [
        "incremental-recheck-rfi-foundation-run-001-foundation-001"
    ]


def test_report_draft_gate_blocks_closed_incremental_rfi_without_completed_recheck_items() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = _sample_state(intake).model_copy(
        update={
            "rfi_items": [
                RFIItem(
                    rfi_id="rfi-pile_length_m",
                    question="Please confirm updated input for Pile Length M.",
                    responsible_party="client",
                    trigger_basis="Field pile_length_m changed from '3.5' to '4.0'.",
                    required_document_or_field="pile_length_m",
                    status="closed",
                    client_response="Confirmed Rev B pile length is 4.0 m.",
                    reopen_review_items=["calculation-recheck-pile_length_m"],
                    triggers_incremental_recheck=True,
                )
            ]
        }
    )

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "blocked"
    assert gate.incremental_recheck_rfi_ids == ["rfi-pile_length_m"]
    assert any("incremental recheck" in reason.lower() for reason in gate.reasons)


def test_report_draft_gate_blocks_closed_incremental_rfi_without_recheck_scope() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = _sample_state(intake).model_copy(
        update={
            "rfi_items": [
                RFIItem(
                    rfi_id="rfi-empty-closeout",
                    question="Please confirm updated input for Pile Length M.",
                    responsible_party="client",
                    trigger_basis="Field pile_length_m changed from '3.5' to '4.0'.",
                    required_document_or_field="pile_length_m",
                    status="closed",
                    client_response="Confirmed Rev B pile length is 4.0 m.",
                    triggers_incremental_recheck=True,
                )
            ]
        }
    )

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "blocked"
    assert gate.incremental_recheck_rfi_ids == ["rfi-empty-closeout"]


def test_report_draft_gate_blocks_responded_incremental_recheck_rfi_before_closeout() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = _sample_state(intake).model_copy(
        update={
            "rfi_items": [
                RFIItem(
                    rfi_id="rfi-pile_length_m",
                    question="Please confirm updated input for Pile Length M.",
                    responsible_party="client",
                    trigger_basis="Field pile_length_m changed from '3.5' to '4.0'.",
                    required_document_or_field="pile_length_m",
                    status="responded",
                    client_response="Client response received; engineer closeout still pending.",
                    reopen_review_items=["calculation-recheck-pile_length_m"],
                    triggers_incremental_recheck=True,
                )
            ]
        }
    )

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "blocked"
    assert gate.incremental_recheck_rfi_ids == ["rfi-pile_length_m"]
    assert any("incremental recheck" in reason.lower() for reason in gate.reasons)
