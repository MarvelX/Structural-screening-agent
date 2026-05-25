from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Optional, Union

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
        for field_id in value_matched_ids
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
        evidence_completeness=_ratio(len(evidence_ready_ids), len(value_matched_ids)),
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


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return numerator / denominator


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
