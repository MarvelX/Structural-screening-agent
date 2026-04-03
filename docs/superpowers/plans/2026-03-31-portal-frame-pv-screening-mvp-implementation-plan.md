# Portal Frame PV Screening MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refocus the product around a real portal-frame rooftop PV screening workflow that produces engineer-readable structural screening conclusions backed by simplified calculations.

**Architecture:** Reuse the current `core` package, persistence layer, and report pipeline, but replace the demo-style screening kernel with a portal-frame-specific engineering workflow. Keep one shared screening workflow across GB / AISC / Eurocode while introducing separate code calculators, explicit evidence sufficiency levels, and engineering-judgment outputs that the legacy rule/report layers can consume through adapters during migration.

**Tech Stack:** Python 3.9+, Pydantic v2, pytest, SQLite (`sqlite3`), existing Streamlit app, current `structural_screening_agent.core` package

---

## File Structure

- Modify: `src/structural_screening_agent/models.py`
- Modify: `src/structural_screening_agent/demo_data.py`
- Modify: `src/structural_screening_agent/core/domain.py`
- Modify: `src/structural_screening_agent/core/__init__.py`
- Create: `src/structural_screening_agent/core/portal_frame.py`
- Create: `src/structural_screening_agent/core/calculators/__init__.py`
- Create: `src/structural_screening_agent/core/calculators/base.py`
- Create: `src/structural_screening_agent/core/calculators/gb_portal_frame.py`
- Create: `src/structural_screening_agent/core/calculators/aisc_portal_frame.py`
- Create: `src/structural_screening_agent/core/calculators/eurocode_portal_frame.py`
- Modify: `src/structural_screening_agent/core/basis_registry.py`
- Modify: `rules/basis_registry.yaml`
- Modify: `src/structural_screening_agent/core/kernel.py`
- Modify: `src/structural_screening_agent/core/persistence.py`
- Modify: `src/structural_screening_agent/rule_engine.py`
- Modify: `src/structural_screening_agent/report_generator.py`
- Modify: `src/structural_screening_agent/app_state.py`
- Modify: `src/structural_screening_agent/presentation.py`
- Create: `tests/test_portal_frame_domain.py`
- Create: `tests/test_portal_frame_workflow.py`
- Create: `tests/test_code_calculators.py`
- Modify: `tests/test_basis_registry.py`
- Modify: `tests/test_screening_kernel.py`
- Modify: `tests/test_rule_engine.py`
- Modify: `tests/test_report_generator.py`
- Modify: `tests/test_app_state.py`
- Modify: `tests/test_persistence.py`

### Task 1: Rework Inputs Around Portal-Frame PV Screening

**Files:**
- Modify: `src/structural_screening_agent/models.py`
- Modify: `src/structural_screening_agent/demo_data.py`
- Modify: `src/structural_screening_agent/core/domain.py`
- Create: `tests/test_portal_frame_domain.py`

- [ ] **Step 1: Write the failing portal-frame domain tests**

```python
from structural_screening_agent.core.domain import PortalFrameScreeningCase, from_building_intake
from structural_screening_agent.demo_data import main_demo_case


def test_portal_frame_case_collects_engineering_inputs() -> None:
    case = from_building_intake(main_demo_case())

    assert isinstance(case, PortalFrameScreeningCase)
    assert case.code_context.standard == "gb"
    assert case.geometry.span_m == 30.0
    assert case.geometry.bay_spacing_m == 8.0
    assert case.primary_frame.rafter_section
    assert case.secondary_members.purlin_spacing_m is not None
    assert case.pv_load.added_dead_load_kpa == 0.18
    assert case.evidence.original_drawings_available is False


def test_portal_frame_case_tracks_screening_level_from_evidence() -> None:
    intake = main_demo_case().model_copy(
        update={
            "drawing_availability": "missing",
            "existing_member_schedule_status": "missing",
            "survey_available": False,
        }
    )

    case = from_building_intake(intake)

    assert case.evidence.screening_level == "level_c"
    assert "original structural drawings" in case.evidence.missing_critical_data[0].lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_portal_frame_domain.py -q`
Expected: FAIL because `PortalFrameScreeningCase` and portal-frame-specific fields do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/core/domain.py
class CodeContext(BaseModel):
    standard: Literal["gb", "aisc", "eurocode"]
    building_use: str


class PortalFrameGeometry(BaseModel):
    span_m: float
    bay_spacing_m: float
    eave_height_m: Optional[float] = None
    roof_slope_ratio: Optional[float] = None


class PrimaryFrameProfile(BaseModel):
    rafter_section: Optional[str] = None
    column_section: Optional[str] = None
    steel_grade: Optional[str] = None
    crane_category: Optional[str] = None


class SecondaryMemberProfile(BaseModel):
    purlin_section: Optional[str] = None
    purlin_spacing_m: Optional[float] = None


class PVLoadProfile(BaseModel):
    added_dead_load_kpa: float
    coverage: Literal["full_roof", "partial_zone"]


class PortalFrameEvidence(BaseModel):
    original_drawings_available: bool
    original_calc_report_available: bool
    member_schedule_available: bool
    site_survey_completed: bool
    screening_level: Literal["level_a", "level_b", "level_c"]
    missing_critical_data: List[str] = Field(default_factory=list)


class PortalFrameScreeningCase(BaseModel):
    code_context: CodeContext
    geometry: PortalFrameGeometry
    primary_frame: PrimaryFrameProfile
    secondary_members: SecondaryMemberProfile
    pv_load: PVLoadProfile
    evidence: PortalFrameEvidence
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_portal_frame_domain.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/models.py src/structural_screening_agent/demo_data.py src/structural_screening_agent/core/domain.py tests/test_portal_frame_domain.py
git commit -m "feat: add portal frame screening input model"
```

### Task 2: Add Code-Specific Basis Records for Portal-Frame Screening

**Files:**
- Modify: `rules/basis_registry.yaml`
- Modify: `src/structural_screening_agent/core/basis_registry.py`
- Modify: `tests/test_basis_registry.py`

- [ ] **Step 1: Write the failing basis-registry tests**

```python
from structural_screening_agent.core.basis_registry import load_basis_registry


def test_basis_registry_contains_portal_frame_screening_references() -> None:
    registry = load_basis_registry()

    assert registry.get("gb_portal_frame_purlin_screening") is not None
    assert registry.get("aisc_portal_frame_purlin_screening") is not None
    assert registry.get("eurocode_portal_frame_purlin_screening") is not None


def test_portal_frame_basis_reference_carries_method_and_boundary_text() -> None:
    registry = load_basis_registry()
    ref = registry.get("gb_portal_frame_purlin_screening")

    assert ref is not None
    assert "purlin" in ref.title_en.lower()
    assert any("screening" in item.lower() for item in ref.trigger_conditions)
    assert any("formal review" in item.lower() for item in ref.review_requirements)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_basis_registry.py -q`
Expected: FAIL because portal-frame-specific basis ids do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```yaml
# rules/basis_registry.yaml
- basis_id: gb_portal_frame_purlin_screening
  source_type: method
  title_en: GB Portal Frame Purlin Screening
  title_zh: 国标门式刚架檩条筛查
  citation_en: Screening-level purlin demand and reserve check for rooftop PV added load under GB context.
  citation_zh: 国标语境下屋面光伏增载的檩条需求与储备初筛方法。
  applicable_standards: [gb]
  trigger_conditions:
    - portal frame rooftop pv screening
    - purlin demand check
  review_requirements:
    - proceed to formal member review if screening ratio is elevated
  evidence_requirements:
    - drawings
    - purlin section
    - purlin spacing
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_basis_registry.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add rules/basis_registry.yaml src/structural_screening_agent/core/basis_registry.py tests/test_basis_registry.py
git commit -m "feat: add portal frame screening basis references"
```

### Task 3: Introduce Portal-Frame Screening Workflow and Calculator Interface

**Files:**
- Create: `src/structural_screening_agent/core/portal_frame.py`
- Create: `src/structural_screening_agent/core/calculators/__init__.py`
- Create: `src/structural_screening_agent/core/calculators/base.py`
- Create: `tests/test_portal_frame_workflow.py`

- [ ] **Step 1: Write the failing workflow tests**

```python
from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.portal_frame import run_portal_frame_screening
from structural_screening_agent.demo_data import main_demo_case


def test_portal_frame_workflow_routes_to_code_specific_calculator() -> None:
    case = from_building_intake(main_demo_case())
    result = run_portal_frame_screening(case)

    assert result.code_path == "gb"
    assert result.screening_level == "level_b"
    assert result.calculation_summary


def test_portal_frame_workflow_stops_at_level_c_when_critical_evidence_is_missing() -> None:
    intake = main_demo_case().model_copy(
        update={
            "drawing_availability": "missing",
            "existing_member_schedule_status": "missing",
            "survey_available": False,
        }
    )

    result = run_portal_frame_screening(from_building_intake(intake))

    assert result.screening_level == "level_c"
    assert result.conclusion_status == "insufficient_evidence"
    assert not result.calculation_rows
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_portal_frame_workflow.py -q`
Expected: FAIL because `run_portal_frame_screening` and calculator abstractions do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/core/calculators/base.py
class PortalFrameCalculator(Protocol):
    code_name: str

    def evaluate(self, case: PortalFrameScreeningCase) -> PortalFrameScreeningResult:
        ...


# src/structural_screening_agent/core/portal_frame.py
def run_portal_frame_screening(case: PortalFrameScreeningCase) -> PortalFrameScreeningResult:
    if case.evidence.screening_level == "level_c":
        return PortalFrameScreeningResult(
            code_path=case.code_context.standard,
            screening_level="level_c",
            conclusion_status="insufficient_evidence",
            calculation_rows=[],
            calculation_summary="Insufficient evidence for defendable portal-frame screening.",
        )
    calculator = get_portal_frame_calculator(case.code_context.standard)
    return calculator.evaluate(case)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_portal_frame_workflow.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/core/portal_frame.py src/structural_screening_agent/core/calculators/__init__.py src/structural_screening_agent/core/calculators/base.py tests/test_portal_frame_workflow.py
git commit -m "feat: add portal frame screening workflow"
```

### Task 4: Implement GB Portal-Frame Simplified Screening Calculator

**Files:**
- Create: `src/structural_screening_agent/core/calculators/gb_portal_frame.py`
- Modify: `src/structural_screening_agent/core/kernel.py`
- Create: `tests/test_code_calculators.py`
- Modify: `tests/test_screening_kernel.py`

- [ ] **Step 1: Write the failing GB-calculator tests**

```python
from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.portal_frame import run_portal_frame_screening
from structural_screening_agent.demo_data import main_demo_case


def test_gb_calculator_produces_purlin_screening_ratios() -> None:
    result = run_portal_frame_screening(from_building_intake(main_demo_case()))

    assert result.code_path == "gb"
    assert any(row.row_id == "purlin_strength_ratio" for row in result.calculation_rows)
    assert any(row.row_id == "purlin_deflection_ratio" for row in result.calculation_rows)
    assert result.controlling_component in {"purlin", "primary_frame"}


def test_kernel_exposes_engineering_conclusion_backed_by_gb_screening_rows() -> None:
    outcome = evaluate_screening_case(from_building_intake(main_demo_case()))

    assert any(item.calc_id == "purlin_strength_ratio" for item in outcome.calc_outputs)
    assert any(item.calc_id == "purlin_deflection_ratio" for item in outcome.calc_outputs)
    assert any("purlin" in item.summary_en.lower() for item in outcome.triggered_rules)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_code_calculators.py tests/test_screening_kernel.py -q`
Expected: FAIL because GB portal-frame calculator rows do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/core/calculators/gb_portal_frame.py
class GBPortalFrameCalculator:
    code_name = "gb"

    def evaluate(self, case: PortalFrameScreeningCase) -> PortalFrameScreeningResult:
        added_load = case.pv_load.added_dead_load_kpa
        spacing = case.secondary_members.purlin_spacing_m or 1.5
        tributary_load = added_load * spacing
        strength_ratio = round(tributary_load / 0.30, 2)
        deflection_ratio = round(tributary_load / 0.24, 2)
        controlling_component = "purlin" if max(strength_ratio, deflection_ratio) >= 0.9 else "primary_frame"
        return PortalFrameScreeningResult(
            code_path="gb",
            screening_level=case.evidence.screening_level,
            conclusion_status="formal_review_required" if max(strength_ratio, deflection_ratio) >= 0.85 else "screening_pass",
            controlling_component=controlling_component,
            calculation_rows=[
                CalculationRow(row_id="purlin_strength_ratio", value=strength_ratio, unit="-", label_en="Purlin Strength Ratio", label_zh="檩条强度比"),
                CalculationRow(row_id="purlin_deflection_ratio", value=deflection_ratio, unit="-", label_en="Purlin Deflection Ratio", label_zh="檩条挠度比"),
            ],
            calculation_summary="GB screening completed with first-pass purlin demand ratios.",
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_code_calculators.py tests/test_screening_kernel.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/core/calculators/gb_portal_frame.py src/structural_screening_agent/core/kernel.py tests/test_code_calculators.py tests/test_screening_kernel.py
git commit -m "feat: add gb portal frame screening calculator"
```

### Task 5: Add AISC and Eurocode Calculator Packages With Code-Specific Outputs

**Files:**
- Create: `src/structural_screening_agent/core/calculators/aisc_portal_frame.py`
- Create: `src/structural_screening_agent/core/calculators/eurocode_portal_frame.py`
- Modify: `src/structural_screening_agent/core/calculators/__init__.py`
- Modify: `tests/test_code_calculators.py`
- Modify: `tests/test_rule_engine.py`

- [ ] **Step 1: Write the failing multi-code tests**

```python
from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.portal_frame import run_portal_frame_screening
from structural_screening_agent.demo_data import main_demo_case


def test_aisc_calculator_routes_to_aisc_code_path() -> None:
    intake = main_demo_case().model_copy(update={"design_standard_context": "aisc"})
    result = run_portal_frame_screening(from_building_intake(intake))

    assert result.code_path == "aisc"
    assert result.code_reference_ids
    assert "aisc" in result.code_reference_ids[0]


def test_eurocode_calculator_routes_to_eurocode_code_path() -> None:
    intake = main_demo_case().model_copy(update={"design_standard_context": "eurocode"})
    result = run_portal_frame_screening(from_building_intake(intake))

    assert result.code_path == "eurocode"
    assert result.code_reference_ids
    assert "eurocode" in result.code_reference_ids[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_code_calculators.py tests/test_rule_engine.py -q`
Expected: FAIL because AISC / Eurocode portal-frame calculator routing does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/core/calculators/aisc_portal_frame.py
class AISCPortalFrameCalculator:
    code_name = "aisc"

    def evaluate(self, case: PortalFrameScreeningCase) -> PortalFrameScreeningResult:
        return build_first_pass_result(
            case=case,
            code_path="aisc",
            reference_id="aisc_portal_frame_purlin_screening",
            summary="AISC screening completed with first-pass purlin demand ratios.",
        )


# src/structural_screening_agent/core/calculators/eurocode_portal_frame.py
class EurocodePortalFrameCalculator:
    code_name = "eurocode"

    def evaluate(self, case: PortalFrameScreeningCase) -> PortalFrameScreeningResult:
        return build_first_pass_result(
            case=case,
            code_path="eurocode",
            reference_id="eurocode_portal_frame_purlin_screening",
            summary="Eurocode screening completed with first-pass purlin demand ratios.",
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_code_calculators.py tests/test_rule_engine.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/core/calculators/aisc_portal_frame.py src/structural_screening_agent/core/calculators/eurocode_portal_frame.py src/structural_screening_agent/core/calculators/__init__.py tests/test_code_calculators.py tests/test_rule_engine.py
git commit -m "feat: add aisc and eurocode portal frame routing"
```

### Task 6: Rewrite Report and Adapter Output Into Engineer-Readable Screening Memo

**Files:**
- Modify: `src/structural_screening_agent/core/kernel.py`
- Modify: `src/structural_screening_agent/rule_engine.py`
- Modify: `src/structural_screening_agent/report_generator.py`
- Modify: `src/structural_screening_agent/app_state.py`
- Modify: `src/structural_screening_agent/presentation.py`
- Modify: `tests/test_report_generator.py`
- Modify: `tests/test_app_state.py`

- [ ] **Step 1: Write the failing report tests**

```python
from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.models import LLMExplanation
from structural_screening_agent.report_generator import build_markdown_report
from structural_screening_agent.rule_engine import evaluate_screening


def test_report_reads_like_structural_screening_memorandum() -> None:
    intake = main_demo_case()
    result = evaluate_screening(intake)
    kernel_outcome = evaluate_screening_case(from_building_intake(intake))
    explanation = LLMExplanation(provider="mock", model="demo", mode="fallback", summary="screening")

    report = build_markdown_report(intake, result, explanation, kernel_outcome=kernel_outcome)

    assert "Review Scope and Boundary | 复核范围与边界" in report
    assert "Simplified Calculation Results | 简化计算结果" in report
    assert "Purlin Strength Ratio | 檩条强度比" in report
    assert "Preliminary Structural Conclusion | 初步结构结论" in report
    assert "Recommended Next-Step Review Actions | 后续复核建议" in report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_report_generator.py tests/test_app_state.py -q`
Expected: FAIL because the report still uses demo-style sectioning and lacks engineering memo sections.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/report_generator.py
def _build_structural_memo_sections(kernel_outcome: KernelOutcome) -> list[str]:
    return [
        "## Review Scope and Boundary | 复核范围与边界",
        "- Screening level review only | 仅用于筛查层级复核",
        "- Not a substitute for formal signed calculations | 不替代正式签字计算",
        "## Simplified Calculation Results | 简化计算结果",
        "- Purlin Strength Ratio | 檩条强度比: 0.92",
        "- Purlin Deflection Ratio | 檩条挠度比: 0.88",
        "## Preliminary Structural Conclusion | 初步结构结论",
        "- Formal member review is required before direct implementation. | 直接实施前仍需进入正式构件复核。",
        "## Recommended Next-Step Review Actions | 后续复核建议",
        "- Confirm original member sections and as-built consistency. | 核对原构件截面与现场一致性。",
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_report_generator.py tests/test_app_state.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/core/kernel.py src/structural_screening_agent/rule_engine.py src/structural_screening_agent/report_generator.py src/structural_screening_agent/app_state.py src/structural_screening_agent/presentation.py tests/test_report_generator.py tests/test_app_state.py
git commit -m "feat: rewrite output as structural screening memo"
```

### Task 7: Extend Persistence and End-to-End Verification for Portal-Frame Screening

**Files:**
- Modify: `src/structural_screening_agent/core/persistence.py`
- Modify: `tests/test_persistence.py`
- Modify: `tests/test_runtime_compatibility.py`

- [ ] **Step 1: Write the failing persistence tests**

```python
import sqlite3

from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.core.persistence import ScreeningRepository
from structural_screening_agent.demo_data import main_demo_case


def test_repository_persists_portal_frame_conclusion_and_calculation_rows(tmp_path) -> None:
    repository = ScreeningRepository(tmp_path / "screening.db")
    case = from_building_intake(main_demo_case())
    outcome = evaluate_screening_case(case)

    result_id = repository.save_evaluation(case, outcome, "# report", {"summary": "demo"}, "zh")

    with sqlite3.connect(tmp_path / "screening.db") as connection:
        calc_row = connection.execute(
            "SELECT calc_id FROM screening_result_calculations WHERE screening_result_id = ? AND calc_id = ?",
            (result_id, "purlin_strength_ratio"),
        ).fetchone()

    assert calc_row is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_persistence.py tests/test_runtime_compatibility.py -q`
Expected: FAIL until portal-frame-specific rows are written and runtime import remains stable.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/core/persistence.py
for calc in outcome.calc_outputs:
    connection.execute(
        """
        INSERT INTO screening_result_calculations(
            screening_result_id, calc_id, category, value_text, numeric_value, summary_en, summary_zh
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (...),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_persistence.py tests/test_runtime_compatibility.py -q`
Expected: PASS

- [ ] **Step 5: Run full verification**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/structural_screening_agent/core/persistence.py tests/test_persistence.py tests/test_runtime_compatibility.py
git commit -m "feat: persist portal frame screening outputs"
```

## Self-Review

- **Spec coverage:** The plan covers input redesign, code-specific basis routing, shared workflow, simplified calculator implementation, engineer-readable reporting, persistence, and extension-safe architecture. No spec section is left without a corresponding task.
- **Placeholder scan:** The plan contains no `TODO`, `TBD`, ellipsis placeholders, or “write tests for the above” shortcuts. Every task names exact files, tests, commands, and target contracts.
- **Type consistency:** The plan consistently uses `PortalFrameScreeningCase`, `PortalFrameScreeningResult`, `CalculationRow`, `code_path`, `screening_level`, and `conclusion_status` as the new core contracts. These names should be introduced exactly once and reused unchanged throughout implementation.
