# Agent Extraction Reliability Eval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline, deterministic reliability evaluation set for the BV Document Intake Agent's parameter extraction behavior.

**Architecture:** Add a small evaluation module under `src/structural_screening_agent/bv_review/` that scores `DocumentIntakeAgentOutput` against curated golden cases. Keep the first version fully offline by using fixture cases and mock agent outputs; no live MiniMax/OpenAI calls, no network dependency, and no change to the existing workflow runner.

**Tech Stack:** Python 3.11, Pydantic, Pytest, existing `DocumentIntakeAgentOutput`, `ExtractedField`, and `DocumentVersion` models.

---

## File Structure

- Create: `src/structural_screening_agent/bv_review/agent_extraction_eval.py`
  - Owns golden-case loading, output scoring, metric aggregation, and a compact markdown summary helper.
  - Depends only on existing BV agent contracts and project-state models.
- Create: `tests/fixtures/bv_agent_extraction_cases.json`
  - Contains the first 10 golden extraction cases.
  - Covers Chinese, English, bilingual, missing-document, conflict, and hallucination-resistance scenarios.
- Create: `tests/fixtures/bv_agent_extraction_outputs.json`
  - Contains deterministic mock `DocumentIntakeAgentOutput` payloads keyed by `case_id`.
  - Includes both high-quality and intentionally flawed outputs so the scorer's penalty behavior is tested.
- Create: `tests/test_bv_review_agent_extraction_eval.py`
  - Unit tests for case loading, field matching, scoring, aggregation, and markdown summary.
- Modify: `src/structural_screening_agent/bv_review/__init__.py`
  - Export the evaluation models and functions that are useful to tests, docs, and future UI/report slices.
- Modify: `docs/bv-pv-design-review-workbench-roadmap.md`
  - Add the offline Agent extraction reliability evaluation as an implemented or active Phase 5 item once code lands.
- Modify: `docs/bv-jd-feature-mapping.md`
  - Connect the reliability evaluation to document completeness, standards/application traceability, and engineering quality responsibility.
- Modify: `tests/test_bv_jd_feature_mapping.py`
  - Keep roadmap/JD documentation synchronized with the new tested capability.

Protected boundaries:

- Do not modify `src/structural_screening_agent/core/`.
- Do not call a live LLM provider.
- Do not create scripts in `scripts/` for this MVP.
- Do not write outputs to `outputs/` or the repo root.
- Do not modify or delete local duplicate files named like `* 2.py` or `* 2.md`.

## Evaluation Semantics

The first version scores field extraction, not full engineering correctness.

Metrics:

- `field_recall`: expected required fields found with matching value and unit.
- `field_precision`: extracted fields that are expected and match value/unit.
- `value_accuracy`: expected fields found with matching value, regardless of unit.
- `unit_accuracy`: expected fields found with matching unit.
- `evidence_completeness`: matched expected fields whose extracted field has `source_document_id`, `page_or_section`, and `quote`.
- `missing_document_recall`: expected missing document keys reported by the agent.
- `missing_document_precision`: reported missing document keys that are expected.
- `no_hallucination_rate`: `1.0` when none of the case's `must_not_extract` field IDs appear in the output; otherwise `0.0`.
- `calculation_readiness_accuracy`: expected `include_in_calculation` flags matched for fields where the case defines the expected readiness.

Matching rules:

- A field matches by `field_id`.
- Numeric values compare after float conversion with absolute tolerance `1e-6`.
- Non-numeric values compare case-insensitively after trimming.
- Unit comparison is case-insensitive after trimming.
- Optional expected fields contribute to precision when extracted correctly, but do not reduce recall when absent.
- Any extracted field listed in `must_not_extract` is a hallucinated field.

## Fixture Schema

`tests/fixtures/bv_agent_extraction_cases.json` uses this shape:

```json
[
  {
    "case_id": "pv-cn-ground-fixed-foundation-001",
    "language": "zh",
    "scenario": "ground_fixed_foundation",
    "source_text": "本项目为河北地面固定支架光伏项目，支架倾角25度，PHC桩径300mm，桩长3.5m，地基承载力特征值fak=180kPa。结构计算书暂未提交。",
    "expected_fields": [
      {
        "field_id": "tilt_angle_deg",
        "expected_value": 25,
        "unit": "deg",
        "required": true,
        "include_in_calculation": false
      },
      {
        "field_id": "pile_diameter_mm",
        "expected_value": 300,
        "unit": "mm",
        "required": true,
        "include_in_calculation": true
      }
    ],
    "expected_missing_document_keys": ["calculation_report"],
    "must_not_extract": ["steel_grade"]
  }
]
```

`tests/fixtures/bv_agent_extraction_outputs.json` uses this shape:

```json
{
  "pv-cn-ground-fixed-foundation-001": {
    "project_id": "pv-cn-ground-fixed-foundation-001",
    "schema_version": "phase2-agent-contracts-v1",
    "requires_engineer_review": true,
    "agent_role": "document_intake",
    "extracted_fields": [
      {
        "field_id": "tilt_angle_deg",
        "name": "Tilt angle",
        "candidate_value": 25,
        "unit": "deg",
        "source_document_id": "project-description",
        "page_or_section": "source text",
        "quote": "支架倾角25度",
        "confidence": 0.94,
        "is_confirmed": false,
        "include_in_calculation": false
      }
    ],
    "document_versions": [],
    "missing_document_keys": ["calculation_report"],
    "notes": []
  }
}
```

## Task 1: Add Golden Extraction Cases

**Files:**
- Create: `tests/fixtures/bv_agent_extraction_cases.json`
- Test: `tests/test_bv_review_agent_extraction_eval.py`

- [ ] **Step 1: Write the failing loader test**

Add this test file with the first test only:

```python
from pathlib import Path

from structural_screening_agent.bv_review.agent_extraction_eval import (
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_agent_extraction_eval.py::test_load_extraction_cases_reads_curated_golden_cases -p no:cacheprovider
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError` for `agent_extraction_eval`.

- [ ] **Step 3: Add the fixture**

Create `tests/fixtures/bv_agent_extraction_cases.json` with exactly 10 cases:

```json
[
  {
    "case_id": "pv-cn-ground-fixed-foundation-001",
    "language": "zh",
    "scenario": "ground_fixed_foundation",
    "source_text": "本项目为河北地面固定支架光伏项目，支架倾角25度，PHC桩径300mm，桩长3.5m，地基承载力特征值fak=180kPa。结构计算书暂未提交。",
    "expected_fields": [
      {"field_id": "tilt_angle_deg", "expected_value": 25, "unit": "deg", "required": true, "include_in_calculation": false},
      {"field_id": "pile_diameter_mm", "expected_value": 300, "unit": "mm", "required": true, "include_in_calculation": true},
      {"field_id": "pile_length_m", "expected_value": 3.5, "unit": "m", "required": true, "include_in_calculation": true},
      {"field_id": "bearing_capacity_characteristic_kpa", "expected_value": 180, "unit": "kPa", "required": true, "include_in_calculation": true}
    ],
    "expected_missing_document_keys": ["calculation_report"],
    "must_not_extract": ["steel_grade"]
  },
  {
    "case_id": "pv-en-ground-fixed-wind-002",
    "language": "en",
    "scenario": "ground_fixed_loads",
    "source_text": "The ground-mounted PV support uses a 25 deg tilt. Basic wind pressure is 0.45 kPa and snow load is 0.35 kPa. The geotechnical report has not been submitted.",
    "expected_fields": [
      {"field_id": "tilt_angle_deg", "expected_value": 25, "unit": "deg", "required": true, "include_in_calculation": false},
      {"field_id": "basic_wind_pressure_kpa", "expected_value": 0.45, "unit": "kPa", "required": true, "include_in_calculation": true},
      {"field_id": "snow_load_kpa", "expected_value": 0.35, "unit": "kPa", "required": true, "include_in_calculation": true}
    ],
    "expected_missing_document_keys": ["geotechnical_report"],
    "must_not_extract": ["pile_length_m", "steel_grade"]
  },
  {
    "case_id": "pv-bilingual-member-003",
    "language": "mixed",
    "scenario": "member_schedule",
    "source_text": "支架材料表 / Member schedule: post section C160, beam section H200x100, purlin section C80. Steel grade is Q355B.",
    "expected_fields": [
      {"field_id": "post_section", "expected_value": "C160", "unit": null, "required": true, "include_in_calculation": false},
      {"field_id": "beam_section", "expected_value": "H200x100", "unit": null, "required": true, "include_in_calculation": false},
      {"field_id": "purlin_section", "expected_value": "C80", "unit": null, "required": true, "include_in_calculation": false},
      {"field_id": "steel_grade", "expected_value": "Q355B", "unit": null, "required": true, "include_in_calculation": false}
    ],
    "expected_missing_document_keys": [],
    "must_not_extract": ["pile_diameter_mm"]
  },
  {
    "case_id": "pv-cn-reaction-table-004",
    "language": "zh",
    "scenario": "foundation_reactions",
    "source_text": "基础反力汇总表：最不利轴力38kN，最不利弯矩12.5kN.m，最不利剪力6.2kN。",
    "expected_fields": [
      {"field_id": "worst_axial_force_kn", "expected_value": 38, "unit": "kN", "required": true, "include_in_calculation": true},
      {"field_id": "worst_bending_moment_knm", "expected_value": 12.5, "unit": "kN.m", "required": true, "include_in_calculation": true},
      {"field_id": "worst_shear_force_kn", "expected_value": 6.2, "unit": "kN", "required": true, "include_in_calculation": true}
    ],
    "expected_missing_document_keys": [],
    "must_not_extract": ["bearing_capacity_characteristic_kpa"]
  },
  {
    "case_id": "pv-cn-missing-geotech-005",
    "language": "zh",
    "scenario": "missing_geotechnical_evidence",
    "source_text": "图纸说明：基础形式按地勘确定。当前提交资料包括结构图和技术规格书，未见地勘报告。",
    "expected_fields": [],
    "expected_missing_document_keys": ["geotechnical_report"],
    "must_not_extract": ["bearing_capacity_characteristic_kpa", "side_resistance_standard_kpa", "pile_length_m"]
  },
  {
    "case_id": "pv-en-contract-standard-006",
    "language": "en",
    "scenario": "contract_requirements",
    "source_text": "The contract requires independent civil and structural design review under Eurocode and IEC 62548. No calculation report is included in the submission package.",
    "expected_fields": [],
    "expected_missing_document_keys": ["calculation_report"],
    "must_not_extract": ["basic_wind_pressure_kpa", "snow_load_kpa", "pile_diameter_mm"]
  },
  {
    "case_id": "pv-cn-unit-expression-007",
    "language": "zh",
    "scenario": "unit_expression",
    "source_text": "基础表：PHC管桩 D=300mm，L=3500mm，桩间距4.2m。",
    "expected_fields": [
      {"field_id": "pile_diameter_mm", "expected_value": 300, "unit": "mm", "required": true, "include_in_calculation": true},
      {"field_id": "pile_length_m", "expected_value": 3.5, "unit": "m", "required": true, "include_in_calculation": true},
      {"field_id": "pile_spacing_m", "expected_value": 4.2, "unit": "m", "required": true, "include_in_calculation": false}
    ],
    "expected_missing_document_keys": [],
    "must_not_extract": ["steel_grade"]
  },
  {
    "case_id": "pv-cn-revision-conflict-008",
    "language": "zh",
    "scenario": "revision_conflict",
    "source_text": "Rev A 基础表桩径300mm；Rev B 基础表桩径350mm，Rev B 替代 Rev A。计算书仍引用 Rev A。",
    "expected_fields": [
      {"field_id": "pile_diameter_mm", "expected_value": 350, "unit": "mm", "required": true, "include_in_calculation": true}
    ],
    "expected_missing_document_keys": [],
    "must_not_extract": ["pile_length_m", "bearing_capacity_characteristic_kpa"]
  },
  {
    "case_id": "pv-cn-rooftop-added-load-009",
    "language": "zh",
    "scenario": "existing_rooftop_added_load",
    "source_text": "既有屋面光伏增载复核：新增恒载0.18kPa，组件及支架布置见屋面平面图。原结构计算书未提供。",
    "expected_fields": [
      {"field_id": "pv_added_dead_load_kpa", "expected_value": 0.18, "unit": "kPa", "required": false, "include_in_calculation": false}
    ],
    "expected_missing_document_keys": ["calculation_report"],
    "must_not_extract": ["pile_diameter_mm", "pile_length_m"]
  },
  {
    "case_id": "pv-cn-no-specific-values-010",
    "language": "zh",
    "scenario": "anti_hallucination",
    "source_text": "设计说明称支架、基础和连接均满足现行规范要求，具体计算参数详见后续计算书。当前文本未列出数值。",
    "expected_fields": [],
    "expected_missing_document_keys": ["calculation_report"],
    "must_not_extract": ["tilt_angle_deg", "pile_diameter_mm", "steel_grade", "basic_wind_pressure_kpa"]
  }
]
```

- [ ] **Step 4: Add minimal loader implementation**

Create `src/structural_screening_agent/bv_review/agent_extraction_eval.py` with:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


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
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_agent_extraction_eval.py::test_load_extraction_cases_reads_curated_golden_cases -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/structural_screening_agent/bv_review/agent_extraction_eval.py tests/fixtures/bv_agent_extraction_cases.json tests/test_bv_review_agent_extraction_eval.py
git commit -m "test: add agent extraction golden cases"
```

## Task 2: Implement Field-Level Scoring

**Files:**
- Modify: `src/structural_screening_agent/bv_review/agent_extraction_eval.py`
- Modify: `tests/test_bv_review_agent_extraction_eval.py`

- [ ] **Step 1: Write failing scoring tests**

Append:

```python
from structural_screening_agent.bv_review import DocumentIntakeAgentOutput
from structural_screening_agent.bv_review.project_state import ExtractedField
from structural_screening_agent.bv_review.agent_extraction_eval import (
    AgentExtractionCase,
    ExpectedExtractedField,
    evaluate_document_intake_output,
)


def _field(
    field_id: str,
    value: object,
    unit: str | None,
    *,
    include_in_calculation: bool = False,
    quote: str = "source quote",
) -> ExtractedField:
    return ExtractedField(
        field_id=field_id,
        name=field_id,
        candidate_value=value,
        unit=unit,
        source_document_id="source-doc",
        page_or_section="section 1",
        quote=quote,
        confidence=0.9,
        include_in_calculation=include_in_calculation,
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
    output = DocumentIntakeAgentOutput(
        project_id="case-perfect",
        extracted_fields=[
            _field("pile_diameter_mm", 300, "mm", include_in_calculation=True),
            _field("pile_length_m", 3.5, "m", include_in_calculation=True),
        ],
        missing_document_keys=["calculation_report"],
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
    output = DocumentIntakeAgentOutput(
        project_id="case-flawed",
        extracted_fields=[
            _field(
                "pile_diameter_mm",
                300,
                "m",
                include_in_calculation=False,
                quote="",
            ),
            _field("steel_grade", "Q355B", None),
        ],
        missing_document_keys=["calculation_report"],
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_agent_extraction_eval.py -p no:cacheprovider
```

Expected: FAIL with `ImportError` for `evaluate_document_intake_output`.

- [ ] **Step 3: Implement scoring**

Add to `agent_extraction_eval.py`:

```python
from structural_screening_agent.bv_review.agent_contracts import DocumentIntakeAgentOutput
from structural_screening_agent.bv_review.project_state import ExtractedField


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
        field_id
        for field_id in value_matched_ids
        if field_id in unit_matched_ids
    ]
    required_fully_matched_ids = [
        field_id for field_id in fully_matched_ids if field_id in required_expected_ids
    ]
    expected_extracted_ids = [
        field_id for field_id in extracted_by_id if field_id in expected_by_id
    ]
    extra_field_ids = [
        field_id for field_id in extracted_by_id if field_id not in expected_by_id
    ]
    hallucinated_field_ids = [
        field_id for field_id in extracted_by_id if field_id in set(case.must_not_extract)
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
        evidence_completeness=_ratio(len(evidence_ready_ids), len(fully_matched_ids)),
        missing_document_recall=_ratio(len(expected_missing & actual_missing), len(expected_missing)),
        missing_document_precision=_ratio(len(expected_missing & actual_missing), len(actual_missing)),
        no_hallucination_rate=0.0 if hallucinated_field_ids else 1.0,
        calculation_readiness_accuracy=_ratio(len(readiness_matched), len(readiness_expected)),
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_agent_extraction_eval.py -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/bv_review/agent_extraction_eval.py tests/test_bv_review_agent_extraction_eval.py
git commit -m "feat: score agent extraction reliability"
```

## Task 3: Add Mock Output Fixture and Aggregate Metrics

**Files:**
- Create: `tests/fixtures/bv_agent_extraction_outputs.json`
- Modify: `src/structural_screening_agent/bv_review/agent_extraction_eval.py`
- Modify: `tests/test_bv_review_agent_extraction_eval.py`

- [ ] **Step 1: Write failing aggregate tests**

Append:

```python
from structural_screening_agent.bv_review.agent_extraction_eval import (
    build_extraction_eval_markdown_summary,
    evaluate_extraction_case_outputs,
    load_mock_document_intake_outputs,
)


def test_load_mock_document_intake_outputs_reads_document_intake_contracts() -> None:
    outputs = load_mock_document_intake_outputs(
        FIXTURE_DIR / "bv_agent_extraction_outputs.json"
    )

    assert "pv-cn-ground-fixed-foundation-001" in outputs
    assert outputs["pv-cn-ground-fixed-foundation-001"].agent_role == "document_intake"
    assert outputs["pv-cn-ground-fixed-foundation-001"].requires_engineer_review is True


def test_evaluate_extraction_case_outputs_summarizes_fixture_performance() -> None:
    cases = load_extraction_cases(FIXTURE_DIR / "bv_agent_extraction_cases.json")
    outputs = load_mock_document_intake_outputs(
        FIXTURE_DIR / "bv_agent_extraction_outputs.json"
    )

    summary = evaluate_extraction_case_outputs(cases, outputs)

    assert summary.case_count == 10
    assert summary.average_field_recall >= 0.7
    assert summary.average_field_precision >= 0.7
    assert summary.average_no_hallucination_rate >= 0.8
    assert summary.failing_case_ids == ["pv-cn-no-specific-values-010"]


def test_build_extraction_eval_markdown_summary_is_portfolio_ready() -> None:
    cases = load_extraction_cases(FIXTURE_DIR / "bv_agent_extraction_cases.json")
    outputs = load_mock_document_intake_outputs(
        FIXTURE_DIR / "bv_agent_extraction_outputs.json"
    )
    summary = evaluate_extraction_case_outputs(cases, outputs)

    markdown = build_extraction_eval_markdown_summary(summary)

    assert markdown.startswith("## Agent Extraction Reliability Evaluation")
    assert "Case count: 10" in markdown
    assert "Field recall" in markdown
    assert "No-hallucination rate" in markdown
    assert "pv-cn-no-specific-values-010" in markdown
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_agent_extraction_eval.py -p no:cacheprovider
```

Expected: FAIL with missing `load_mock_document_intake_outputs`.

- [ ] **Step 3: Add mock output fixture**

Create `tests/fixtures/bv_agent_extraction_outputs.json`.

Use valid `DocumentIntakeAgentOutput` payloads for all 10 `case_id` values. For cases 1 through 9, make most outputs correct. For `pv-cn-no-specific-values-010`, include an intentional hallucinated `steel_grade` field so the aggregate test has one known failing case.

The first and last entries must be:

```json
{
  "pv-cn-ground-fixed-foundation-001": {
    "project_id": "pv-cn-ground-fixed-foundation-001",
    "schema_version": "phase2-agent-contracts-v1",
    "requires_engineer_review": true,
    "agent_role": "document_intake",
    "extracted_fields": [
      {
        "field_id": "tilt_angle_deg",
        "name": "Tilt angle",
        "candidate_value": 25,
        "unit": "deg",
        "source_document_id": "project-description",
        "page_or_section": "source text",
        "quote": "支架倾角25度",
        "confidence": 0.94,
        "is_confirmed": false,
        "include_in_calculation": false
      },
      {
        "field_id": "pile_diameter_mm",
        "name": "Pile diameter",
        "candidate_value": 300,
        "unit": "mm",
        "source_document_id": "project-description",
        "page_or_section": "source text",
        "quote": "PHC桩径300mm",
        "confidence": 0.93,
        "is_confirmed": false,
        "include_in_calculation": true
      },
      {
        "field_id": "pile_length_m",
        "name": "Pile length",
        "candidate_value": 3.5,
        "unit": "m",
        "source_document_id": "project-description",
        "page_or_section": "source text",
        "quote": "桩长3.5m",
        "confidence": 0.93,
        "is_confirmed": false,
        "include_in_calculation": true
      },
      {
        "field_id": "bearing_capacity_characteristic_kpa",
        "name": "Bearing capacity characteristic",
        "candidate_value": 180,
        "unit": "kPa",
        "source_document_id": "project-description",
        "page_or_section": "source text",
        "quote": "地基承载力特征值fak=180kPa",
        "confidence": 0.9,
        "is_confirmed": false,
        "include_in_calculation": true
      }
    ],
    "document_versions": [],
    "missing_document_keys": ["calculation_report"],
    "notes": []
  },
  "pv-cn-no-specific-values-010": {
    "project_id": "pv-cn-no-specific-values-010",
    "schema_version": "phase2-agent-contracts-v1",
    "requires_engineer_review": true,
    "agent_role": "document_intake",
    "extracted_fields": [
      {
        "field_id": "steel_grade",
        "name": "Steel grade",
        "candidate_value": "Q355B",
        "unit": null,
        "source_document_id": "design-note",
        "page_or_section": "source text",
        "quote": "设计说明称支架、基础和连接均满足现行规范要求",
        "confidence": 0.2,
        "is_confirmed": false,
        "include_in_calculation": false
      }
    ],
    "document_versions": [],
    "missing_document_keys": ["calculation_report"],
    "notes": ["Intentional flawed output for hallucination scoring."]
  }
}
```

Fill cases 2 through 9 with the expected fields from `bv_agent_extraction_cases.json`, using `source_document_id`, `page_or_section`, and `quote` values that cite the relevant source-text phrase. Keep `is_confirmed` false for all extracted fields.

- [ ] **Step 4: Implement output loading and aggregation**

Add to `agent_extraction_eval.py`:

```python
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


def load_mock_document_intake_outputs(path: Path) -> dict[str, DocumentIntakeAgentOutput]:
    raw_outputs = json.loads(path.read_text(encoding="utf-8"))
    return {
        case_id: DocumentIntakeAgentOutput.model_validate(raw_output)
        for case_id, raw_output in raw_outputs.items()
    }


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


def _average(values: object) -> float:
    materialized = list(values)
    if not materialized:
        return 1.0
    return sum(materialized) / len(materialized)
```

- [ ] **Step 5: Run aggregate tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_agent_extraction_eval.py -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/structural_screening_agent/bv_review/agent_extraction_eval.py tests/fixtures/bv_agent_extraction_outputs.json tests/test_bv_review_agent_extraction_eval.py
git commit -m "feat: aggregate agent extraction eval metrics"
```

## Task 4: Export Public API and Synchronize Product Docs

**Files:**
- Modify: `src/structural_screening_agent/bv_review/__init__.py`
- Modify: `docs/bv-pv-design-review-workbench-roadmap.md`
- Modify: `docs/bv-jd-feature-mapping.md`
- Modify: `tests/test_bv_jd_feature_mapping.py`
- Modify: `tests/test_bv_review_agent_extraction_eval.py`

- [ ] **Step 1: Write failing public API and docs tests**

Append to `tests/test_bv_review_agent_extraction_eval.py`:

```python
from structural_screening_agent.bv_review import (
    AgentExtractionCase,
    AgentExtractionCaseScore,
    AgentExtractionEvaluationSummary,
    ExpectedExtractedField,
)


def test_agent_extraction_eval_models_are_publicly_exported() -> None:
    assert AgentExtractionCase is not None
    assert AgentExtractionCaseScore is not None
    assert AgentExtractionEvaluationSummary is not None
    assert ExpectedExtractedField is not None
```

Modify `tests/test_bv_jd_feature_mapping.py` by adding this phrase to the `completed_phrase` loop:

```python
"agent extraction reliability evaluation",
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_agent_extraction_eval.py tests/test_bv_jd_feature_mapping.py -p no:cacheprovider
```

Expected: FAIL until exports and docs are updated.

- [ ] **Step 3: Export evaluation API**

Modify `src/structural_screening_agent/bv_review/__init__.py`:

```python
from structural_screening_agent.bv_review.agent_extraction_eval import (
    AgentExtractionCase,
    AgentExtractionCaseScore,
    AgentExtractionEvaluationSummary,
    ExpectedExtractedField,
    build_extraction_eval_markdown_summary,
    evaluate_document_intake_output,
    evaluate_extraction_case_outputs,
    load_extraction_cases,
    load_mock_document_intake_outputs,
)
```

Add the same names to `__all__`.

- [ ] **Step 4: Update roadmap**

Add under Phase 5 implemented or active work:

```markdown
- agent extraction reliability evaluation for offline scoring of `DocumentIntakeAgentOutput` against curated PV review golden cases, including field recall, field precision, value accuracy, unit accuracy, evidence completeness, missing-document accuracy, no-hallucination rate, and calculation-readiness accuracy.
```

- [ ] **Step 5: Update JD mapping**

In `docs/bv-jd-feature-mapping.md`, update:

- Document review row: mention tested extraction reliability for submitted documents and calculation snippets.
- Quality system row: mention measurable Agent extraction reliability metrics.
- Standards/application row: mention future extension for standards extraction while keeping first version focused on Document Intake.
- Current coverage summary: add one numbered item:

```markdown
14. Agent 抽取可靠性评测：agent extraction reliability evaluation 用 curated golden cases 衡量资料参数抽取、单位、证据、缺失资料和反幻觉表现。
```

- [ ] **Step 6: Run docs and API tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_agent_extraction_eval.py tests/test_bv_jd_feature_mapping.py -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/structural_screening_agent/bv_review/__init__.py docs/bv-pv-design-review-workbench-roadmap.md docs/bv-jd-feature-mapping.md tests/test_bv_jd_feature_mapping.py tests/test_bv_review_agent_extraction_eval.py
git commit -m "docs: align agent extraction reliability eval"
```

## Task 5: Final Verification and Cleanliness Check

**Files:**
- No new implementation files beyond Tasks 1-4.

- [ ] **Step 1: Run focused tests**

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_bv_review_agent_extraction_eval.py tests/test_bv_jd_feature_mapping.py -p no:cacheprovider
```

Expected: PASS.

- [ ] **Step 2: Run app import smoke check**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c "import app; print('app import ok')"
```

Expected: Streamlit bare-mode warnings may appear, and the final line must include `app import ok`.

- [ ] **Step 3: Run full test suite**

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider
```

Expected: PASS with the updated total test count.

- [ ] **Step 4: Check protected core was not touched**

```bash
git diff --name-only -- src/structural_screening_agent/core src/structural_screening_agent/core/portal_frame.py src/structural_screening_agent/core/calculators
```

Expected: no output.

- [ ] **Step 5: Check whitespace and staged status**

```bash
git diff --check
git status --short --branch
```

Expected: no whitespace errors. Before final commit, status should show only intended modified/new files.

- [ ] **Step 6: Final commit if verification changed docs or tests**

If any verification-driven correction was made after Task 4:

```bash
git add src/structural_screening_agent/bv_review/agent_extraction_eval.py src/structural_screening_agent/bv_review/__init__.py tests/fixtures/bv_agent_extraction_cases.json tests/fixtures/bv_agent_extraction_outputs.json tests/test_bv_review_agent_extraction_eval.py docs/bv-pv-design-review-workbench-roadmap.md docs/bv-jd-feature-mapping.md tests/test_bv_jd_feature_mapping.py
git commit -m "test: verify agent extraction reliability eval"
```

- [ ] **Step 7: Push**

```bash
git push origin main
```

Expected: `main -> main` on the GitHub remote.

## Self-Review Checklist

- The plan is offline-first and does not require API keys.
- The plan uses existing `DocumentIntakeAgentOutput` and `ExtractedField` contracts.
- The plan does not change portal-frame or core screening behavior.
- The plan has explicit tests before implementation steps.
- The plan includes fixture paths and exact verification commands.
- The plan includes documentation synchronization so the portfolio story stays aligned with tested behavior.
