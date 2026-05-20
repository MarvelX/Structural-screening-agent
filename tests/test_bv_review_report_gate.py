from structural_screening_agent.bv_review.human_gate import build_report_draft_gate_result
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.project_state import (
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
                    triggers_incremental_recheck=True,
                )
            ]
        }
    )

    gate = build_report_draft_gate_result(state, result)

    assert gate.status == "ready"


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
    assert any("incremental recheck" in reason.lower() for reason in gate.reasons)
