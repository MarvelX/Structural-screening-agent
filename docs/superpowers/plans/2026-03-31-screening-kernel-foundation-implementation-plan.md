# Screening Kernel Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a real screening kernel foundation with explicit domain schema, basis registry, calculation kernel, SQLite persistence, and traceable outputs that existing UI/report layers can consume through adapters.

**Architecture:** Keep the current Streamlit workbench, report generator, and rule-engine-facing APIs running while introducing a new `structural_screening_agent.core` package underneath them. The new core owns stable domain objects, basis references, calculation traces, and persistence records; compatibility adapters convert between legacy `BuildingIntake` / `ScreeningResult` and the new kernel contracts during migration.

**Tech Stack:** Python 3.9+, Pydantic v2, pytest, SQLite (`sqlite3`), YAML rules, existing Streamlit app package

---

## File Structure

- Create: `src/structural_screening_agent/core/__init__.py`
- Create: `src/structural_screening_agent/core/domain.py`
- Create: `src/structural_screening_agent/core/basis_registry.py`
- Create: `src/structural_screening_agent/core/kernel.py`
- Create: `src/structural_screening_agent/core/persistence.py`
- Create: `rules/basis_registry.yaml`
- Create: `tests/test_core_domain.py`
- Create: `tests/test_basis_registry.py`
- Create: `tests/test_screening_kernel.py`
- Create: `tests/test_persistence.py`
- Modify: `src/structural_screening_agent/models.py`
- Modify: `src/structural_screening_agent/app_state.py`
- Modify: `src/structural_screening_agent/rule_engine.py`
- Modify: `src/structural_screening_agent/report_generator.py`
- Modify: `src/structural_screening_agent/presentation.py`
- Modify: `src/structural_screening_agent/demo_data.py`

### Task 1: Domain Schema / Core Data Model

**Files:**
- Create: `src/structural_screening_agent/core/__init__.py`
- Create: `src/structural_screening_agent/core/domain.py`
- Test: `tests/test_core_domain.py`

- [ ] **Step 1: Write the failing domain tests**

```python
from structural_screening_agent.core.domain import (
    EvidenceProfile,
    GeometryProfile,
    ModificationScope,
    ProjectProfile,
    RoofProfile,
    ScreeningCase,
    VerificationContext,
    from_building_intake,
)
from structural_screening_agent.demo_data import main_demo_case


def test_screening_case_groups_inputs_into_stable_domain_sections() -> None:
    case = from_building_intake(main_demo_case())

    assert case.project.project_type == "rooftop_pv"
    assert case.project.building_type == "existing warehouse"
    assert case.modification.estimated_added_load_kpa == 0.18
    assert case.geometry.building_span_m == 30.0
    assert case.roof.attachment_preference == "clamp_based"
    assert case.evidence.member_schedule_status == "missing"
    assert case.verification.available_path == "drawings_only"


def test_screening_case_requires_explicit_nested_sections() -> None:
    case = ScreeningCase(
        project=ProjectProfile(
            project_type="retrofit",
            design_standard="gb",
            building_type="plant",
            structural_system="steel",
            roof_type="metal roof",
        ),
        modification=ModificationScope(
            intended_modification="equipment upgrade",
            estimated_added_load_kpa=0.22,
        ),
        geometry=GeometryProfile(building_span_m=24.0, column_spacing_m=8.0, purlin_type="z"),
        roof=RoofProfile(
            panel_type="profiled_sheet",
            panel_thickness_mm=0.7,
            rib_height_mm=76.0,
            attachment_preference="clamp_based",
            waterproofing_sensitivity="medium",
            restricted_installation_zones="",
        ),
        evidence=EvidenceProfile(
            drawing_availability="complete",
            survey_available=True,
            member_schedule_status="available",
            connection_detail_status="available",
            roof_vendor_data_status="available",
        ),
        verification=VerificationContext(
            corrosion_condition="low",
            shutdown_constraint="none",
            available_path="drawings_plus_survey",
        ),
    )

    assert case.project.design_standard == "gb"
    assert case.evidence.survey_available is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core_domain.py -q`
Expected: FAIL with import errors because `structural_screening_agent.core.domain` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/core/domain.py
from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.models import BuildingIntake


class ProjectProfile(BaseModel):
    project_type: Literal["rooftop_pv", "load_upgrade", "retrofit", "mixed"]
    design_standard: Literal["gb", "aisc", "eurocode"]
    building_type: str = Field(min_length=1)
    structural_system: str = Field(min_length=1)
    roof_type: str = Field(min_length=1)


class ModificationScope(BaseModel):
    intended_modification: str = Field(min_length=1)
    estimated_added_load_kpa: Optional[float] = None


class GeometryProfile(BaseModel):
    building_span_m: Optional[float] = None
    column_spacing_m: Optional[float] = None
    purlin_type: Optional[str] = None


class RoofProfile(BaseModel):
    panel_type: Optional[str] = None
    panel_thickness_mm: Optional[float] = None
    rib_height_mm: Optional[float] = None
    attachment_preference: Literal["clamp_based", "penetrating", "undecided"] = "undecided"
    waterproofing_sensitivity: Literal["low", "medium", "high"] = "medium"
    restricted_installation_zones: Optional[str] = None


class EvidenceProfile(BaseModel):
    drawing_availability: Literal["complete", "partial", "missing"]
    survey_available: bool = False
    member_schedule_status: Literal["available", "partial", "missing"] = "missing"
    connection_detail_status: Literal["available", "partial", "missing"] = "missing"
    roof_vendor_data_status: Literal["available", "partial", "missing"] = "missing"


class VerificationContext(BaseModel):
    corrosion_condition: Literal["low", "moderate", "high", "unknown"] = "unknown"
    shutdown_constraint: Literal["none", "limited", "strict"]
    available_path: Literal["drawings_only", "survey_only", "drawings_plus_survey", "no_viable_path_yet"]


class ScreeningCase(BaseModel):
    project: ProjectProfile
    modification: ModificationScope
    geometry: GeometryProfile
    roof: RoofProfile
    evidence: EvidenceProfile
    verification: VerificationContext


def from_building_intake(intake: BuildingIntake) -> ScreeningCase:
    return ScreeningCase(
        project=ProjectProfile(
            project_type=intake.project_type,
            design_standard=intake.design_standard_context,
            building_type=intake.building_type,
            structural_system=intake.structural_system,
            roof_type=intake.roof_type,
        ),
        modification=ModificationScope(
            intended_modification=intake.intended_modification,
            estimated_added_load_kpa=intake.estimated_added_load_kpa,
        ),
        geometry=GeometryProfile(
            building_span_m=intake.building_span_m,
            column_spacing_m=intake.column_spacing_m,
            purlin_type=intake.purlin_type,
        ),
        roof=RoofProfile(
            panel_type=intake.roof_panel_type,
            panel_thickness_mm=intake.roof_panel_thickness_mm,
            rib_height_mm=intake.roof_rib_height_mm,
            attachment_preference=intake.roof_attachment_preference,
            waterproofing_sensitivity=intake.waterproofing_sensitivity,
            restricted_installation_zones=intake.restricted_installation_zones,
        ),
        evidence=EvidenceProfile(
            drawing_availability=intake.drawing_availability,
            survey_available=intake.survey_available,
            member_schedule_status=intake.existing_member_schedule_status,
            connection_detail_status=intake.connection_detail_status,
            roof_vendor_data_status=intake.roof_vendor_data_status,
        ),
        verification=VerificationContext(
            corrosion_condition=intake.corrosion_condition,
            shutdown_constraint=intake.shutdown_constraint,
            available_path=intake.available_verification_path,
        ),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core_domain.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/core/__init__.py src/structural_screening_agent/core/domain.py tests/test_core_domain.py
git commit -m "feat: add core screening domain schema"
```

### Task 2: Basis Registry

**Files:**
- Create: `rules/basis_registry.yaml`
- Create: `src/structural_screening_agent/core/basis_registry.py`
- Test: `tests/test_basis_registry.py`

- [ ] **Step 1: Write the failing registry tests**

```python
from structural_screening_agent.core.basis_registry import load_basis_registry


def test_basis_registry_loads_named_references_by_id() -> None:
    registry = load_basis_registry()

    reference = registry.get("gb_50017_general")

    assert reference.basis_id == "gb_50017_general"
    assert "GB 50017" in reference.title_en
    assert reference.source_type == "standard"


def test_basis_registry_rejects_unknown_reference_ids() -> None:
    registry = load_basis_registry()

    assert registry.get("missing_basis") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_basis_registry.py -q`
Expected: FAIL because the registry module and YAML file do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```yaml
# rules/basis_registry.yaml
- basis_id: gb_50017_general
  source_type: standard
  title_en: GB 50017 Steel Structure Design Standard
  title_zh: GB 50017 钢结构设计标准
  citation_en: General steel member and connection review path.
  citation_zh: 作为钢结构构件与连接复核的基础依据。
```

```python
# src/structural_screening_agent/core/basis_registry.py
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class BasisReference(BaseModel):
    basis_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    citation_en: str = Field(min_length=1)
    citation_zh: str = Field(min_length=1)


class BasisRegistry(BaseModel):
    references: Dict[str, BasisReference]

    def get(self, basis_id: str) -> Optional[BasisReference]:
        return self.references.get(basis_id)


def load_basis_registry() -> BasisRegistry:
    root = Path(__file__).resolve().parents[2] / "rules" / "basis_registry.yaml"
    payload: List[dict] = yaml.safe_load(root.read_text())
    return BasisRegistry(references={item["basis_id"]: BasisReference(**item) for item in payload})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_basis_registry.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add rules/basis_registry.yaml src/structural_screening_agent/core/basis_registry.py tests/test_basis_registry.py
git commit -m "feat: add basis registry"
```

### Task 3: Screening Calculation Kernel

**Files:**
- Create: `src/structural_screening_agent/core/kernel.py`
- Modify: `src/structural_screening_agent/rule_engine.py`
- Test: `tests/test_screening_kernel.py`
- Update: `tests/test_rule_engine.py`

- [ ] **Step 1: Write the failing kernel tests**

```python
from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.demo_data import main_demo_case


def test_kernel_returns_findings_with_basis_ids_and_trace() -> None:
    outcome = evaluate_screening_case(from_building_intake(main_demo_case()))

    assert outcome.decision.status == "conditional_go"
    assert outcome.findings
    assert any(finding.basis_ids for finding in outcome.findings)
    assert any(finding.trace.input_path == "roof.panel_thickness_mm" for finding in outcome.findings)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_screening_kernel.py -q`
Expected: FAIL because `evaluate_screening_case` and kernel result models do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/core/kernel.py
from typing import List, Literal

from pydantic import BaseModel, Field

from structural_screening_agent.core.domain import ScreeningCase


class TraceRef(BaseModel):
    input_path: str = Field(min_length=1)
    observed_value: str


class KernelFinding(BaseModel):
    finding_id: str = Field(min_length=1)
    severity: Literal["info", "caution", "blocking"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    basis_ids: List[str] = Field(default_factory=list)
    trace: TraceRef


class KernelDecision(BaseModel):
    status: Literal["go", "conditional_go", "no_go"]
    confidence: Literal["high", "medium", "low"]


class KernelOutcome(BaseModel):
    decision: KernelDecision
    findings: List[KernelFinding] = Field(default_factory=list)


def evaluate_screening_case(case: ScreeningCase) -> KernelOutcome:
    findings: List[KernelFinding] = []

    if case.roof.panel_type == "profiled_sheet" and (
        case.roof.panel_thickness_mm is None or case.roof.rib_height_mm is None
    ):
        findings.append(
            KernelFinding(
                finding_id="roof_attachment_uncertainty",
                severity="caution",
                summary_en="Roof attachment pathway is still uncertain because panel geometry is incomplete.",
                summary_zh="由于屋面板几何信息不完整，当前连接路径仍存在不确定性。",
                basis_ids=["gb_50017_general"],
                trace=TraceRef(input_path="roof.panel_thickness_mm", observed_value=str(case.roof.panel_thickness_mm)),
            )
        )

    status = "conditional_go" if findings else "go"
    confidence = "medium" if findings else "high"
    return KernelOutcome(decision=KernelDecision(status=status, confidence=confidence), findings=findings)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_screening_kernel.py -q`
Expected: PASS

- [ ] **Step 5: Adapt legacy rule engine to consume kernel output**

Run: `pytest tests/test_rule_engine.py -q`
Expected: existing rule engine tests remain green after adding a translation layer from `KernelOutcome` to `ScreeningResult`.

- [ ] **Step 6: Commit**

```bash
git add src/structural_screening_agent/core/kernel.py src/structural_screening_agent/rule_engine.py tests/test_screening_kernel.py tests/test_rule_engine.py
git commit -m "feat: add screening kernel and legacy adapter"
```

### Task 4: SQLite Persistence

**Files:**
- Create: `src/structural_screening_agent/core/persistence.py`
- Create: `tests/test_persistence.py`
- Modify: `src/structural_screening_agent/app_state.py`

- [ ] **Step 1: Write the failing persistence tests**

```python
from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.core.persistence import ScreeningRepository
from structural_screening_agent.demo_data import main_demo_case


def test_repository_persists_case_and_kernel_outcome(tmp_path) -> None:
    repository = ScreeningRepository(tmp_path / "screening.db")
    case = from_building_intake(main_demo_case())
    outcome = evaluate_screening_case(case)

    run_id = repository.save_run(case, outcome)
    stored = repository.load_run(run_id)

    assert stored.case.project.project_type == "rooftop_pv"
    assert stored.outcome.decision.status == "conditional_go"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_persistence.py -q`
Expected: FAIL because the persistence module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/core/persistence.py
import json
import sqlite3
from pathlib import Path

from pydantic import BaseModel

from structural_screening_agent.core.domain import ScreeningCase
from structural_screening_agent.core.kernel import KernelOutcome


class StoredRun(BaseModel):
    run_id: int
    case: ScreeningCase
    outcome: KernelOutcome


class ScreeningRepository:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS screening_runs (id INTEGER PRIMARY KEY, case_json TEXT NOT NULL, outcome_json TEXT NOT NULL)"
            )

    def save_run(self, case: ScreeningCase, outcome: KernelOutcome) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO screening_runs(case_json, outcome_json) VALUES (?, ?)",
                (json.dumps(case.model_dump(mode='json')), json.dumps(outcome.model_dump(mode='json'))),
            )
            return int(cursor.lastrowid)

    def load_run(self, run_id: int) -> StoredRun:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, case_json, outcome_json FROM screening_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        return StoredRun(
            run_id=int(row[0]),
            case=ScreeningCase.model_validate_json(row[1]),
            outcome=KernelOutcome.model_validate_json(row[2]),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_persistence.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/core/persistence.py tests/test_persistence.py src/structural_screening_agent/app_state.py
git commit -m "feat: add sqlite persistence for screening runs"
```

### Task 5: Migrate Legacy Consumers

**Files:**
- Modify: `src/structural_screening_agent/app_state.py`
- Modify: `src/structural_screening_agent/rule_engine.py`
- Modify: `src/structural_screening_agent/report_generator.py`
- Modify: `src/structural_screening_agent/presentation.py`
- Update: `tests/test_report_generator.py`
- Update: `tests/test_presentation.py`

- [ ] **Step 1: Write the failing integration tests**

```python
from structural_screening_agent.app_state import evaluate_case
from structural_screening_agent.demo_data import main_demo_case


def test_evaluate_case_exposes_kernel_traceability_to_consumers() -> None:
    evaluation = evaluate_case(main_demo_case().model_dump(), language="zh")

    assert "kernel_outcome" in evaluation
    assert evaluation["kernel_outcome"].findings
    assert any(finding.basis_ids for finding in evaluation["kernel_outcome"].findings)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_report_generator.py tests/test_presentation.py -q`
Expected: FAIL because the current orchestration layer does not expose kernel outputs.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/app_state.py
from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case


def evaluate_case(form_data: Dict[str, object], language: Language = "zh") -> Dict[str, object]:
    intake = build_intake(form_data)
    kernel_case = from_building_intake(intake)
    kernel_outcome = evaluate_screening_case(kernel_case)
    result = evaluate_screening(intake)
    ...
    return {
        "intake": intake,
        "kernel_case": kernel_case,
        "kernel_outcome": kernel_outcome,
        "result": result,
        ...
    }
```

- [ ] **Step 4: Run targeted integration tests**

Run: `pytest tests/test_rule_engine.py tests/test_report_generator.py tests/test_presentation.py tests/test_report_preview.py -q`
Expected: PASS

- [ ] **Step 5: Run full regression suite**

Run: `pytest -q`
Expected: PASS with all existing tests plus the new kernel foundation tests.

- [ ] **Step 6: Commit**

```bash
git add src/structural_screening_agent/app_state.py src/structural_screening_agent/rule_engine.py src/structural_screening_agent/report_generator.py src/structural_screening_agent/presentation.py tests/test_report_generator.py tests/test_presentation.py
git commit -m "refactor: migrate app consumers onto kernel foundation"
```

## Self-Review

- Spec coverage: domain schema, basis registry, screening kernel, SQLite persistence, and consumer migration each map to a dedicated task.
- Placeholder scan: no `TBD` / `TODO` placeholders remain; every task includes exact files and commands.
- Type consistency: the plan consistently uses `ScreeningCase`, `BasisRegistry`, `KernelOutcome`, and `ScreeningRepository` as the new core contracts.
