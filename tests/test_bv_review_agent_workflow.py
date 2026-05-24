import pytest

from structural_screening_agent.bv_review import (
    BasisCodeAgentOutput,
    BVReviewIntake,
    CalculationCheckAgentOutput,
    DocumentIntakeAgentOutput,
    ProjectReviewState,
    ReportComposerAgentOutput,
    ReviewPlanAgentOutput,
    RiskNCRAgentOutput,
    StructuralReviewAgentOutput,
    apply_agent_output_to_state,
)
from structural_screening_agent.bv_review.project_state import CalculationRun
from structural_screening_agent.bv_review.project_state import EngineerApproval


def test_document_intake_agent_output_updates_state_and_waits_for_engineer_review() -> None:
    state = ProjectReviewState(project_id="pv-001", intake=_sample_intake())
    output = DocumentIntakeAgentOutput(
        project_id="pv-001",
        document_versions=[
            {
                "document_id": "foundation-drawing-f201",
                "document_type": "foundation_drawing",
                "revision": "A",
                "source_name": "F-201 Foundation Schedule Rev A.pdf",
                "status": "available",
            }
        ],
        extracted_fields=[
            {
                "field_id": "pile_length_m",
                "name": "Pile length",
                "candidate_value": "3.5",
                "unit": "m",
                "source_document_id": "foundation-drawing-f201",
                "page_or_section": "Sheet F-201",
                "quote": "Pile length L=3.5m",
                "confidence": 0.9,
            }
        ],
    )

    updated = apply_agent_output_to_state(state, output)

    assert [document.document_id for document in updated.document_versions] == [
        "foundation-drawing-f201"
    ]
    assert [field.field_id for field in updated.extracted_fields] == ["pile_length_m"]
    assert updated.current_phase == "document_check"
    assert updated.phase_statuses["document_check"] == "waiting_for_engineer"
    assert len(updated.agent_events) == 1
    event = updated.agent_events[0]
    assert event.event_id == "agent-event-001"
    assert event.agent_role == "document_intake"
    assert event.target_phase == "document_check"
    assert event.status == "applied"
    assert event.output_schema_version == output.schema_version
    assert event.created_at is not None
    assert "T" in event.created_at
    assert event.requires_engineer_review is True
    assert event.summary_counts == {
        "document_versions": 1,
        "extracted_fields": 1,
        "missing_document_keys": 0,
    }
    assert state.document_versions == []
    assert state.agent_events == []


def test_basis_agent_output_updates_traceable_basis_references() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="document_check",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "document_check": "approved",
        },
    )
    output = BasisCodeAgentOutput(
        project_id="pv-001",
        basis_references=[
            {
                "basis_id": "GB-50797",
                "title": "GB 50797 PV power station design code",
                "source_type": "code",
                "standards_systems": ["gb"],
                "review_objects": ["mounting_structure", "foundation"],
                "trigger_conditions": ["China ground-mounted PV project"],
                "evidence_requirements": ["Project country and project type"],
                "review_actions": ["Use as basis for civil and structural review plan."],
            }
        ],
    )

    updated = apply_agent_output_to_state(state, output)

    assert updated.basis_references[0].basis_id == "GB-50797"
    assert updated.current_phase == "basis_build"
    assert updated.phase_statuses["basis_build"] == "waiting_for_engineer"


def test_review_plan_and_structural_review_outputs_update_state() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="basis_build",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "basis_build": "approved",
        },
    )
    with_plan = apply_agent_output_to_state(
        state,
        ReviewPlanAgentOutput(
            project_id="pv-001",
            review_plan=[
                {
                    "item_id": "PLAN-001",
                    "phase": "technical_check",
                    "review_object": "foundation",
                    "input_documents": ["foundation-drawing-f201"],
                    "method": "Check confirmed pile and geotechnical inputs before engine run.",
                    "responsible_role": "PV structural review engineer",
                    "blocking_condition": "Pile length or geotechnical values are unconfirmed.",
                    "deliverable": "Foundation check input package",
                }
            ],
        ),
    )
    plan_approved_state = with_plan.model_copy(
        update={
            "phase_statuses": {
                **with_plan.phase_statuses,
                "review_plan": "approved",
            }
        }
    )
    with_path = apply_agent_output_to_state(
        plan_approved_state,
        StructuralReviewAgentOutput(
            project_id="pv-001",
            review_paths=[
                {
                    "path_id": "PATH-FOUNDATION",
                    "review_object": "foundation",
                    "title": "Foundation uplift screening path",
                    "method": "Use locked pile and geotechnical fields for deterministic screening.",
                    "required_inputs": ["pile_length_m", "side_resistance_standard_kpa"],
                    "deliverables": ["Foundation screening run"],
                    "status": "manual_confirmation_required",
                }
            ],
        ),
    )

    assert with_plan.review_plan[0].item_id == "PLAN-001"
    assert with_plan.current_phase == "review_plan"
    assert with_plan.phase_statuses["review_plan"] == "waiting_for_engineer"
    assert with_path.review_paths[0].path_id == "PATH-FOUNDATION"
    assert with_path.current_phase == "engineer_data_lock"
    assert with_path.phase_statuses["engineer_data_lock"] == "waiting_for_engineer"
    assert [event.agent_role for event in with_path.agent_events] == [
        "review_plan",
        "structural_review",
    ]


def test_calculation_check_agent_output_only_resolves_existing_state_runs() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "engineer_data_lock": "approved",
        },
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
                engine_version="phase1-deterministic-screening",
                input_field_ids=["pile_length_m"],
                input_locked=True,
                status="completed",
                result_summary={"screening_boundary": "screening-level review support only"},
            )
        ],
    )

    updated = apply_agent_output_to_state(
        state,
        CalculationCheckAgentOutput(
            project_id="pv-001",
            calculation_run_ids=["foundation-run-001"],
        ),
    )

    assert updated.calculation_runs == state.calculation_runs
    assert updated.current_phase == "calculation_check"
    assert updated.phase_statuses["calculation_check"] == "waiting_for_engineer"

    with pytest.raises(ValueError, match="does not exist"):
        apply_agent_output_to_state(
            state,
            CalculationCheckAgentOutput(
                project_id="pv-001",
                calculation_run_ids=["fabricated-run-999"],
            ),
        )


def test_risk_and_report_agent_outputs_update_state_without_formal_issue_claims() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="calculation_check",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "calculation_check": "approved",
        },
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["pile_length_m"],
                input_locked=True,
                status="completed",
                result_summary={"screening_boundary": "screening-level review support only"},
            )
        ],
    )
    with_risk = apply_agent_output_to_state(
        state,
        RiskNCRAgentOutput(
            project_id="pv-001",
            source_calculation_run_ids=["foundation-run-001"],
            risks=[
                {
                    "risk_id": "R-001",
                    "title": "Missing confirmed pile length",
                    "severity": "high",
                    "trigger_basis": "Pile length has not been confirmed by engineer.",
                    "linked_field_ids": ["pile_length_m"],
                    "impact_scope": "Foundation uplift screening cannot be completed.",
                    "recommendation": "Request revised foundation schedule and engineer confirmation.",
                    "blocks_report_issue": True,
                    "category": "risk",
                }
            ],
        ),
    )
    risk_approved_state = with_risk.model_copy(
        update={
            "phase_statuses": {
                **with_risk.phase_statuses,
                "risk_register": "approved",
            }
        }
    )
    with_report = apply_agent_output_to_state(
        risk_approved_state,
        ReportComposerAgentOutput(
            project_id="pv-001",
            report_sections=[
                {
                    "heading": "Review boundary",
                    "items": ["This draft is for screening-level review support only."],
                }
            ],
            rfi_items=[
                {
                    "rfi_id": "RFI-001",
                    "question": "Please provide confirmed pile length.",
                    "responsible_party": "client",
                    "trigger_basis": "Missing confirmed field",
                    "required_document_or_field": "pile_length_m",
                    "status": "open",
                }
            ],
            boundary_statement="This draft is for screening-level review-support only.",
        ),
    )

    assert with_risk.risks[0].risk_id == "R-001"
    assert with_risk.current_phase == "risk_register"
    assert with_risk.phase_statuses["risk_register"] == "waiting_for_engineer"
    assert with_report.report_sections[0].heading == "Review boundary"
    assert with_report.rfi_items[0].rfi_id == "RFI-001"
    assert with_report.current_phase == "report_draft"
    assert with_report.phase_statuses["report_draft"] == "waiting_for_engineer"


def test_report_composer_cannot_close_or_respond_to_rfi_during_report_draft() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="risk_register",
    )

    with pytest.raises(ValueError, match="Report composer output can only draft open RFI"):
        apply_agent_output_to_state(
            state,
            ReportComposerAgentOutput(
                project_id="pv-001",
                report_sections=[
                    {
                        "heading": "Review boundary",
                        "items": ["This draft is for screening-level review support only."],
                    }
                ],
                rfi_items=[
                    {
                        "rfi_id": "RFI-001",
                        "question": "Please confirm updated pile length.",
                        "responsible_party": "client",
                        "trigger_basis": "Client response received",
                        "required_document_or_field": "pile_length_m",
                        "status": "closed",
                        "client_response": "Updated drawing received.",
                    }
                ],
                boundary_statement="This draft is for screening-level review-support only.",
            ),
        )


def test_agent_output_project_id_must_match_state() -> None:
    state = ProjectReviewState(project_id="pv-001", intake=_sample_intake())

    with pytest.raises(ValueError, match="project_id"):
        apply_agent_output_to_state(
            state,
            DocumentIntakeAgentOutput(project_id="pv-999"),
        )


def test_agent_output_cannot_skip_required_workflow_phase() -> None:
    state = ProjectReviewState(project_id="pv-001", intake=_sample_intake())

    with pytest.raises(ValueError, match="Cannot apply basis_code"):
        apply_agent_output_to_state(
            state,
            BasisCodeAgentOutput(
                project_id="pv-001",
                basis_references=[
                    {
                        "basis_id": "GB-50797",
                        "title": "GB 50797 PV power station design code",
                        "source_type": "code",
                    }
                ],
            ),
        )


def test_agent_output_cannot_advance_before_current_phase_engineer_approval() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="document_check",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "document_check": "waiting_for_engineer",
        },
    )

    with pytest.raises(ValueError, match="requires engineer approval"):
        apply_agent_output_to_state(
            state,
            BasisCodeAgentOutput(
                project_id="pv-001",
                basis_references=[
                    {
                        "basis_id": "GB-50797",
                        "title": "GB 50797 PV power station design code",
                        "source_type": "code",
                    }
                ],
            ),
        )


def test_calculation_check_output_requires_locked_engineer_gate() -> None:
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="engineer_data_lock",
        phase_statuses={
            **ProjectReviewState(project_id="pv-001", intake=_sample_intake()).phase_statuses,
            "engineer_data_lock": "approved",
        },
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["pile_length_m"],
                input_locked=True,
                status="completed",
                result_summary={"screening_boundary": "screening-level review support only"},
            )
        ],
    )

    with pytest.raises(ValueError, match="Calculation gate"):
        apply_agent_output_to_state(
            state,
            CalculationCheckAgentOutput(
                project_id="pv-001",
                calculation_run_ids=["foundation-run-001"],
            ),
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
