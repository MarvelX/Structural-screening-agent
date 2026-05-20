import pytest
from pydantic import ValidationError

from structural_screening_agent.bv_review import (
    BVReviewIntake,
    ExtractedField,
    FieldDiff,
    FoundationEngineInput,
    ProjectReviewState,
    SuperstructureEngineInput,
    advance_project_phase,
    close_rfi_after_engineer_review,
    diff_extracted_fields,
    evaluate_bv_review,
    build_foundation_calculation_run,
    build_foundation_calculation_run_from_fields,
    build_superstructure_calculation_run,
    build_superstructure_calculation_run_from_fields,
    record_rfi_client_response,
)
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    DocumentVersion,
    EngineerApproval,
    PVStructuralSpec,
    REVIEW_PHASES,
    RFIItem,
)


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents={"structural_drawings": "available"},
    )


def test_project_review_state_defaults_include_all_review_phases() -> None:
    state = ProjectReviewState(project_id="pv-001", intake=_sample_intake())

    assert state.current_phase == "intake"
    assert tuple(state.phase_statuses) == REVIEW_PHASES
    assert set(state.phase_statuses.values()) == {"pending"}


def test_extracted_field_cannot_enter_calculation_before_confirmation() -> None:
    with pytest.raises(ValidationError):
        ExtractedField(
            field_id="tilt",
            name="Tilt angle",
            candidate_value="25",
            source_document_id="structural-drawing-a101",
            page_or_section="Sheet S-101, mounting layout note 3",
            quote="Tilt angle: 25 deg",
            confidence=0.9,
            include_in_calculation=True,
        )


def test_extracted_field_requires_source_page_quote_and_confidence() -> None:
    with pytest.raises(ValidationError):
        ExtractedField(
            field_id="pile_length",
            name="Pile length",
            candidate_value="3.5",
            page_or_section="Sheet F-201, foundation schedule",
            quote="Pile length L=3.5m",
            confidence=0.86,
        )


def test_pv_structural_spec_carries_ground_fixed_foundation_geotech_member_and_force_data() -> None:
    spec = PVStructuralSpec(
        tilt_angle_deg=25,
        pile_diameter_mm=300,
        pile_length_m=3.5,
        pile_spacing_m=4.2,
        steel_grade="Q355B",
        post_section="C160",
        beam_section="H200x100",
        purlin_section="C80",
        basic_wind_pressure_kpa=0.45,
        snow_load_kpa=0.35,
        bearing_capacity_characteristic_kpa=180,
        side_resistance_standard_kpa=45,
        worst_axial_force_kn=38,
        worst_bending_moment_knm=12.5,
        worst_shear_force_kn=6.2,
    )

    assert spec.support_type == "ground_fixed"
    assert spec.pile_diameter_mm == 300
    assert spec.bearing_capacity_characteristic_kpa == 180
    assert spec.post_section == "C160"
    assert spec.worst_bending_moment_knm == 12.5


def test_engineer_approval_locked_requires_approved_status() -> None:
    with pytest.raises(ValidationError):
        EngineerApproval(
            approval_id="gate-001",
            target_type="gate",
            target_id="calculation",
            status="pending",
            locked=True,
        )


def test_calculation_run_ready_or_completed_requires_locked_inputs() -> None:
    with pytest.raises(ValidationError):
        CalculationRun(
            run_id="run-001",
            engine_name="foundation",
            engine_version="phase1-placeholder",
            input_field_ids=["tilt"],
            input_locked=False,
            status="ready",
        )

    blocked = CalculationRun(
        run_id="run-002",
        engine_name="foundation",
        engine_version="phase1-placeholder",
        input_field_ids=["tilt"],
        input_locked=False,
        status="blocked",
        structured_errors=["Engineer confirmation is required before calculation."],
    )
    assert blocked.structured_errors


def test_rfi_responded_or_closed_requires_client_response_and_reopened_can_trigger_recheck() -> None:
    with pytest.raises(ValidationError):
        RFIItem(
            rfi_id="rfi-001",
            question="Please confirm pile length.",
            responsible_party="client",
            trigger_basis="Missing foundation input",
            required_document_or_field="pile_length_m",
            status="closed",
        )

    with pytest.raises(ValidationError):
        RFIItem(
            rfi_id="rfi-001a",
            question="Please confirm pile length.",
            responsible_party="client",
            trigger_basis="Missing foundation input",
            required_document_or_field="pile_length_m",
            status="responded",
        )

    reopened = RFIItem(
        rfi_id="rfi-002",
        question="Please confirm pile length.",
        responsible_party="client",
        trigger_basis="Client changed foundation drawing.",
        required_document_or_field="pile_length_m",
        status="reopened",
        reopen_review_items=["foundation_input_check"],
        triggers_incremental_recheck=True,
    )
    assert reopened.triggers_incremental_recheck is True


def test_rfi_open_or_reopened_incremental_recheck_requires_reopen_review_items() -> None:
    with pytest.raises(ValidationError):
        RFIItem(
            rfi_id="rfi-003",
            question="Please confirm updated pile length.",
            responsible_party="client",
            trigger_basis="Pile length changed in revised foundation drawing.",
            required_document_or_field="pile_length_m",
            status="open",
            triggers_incremental_recheck=True,
        )

    with pytest.raises(ValidationError):
        RFIItem(
            rfi_id="rfi-004",
            question="Please confirm updated pile length.",
            responsible_party="client",
            trigger_basis="Pile length changed in revised foundation drawing.",
            required_document_or_field="pile_length_m",
            status="reopened",
            triggers_incremental_recheck=True,
        )


def test_document_version_supersedes_cannot_reference_itself() -> None:
    with pytest.raises(ValidationError):
        DocumentVersion(
            document_id="foundation-drawing-f201",
            document_type="structural_drawings",
            revision="B",
            source_name="F-201 Foundation Schedule Rev B.pdf",
            status="available",
            supersedes="foundation-drawing-f201",
        )


def test_project_review_state_returns_locked_calculation_fields_and_gate_status() -> None:
    state = ProjectReviewState(
        project_id="pv-002",
        intake=_sample_intake(),
        extracted_fields=[
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
                field_id="note",
                name="Drawing note",
                candidate_value="Issued for review",
                source_document_id="structural-drawing-a101",
                page_or_section="Title block",
                quote="Issued for review",
                confidence=0.8,
            ),
        ],
        approvals=[
            EngineerApproval(
                approval_id="approval-001",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            )
        ],
    )

    assert [field.field_id for field in state.locked_calculation_fields()] == ["tilt"]
    assert state.is_gate_locked("calculation") is True
    assert state.is_gate_locked("report") is False


def test_bv_review_package_exports_existing_and_phase1_state_objects() -> None:
    assert BVReviewIntake is not None
    assert evaluate_bv_review is not None
    assert ProjectReviewState is not None
    assert ExtractedField is not None
    assert advance_project_phase is not None
    assert FieldDiff is not None
    assert diff_extracted_fields is not None
    assert FoundationEngineInput is not None
    assert SuperstructureEngineInput is not None
    assert build_foundation_calculation_run is not None
    assert build_foundation_calculation_run_from_fields is not None
    assert build_superstructure_calculation_run is not None
    assert build_superstructure_calculation_run_from_fields is not None
    assert record_rfi_client_response is not None
    assert close_rfi_after_engineer_review is not None
