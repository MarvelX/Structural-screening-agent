import pytest
from pydantic import ValidationError

from structural_screening_agent.bv_review import (
    AGENT_ROLE_SEQUENCE,
    BVReviewIntake,
    CalculationCheckAgentOutput,
    DocumentIntakeAgentOutput,
    ProjectReviewState,
    ReportComposerAgentOutput,
    validate_calculation_check_output_against_state,
)


def test_agent_role_sequence_matches_goal_matrix() -> None:
    assert AGENT_ROLE_SEQUENCE == (
        "document_intake",
        "basis_code",
        "review_plan",
        "structural_review",
        "calculation_check",
        "risk_ncr",
        "report_composer",
    )


def test_document_intake_output_accepts_traceable_extracted_fields_and_documents() -> None:
    output = DocumentIntakeAgentOutput(
        project_id="pv-001",
        extracted_fields=[
            {
                "field_id": "pile_length_m",
                "name": "Pile length",
                "candidate_value": "3.5",
                "unit": "m",
                "source_document_id": "foundation-drawing-f201",
                "page_or_section": "Sheet F-201, foundation schedule",
                "quote": "Pile length L=3.5m",
                "confidence": 0.9,
            }
        ],
        document_versions=[
            {
                "document_id": "foundation-drawing-f201",
                "document_type": "foundation_drawing",
                "revision": "A",
                "source_name": "F-201 Foundation Schedule Rev A.pdf",
                "status": "available",
            }
        ],
    )

    assert output.agent_role == "document_intake"
    assert output.requires_engineer_review is True
    assert output.extracted_fields[0].source_document_id == "foundation-drawing-f201"


def test_document_intake_output_rejects_extracted_fields_without_source_evidence() -> None:
    with pytest.raises(ValidationError):
        DocumentIntakeAgentOutput(
            project_id="pv-001",
            extracted_fields=[
                {
                    "field_id": "pile_length_m",
                    "name": "Pile length",
                    "candidate_value": "3.5",
                    "unit": "m",
                    "page_or_section": "Sheet F-201, foundation schedule",
                    "quote": "Pile length L=3.5m",
                    "confidence": 0.9,
                }
            ],
        )


def test_calculation_check_output_requires_deterministic_screening_boundary() -> None:
    valid = CalculationCheckAgentOutput(
        project_id="pv-001",
        calculation_run_ids=["foundation-run-001"],
    )
    assert valid.requires_engineer_review is True

    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        calculation_runs=[
            _completed_foundation_run(
                "foundation-run-001",
                {"screening_boundary": "screening-level review support only"},
            )
        ],
    )
    validate_calculation_check_output_against_state(valid, state)

    missing_boundary_state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        calculation_runs=[
            _completed_foundation_run(
                "foundation-run-001",
                {"controlling_utilization_ratio": 0.82},
            )
        ],
    )
    with pytest.raises(ValueError, match="screening boundary"):
        validate_calculation_check_output_against_state(valid, missing_boundary_state)


def test_calculation_check_output_rejects_agent_supplied_calculation_runs() -> None:
    with pytest.raises(ValidationError):
        CalculationCheckAgentOutput(
            project_id="pv-001",
            calculation_run_ids=["foundation-run-001"],
            calculation_runs=[
                _completed_foundation_run(
                    "foundation-run-001",
                    {"screening_boundary": "screening-level review support only"},
                )
            ],
        )


def test_calculation_check_output_must_match_existing_project_state_runs() -> None:
    output = CalculationCheckAgentOutput(
        project_id="pv-001",
        calculation_run_ids=["foundation-run-001"],
    )
    state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        calculation_runs=[
            _completed_foundation_run(
                "foundation-run-001",
                {
                    "screening_boundary": "screening-level review support only",
                    "controlling_utilization_ratio": 0.82,
                },
            )
        ],
    )

    validate_calculation_check_output_against_state(output, state)

    with pytest.raises(ValueError, match="does not exist"):
        validate_calculation_check_output_against_state(
            CalculationCheckAgentOutput(
                project_id="pv-001",
                calculation_run_ids=["fabricated-run-999"],
            ),
            state,
        )

    wrong_project_state = ProjectReviewState(
        project_id="pv-999",
        intake=_sample_intake(),
        calculation_runs=state.calculation_runs,
    )
    with pytest.raises(ValueError, match="project_id"):
        validate_calculation_check_output_against_state(output, wrong_project_state)


def test_report_composer_output_requires_review_support_boundary() -> None:
    output = ReportComposerAgentOutput(
        project_id="pv-001",
        report_sections=[
            {
                "heading": "Review boundary",
                "items": ["This draft is for screening-level review support only."],
            }
        ],
        boundary_statement="This draft is for screening-level review-support only.",
    )
    assert output.agent_role == "report_composer"

    with pytest.raises(ValidationError, match="screening-level or review-support"):
        ReportComposerAgentOutput(
            project_id="pv-001",
            report_sections=[{"heading": "Conclusion", "items": ["Acceptable."]}],
            boundary_statement="This is an official BV issue-ready report.",
        )

    with pytest.raises(ValidationError, match="must not claim formal signing"):
        ReportComposerAgentOutput(
            project_id="pv-001",
            report_sections=[{"heading": "Conclusion", "items": ["Acceptable."]}],
            boundary_statement="This screening-level draft is ready for stamped approval.",
        )


def test_report_composer_output_rejects_formal_signing_terms_in_body_and_rfi() -> None:
    with pytest.raises(ValidationError, match="must not claim formal signing"):
        ReportComposerAgentOutput(
            project_id="pv-001",
            report_sections=[
                {
                    "heading": "Conclusion",
                    "items": ["This section can be used for stamped approval."],
                }
            ],
            boundary_statement="This draft is for screening-level review-support only.",
        )

    with pytest.raises(ValidationError, match="must not claim formal signing"):
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
                    "rfi_id": "rfi-001",
                    "question": "Please confirm whether this can be 正式签发.",
                    "responsible_party": "client",
                    "trigger_basis": "Report boundary clarification",
                    "required_document_or_field": "client confirmation",
                    "status": "open",
                }
            ],
            boundary_statement="This draft is for screening-level review-support only.",
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


def _completed_foundation_run(
    run_id: str,
    result_summary: dict[str, str | float | int | bool],
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "engine_name": "foundation",
        "engine_version": "phase1-deterministic-screening",
        "input_field_ids": ["pile_length_m"],
        "input_locked": True,
        "status": "completed",
        "result_summary": result_summary,
    }
