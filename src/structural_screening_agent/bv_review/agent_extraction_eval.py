from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Literal, Optional, Union

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.agent_contracts import DocumentIntakeAgentOutput
from structural_screening_agent.bv_review.project_state import ExtractedField


ExpectedValue = Union[str, float, int, bool]


class ExpectedExtractedField(BaseModel):
    field_id: str = Field(min_length=1)
    expected_value: ExpectedValue
    unit: Optional[str] = None
    required: bool = True
    include_in_calculation: Optional[bool] = None


class AgentExtractionCase(BaseModel):
    case_id: str = Field(min_length=1)
    language: Literal["zh", "en", "mixed"]
    scenario: str = Field(min_length=1)
    source_text: str = Field(min_length=1)
    expected_fields: list[ExpectedExtractedField] = Field(default_factory=list)
    expected_missing_document_keys: list[str] = Field(default_factory=list)
    must_not_extract: list[str] = Field(default_factory=list)


def load_extraction_cases(path: Path) -> list[AgentExtractionCase]:
    raw_cases = json.loads(path.read_text(encoding="utf-8"))
    return [AgentExtractionCase.model_validate(raw_case) for raw_case in raw_cases]


class AgentExtractionCaseScore(BaseModel):
    case_id: str = Field(min_length=1)
    field_recall: float = Field(ge=0, le=1)
    field_precision: float = Field(ge=0, le=1)
    value_accuracy: float = Field(ge=0, le=1)
    unit_accuracy: float = Field(ge=0, le=1)
    evidence_completeness: float = Field(ge=0, le=1)
    missing_document_recall: float = Field(ge=0, le=1)
    missing_document_precision: float = Field(ge=0, le=1)
    no_hallucination_rate: float = Field(ge=0, le=1)
    calculation_readiness_accuracy: float = Field(ge=0, le=1)
    matched_field_ids: list[str] = Field(default_factory=list)
    missing_field_ids: list[str] = Field(default_factory=list)
    extra_field_ids: list[str] = Field(default_factory=list)
    hallucinated_field_ids: list[str] = Field(default_factory=list)


class AgentExtractionEvaluationSummary(BaseModel):
    case_count: int = Field(ge=0)
    average_field_recall: float = Field(ge=0, le=1)
    average_field_precision: float = Field(ge=0, le=1)
    average_value_accuracy: float = Field(ge=0, le=1)
    average_unit_accuracy: float = Field(ge=0, le=1)
    average_evidence_completeness: float = Field(ge=0, le=1)
    average_missing_document_recall: float = Field(ge=0, le=1)
    average_missing_document_precision: float = Field(ge=0, le=1)
    average_no_hallucination_rate: float = Field(ge=0, le=1)
    average_calculation_readiness_accuracy: float = Field(ge=0, le=1)
    failing_case_ids: list[str] = Field(default_factory=list)
    case_scores: list[AgentExtractionCaseScore] = Field(default_factory=list)


def load_mock_document_intake_outputs(
    path: Path,
) -> dict[str, DocumentIntakeAgentOutput]:
    raw_outputs = json.loads(path.read_text(encoding="utf-8"))
    return {
        case_id: DocumentIntakeAgentOutput.model_validate(raw_output)
        for case_id, raw_output in raw_outputs.items()
    }


def evaluate_document_intake_output(
    case: AgentExtractionCase,
    output: DocumentIntakeAgentOutput,
) -> AgentExtractionCaseScore:
    expected_by_id = {field.field_id: field for field in case.expected_fields}
    required_expected_ids = {
        field.field_id for field in case.expected_fields if field.required
    }
    extracted_by_id = {field.field_id: field for field in output.extracted_fields}

    value_matched_ids = [
        field_id
        for field_id, expected in expected_by_id.items()
        if field_id in extracted_by_id
        and _value_matches(expected.expected_value, extracted_by_id[field_id].candidate_value)
    ]
    unit_matched_ids = [
        field_id
        for field_id, expected in expected_by_id.items()
        if field_id in extracted_by_id
        and _unit_matches(expected.unit, extracted_by_id[field_id].unit)
    ]
    fully_matched_ids = [
        field_id for field_id in value_matched_ids if field_id in unit_matched_ids
    ]
    required_fully_matched_ids = [
        field_id for field_id in fully_matched_ids if field_id in required_expected_ids
    ]
    extra_field_ids = [
        field_id for field_id in extracted_by_id if field_id not in expected_by_id
    ]
    must_not_extract = set(case.must_not_extract)
    hallucinated_field_ids = [
        field_id for field_id in extracted_by_id if field_id in must_not_extract
    ]
    readiness_expected = [
        field for field in case.expected_fields if field.include_in_calculation is not None
    ]
    readiness_matched = [
        field.field_id
        for field in readiness_expected
        if field.field_id in extracted_by_id
        and extracted_by_id[field.field_id].include_in_calculation
        == field.include_in_calculation
    ]
    evidence_ready_ids = [
        field_id
        for field_id in fully_matched_ids
        if _has_complete_evidence(extracted_by_id[field_id])
    ]
    expected_missing = set(case.expected_missing_document_keys)
    actual_missing = set(output.missing_document_keys)

    return AgentExtractionCaseScore(
        case_id=case.case_id,
        field_recall=_ratio(len(required_fully_matched_ids), len(required_expected_ids)),
        field_precision=_ratio(len(fully_matched_ids), len(extracted_by_id)),
        value_accuracy=_ratio(len(value_matched_ids), len(expected_by_id)),
        unit_accuracy=_ratio(len(unit_matched_ids), len(expected_by_id)),
        evidence_completeness=_evidence_ratio(
            len(evidence_ready_ids),
            len(fully_matched_ids),
            len(expected_by_id),
        ),
        missing_document_recall=_ratio(
            len(expected_missing & actual_missing),
            len(expected_missing),
        ),
        missing_document_precision=_ratio(
            len(expected_missing & actual_missing),
            len(actual_missing),
        ),
        no_hallucination_rate=0.0 if hallucinated_field_ids else 1.0,
        calculation_readiness_accuracy=_ratio(
            len(readiness_matched),
            len(readiness_expected),
        ),
        matched_field_ids=sorted(fully_matched_ids),
        missing_field_ids=sorted(required_expected_ids - set(required_fully_matched_ids)),
        extra_field_ids=sorted(extra_field_ids),
        hallucinated_field_ids=sorted(hallucinated_field_ids),
    )


def evaluate_extraction_case_outputs(
    cases: list[AgentExtractionCase],
    outputs_by_case_id: dict[str, DocumentIntakeAgentOutput],
) -> AgentExtractionEvaluationSummary:
    scores = [
        evaluate_document_intake_output(case, outputs_by_case_id[case.case_id])
        for case in cases
    ]
    failing_case_ids = [
        score.case_id
        for score in scores
        if min(
            score.field_recall,
            score.field_precision,
            score.no_hallucination_rate,
        )
        < 1.0
    ]
    return AgentExtractionEvaluationSummary(
        case_count=len(scores),
        average_field_recall=_average(score.field_recall for score in scores),
        average_field_precision=_average(score.field_precision for score in scores),
        average_value_accuracy=_average(score.value_accuracy for score in scores),
        average_unit_accuracy=_average(score.unit_accuracy for score in scores),
        average_evidence_completeness=_average(
            score.evidence_completeness for score in scores
        ),
        average_missing_document_recall=_average(
            score.missing_document_recall for score in scores
        ),
        average_missing_document_precision=_average(
            score.missing_document_precision for score in scores
        ),
        average_no_hallucination_rate=_average(
            score.no_hallucination_rate for score in scores
        ),
        average_calculation_readiness_accuracy=_average(
            score.calculation_readiness_accuracy for score in scores
        ),
        failing_case_ids=failing_case_ids,
        case_scores=scores,
    )


def build_extraction_eval_markdown_summary(
    summary: AgentExtractionEvaluationSummary,
) -> str:
    lines = [
        "## Agent Extraction Reliability Evaluation",
        "",
        f"- Case count: {summary.case_count}",
        f"- Field recall: {summary.average_field_recall:.2f}",
        f"- Field precision: {summary.average_field_precision:.2f}",
        f"- Value accuracy: {summary.average_value_accuracy:.2f}",
        f"- Unit accuracy: {summary.average_unit_accuracy:.2f}",
        f"- Evidence completeness: {summary.average_evidence_completeness:.2f}",
        f"- Missing document recall: {summary.average_missing_document_recall:.2f}",
        f"- Missing document precision: {summary.average_missing_document_precision:.2f}",
        f"- No-hallucination rate: {summary.average_no_hallucination_rate:.2f}",
        f"- Calculation readiness accuracy: {summary.average_calculation_readiness_accuracy:.2f}",
        f"- Failing cases: {', '.join(summary.failing_case_ids) or 'None'}",
    ]
    return "\n".join(lines) + "\n"


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator


def _evidence_ratio(
    evidence_ready_count: int,
    fully_matched_count: int,
    expected_field_count: int,
) -> float:
    if expected_field_count == 0:
        return 1.0
    if fully_matched_count == 0:
        return 0.0
    return evidence_ready_count / fully_matched_count


def _value_matches(expected: ExpectedValue, actual: object) -> bool:
    try:
        return abs(float(expected) - float(actual)) <= 1e-6
    except (TypeError, ValueError):
        return str(expected).strip().lower() == str(actual).strip().lower()


def _unit_matches(expected: Optional[str], actual: Optional[str]) -> bool:
    return (expected or "").strip().lower() == (actual or "").strip().lower()


def _has_complete_evidence(field: ExtractedField) -> bool:
    return all(
        [
            bool(field.source_document_id.strip()),
            bool(field.page_or_section.strip()),
            bool(field.quote.strip()),
        ]
    )


def _average(values: Iterable[float]) -> float:
    materialized = list(values)
    if not materialized:
        return 1.0
    return sum(materialized) / len(materialized)
