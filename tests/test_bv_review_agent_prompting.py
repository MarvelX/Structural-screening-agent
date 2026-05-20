import json

import pytest

from structural_screening_agent.bv_review import (
    AGENT_ROLE_SEQUENCE,
    ProjectReviewState,
)
from structural_screening_agent.bv_review.agent_prompting import (
    build_agent_prompt_package,
    build_agent_prompt_packages,
    parse_agent_json_response,
)
from structural_screening_agent.bv_review.agent_contracts import (
    DocumentIntakeAgentOutput,
    ReportComposerAgentOutput,
)
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.project_state import CalculationRun


def test_agent_prompt_package_includes_json_schema_and_engineering_boundaries() -> None:
    state = ProjectReviewState(project_id="pv-prompt-001", intake=_sample_intake())

    package = build_agent_prompt_package("document_intake", state)

    assert package.agent_role == "document_intake"
    assert package.schema_version == "phase2-agent-contracts-v1"
    assert package.output_model_name == "DocumentIntakeAgentOutput"
    assert package.output_schema["additionalProperties"] is False
    assert package.output_schema["properties"]["project_id"]["minLength"] == 1
    assert "Return exactly one JSON object" in package.system_prompt
    assert "Do not produce formal engineering conclusions" in package.system_prompt
    assert "Do not claim official BV signing or issue authority" in package.system_prompt
    assert "pv-prompt-001" in package.user_prompt
    assert "Ground PV prompt demo" in package.user_prompt


def test_build_agent_prompt_packages_follows_goal_agent_sequence() -> None:
    state = ProjectReviewState(project_id="pv-prompt-001", intake=_sample_intake())

    packages = build_agent_prompt_packages(state)

    assert [package.agent_role for package in packages] == list(AGENT_ROLE_SEQUENCE)
    assert len({package.output_model_name for package in packages}) == len(packages)


def test_calculation_check_prompt_references_existing_runs_without_authoring_calculations() -> None:
    state = ProjectReviewState(
        project_id="pv-prompt-001",
        intake=_sample_intake(),
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_locked=True,
                status="completed",
                result_summary={"screening_boundary": "screening-level review support only"},
            )
        ],
    )

    package = build_agent_prompt_package("calculation_check", state)

    assert "foundation-run-001" in package.user_prompt
    assert "Do not create calculation results" in package.system_prompt
    assert "calculation_runs" not in package.output_schema["properties"]


def test_parse_agent_json_response_validates_role_schema_and_state_constraints() -> None:
    state = ProjectReviewState(
        project_id="pv-prompt-001",
        intake=_sample_intake(),
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_locked=True,
                status="completed",
                result_summary={"screening_boundary": "screening-level review support only"},
            )
        ],
    )

    parsed = parse_agent_json_response(
        "document_intake",
        json.dumps(
            {
                "project_id": "pv-prompt-001",
                "document_versions": [
                    {
                        "document_id": "foundation-drawing-f201",
                        "document_type": "foundation_drawing",
                        "revision": "A",
                        "source_name": "F-201 Foundation Schedule Rev A.pdf",
                        "status": "available",
                    }
                ],
            }
        ),
    )

    assert isinstance(parsed, DocumentIntakeAgentOutput)
    assert parsed.document_versions[0].document_id == "foundation-drawing-f201"

    with pytest.raises(ValueError, match="Calculation run"):
        parse_agent_json_response(
            "calculation_check",
            json.dumps(
                {
                    "project_id": "pv-prompt-001",
                    "calculation_run_ids": ["fabricated-run-999"],
                }
            ),
            state=state,
        )


def test_parse_calculation_check_response_requires_project_state() -> None:
    with pytest.raises(ValueError, match="project state"):
        parse_agent_json_response(
            "calculation_check",
            json.dumps(
                {
                    "project_id": "pv-prompt-001",
                    "calculation_run_ids": ["fabricated-run-999"],
                }
            ),
        )


def test_parse_calculation_check_response_rejects_non_deterministic_existing_run() -> None:
    state = ProjectReviewState(
        project_id="pv-prompt-001",
        intake=_sample_intake(),
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-agent-authored",
                input_locked=True,
                status="completed",
                result_summary={"screening_boundary": "screening-level review support only"},
            )
        ],
    )

    with pytest.raises(ValueError, match="deterministic"):
        parse_agent_json_response(
            "calculation_check",
            json.dumps(
                {
                    "project_id": "pv-prompt-001",
                    "calculation_run_ids": ["foundation-run-001"],
                }
            ),
            state=state,
        )


def test_parse_agent_json_response_rejects_response_role_mismatch() -> None:
    with pytest.raises(ValueError, match="role does not match"):
        parse_agent_json_response(
            "basis_code",
            json.dumps(
                {
                    "project_id": "pv-prompt-001",
                    "agent_role": "document_intake",
                    "basis_references": [
                        {
                            "basis_id": "gb-50797",
                            "title": "GB 50797",
                            "source_type": "code",
                        }
                    ],
                }
            ),
        )


def test_parse_agent_json_response_rejects_non_json_extra_fields_and_signing_claims() -> None:
    with pytest.raises(ValueError, match="valid JSON object"):
        parse_agent_json_response("document_intake", "not json")

    with pytest.raises(ValueError, match="Extra inputs"):
        parse_agent_json_response(
            "document_intake",
            json.dumps({"project_id": "pv-prompt-001", "unexpected": "field"}),
        )

    with pytest.raises(ValueError, match="formal signing"):
        parse_agent_json_response(
            "report_composer",
            json.dumps(
                {
                    "project_id": "pv-prompt-001",
                    "report_sections": [
                        {
                            "heading": "Conclusion",
                            "items": ["This is ready for official BV issue."],
                        }
                    ],
                    "boundary_statement": (
                        "This draft is for screening-level review-support only."
                    ),
                }
            ),
        )


def test_parse_agent_json_response_returns_report_composer_output_for_valid_boundary() -> None:
    parsed = parse_agent_json_response(
        "report_composer",
        json.dumps(
            {
                "project_id": "pv-prompt-001",
                "report_sections": [
                    {
                        "heading": "Review boundary",
                        "items": ["This draft is for screening-level review support only."],
                    }
                ],
                "boundary_statement": "This draft is for screening-level review-support only.",
            }
        ),
    )

    assert isinstance(parsed, ReportComposerAgentOutput)


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV prompt demo",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents={
            "structural_drawings": "available",
            "calculation_report": "partial",
            "geotechnical_report": "missing",
        },
    )
