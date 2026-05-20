import pytest

from structural_screening_agent.bv_review.human_gate import (
    build_calculation_gate_run,
    build_engineer_approval,
    build_report_draft_gate_result,
    record_report_revision,
    record_agent_review_decision,
    fields_ready_for_calculation,
)
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.report import build_bv_report_preview
from structural_screening_agent.bv_review.workflow import evaluate_bv_review
from structural_screening_agent.bv_review.project_state import (
    AgentWorkflowEvent,
    CalculationRun,
    EngineerApproval,
    ExtractedField,
    ProjectReviewState,
)


def _review_state() -> ProjectReviewState:
    intake = BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb"],
        review_objects=["mounting_structure", "foundation"],
        documents={"structural_drawings": "available"},
    )
    return ProjectReviewState(
        project_id="pv-human-review",
        intake=intake,
        current_phase="document_check",
        phase_statuses={
            "intake": "approved",
            "document_check": "waiting_for_engineer",
            "basis_build": "pending",
            "review_plan": "pending",
            "engineer_data_lock": "pending",
            "calculation_check": "pending",
            "risk_register": "pending",
            "report_draft": "pending",
            "engineer_approval": "pending",
            "issue_rfi_closeout": "pending",
        },
        agent_events=[
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
    )


def _report_ready_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents={
            "structural_drawings": "available",
            "calculation_report": "available",
            "technical_specification": "available",
            "geotechnical_report": "available",
            "vendor_datasheets": "available",
            "contract_requirements": "available",
        },
    )


def test_fields_ready_for_calculation_blocks_unconfirmed_fields() -> None:
    unconfirmed = ExtractedField(
        field_id="pile_length",
        name="Pile length",
        candidate_value="3.5",
        source_document_id="foundation-drawing-f201",
        page_or_section="Sheet F-201, foundation schedule",
        quote="Pile length L=3.5m",
        confidence=0.85,
    )

    assert fields_ready_for_calculation([unconfirmed]) is False


def test_fields_ready_for_calculation_requires_at_least_one_calculation_field() -> None:
    confirmed_but_excluded = ExtractedField(
        field_id="drawing_note",
        name="Drawing note",
        candidate_value="Issued for review",
        source_document_id="structural-drawing-a101",
        page_or_section="Title block",
        quote="Issued for review",
        confidence=0.8,
        is_confirmed=True,
        confirmed_value="Issued for review",
    )

    assert fields_ready_for_calculation([confirmed_but_excluded]) is False


def test_build_engineer_approval_returns_locked_gate_approval() -> None:
    approval = build_engineer_approval(
        approval_id="approval-001",
        target_id="calculation",
        reviewer="Engineer A",
        comment="Inputs confirmed for Phase 1 gate.",
    )

    assert approval.target_type == "gate"
    assert approval.target_id == "calculation"
    assert approval.status == "approved"
    assert approval.locked is True
    assert approval.reviewer == "Engineer A"


def test_record_agent_review_decision_approves_pending_agent_event_phase() -> None:
    state = _review_state()

    reviewed = record_agent_review_decision(
        state,
        event_id="agent-event-001",
        decision="approved",
        reviewer="Engineer A",
        comment="Document intake evidence reviewed.",
    )

    assert reviewed.phase_statuses["document_check"] == "approved"
    assert reviewed.approvals[-1] == EngineerApproval(
        approval_id="agent-review-agent-event-001",
        target_type="agent_event",
        target_id="agent-event-001",
        status="approved",
        reviewer="Engineer A",
        comment="Document intake evidence reviewed.",
        locked=True,
    )
    assert state.phase_statuses["document_check"] == "waiting_for_engineer"
    assert state.approvals == []


def test_record_agent_review_decision_rejects_pending_agent_event_without_locking() -> None:
    reviewed = record_agent_review_decision(
        _review_state(),
        event_id="agent-event-001",
        decision="rejected",
        reviewer="Engineer B",
        comment="Source evidence is incomplete.",
    )

    assert reviewed.phase_statuses["document_check"] == "rejected"
    assert reviewed.approvals[-1].target_type == "agent_event"
    assert reviewed.approvals[-1].target_id == "agent-event-001"
    assert reviewed.approvals[-1].status == "rejected"
    assert reviewed.approvals[-1].locked is False


def test_record_agent_review_decision_rejects_unknown_or_non_review_event() -> None:
    with pytest.raises(ValueError, match="Agent event"):
        record_agent_review_decision(
            _review_state(),
            event_id="missing-event",
            decision="approved",
            reviewer="Engineer A",
        )

    non_review_state = _review_state().model_copy(
        update={
            "agent_events": [
                _review_state().agent_events[0].model_copy(
                    update={"requires_engineer_review": False}
                )
            ]
        }
    )
    with pytest.raises(ValueError, match="does not require"):
        record_agent_review_decision(
            non_review_state,
            event_id="agent-event-001",
            decision="approved",
            reviewer="Engineer A",
        )


def test_record_agent_review_decision_rejects_duplicate_or_non_pending_event() -> None:
    reviewed = record_agent_review_decision(
        _review_state(),
        event_id="agent-event-001",
        decision="approved",
        reviewer="Engineer A",
    )

    with pytest.raises(ValueError, match="already has"):
        record_agent_review_decision(
            reviewed,
            event_id="agent-event-001",
            decision="approved",
            reviewer="Engineer A",
        )

    non_pending_state = _review_state().model_copy(
        update={
            "phase_statuses": {
                **_review_state().phase_statuses,
                "document_check": "blocked",
            }
        }
    )
    with pytest.raises(ValueError, match="not pending"):
        record_agent_review_decision(
            non_pending_state,
            event_id="agent-event-001",
            decision="approved",
            reviewer="Engineer A",
        )


def test_build_calculation_gate_run_blocks_when_fields_are_not_locked() -> None:
    run = build_calculation_gate_run(
        run_id="run-001",
        engine_name="foundation",
        fields=[
            ExtractedField(
                field_id="tilt",
                name="Tilt angle",
                candidate_value="25",
                source_document_id="structural-drawing-a101",
                page_or_section="Sheet S-101, mounting layout note 3",
                quote="Tilt angle: 25 deg",
                confidence=0.9,
            )
        ],
    )

    assert run.status == "blocked"
    assert run.input_locked is False
    assert run.structured_errors


def test_build_calculation_gate_run_returns_ready_placeholder_for_confirmed_fields() -> None:
    run = build_calculation_gate_run(
        run_id="run-002",
        engine_name="superstructure",
        fields=[
            ExtractedField(
                field_id="tilt",
                name="Tilt angle",
                candidate_value="25",
                source_document_id="structural-drawing-a101",
                page_or_section="Sheet S-101, mounting layout note 3",
                quote="Tilt angle: 25 deg",
                confidence=0.95,
                is_confirmed=True,
                confirmed_value="25",
                include_in_calculation=True,
            ),
            ExtractedField(
                field_id="pile_length",
                name="Pile length",
                candidate_value="3.5",
                source_document_id="foundation-drawing-f201",
                page_or_section="Sheet F-201, foundation schedule",
                quote="Pile length L=3.5m",
                confidence=0.9,
                is_confirmed=True,
                confirmed_value="3.5",
                include_in_calculation=True,
            ),
        ],
    )

    assert run.status == "ready"
    assert run.input_locked is True
    assert run.input_field_ids == ["tilt", "pile_length"]
    assert run.result_summary == {}


def test_record_report_revision_requires_ready_gate_and_report_engineer_approval() -> None:
    result = evaluate_bv_review(_review_state().intake)
    preview = build_bv_report_preview(_review_state().intake, result)
    gate = build_report_draft_gate_result(_review_state(), result)

    with pytest.raises(ValueError, match="report draft gate"):
        record_report_revision(
            _review_state(),
            revision_id="report-rev-001",
            report_preview=preview,
            gate_result=gate,
            reviewer="Engineer A",
        )

    ready_intake = _report_ready_intake()
    ready_result = evaluate_bv_review(ready_intake)
    ready_preview = build_bv_report_preview(ready_intake, ready_result)
    ready_state = ProjectReviewState(
        project_id="pv-report-ready",
        intake=ready_intake,
        approvals=[
            EngineerApproval(
                approval_id="approval-calculation",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            )
        ],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-human-gate",
                input_field_ids=["pile_length"],
                input_locked=True,
                status="ready",
            )
        ],
    )
    ready_gate = build_report_draft_gate_result(ready_state, ready_result)

    with pytest.raises(ValueError, match="Report gate"):
        record_report_revision(
            ready_state,
            revision_id="report-rev-001",
            report_preview=ready_preview,
            gate_result=ready_gate,
            reviewer="Engineer A",
        )


def test_record_report_revision_appends_traceable_ready_report_snapshot() -> None:
    intake = _report_ready_intake()
    result = evaluate_bv_review(intake)
    preview = build_bv_report_preview(intake, result)
    state = ProjectReviewState(
        project_id="pv-report-ready",
        intake=intake,
        current_phase="report_draft",
        approvals=[
            EngineerApproval(
                approval_id="approval-calculation",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            ),
            EngineerApproval(
                approval_id="approval-report",
                target_type="gate",
                target_id="report",
                status="approved",
                locked=True,
                reviewer="Engineer A",
            ),
        ],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-human-gate",
                input_field_ids=["pile_length"],
                input_locked=True,
                status="ready",
            )
        ],
    )
    gate = build_report_draft_gate_result(state, result)

    updated = record_report_revision(
        state,
        revision_id="report-rev-001",
        report_preview=preview,
        gate_result=gate,
        reviewer="Engineer A",
        note="Ready for internal review package.",
        created_at="2026-05-21T10:00:00+08:00",
    )

    revision = updated.report_revisions[-1]
    assert revision.revision_id == "report-rev-001"
    assert revision.report_title == preview.title
    assert revision.source_phase == "report_draft"
    assert revision.section_count == len(preview.sections)
    assert revision.rfi_count == len(updated.rfi_items)
    assert revision.blocking_risk_ids == []
    assert revision.calculation_run_ids == ["foundation-run-001"]
    assert revision.created_by == "Engineer A"
    assert revision.created_at == "2026-05-21T10:00:00+08:00"
    assert revision.note == "Ready for internal review package."
    assert state.report_revisions == []

    with pytest.raises(ValueError, match="already exists"):
        record_report_revision(
            updated,
            revision_id="report-rev-001",
            report_preview=preview,
            gate_result=gate,
            reviewer="Engineer A",
        )
