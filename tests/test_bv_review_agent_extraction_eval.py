from pathlib import Path

from structural_screening_agent.bv_review import DocumentIntakeAgentOutput
from structural_screening_agent.bv_review.project_state import ExtractedField
from structural_screening_agent.bv_review.agent_extraction_eval import (
    AgentExtractionCase,
    ExpectedExtractedField,
    evaluate_document_intake_output,
    load_extraction_cases,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_load_extraction_cases_reads_curated_golden_cases() -> None:
    cases = load_extraction_cases(FIXTURE_DIR / "bv_agent_extraction_cases.json")

    assert len(cases) == 10
    assert cases[0].case_id == "pv-cn-ground-fixed-foundation-001"
    assert cases[0].language == "zh"
    assert cases[0].scenario == "ground_fixed_foundation"
    assert cases[0].expected_fields[0].field_id == "tilt_angle_deg"
    assert cases[0].expected_fields[0].expected_value == 25
    assert "steel_grade" in cases[0].must_not_extract


def _field(
    field_id: str,
    value: object,
    unit: str | None,
    *,
    include_in_calculation: bool = False,
    quote: str = "source quote",
) -> ExtractedField:
    return ExtractedField.model_construct(
        field_id=field_id,
        name=field_id,
        candidate_value=value,
        unit=unit,
        source_document_id="source-doc",
        page_or_section="section 1",
        quote=quote,
        confidence=0.9,
        is_confirmed=False,
        include_in_calculation=include_in_calculation,
    )


def _output(
    project_id: str,
    extracted_fields: list[ExtractedField],
    missing_document_keys: list[str],
) -> DocumentIntakeAgentOutput:
    return DocumentIntakeAgentOutput.model_construct(
        project_id=project_id,
        schema_version="phase2-agent-contracts-v1",
        requires_engineer_review=True,
        agent_role="document_intake",
        extracted_fields=extracted_fields,
        document_versions=[],
        missing_document_keys=missing_document_keys,
        notes=[],
    )


def test_evaluate_document_intake_output_scores_matched_fields_and_evidence() -> None:
    case = AgentExtractionCase(
        case_id="case-perfect",
        language="zh",
        scenario="foundation",
        source_text="桩径300mm，桩长3.5m。",
        expected_fields=[
            ExpectedExtractedField(
                field_id="pile_diameter_mm",
                expected_value=300,
                unit="mm",
                include_in_calculation=True,
            ),
            ExpectedExtractedField(
                field_id="pile_length_m",
                expected_value=3.5,
                unit="m",
                include_in_calculation=True,
            ),
        ],
        expected_missing_document_keys=["calculation_report"],
        must_not_extract=["steel_grade"],
    )
    output = _output(
        "case-perfect",
        [
            _field("pile_diameter_mm", 300, "mm", include_in_calculation=True),
            _field("pile_length_m", 3.5, "m", include_in_calculation=True),
        ],
        ["calculation_report"],
    )

    score = evaluate_document_intake_output(case, output)

    assert score.case_id == "case-perfect"
    assert score.field_recall == 1.0
    assert score.field_precision == 1.0
    assert score.value_accuracy == 1.0
    assert score.unit_accuracy == 1.0
    assert score.evidence_completeness == 1.0
    assert score.missing_document_recall == 1.0
    assert score.missing_document_precision == 1.0
    assert score.no_hallucination_rate == 1.0
    assert score.calculation_readiness_accuracy == 1.0
    assert score.hallucinated_field_ids == []


def test_evaluate_document_intake_output_penalizes_wrong_units_and_hallucinations() -> None:
    case = AgentExtractionCase(
        case_id="case-flawed",
        language="zh",
        scenario="foundation",
        source_text="桩径300mm。",
        expected_fields=[
            ExpectedExtractedField(
                field_id="pile_diameter_mm",
                expected_value=300,
                unit="mm",
                include_in_calculation=True,
            )
        ],
        expected_missing_document_keys=["geotechnical_report"],
        must_not_extract=["steel_grade"],
    )
    output = _output(
        "case-flawed",
        [
            _field(
                "pile_diameter_mm",
                300,
                "m",
                include_in_calculation=False,
                quote="",
            ),
            _field("steel_grade", "Q355B", None),
        ],
        ["calculation_report"],
    )

    score = evaluate_document_intake_output(case, output)

    assert score.field_recall == 0.0
    assert score.field_precision == 0.0
    assert score.value_accuracy == 1.0
    assert score.unit_accuracy == 0.0
    assert score.evidence_completeness == 0.0
    assert score.missing_document_recall == 0.0
    assert score.missing_document_precision == 0.0
    assert score.no_hallucination_rate == 0.0
    assert score.calculation_readiness_accuracy == 0.0
    assert score.hallucinated_field_ids == ["steel_grade"]
