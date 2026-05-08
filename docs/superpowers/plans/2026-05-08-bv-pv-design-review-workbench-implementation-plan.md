# BV PV Design Review Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first BV Review Mode backend slice: domain models, review basis, document checklist, structural review path, risk register, ITP/review plan, workflow orchestration, and BV-style report preview.

**Architecture:** Add a focused `structural_screening_agent.bv_review` package that does not modify the existing portal-frame kernel. The BV workflow composes new deterministic review objects and optionally embeds the existing rooftop added-load screening outcome when that review object is selected.

**Tech Stack:** Python 3.9+, Pydantic v2, pytest, existing report preview/export models.

---

## File Structure

- Create: `src/structural_screening_agent/bv_review/__init__.py`
  - Public package exports for the BV workflow.
- Create: `src/structural_screening_agent/bv_review/models.py`
  - Pydantic models for BV intake, basis references, checklist items, review paths, risks, ITP items, report sections, and workflow result.
- Create: `src/structural_screening_agent/bv_review/basis.py`
  - Deterministic basis builder keyed by standards system and review objects.
- Create: `src/structural_screening_agent/bv_review/checklist.py`
  - Document completeness checks and unavailable-review-item detection.
- Create: `src/structural_screening_agent/bv_review/review_path.py`
  - Structural review path generator for mounting structures, steel, concrete, foundations, connections, loads, and existing rooftop added load.
- Create: `src/structural_screening_agent/bv_review/review_plan.py`
  - ITP and design review plan generator.
- Create: `src/structural_screening_agent/bv_review/risk_register.py`
  - Risk and nonconformity register builder.
- Create: `src/structural_screening_agent/bv_review/report.py`
  - BV-style report preview composer.
- Create: `src/structural_screening_agent/bv_review/workflow.py`
  - Orchestrates all BV review builders and optional existing portal-frame screening integration.
- Create: `tests/test_bv_review_models.py`
  - Model contract tests.
- Create: `tests/test_bv_review_workflow.py`
  - Basis, checklist, path, risk, review plan, and workflow tests.
- Create: `tests/test_bv_review_report.py`
  - Report section and boundary statement tests.

## Task 1: BV Domain Models

**Files:**
- Create: `src/structural_screening_agent/bv_review/__init__.py`
- Create: `src/structural_screening_agent/bv_review/models.py`
- Create: `tests/test_bv_review_models.py`

- [x] **Step 1: Write the failing model tests**

Add `tests/test_bv_review_models.py`:

```python
import pytest
from pydantic import ValidationError

from structural_screening_agent.bv_review.models import (
    BVDocumentStatus,
    BVReviewIntake,
)


def test_bv_review_intake_captures_project_standards_objects_and_documents() -> None:
    intake = BVReviewIntake(
        project_name="Hebei rooftop PV design review",
        country_or_region="China",
        project_type="rooftop_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "existing_rooftop_added_load"],
        client_requirements=["BV-style independent design review report"],
        documents={
            "structural_drawings": "partial",
            "calculation_report": "missing",
            "technical_specification": "available",
            "geotechnical_report": "missing",
            "vendor_datasheets": "partial",
            "contract_requirements": "available",
        },
    )

    assert intake.project_name == "Hebei rooftop PV design review"
    assert "gb" in intake.standards_systems
    assert "existing_rooftop_added_load" in intake.review_objects
    assert intake.documents["calculation_report"] == "missing"


def test_bv_review_intake_rejects_empty_standards_and_objects() -> None:
    with pytest.raises(ValidationError):
        BVReviewIntake(
            project_name="Invalid review",
            country_or_region="China",
            project_type="rooftop_pv",
            design_stage="tender",
            standards_systems=[],
            review_objects=[],
            documents={},
        )


def test_bv_document_status_type_accepts_expected_status_values() -> None:
    status: BVDocumentStatus = "partial"

    assert status == "partial"
```

- [x] **Step 2: Run the model tests to verify they fail**

Run: `pytest tests/test_bv_review_models.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'structural_screening_agent.bv_review'`.

- [x] **Step 3: Create the BV package and minimal models**

Create `src/structural_screening_agent/bv_review/__init__.py`:

```python
from structural_screening_agent.bv_review.models import (
    BVReviewIntake,
    BVReviewResult,
)

__all__ = ["BVReviewIntake", "BVReviewResult"]
```

Create `src/structural_screening_agent/bv_review/models.py`:

```python
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


BVStandardSystem = Literal["gb", "iec", "as_nzs", "eurocode"]
BVReviewObject = Literal[
    "mounting_structure",
    "steel_structure",
    "concrete_structure",
    "foundation",
    "connection",
    "load_calculation",
    "existing_rooftop_added_load",
]
BVDocumentStatus = Literal["available", "partial", "missing", "not_applicable"]
BVReviewDecision = Literal["ready_for_review", "review_with_holds", "not_ready"]
BVSeverity = Literal["low", "medium", "high", "critical"]


class BVReviewIntake(BaseModel):
    project_name: str = Field(min_length=1)
    country_or_region: str = Field(min_length=1)
    project_type: Literal["utility_pv", "rooftop_pv", "distributed_pv", "mixed"]
    design_stage: Literal["concept", "tender", "detailed_design", "construction_drawing", "as_built"]
    standards_systems: List[BVStandardSystem] = Field(min_length=1)
    review_objects: List[BVReviewObject] = Field(min_length=1)
    client_requirements: List[str] = Field(default_factory=list)
    documents: Dict[str, BVDocumentStatus] = Field(default_factory=dict)


class BVBasisReference(BaseModel):
    basis_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: Literal["code", "iec_standard", "project_specification", "contract", "screening_method"]
    standards_systems: List[BVStandardSystem] = Field(default_factory=list)
    review_objects: List[BVReviewObject] = Field(default_factory=list)
    trigger_conditions: List[str] = Field(default_factory=list)
    evidence_requirements: List[str] = Field(default_factory=list)
    review_actions: List[str] = Field(default_factory=list)


class BVChecklistItem(BaseModel):
    document_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: BVDocumentStatus
    affected_review_objects: List[BVReviewObject] = Field(default_factory=list)
    review_blocked: bool = False
    required_action: str = Field(min_length=1)


class BVReviewPathItem(BaseModel):
    path_id: str = Field(min_length=1)
    review_object: BVReviewObject
    title: str = Field(min_length=1)
    method: str = Field(min_length=1)
    required_inputs: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)
    status: Literal["ready", "hold", "manual_confirmation_required"]


class BVRiskItem(BaseModel):
    risk_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    severity: BVSeverity
    trigger_basis: str = Field(min_length=1)
    impact_scope: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    blocks_report_issue: bool = False
    category: Literal["risk", "nonconformity", "optimization"]


class BVReviewPlanItem(BaseModel):
    item_id: str = Field(min_length=1)
    phase: Literal["intake", "document_review", "technical_check", "reporting"]
    review_object: Optional[BVReviewObject] = None
    input_documents: List[str] = Field(default_factory=list)
    method: str = Field(min_length=1)
    responsible_role: str = Field(min_length=1)
    blocking_condition: Optional[str] = None
    deliverable: str = Field(min_length=1)


class BVReportSection(BaseModel):
    heading: str = Field(min_length=1)
    items: List[str] = Field(default_factory=list)


class BVReportPreview(BaseModel):
    title: str = Field(min_length=1)
    sections: List[BVReportSection] = Field(default_factory=list)


class BVReviewResult(BaseModel):
    decision: BVReviewDecision
    basis_references: List[BVBasisReference] = Field(default_factory=list)
    checklist_items: List[BVChecklistItem] = Field(default_factory=list)
    review_paths: List[BVReviewPathItem] = Field(default_factory=list)
    risks: List[BVRiskItem] = Field(default_factory=list)
    review_plan: List[BVReviewPlanItem] = Field(default_factory=list)
    report_preview: Optional[BVReportPreview] = None
```

- [x] **Step 4: Run the model tests to verify they pass**

Run: `pytest tests/test_bv_review_models.py -q`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add src/structural_screening_agent/bv_review/__init__.py src/structural_screening_agent/bv_review/models.py tests/test_bv_review_models.py
git commit -m "feat: add bv review domain models"
```

## Task 2: Review Basis Builder

**Files:**
- Create: `src/structural_screening_agent/bv_review/basis.py`
- Modify: `src/structural_screening_agent/bv_review/__init__.py`
- Create: `tests/test_bv_review_workflow.py`

- [x] **Step 1: Write the failing basis tests**

Add to `tests/test_bv_review_workflow.py`:

```python
from structural_screening_agent.bv_review.basis import build_review_basis
from structural_screening_agent.bv_review.models import BVReviewIntake


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Hebei rooftop PV design review",
        country_or_region="China",
        project_type="rooftop_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "existing_rooftop_added_load"],
        client_requirements=["Client requires independent structural design review."],
        documents={
            "structural_drawings": "partial",
            "calculation_report": "missing",
            "technical_specification": "available",
            "geotechnical_report": "missing",
            "vendor_datasheets": "partial",
            "contract_requirements": "available",
        },
    )


def test_review_basis_builder_maps_standards_and_review_objects_to_references() -> None:
    basis = build_review_basis(_sample_intake())

    basis_ids = {item.basis_id for item in basis}
    assert "gb_50797_pv_power_station_design" in basis_ids
    assert "gb_50017_steel_structure_design" in basis_ids
    assert "iec_62548_pv_array_design" in basis_ids
    assert "project_contract_requirements" in basis_ids
    assert any("支架" in item.title for item in basis)
    assert all(item.evidence_requirements for item in basis)
```

- [x] **Step 2: Run the basis test to verify it fails**

Run: `pytest tests/test_bv_review_workflow.py::test_review_basis_builder_maps_standards_and_review_objects_to_references -q`

Expected: FAIL with `ModuleNotFoundError` or `ImportError` for `structural_screening_agent.bv_review.basis`.

- [x] **Step 3: Implement deterministic basis builder**

Create `src/structural_screening_agent/bv_review/basis.py`:

```python
from structural_screening_agent.bv_review.models import BVBasisReference, BVReviewIntake


def build_review_basis(intake: BVReviewIntake) -> list[BVBasisReference]:
    references: list[BVBasisReference] = []

    if "gb" in intake.standards_systems:
        references.append(
            BVBasisReference(
                basis_id="gb_50797_pv_power_station_design",
                title="GB 50797 光伏发电站设计规范审核依据",
                source_type="code",
                standards_systems=["gb"],
                review_objects=list(intake.review_objects),
                trigger_conditions=["项目采用 GB 体系或位于中国项目语境"],
                evidence_requirements=["项目技术规格书", "设计说明", "总平面与结构专业图纸"],
                review_actions=["核对光伏电站总体设计、结构接口和设计边界"],
            )
        )
    if "gb" in intake.standards_systems and any(
        item in intake.review_objects for item in ["mounting_structure", "steel_structure", "connection", "existing_rooftop_added_load"]
    ):
        references.append(
            BVBasisReference(
                basis_id="gb_50017_steel_structure_design",
                title="GB 50017 钢结构设计标准审核依据",
                source_type="code",
                standards_systems=["gb"],
                review_objects=["mounting_structure", "steel_structure", "connection", "existing_rooftop_added_load"],
                trigger_conditions=["审核对象包含钢结构、支架、连接或既有钢结构增载"],
                evidence_requirements=["结构计算书", "构件截面表", "节点详图", "钢材牌号"],
                review_actions=["核对强度、稳定、变形、连接和构造审查路径"],
            )
        )
    if "iec" in intake.standards_systems:
        references.append(
            BVBasisReference(
                basis_id="iec_62548_pv_array_design",
                title="IEC 62548 光伏阵列设计结构接口审核依据",
                source_type="iec_standard",
                standards_systems=["iec"],
                review_objects=["mounting_structure", "connection", "load_calculation"],
                trigger_conditions=["项目选择 IEC 体系或需核对组件阵列安装接口"],
                evidence_requirements=["组件布置图", "支架厂家资料", "安装说明", "接地与桥架接口说明"],
                review_actions=["核对阵列安装、支架接口、维护通道和结构接口边界"],
            )
        )
    if "as_nzs" in intake.standards_systems:
        references.append(
            BVBasisReference(
                basis_id="as_nzs_structural_review_context",
                title="AS/NZS 结构设计审核路径",
                source_type="code",
                standards_systems=["as_nzs"],
                review_objects=list(intake.review_objects),
                trigger_conditions=["项目选择 AS/NZS 体系"],
                evidence_requirements=["项目适用标准清单", "风荷载参数", "结构计算书"],
                review_actions=["按项目指定 AS/NZS 条款组织结构审核路径"],
            )
        )
    if "eurocode" in intake.standards_systems:
        references.append(
            BVBasisReference(
                basis_id="eurocode_structural_review_context",
                title="Eurocode 结构设计审核路径",
                source_type="code",
                standards_systems=["eurocode"],
                review_objects=list(intake.review_objects),
                trigger_conditions=["项目选择 Eurocode 体系"],
                evidence_requirements=["National Annex", "荷载参数", "结构计算书"],
                review_actions=["按 Eurocode 与项目 National Annex 组织结构审核路径"],
            )
        )
    references.append(
        BVBasisReference(
            basis_id="project_contract_requirements",
            title="项目技术规格书与合同要求",
            source_type="contract",
            standards_systems=list(intake.standards_systems),
            review_objects=list(intake.review_objects),
            trigger_conditions=["所有第三方设计审核项目均应核对合同和客户技术要求"],
            evidence_requirements=["合同技术条款", "业主要求", "设计输入条件"],
            review_actions=["确认审核范围、交付物、设计边界和报告签发条件"],
        )
    )
    return references
```

Update `src/structural_screening_agent/bv_review/__init__.py`:

```python
from structural_screening_agent.bv_review.basis import build_review_basis
from structural_screening_agent.bv_review.models import (
    BVReviewIntake,
    BVReviewResult,
)

__all__ = ["BVReviewIntake", "BVReviewResult", "build_review_basis"]
```

- [x] **Step 4: Run the basis test to verify it passes**

Run: `pytest tests/test_bv_review_workflow.py::test_review_basis_builder_maps_standards_and_review_objects_to_references -q`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add src/structural_screening_agent/bv_review/__init__.py src/structural_screening_agent/bv_review/basis.py tests/test_bv_review_workflow.py
git commit -m "feat: add bv review basis builder"
```

## Task 3: Document Checklist And Structural Review Path

**Files:**
- Create: `src/structural_screening_agent/bv_review/checklist.py`
- Create: `src/structural_screening_agent/bv_review/review_path.py`
- Modify: `tests/test_bv_review_workflow.py`

- [x] **Step 1: Write the failing checklist and path tests**

Add to `tests/test_bv_review_workflow.py`:

```python
from structural_screening_agent.bv_review.checklist import build_document_checklist
from structural_screening_agent.bv_review.review_path import build_structural_review_path


def test_document_checklist_marks_missing_calculation_and_geotechnical_reports_as_review_holds() -> None:
    checklist = build_document_checklist(_sample_intake())

    missing_keys = {item.document_key for item in checklist if item.review_blocked}
    assert "calculation_report" in missing_keys
    assert "geotechnical_report" in missing_keys
    assert any("补充结构计算书" in item.required_action for item in checklist)
    assert any("foundation" in item.affected_review_objects for item in checklist)


def test_structural_review_path_creates_object_specific_review_methods_and_holds() -> None:
    checklist = build_document_checklist(_sample_intake())
    paths = build_structural_review_path(_sample_intake(), checklist)

    path_ids = {item.path_id for item in paths}
    assert "mounting_structure_review" in path_ids
    assert "foundation_review" in path_ids
    assert "existing_rooftop_added_load_review" in path_ids
    foundation_path = next(item for item in paths if item.path_id == "foundation_review")
    assert foundation_path.status == "hold"
    assert "地勘报告" in foundation_path.method
```

- [x] **Step 2: Run the checklist/path tests to verify they fail**

Run: `pytest tests/test_bv_review_workflow.py::test_document_checklist_marks_missing_calculation_and_geotechnical_reports_as_review_holds tests/test_bv_review_workflow.py::test_structural_review_path_creates_object_specific_review_methods_and_holds -q`

Expected: FAIL with import errors for `checklist` and `review_path`.

- [x] **Step 3: Implement checklist builder**

Create `src/structural_screening_agent/bv_review/checklist.py`:

```python
from structural_screening_agent.bv_review.models import BVChecklistItem, BVReviewIntake


DOCUMENT_RULES = {
    "structural_drawings": ("结构图纸", ["mounting_structure", "steel_structure", "concrete_structure", "connection", "existing_rooftop_added_load"], "补充结构图纸或最新版设计图。"),
    "calculation_report": ("结构计算书", ["mounting_structure", "steel_structure", "foundation", "connection", "load_calculation", "existing_rooftop_added_load"], "补充结构计算书、荷载取值和设计校核过程。"),
    "technical_specification": ("项目技术规格书", ["mounting_structure", "foundation", "connection", "load_calculation"], "补充项目技术规格书和设计输入条件。"),
    "geotechnical_report": ("地勘报告", ["foundation"], "补充地勘报告、地基承载力和地下水条件。"),
    "vendor_datasheets": ("厂家资料", ["mounting_structure", "connection"], "补充支架、夹具、锚栓或组件厂家资料。"),
    "contract_requirements": ("合同技术要求", ["mounting_structure", "foundation", "connection", "load_calculation"], "补充合同技术条款和客户特殊要求。"),
}


def build_document_checklist(intake: BVReviewIntake) -> list[BVChecklistItem]:
    items: list[BVChecklistItem] = []
    selected_objects = set(intake.review_objects)
    for document_key, (title, affected_objects, action) in DOCUMENT_RULES.items():
        relevant_objects = [item for item in affected_objects if item in selected_objects]
        if not relevant_objects:
            continue
        status = intake.documents.get(document_key, "missing")
        review_blocked = status == "missing"
        if status == "available":
            required_action = "资料已提供，进入技术审核。"
        elif status == "partial":
            required_action = f"资料部分提供；{action}"
        else:
            required_action = action
        items.append(
            BVChecklistItem(
                document_key=document_key,
                title=title,
                status=status,
                affected_review_objects=relevant_objects,
                review_blocked=review_blocked,
                required_action=required_action,
            )
        )
    return items
```

- [x] **Step 4: Implement structural review path builder**

Create `src/structural_screening_agent/bv_review/review_path.py`:

```python
from structural_screening_agent.bv_review.models import BVChecklistItem, BVReviewIntake, BVReviewPathItem, BVReviewObject


PATH_DEFINITIONS = {
    "mounting_structure": ("mounting_structure_review", "支架结构审核", "核对支架布置、构件强度、变形、防腐和厂家资料。", ["结构图纸", "结构计算书", "厂家资料"], ["支架结构审核意见"]),
    "steel_structure": ("steel_structure_review", "钢结构审核", "核对钢构件强度、稳定、节点构造和防腐等级。", ["结构图纸", "结构计算书"], ["钢结构审核意见"]),
    "concrete_structure": ("concrete_structure_review", "混凝土结构审核", "核对混凝土构件、预埋件、裂缝控制和耐久性要求。", ["结构图纸", "结构计算书"], ["混凝土结构审核意见"]),
    "foundation": ("foundation_review", "地基与基础审核", "核对地勘报告、基础形式、承载力、抗拔和沉降控制。", ["地勘报告", "基础计算书"], ["基础审核意见"]),
    "connection": ("connection_review", "连接节点审核", "核对夹具、锚栓、焊缝、螺栓和防水构造。", ["节点详图", "厂家资料", "结构计算书"], ["连接节点审核意见"]),
    "load_calculation": ("load_calculation_review", "荷载计算审核", "核对恒载、风荷载、雪荷载、检修荷载和组合路径。", ["荷载计算书", "项目技术规格书"], ["荷载审核意见"]),
    "existing_rooftop_added_load": ("existing_rooftop_added_load_review", "既有屋面增载审核", "复用现有门式刚架屋面光伏增载 screening kernel，并核对图纸、计算书和现场调查边界。", ["原结构图纸", "既有计算书", "现场调查"], ["既有结构增载初筛摘要"]),
}


def _object_is_blocked(review_object: BVReviewObject, checklist: list[BVChecklistItem]) -> bool:
    return any(item.review_blocked and review_object in item.affected_review_objects for item in checklist)


def build_structural_review_path(intake: BVReviewIntake, checklist: list[BVChecklistItem]) -> list[BVReviewPathItem]:
    paths: list[BVReviewPathItem] = []
    for review_object in intake.review_objects:
        path_id, title, method, required_inputs, deliverables = PATH_DEFINITIONS[review_object]
        blocked = _object_is_blocked(review_object, checklist)
        paths.append(
            BVReviewPathItem(
                path_id=path_id,
                review_object=review_object,
                title=title,
                method=method,
                required_inputs=required_inputs,
                deliverables=deliverables,
                status="hold" if blocked else "ready",
            )
        )
    return paths
```

- [x] **Step 5: Run the checklist/path tests to verify they pass**

Run: `pytest tests/test_bv_review_workflow.py::test_document_checklist_marks_missing_calculation_and_geotechnical_reports_as_review_holds tests/test_bv_review_workflow.py::test_structural_review_path_creates_object_specific_review_methods_and_holds -q`

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add src/structural_screening_agent/bv_review/checklist.py src/structural_screening_agent/bv_review/review_path.py tests/test_bv_review_workflow.py
git commit -m "feat: add bv document checklist and review paths"
```

## Task 4: Review Plan And Risk Register

**Files:**
- Create: `src/structural_screening_agent/bv_review/review_plan.py`
- Create: `src/structural_screening_agent/bv_review/risk_register.py`
- Modify: `tests/test_bv_review_workflow.py`

- [x] **Step 1: Write the failing review plan and risk tests**

Add to `tests/test_bv_review_workflow.py`:

```python
from structural_screening_agent.bv_review.risk_register import build_risk_register
from structural_screening_agent.bv_review.review_plan import build_review_plan


def test_review_plan_generates_itp_items_with_roles_methods_and_deliverables() -> None:
    checklist = build_document_checklist(_sample_intake())
    paths = build_structural_review_path(_sample_intake(), checklist)
    plan = build_review_plan(_sample_intake(), checklist, paths)

    assert any(item.phase == "document_review" for item in plan)
    assert any(item.phase == "technical_check" for item in plan)
    assert any(item.responsible_role == "BV structural review engineer" for item in plan)
    assert any("设计审核意见" in item.deliverable or "初筛摘要" in item.deliverable for item in plan)


def test_risk_register_flags_blocking_missing_documents_and_optimization_items() -> None:
    checklist = build_document_checklist(_sample_intake())
    paths = build_structural_review_path(_sample_intake(), checklist)
    risks = build_risk_register(_sample_intake(), checklist, paths)

    assert any(item.category == "nonconformity" and item.blocks_report_issue for item in risks)
    assert any(item.severity in {"high", "critical"} for item in risks)
    assert any(item.category == "optimization" for item in risks)
    assert any("结构计算书" in item.recommendation for item in risks)
```

- [x] **Step 2: Run the review plan/risk tests to verify they fail**

Run: `pytest tests/test_bv_review_workflow.py::test_review_plan_generates_itp_items_with_roles_methods_and_deliverables tests/test_bv_review_workflow.py::test_risk_register_flags_blocking_missing_documents_and_optimization_items -q`

Expected: FAIL with import errors for `review_plan` and `risk_register`.

- [x] **Step 3: Implement review plan generator**

Create `src/structural_screening_agent/bv_review/review_plan.py`:

```python
from structural_screening_agent.bv_review.models import BVChecklistItem, BVReviewIntake, BVReviewPathItem, BVReviewPlanItem


def build_review_plan(
    intake: BVReviewIntake,
    checklist: list[BVChecklistItem],
    review_paths: list[BVReviewPathItem],
) -> list[BVReviewPlanItem]:
    plan: list[BVReviewPlanItem] = [
        BVReviewPlanItem(
            item_id="intake_scope_confirmation",
            phase="intake",
            input_documents=["合同技术要求", "项目技术规格书"],
            method="确认审核范围、标准体系、设计阶段、客户特殊要求和报告交付边界。",
            responsible_role="BV project review lead",
            blocking_condition="审核范围或适用标准未确认",
            deliverable="设计审核范围确认记录",
        )
    ]
    for item in checklist:
        plan.append(
            BVReviewPlanItem(
                item_id=f"document_check_{item.document_key}",
                phase="document_review",
                input_documents=[item.title],
                method=f"核对{item.title}是否满足当前审核对象的输入需求。",
                responsible_role="BV document controller",
                blocking_condition=item.required_action if item.review_blocked else None,
                deliverable=f"{item.title}完整性检查记录",
            )
        )
    for path in review_paths:
        plan.append(
            BVReviewPlanItem(
                item_id=path.path_id,
                phase="technical_check",
                review_object=path.review_object,
                input_documents=path.required_inputs,
                method=path.method,
                responsible_role="BV structural review engineer",
                blocking_condition="必要输入资料未闭合" if path.status == "hold" else None,
                deliverable=path.deliverables[0],
            )
        )
    plan.append(
        BVReviewPlanItem(
            item_id="report_issue_review",
            phase="reporting",
            input_documents=["资料完整性检查记录", "技术审核意见", "风险与不符合项清单"],
            method="汇总审核范围、依据、主要发现、不符合项、风险、优化建议和后续行动。",
            responsible_role="BV project review lead",
            blocking_condition="存在阻塞报告签发的不符合项",
            deliverable="BV 风格设计审查报告",
        )
    )
    return plan
```

- [x] **Step 4: Implement risk register builder**

Create `src/structural_screening_agent/bv_review/risk_register.py`:

```python
from structural_screening_agent.bv_review.models import BVChecklistItem, BVRiskItem, BVReviewIntake, BVReviewPathItem


def build_risk_register(
    intake: BVReviewIntake,
    checklist: list[BVChecklistItem],
    review_paths: list[BVReviewPathItem],
) -> list[BVRiskItem]:
    risks: list[BVRiskItem] = []
    for item in checklist:
        if item.status == "missing":
            risks.append(
                BVRiskItem(
                    risk_id=f"missing_{item.document_key}",
                    title=f"{item.title}缺失",
                    severity="critical" if item.review_blocked else "medium",
                    trigger_basis=item.title,
                    impact_scope="、".join(item.affected_review_objects),
                    recommendation=item.required_action,
                    blocks_report_issue=item.review_blocked,
                    category="nonconformity",
                )
            )
        elif item.status == "partial":
            risks.append(
                BVRiskItem(
                    risk_id=f"partial_{item.document_key}",
                    title=f"{item.title}不完整",
                    severity="high",
                    trigger_basis=item.title,
                    impact_scope="、".join(item.affected_review_objects),
                    recommendation=item.required_action,
                    blocks_report_issue=False,
                    category="risk",
                )
            )
    if "mounting_structure" in intake.review_objects:
        risks.append(
            BVRiskItem(
                risk_id="mounting_layout_optimization",
                title="支架布置与施工可行性优化",
                severity="medium",
                trigger_basis="项目技术规格书与支架厂家资料",
                impact_scope="支架布置、防腐、施工通道和维护空间",
                recommendation="复核支架排布、檩条或基础接口、防腐等级和施工维护通道，形成优化建议。",
                blocks_report_issue=False,
                category="optimization",
            )
        )
    if any(path.status == "hold" for path in review_paths):
        risks.append(
            BVRiskItem(
                risk_id="review_path_has_holds",
                title="部分技术审核路径被资料缺口阻塞",
                severity="high",
                trigger_basis="资料完整性检查",
                impact_scope="设计审核计划与报告签发",
                recommendation="先关闭阻塞资料项，再签发无保留的设计审查报告。",
                blocks_report_issue=True,
                category="risk",
            )
        )
    return risks
```

- [x] **Step 5: Run the review plan/risk tests to verify they pass**

Run: `pytest tests/test_bv_review_workflow.py::test_review_plan_generates_itp_items_with_roles_methods_and_deliverables tests/test_bv_review_workflow.py::test_risk_register_flags_blocking_missing_documents_and_optimization_items -q`

Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add src/structural_screening_agent/bv_review/review_plan.py src/structural_screening_agent/bv_review/risk_register.py tests/test_bv_review_workflow.py
git commit -m "feat: add bv review plan and risk register"
```

## Task 5: Workflow Orchestration

**Files:**
- Create: `src/structural_screening_agent/bv_review/workflow.py`
- Modify: `src/structural_screening_agent/bv_review/__init__.py`
- Modify: `tests/test_bv_review_workflow.py`

- [x] **Step 1: Write the failing workflow test**

Add to `tests/test_bv_review_workflow.py`:

```python
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def test_bv_review_workflow_composes_basis_checklist_paths_risks_and_plan() -> None:
    result = evaluate_bv_review(_sample_intake())

    assert result.decision == "not_ready"
    assert result.basis_references
    assert result.checklist_items
    assert result.review_paths
    assert result.risks
    assert result.review_plan
    assert any(item.blocks_report_issue for item in result.risks)


def test_bv_review_workflow_marks_review_with_holds_when_only_partial_documents_remain() -> None:
    intake = _sample_intake().model_copy(
        update={
            "documents": {
                "structural_drawings": "partial",
                "calculation_report": "partial",
                "technical_specification": "available",
                "geotechnical_report": "partial",
                "vendor_datasheets": "partial",
                "contract_requirements": "available",
            }
        }
    )

    result = evaluate_bv_review(intake)

    assert result.decision == "review_with_holds"
    assert not any(item.blocks_report_issue for item in result.risks)


def test_bv_review_workflow_marks_ready_when_all_documents_are_available() -> None:
    intake = _sample_intake().model_copy(
        update={
            "documents": {
                "structural_drawings": "available",
                "calculation_report": "available",
                "technical_specification": "available",
                "geotechnical_report": "available",
                "vendor_datasheets": "available",
                "contract_requirements": "available",
            }
        }
    )

    result = evaluate_bv_review(intake)

    assert result.decision == "ready_for_review"
```

- [x] **Step 2: Run the workflow tests to verify they fail**

Run: `pytest tests/test_bv_review_workflow.py::test_bv_review_workflow_composes_basis_checklist_paths_risks_and_plan tests/test_bv_review_workflow.py::test_bv_review_workflow_marks_review_with_holds_when_only_partial_documents_remain tests/test_bv_review_workflow.py::test_bv_review_workflow_marks_ready_when_all_documents_are_available -q`

Expected: FAIL with import error for `workflow`.

- [x] **Step 3: Implement workflow orchestration**

Create `src/structural_screening_agent/bv_review/workflow.py`:

```python
from structural_screening_agent.bv_review.basis import build_review_basis
from structural_screening_agent.bv_review.checklist import build_document_checklist
from structural_screening_agent.bv_review.models import BVReviewDecision, BVReviewIntake, BVReviewResult
from structural_screening_agent.bv_review.review_path import build_structural_review_path
from structural_screening_agent.bv_review.review_plan import build_review_plan
from structural_screening_agent.bv_review.risk_register import build_risk_register


def _resolve_decision(result: BVReviewResult) -> BVReviewDecision:
    if any(item.blocks_report_issue for item in result.risks):
        return "not_ready"
    if any(item.status in {"partial", "missing"} for item in result.checklist_items):
        return "review_with_holds"
    return "ready_for_review"


def evaluate_bv_review(intake: BVReviewIntake) -> BVReviewResult:
    basis = build_review_basis(intake)
    checklist = build_document_checklist(intake)
    review_paths = build_structural_review_path(intake, checklist)
    risks = build_risk_register(intake, checklist, review_paths)
    review_plan = build_review_plan(intake, checklist, review_paths)
    result = BVReviewResult(
        decision="review_with_holds",
        basis_references=basis,
        checklist_items=checklist,
        review_paths=review_paths,
        risks=risks,
        review_plan=review_plan,
    )
    return result.model_copy(update={"decision": _resolve_decision(result)})
```

Update `src/structural_screening_agent/bv_review/__init__.py`:

```python
from structural_screening_agent.bv_review.basis import build_review_basis
from structural_screening_agent.bv_review.models import (
    BVReviewIntake,
    BVReviewResult,
)
from structural_screening_agent.bv_review.workflow import evaluate_bv_review

__all__ = ["BVReviewIntake", "BVReviewResult", "build_review_basis", "evaluate_bv_review"]
```

- [x] **Step 4: Run the workflow tests to verify they pass**

Run: `pytest tests/test_bv_review_workflow.py::test_bv_review_workflow_composes_basis_checklist_paths_risks_and_plan tests/test_bv_review_workflow.py::test_bv_review_workflow_marks_review_with_holds_when_only_partial_documents_remain tests/test_bv_review_workflow.py::test_bv_review_workflow_marks_ready_when_all_documents_are_available -q`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add src/structural_screening_agent/bv_review/__init__.py src/structural_screening_agent/bv_review/workflow.py tests/test_bv_review_workflow.py
git commit -m "feat: compose bv review workflow"
```

## Task 6: BV Report Preview Composer

**Files:**
- Create: `src/structural_screening_agent/bv_review/report.py`
- Modify: `src/structural_screening_agent/bv_review/workflow.py`
- Create: `tests/test_bv_review_report.py`

- [x] **Step 1: Write the failing report tests**

Add `tests/test_bv_review_report.py`:

```python
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.report import build_bv_report_preview
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Hebei rooftop PV design review",
        country_or_region="China",
        project_type="rooftop_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "existing_rooftop_added_load"],
        client_requirements=["Client requires independent structural design review."],
        documents={
            "structural_drawings": "partial",
            "calculation_report": "missing",
            "technical_specification": "available",
            "geotechnical_report": "missing",
            "vendor_datasheets": "partial",
            "contract_requirements": "available",
        },
    )


def test_bv_report_preview_contains_required_design_review_sections() -> None:
    result = evaluate_bv_review(_sample_intake())
    preview = build_bv_report_preview(_sample_intake(), result)

    headings = [section.heading for section in preview.sections]
    assert preview.title == "BV 光伏结构设计审查报告"
    assert "项目与审核范围" in headings
    assert "审核依据" in headings
    assert "提交资料清单与完整性状态" in headings
    assert "审核路径与方法" in headings
    assert "主要发现" in headings
    assert "不符合项与阻塞项" in headings
    assert "技术风险与优化建议" in headings
    assert "后续行动" in headings
    assert "审核边界声明" in headings


def test_bv_report_boundary_statement_does_not_claim_formal_design_or_bv_official_issue() -> None:
    result = evaluate_bv_review(_sample_intake())
    preview = build_bv_report_preview(_sample_intake(), result)

    boundary = next(section for section in preview.sections if section.heading == "审核边界声明")
    text = "\n".join(boundary.items)
    assert "不替代正式设计" in text
    assert "不代表 BV 官方签发流程" in text
    assert "合格工程师复核" in text
```

- [x] **Step 2: Run the report tests to verify they fail**

Run: `pytest tests/test_bv_review_report.py -q`

Expected: FAIL with import error for `structural_screening_agent.bv_review.report`.

- [x] **Step 3: Implement report preview composer**

Create `src/structural_screening_agent/bv_review/report.py`:

```python
from structural_screening_agent.bv_review.models import BVReportPreview, BVReportSection, BVReviewIntake, BVReviewResult


def build_bv_report_preview(intake: BVReviewIntake, result: BVReviewResult) -> BVReportPreview:
    blocking_items = [item for item in result.risks if item.blocks_report_issue]
    optimization_items = [item for item in result.risks if item.category == "optimization"]
    sections = [
        BVReportSection(
            heading="项目与审核范围",
            items=[
                f"项目名称: {intake.project_name}",
                f"国家/地区: {intake.country_or_region}",
                f"设计阶段: {intake.design_stage}",
                f"审核对象: {', '.join(intake.review_objects)}",
                f"当前审核结论: {result.decision}",
            ],
        ),
        BVReportSection(
            heading="审核依据",
            items=[f"{item.title}: {'; '.join(item.review_actions)}" for item in result.basis_references],
        ),
        BVReportSection(
            heading="提交资料清单与完整性状态",
            items=[f"{item.title}: {item.status} | {item.required_action}" for item in result.checklist_items],
        ),
        BVReportSection(
            heading="审核路径与方法",
            items=[f"{item.title}: {item.status} | {item.method}" for item in result.review_paths],
        ),
        BVReportSection(
            heading="主要发现",
            items=[
                f"阻塞项数量: {len(blocking_items)}",
                f"风险与不符合项数量: {len(result.risks)}",
                f"审核计划条目数量: {len(result.review_plan)}",
            ],
        ),
        BVReportSection(
            heading="不符合项与阻塞项",
            items=[
                f"{item.title}: {item.recommendation}"
                for item in result.risks
                if item.category == "nonconformity" or item.blocks_report_issue
            ]
            or ["当前未识别阻塞报告签发的不符合项。"],
        ),
        BVReportSection(
            heading="技术风险与优化建议",
            items=[
                f"{item.title}: {item.recommendation}"
                for item in result.risks
                if item.category == "risk" or item in optimization_items
            ]
            or ["当前未识别需要单独列示的优化建议。"],
        ),
        BVReportSection(
            heading="后续行动",
            items=[f"{item.phase}: {item.method} | 交付物: {item.deliverable}" for item in result.review_plan[:8]],
        ),
        BVReportSection(
            heading="审核边界声明",
            items=[
                "本工具用于设计审核前期组织、资料完整性判断、风险识别和 screening-level 技术路径梳理。",
                "输出不替代正式设计、第三方签章、有限元计算、施工图审查，也不代表 BV 官方签发流程。",
                "所有自动生成的不符合项、技术风险和优化建议均需由合格工程师复核。",
            ],
        ),
    ]
    return BVReportPreview(title="BV 光伏结构设计审查报告", sections=sections)
```

- [x] **Step 4: Attach report preview in workflow**

Modify `src/structural_screening_agent/bv_review/workflow.py`:

```python
from structural_screening_agent.bv_review.basis import build_review_basis
from structural_screening_agent.bv_review.checklist import build_document_checklist
from structural_screening_agent.bv_review.models import BVReviewDecision, BVReviewIntake, BVReviewResult
from structural_screening_agent.bv_review.report import build_bv_report_preview
from structural_screening_agent.bv_review.review_path import build_structural_review_path
from structural_screening_agent.bv_review.review_plan import build_review_plan
from structural_screening_agent.bv_review.risk_register import build_risk_register


def _resolve_decision(result: BVReviewResult) -> BVReviewDecision:
    if any(item.blocks_report_issue for item in result.risks):
        return "not_ready"
    if any(item.status in {"partial", "missing"} for item in result.checklist_items):
        return "review_with_holds"
    return "ready_for_review"


def evaluate_bv_review(intake: BVReviewIntake) -> BVReviewResult:
    basis = build_review_basis(intake)
    checklist = build_document_checklist(intake)
    review_paths = build_structural_review_path(intake, checklist)
    risks = build_risk_register(intake, checklist, review_paths)
    review_plan = build_review_plan(intake, checklist, review_paths)
    result = BVReviewResult(
        decision="review_with_holds",
        basis_references=basis,
        checklist_items=checklist,
        review_paths=review_paths,
        risks=risks,
        review_plan=review_plan,
    )
    result = result.model_copy(update={"decision": _resolve_decision(result)})
    return result.model_copy(update={"report_preview": build_bv_report_preview(intake, result)})
```

- [x] **Step 5: Run the report tests to verify they pass**

Run: `pytest tests/test_bv_review_report.py -q`

Expected: PASS.

- [x] **Step 6: Run BV workflow tests**

Run: `pytest tests/test_bv_review_models.py tests/test_bv_review_workflow.py tests/test_bv_review_report.py -q`

Expected: PASS.

- [x] **Step 7: Commit**

```bash
git add src/structural_screening_agent/bv_review/report.py src/structural_screening_agent/bv_review/workflow.py tests/test_bv_review_report.py
git commit -m "feat: compose bv design review report preview"
```

## Task 7: Regression And Plan Closure

**Files:**
- Modify: `docs/superpowers/plans/2026-05-08-bv-pv-design-review-workbench-implementation-plan.md`

- [x] **Step 1: Run all tests**

Run: `pytest -q`

Expected: PASS with all existing tests plus new BV tests.

- [x] **Step 2: Verify no unexpected files changed**

Run: `git status --short`

Expected: only intentional files are modified or the worktree is clean after the final commit.

- [x] **Step 3: Mark completed checkboxes in this plan**

Edit this plan so completed steps use `- [x]` for tasks actually executed in the current branch. Do not mark future UI and showcase refresh work as completed in this Phase 1 plan.

- [x] **Step 4: Commit plan checkbox updates if any were made**

```bash
git add docs/superpowers/plans/2026-05-08-bv-pv-design-review-workbench-implementation-plan.md
git commit -m "docs: update bv review implementation plan progress"
```

## Phase 1 Completion Criteria

- `structural_screening_agent.bv_review` package exists and imports cleanly.
- BV intake expresses project name, region, project type, design stage, standards systems, review objects, client requirements, and document status.
- Basis builder outputs GB, IEC, AS/NZS, Eurocode, and project contract basis when triggered by intake.
- Checklist maps missing and partial documents into review holds and required actions.
- Review path generator covers mounting structure, steel, concrete, foundation, connection, load calculation, and existing rooftop added load.
- Risk register outputs risks, nonconformities, optimization items, severity, impact scope, recommendations, and report-blocking status.
- Review plan outputs intake, document review, technical check, and reporting phases.
- Workflow composes all BV review outputs into `BVReviewResult`.
- BV report preview contains required design review sections and boundary statement.
- `pytest -q` passes.

## Follow-Up Plans After Phase 1

- Phase 2: Streamlit BV Review Mode UI and existing portal-frame scenario module wiring.
- Phase 3: Markdown / Word / PDF export integration for BV report preview.
- Phase 4: README, showcase docs, and screenshot refresh for BV positioning.
