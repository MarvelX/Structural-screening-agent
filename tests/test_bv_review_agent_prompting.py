import json

import pytest

from structural_screening_agent.bv_review import (
    AGENT_ROLE_SEQUENCE,
    ProjectReviewState,
)
from structural_screening_agent.bv_review.agent_prompting import (
    build_agent_provider_invocation_request,
    build_agent_provider_invocation_rows,
    build_agent_prompt_package,
    build_agent_prompt_package_rows,
    build_agent_prompt_packages,
    build_agent_response_impact_rows,
    build_sample_agent_response_json,
    parse_agent_json_response,
    preview_agent_response_impact,
    validate_agent_json_response,
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


def test_agent_prompt_package_rows_are_localized_for_workbench_preview() -> None:
    state = ProjectReviewState(project_id="pv-prompt-001", intake=_sample_intake())
    packages = build_agent_prompt_packages(state)

    zh_rows = build_agent_prompt_package_rows(packages, "zh")
    en_rows = build_agent_prompt_package_rows(packages, "en")

    assert zh_rows[0]["Agent"] == "资料接收 Agent"
    assert zh_rows[0]["输出模型"] == "DocumentIntakeAgentOutput"
    assert zh_rows[0]["边界"] == "JSON 输出 / 工程师复核 / 不替代签发"
    assert en_rows[0]["Agent"] == "Document Intake Agent"
    assert en_rows[0]["Output Model"] == "DocumentIntakeAgentOutput"
    assert en_rows[0]["Boundary"] == "JSON output / engineer review / no signing authority"


def test_agent_provider_invocation_request_is_minimax_compatible_without_secrets() -> None:
    state = ProjectReviewState(project_id="pv-prompt-001", intake=_sample_intake())
    package = build_agent_prompt_package("document_intake", state)

    request = build_agent_provider_invocation_request(
        package,
        provider_name="minimax",
        model_name="MiniMax-M2.5",
    )

    assert request.agent_role == "document_intake"
    assert request.provider_name == "minimax"
    assert request.model_name == "MiniMax-M2.5"
    assert request.mode == "preview"
    assert request.messages == [
        {"role": "system", "content": package.system_prompt},
        {"role": "user", "content": package.user_prompt},
    ]
    assert request.response_format["type"] == "json_schema"
    assert request.response_format["json_schema"]["name"] == "DocumentIntakeAgentOutput"
    assert request.response_format["json_schema"]["strict"] is True
    assert request.response_format["json_schema"]["schema"] == package.output_schema
    assert request.temperature == 0.0
    assert request.output_schema["title"] == "DocumentIntakeAgentOutput"
    assert request.boundary_statement == (
        "Invocation preview only; no network request is sent and no API key is stored."
    )
    request_payload = request.model_dump()
    assert "api_key" not in request_payload
    assert "MINIMAX_API_KEY" not in str(request_payload)
    assert "OPENAI_API_KEY" not in str(request_payload)
    assert "Authorization" not in str(request_payload)
    assert "test-key" not in str(request_payload)


def test_agent_provider_invocation_rows_are_localized_for_workbench() -> None:
    package = build_agent_prompt_package(
        "report_composer",
        ProjectReviewState(project_id="pv-prompt-001", intake=_sample_intake()),
    )
    request = build_agent_provider_invocation_request(
        package,
        provider_name="mock",
        model_name="demo-mock",
    )

    zh_rows = build_agent_provider_invocation_rows(request, "zh")
    en_rows = build_agent_provider_invocation_rows(request, "en")

    assert {"项目": "供应商", "内容": "mock"} in zh_rows
    assert {"项目": "响应格式", "内容": "json_schema"} in zh_rows
    assert {"项目": "Schema 严格模式", "内容": "是"} in zh_rows
    assert {"项目": "网络调用", "内容": "否"} in zh_rows
    assert {"Item": "Provider", "Value": "mock"} in en_rows
    assert {"Item": "Response Format", "Value": "json_schema"} in en_rows
    assert {"Item": "Schema Strict", "Value": "Yes"} in en_rows
    assert {"Item": "Network Request", "Value": "No"} in en_rows


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


def test_parse_agent_json_response_rejects_project_id_mismatch_when_state_is_provided() -> None:
    with pytest.raises(ValueError, match="project_id"):
        parse_agent_json_response(
            "document_intake",
            json.dumps(
                {
                    "project_id": "other-project",
                    "document_versions": [],
                    "extracted_fields": [],
                }
            ),
            state=ProjectReviewState(project_id="pv-prompt-001", intake=_sample_intake()),
        )

    validation = validate_agent_json_response(
        "document_intake",
        json.dumps(
            {
                "project_id": "other-project",
                "document_versions": [],
                "extracted_fields": [],
            }
        ),
        state=ProjectReviewState(project_id="pv-prompt-001", intake=_sample_intake()),
    )

    assert validation.ok is False
    assert "project_id" in validation.error


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


def test_validate_agent_json_response_returns_structured_success_and_failure() -> None:
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

    success = validate_agent_json_response(
        "calculation_check",
        json.dumps(
            {
                "project_id": "pv-prompt-001",
                "calculation_run_ids": ["foundation-run-001"],
            }
        ),
        state=state,
    )
    failure = validate_agent_json_response(
        "calculation_check",
        json.dumps(
            {
                "project_id": "pv-prompt-001",
                "calculation_run_ids": ["fabricated-run-999"],
            }
        ),
        state=state,
    )

    assert success.ok is True
    assert success.output_model_name == "CalculationCheckAgentOutput"
    assert success.summary == "Validated CalculationCheckAgentOutput for calculation_check."
    assert failure.ok is False
    assert failure.output_model_name == "CalculationCheckAgentOutput"
    assert "fabricated-run-999" in failure.error


def test_sample_agent_response_json_matches_selected_contract() -> None:
    document_sample = build_sample_agent_response_json(
        "document_intake",
        ProjectReviewState(project_id="pv-prompt-001", intake=_sample_intake()),
    )
    calculation_sample = build_sample_agent_response_json(
        "calculation_check",
        ProjectReviewState(
            project_id="pv-prompt-001",
            intake=_sample_intake(),
            calculation_runs=[
                CalculationRun(
                    run_id="foundation-run-001",
                    engine_name="foundation",
                    engine_version="phase1-deterministic-screening",
                    input_locked=True,
                    status="completed",
                    result_summary={
                        "screening_boundary": "screening-level review support only"
                    },
                )
            ],
        ),
    )

    assert json.loads(document_sample)["project_id"] == "pv-prompt-001"
    assert json.loads(document_sample)["document_versions"][0]["document_id"]
    assert json.loads(calculation_sample)["calculation_run_ids"] == ["foundation-run-001"]


def test_preview_agent_response_impact_reports_artifact_counts_without_mutating_state() -> None:
    state = ProjectReviewState(project_id="pv-prompt-001", intake=_sample_intake())
    response_text = json.dumps(
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
            "extracted_fields": [
                {
                    "field_id": "pile-length",
                    "name": "Pile length",
                    "candidate_value": 2.8,
                    "unit": "m",
                    "source_document_id": "foundation-drawing-f201",
                    "page_or_section": "Foundation schedule",
                    "quote": "Pile length 2.8 m",
                    "confidence": 0.86,
                }
            ],
        }
    )

    preview = preview_agent_response_impact(
        "document_intake",
        response_text,
        state=state,
    )

    assert preview.agent_role == "document_intake"
    assert preview.output_model_name == "DocumentIntakeAgentOutput"
    assert preview.target_phase == "document_check"
    assert preview.summary_counts == {
        "document_versions": 1,
        "extracted_fields": 1,
        "missing_document_keys": 0,
    }
    assert preview.would_update == ["document_versions", "extracted_fields"]
    assert preview.requires_engineer_review is True
    assert preview.blocks_direct_apply is True
    assert preview.passes_apply_prechecks is True
    assert preview.apply_blockers == []
    assert (
        preview.boundary_statement
        == "Preview only; engineer approval is still required before applying agent output."
    )
    assert state.document_versions == []
    assert state.extracted_fields == []


def test_preview_agent_response_impact_preserves_calculation_check_state_validation() -> None:
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

    with pytest.raises(ValueError, match="fabricated-run-999"):
        preview_agent_response_impact(
            "calculation_check",
            json.dumps(
                {
                    "project_id": "pv-prompt-001",
                    "calculation_run_ids": ["fabricated-run-999"],
                }
            ),
            state=state,
        )


def test_preview_agent_response_impact_reports_apply_precheck_blockers() -> None:
    state = ProjectReviewState(
        project_id="pv-prompt-001",
        intake=_sample_intake(),
        current_phase="calculation_check",
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

    preview = preview_agent_response_impact(
        "calculation_check",
        json.dumps(
            {
                "project_id": "pv-prompt-001",
                "calculation_run_ids": ["foundation-run-001"],
            }
        ),
        state=state,
    )

    assert preview.target_phase == "calculation_check"
    assert preview.summary_counts == {"calculation_run_ids": 1}
    assert preview.passes_apply_prechecks is False
    assert preview.apply_blockers == [
        "Calculation gate must be locked before applying calculation check output."
    ]


def test_agent_response_impact_rows_are_localized_for_workbench() -> None:
    preview = preview_agent_response_impact(
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
        state=ProjectReviewState(
            project_id="pv-prompt-001",
            intake=_sample_intake(),
            current_phase="report_draft",
        ),
    )

    zh_rows = build_agent_response_impact_rows(preview, "zh")
    en_rows = build_agent_response_impact_rows(preview, "en")

    assert zh_rows[0] == {"项目": "目标阶段", "值": "report_draft"}
    assert {"项目": "会更新", "值": "report_sections"} in zh_rows
    assert {"项目": "应用前置检查", "值": "通过"} in zh_rows
    assert {"Item": "Target Phase", "Value": "report_draft"} in en_rows
    assert {"Item": "Apply Pre-checks", "Value": "Pass"} in en_rows
    assert {
        "Item": "Boundary",
        "Value": "Preview only; engineer approval is still required before applying agent output.",
    } in en_rows


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
