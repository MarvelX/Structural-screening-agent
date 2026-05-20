from structural_screening_agent.bv_review.human_gate import (
    build_calculation_gate_run,
    build_engineer_approval,
    fields_ready_for_calculation,
)
from structural_screening_agent.bv_review.project_state import ExtractedField


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
