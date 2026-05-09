# BV Review Mode UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the Phase 1 `bv_review` backend to the Streamlit app so the first screen becomes a BV PV design review workbench while preserving the existing portal-frame rooftop PV screening module.

**Architecture:** Add a small BV UI state helper for default intake and labels, then render a new Streamlit BV review tab using `evaluate_bv_review`. Keep existing portal-frame screening inputs, calculations, traceability, and export behavior intact as a scenario module; do not integrate BV Word/PDF export in this phase.

**Tech Stack:** Streamlit, Pydantic v2, pytest, `streamlit.testing.v1.AppTest`, existing `structural_screening_agent.bv_review` package.

---

## Frontend Direction

- Visual thesis: restrained technical review console with dense, scannable evidence and risk status.
- Content plan: BV overview, project review intake, basis/path summary, ITP and risk register, existing portal-frame scenario module.
- Interaction thesis: use Streamlit tabs and compact metrics for quick scanning; use multiselect/selectbox inputs for review scope; keep report preview as readable section lists without adding decorative UI.

## File Structure

- Create: `src/structural_screening_agent/bv_review/ui_state.py`
  - Default BV intake, label maps, document keys, option lists, and a safe builder for UI-provided values.
- Modify: `app.py`
  - Change app/page title to `BV PV Design Review Workbench`.
  - Add a `BV Review` tab before the existing portal-frame tabs.
  - Render BV project review intake controls, overview metrics, checklist/path/risk/plan summaries, and report preview.
  - Keep the existing portal-frame screening workflow available in existing tabs.
- Modify: `tests/test_project_layout.py`
  - Static assertions that the app imports and renders BV Review Mode.
  - AppTest smoke still verifies no Streamlit exceptions.
- Create: `tests/test_bv_review_ui_state.py`
  - Unit tests for default BV intake and UI intake builder.

## Task 1: BV UI State Helper

**Files:**
- Create: `src/structural_screening_agent/bv_review/ui_state.py`
- Create: `tests/test_bv_review_ui_state.py`

- [x] **Step 1: Write the failing UI state tests**

Create `tests/test_bv_review_ui_state.py`:

```python
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.ui_state import (
    BV_DOCUMENT_LABELS,
    BV_REVIEW_OBJECT_LABELS,
    build_bv_review_intake,
    default_bv_review_intake,
)
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def test_default_bv_review_intake_runs_through_workflow() -> None:
    intake = default_bv_review_intake()
    result = evaluate_bv_review(intake)

    assert isinstance(intake, BVReviewIntake)
    assert intake.project_name == "BV rooftop PV design review demo"
    assert "gb" in intake.standards_systems
    assert "iec" in intake.standards_systems
    assert "mounting_structure" in intake.review_objects
    assert result.report_preview is not None
    assert result.report_preview.title == "BV 光伏结构设计审查报告"


def test_bv_ui_labels_cover_default_documents_and_review_objects() -> None:
    intake = default_bv_review_intake()

    assert set(intake.documents) <= set(BV_DOCUMENT_LABELS)
    assert set(intake.review_objects) <= set(BV_REVIEW_OBJECT_LABELS)
    assert BV_DOCUMENT_LABELS["calculation_report"]["zh"] == "结构计算书"
    assert BV_REVIEW_OBJECT_LABELS["existing_rooftop_added_load"]["zh"] == "既有屋面增载"


def test_build_bv_review_intake_preserves_user_selected_scope_and_documents() -> None:
    intake = build_bv_review_intake(
        project_name="Owner review package",
        country_or_region="Australia",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["iec", "as_nzs"],
        review_objects=["foundation", "load_calculation"],
        client_requirements_text="Independent review before IFC release",
        documents={
            "technical_specification": "available",
            "geotechnical_report": "partial",
            "calculation_report": "missing",
        },
    )

    assert intake.project_name == "Owner review package"
    assert intake.country_or_region == "Australia"
    assert intake.standards_systems == ["iec", "as_nzs"]
    assert intake.review_objects == ["foundation", "load_calculation"]
    assert intake.client_requirements == ["Independent review before IFC release"]
    assert intake.documents["geotechnical_report"] == "partial"
```

- [x] **Step 2: Run the UI state tests to verify they fail**

Run: `pytest tests/test_bv_review_ui_state.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'structural_screening_agent.bv_review.ui_state'`.

- [x] **Step 3: Implement UI state helper**

Create `src/structural_screening_agent/bv_review/ui_state.py`:

```python
from structural_screening_agent.bv_review.models import BVReviewIntake


BV_STANDARD_LABELS = {
    "gb": {"zh": "GB 国标", "en": "GB"},
    "iec": {"zh": "IEC 光伏标准", "en": "IEC"},
    "as_nzs": {"zh": "AS/NZS", "en": "AS/NZS"},
    "eurocode": {"zh": "Eurocode", "en": "Eurocode"},
}

BV_REVIEW_OBJECT_LABELS = {
    "mounting_structure": {"zh": "支架结构", "en": "Mounting Structure"},
    "steel_structure": {"zh": "钢结构", "en": "Steel Structure"},
    "concrete_structure": {"zh": "混凝土结构", "en": "Concrete Structure"},
    "foundation": {"zh": "地基与基础", "en": "Foundation"},
    "connection": {"zh": "连接节点", "en": "Connection"},
    "load_calculation": {"zh": "荷载计算", "en": "Load Calculation"},
    "existing_rooftop_added_load": {"zh": "既有屋面增载", "en": "Existing Rooftop Added Load"},
}

BV_DOCUMENT_LABELS = {
    "structural_drawings": {"zh": "结构图纸", "en": "Structural Drawings"},
    "calculation_report": {"zh": "结构计算书", "en": "Calculation Report"},
    "technical_specification": {"zh": "项目技术规格书", "en": "Technical Specification"},
    "geotechnical_report": {"zh": "地勘报告", "en": "Geotechnical Report"},
    "vendor_datasheets": {"zh": "厂家资料", "en": "Vendor Datasheets"},
    "contract_requirements": {"zh": "合同技术要求", "en": "Contract Requirements"},
}

BV_PROJECT_TYPE_LABELS = {
    "utility_pv": {"zh": "集中式光伏", "en": "Utility PV"},
    "rooftop_pv": {"zh": "屋面光伏", "en": "Rooftop PV"},
    "distributed_pv": {"zh": "分布式光伏", "en": "Distributed PV"},
    "mixed": {"zh": "混合项目", "en": "Mixed"},
}

BV_DESIGN_STAGE_LABELS = {
    "concept": {"zh": "概念阶段", "en": "Concept"},
    "tender": {"zh": "招标阶段", "en": "Tender"},
    "detailed_design": {"zh": "详细设计", "en": "Detailed Design"},
    "construction_drawing": {"zh": "施工图阶段", "en": "Construction Drawing"},
    "as_built": {"zh": "竣工资料", "en": "As-built"},
}

BV_DOCUMENT_STATUS_LABELS = {
    "available": {"zh": "已提供", "en": "Available"},
    "partial": {"zh": "部分提供", "en": "Partial"},
    "missing": {"zh": "缺失", "en": "Missing"},
    "not_applicable": {"zh": "不适用", "en": "Not Applicable"},
}


def _split_client_requirements(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def default_bv_review_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="BV rooftop PV design review demo",
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


def build_bv_review_intake(
    *,
    project_name: str,
    country_or_region: str,
    project_type: str,
    design_stage: str,
    standards_systems: list[str],
    review_objects: list[str],
    client_requirements_text: str,
    documents: dict[str, str],
) -> BVReviewIntake:
    default = default_bv_review_intake()
    return BVReviewIntake(
        project_name=project_name.strip() or default.project_name,
        country_or_region=country_or_region.strip() or default.country_or_region,
        project_type=project_type,
        design_stage=design_stage,
        standards_systems=standards_systems or list(default.standards_systems),
        review_objects=review_objects or list(default.review_objects),
        client_requirements=_split_client_requirements(client_requirements_text),
        documents={key: documents.get(key, default.documents[key]) for key in BV_DOCUMENT_LABELS},
    )
```

- [x] **Step 4: Run the UI state tests to verify they pass**

Run: `pytest tests/test_bv_review_ui_state.py -q`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add src/structural_screening_agent/bv_review/ui_state.py tests/test_bv_review_ui_state.py
git commit -m "feat: add bv review ui state"
```

## Task 2: Streamlit BV Review Tab

**Files:**
- Modify: `app.py`
- Modify: `tests/test_project_layout.py`

- [x] **Step 1: Write the failing app layout test**

Add assertions to `test_app_py_uses_tabbed_information_architecture` in `tests/test_project_layout.py`:

```python
    assert "BV PV Design Review Workbench" in source
    assert "evaluate_bv_review" in source
    assert "default_bv_review_intake" in source
    assert "build_bv_review_intake" in source
    assert "bv_review_tab" in source
    assert "BV Review" in source
    assert "Risk & Nonconformity Register" in source
    assert "Portal-Frame Scenario Module" in source
```

- [x] **Step 2: Run the layout test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture -q`

Expected: FAIL because `app.py` still uses the portal-frame product title and has no BV review tab.

- [x] **Step 3: Import BV UI helpers in app**

Modify `app.py` imports by adding:

```python
from structural_screening_agent.bv_review.ui_state import (
    BV_DESIGN_STAGE_LABELS,
    BV_DOCUMENT_LABELS,
    BV_DOCUMENT_STATUS_LABELS,
    BV_PROJECT_TYPE_LABELS,
    BV_REVIEW_OBJECT_LABELS,
    BV_STANDARD_LABELS,
    build_bv_review_intake,
    default_bv_review_intake,
)
from structural_screening_agent.bv_review.workflow import evaluate_bv_review
```

- [x] **Step 4: Update page title and app heading**

Change:

```python
st.set_page_config(page_title="Portal-Frame Rooftop PV Screening", layout="wide")
```

to:

```python
st.set_page_config(page_title="BV PV Design Review Workbench", layout="wide")
```

Change the title/caption block to:

```python
st.title("BV PV Design Review Workbench" if ui_language == "en" else "BV 光伏结构设计审核工作台")
st.caption(
    "Third-party PV civil, structural, mounting, foundation, and existing-rooftop design review workbench."
    if ui_language == "en"
    else "面向第三方审核工程师的光伏土建、钢结构、支架、基础与既有屋面增载设计审核工作台。"
)
```

- [x] **Step 5: Add BV tab before existing portal-frame tabs**

Change tab assignment to:

```python
bv_review_tab, assessment_tab, input_tab, basis_tab, export_tab, extension_tab = st.tabs(
    [
        "BV Review" if ui_language == "en" else "BV 审核总览",
        translate(ui_language, "assessment_tab"),
        translate(ui_language, "project_input_tab"),
        translate(ui_language, "basis_traceability_tab"),
        translate(ui_language, "report_export_tab"),
        "Portal-Frame Scenario Module" if ui_language == "en" else "门刚场景模块",
    ]
)
```

- [x] **Step 6: Add small local label helpers in app**

Add after `_render_key_calculation_cards`:

```python
def _label(label_map: dict[str, dict[str, str]], value: str, language: Language) -> str:
    return label_map.get(value, {}).get(language, value)


def _render_bv_section(title: str, items: list[str], limit: Optional[int] = None) -> None:
    st.markdown(f"#### {title}")
    visible_items = items if limit is None else items[:limit]
    for item in visible_items:
        st.write(f"- {item}")
```

- [x] **Step 7: Render BV review tab**

Add after the existing line `report_pdf_filename = report_filename.replace(".md", ".pdf")` and before `with assessment_tab:`:

```python
with bv_review_tab:
    default_bv_intake = default_bv_review_intake()
    st.subheader("Project Review Intake" if ui_language == "en" else "项目设计审核输入")
    st.caption(
        "BV Review Mode organizes scope, basis, document completeness, ITP, risks, and report preview."
        if ui_language == "en"
        else "BV 审核模式用于组织审核范围、依据、资料完整性、ITP、风险清单和报告预览。"
    )

    bv_col_1, bv_col_2 = st.columns(2)
    with bv_col_1:
        bv_project_name = st.text_input(
            "Project Name" if ui_language == "en" else "项目名称",
            value=default_bv_intake.project_name,
            key="bv_project_name",
        )
        bv_country_or_region = st.text_input(
            "Country / Region" if ui_language == "en" else "国家 / 地区",
            value=default_bv_intake.country_or_region,
            key="bv_country_or_region",
        )
        bv_project_type = st.selectbox(
            "Project Type" if ui_language == "en" else "项目类型",
            list(BV_PROJECT_TYPE_LABELS),
            index=list(BV_PROJECT_TYPE_LABELS).index(default_bv_intake.project_type),
            format_func=lambda value: _label(BV_PROJECT_TYPE_LABELS, value, ui_language),
            key="bv_project_type",
        )
        bv_design_stage = st.selectbox(
            "Design Stage" if ui_language == "en" else "设计阶段",
            list(BV_DESIGN_STAGE_LABELS),
            index=list(BV_DESIGN_STAGE_LABELS).index(default_bv_intake.design_stage),
            format_func=lambda value: _label(BV_DESIGN_STAGE_LABELS, value, ui_language),
            key="bv_design_stage",
        )
    with bv_col_2:
        bv_standards = st.multiselect(
            "Standards Systems" if ui_language == "en" else "标准体系",
            list(BV_STANDARD_LABELS),
            default=list(default_bv_intake.standards_systems),
            format_func=lambda value: _label(BV_STANDARD_LABELS, value, ui_language),
            key="bv_standards",
        )
        bv_review_objects = st.multiselect(
            "Review Objects" if ui_language == "en" else "审核对象",
            list(BV_REVIEW_OBJECT_LABELS),
            default=list(default_bv_intake.review_objects),
            format_func=lambda value: _label(BV_REVIEW_OBJECT_LABELS, value, ui_language),
            key="bv_review_objects",
        )
        bv_client_requirements_text = st.text_area(
            "Client Requirements" if ui_language == "en" else "客户要求",
            value="\\n".join(default_bv_intake.client_requirements),
            height=90,
            key="bv_client_requirements",
        )

    st.markdown("#### Design Document Checklist" if ui_language == "en" else "设计资料完整性")
    document_statuses = {}
    doc_cols = st.columns(3)
    for index, (document_key, labels) in enumerate(BV_DOCUMENT_LABELS.items()):
        with doc_cols[index % 3]:
            document_statuses[document_key] = st.selectbox(
                labels[ui_language],
                list(BV_DOCUMENT_STATUS_LABELS),
                index=list(BV_DOCUMENT_STATUS_LABELS).index(default_bv_intake.documents[document_key]),
                format_func=lambda value: _label(BV_DOCUMENT_STATUS_LABELS, value, ui_language),
                key=f"bv_doc_{document_key}",
            )

    bv_intake = build_bv_review_intake(
        project_name=bv_project_name,
        country_or_region=bv_country_or_region,
        project_type=bv_project_type,
        design_stage=bv_design_stage,
        standards_systems=bv_standards,
        review_objects=bv_review_objects,
        client_requirements_text=bv_client_requirements_text,
        documents=document_statuses,
    )
    bv_result = evaluate_bv_review(bv_intake)
    blockers = [item for item in bv_result.risks if item.blocks_report_issue]

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Decision" if ui_language == "en" else "审核结论", bv_result.decision)
    metric_2.metric("Blocking Items" if ui_language == "en" else "阻塞项", len(blockers))
    metric_3.metric("Review Paths" if ui_language == "en" else "审核路径", len(bv_result.review_paths))

    overview_col, risk_col = st.columns([1.0, 1.0])
    with overview_col:
        _render_bv_section(
            "Review Basis Builder" if ui_language == "en" else "审核依据",
            [f"{item.title}: {'; '.join(item.review_actions)}" for item in bv_result.basis_references],
            limit=4,
        )
        _render_bv_section(
            "Structural Review Path" if ui_language == "en" else "结构审核路径",
            [f"{item.title}: {item.status} | {item.method}" for item in bv_result.review_paths],
            limit=5,
        )
    with risk_col:
        _render_bv_section(
            "Risk & Nonconformity Register" if ui_language == "en" else "风险与不符合项清单",
            [f"{item.severity} | {item.title}: {item.recommendation}" for item in bv_result.risks],
            limit=6,
        )
        _render_bv_section(
            "ITP & Review Plan" if ui_language == "en" else "ITP 与审核计划",
            [f"{item.phase}: {item.method} | {item.deliverable}" for item in bv_result.review_plan],
            limit=5,
        )

    if bv_result.report_preview is not None:
        st.markdown("#### Design Review Report Preview" if ui_language == "en" else "设计审查报告预览")
        for section in bv_result.report_preview.sections[:4]:
            with st.container(border=True):
                st.markdown(f"**{section.heading}**")
                for item in section.items[:4]:
                    st.write(item)
```

- [x] **Step 8: Run the layout test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture -q`

Expected: PASS.

- [x] **Step 9: Run AppTest smoke**

Run: `pytest tests/test_project_layout.py::test_app_runs_without_streamlit_exceptions -q`

Expected: PASS.

- [x] **Step 10: Commit**

```bash
git add app.py tests/test_project_layout.py
git commit -m "feat: add bv review mode to streamlit app"
```

## Task 3: Regression And Plan Closure

**Files:**
- Modify: `docs/superpowers/plans/2026-05-08-bv-review-mode-ui-implementation-plan.md`

- [x] **Step 1: Run focused BV and UI tests**

Run: `pytest tests/test_bv_review_ui_state.py tests/test_bv_review_models.py tests/test_bv_review_workflow.py tests/test_bv_review_report.py tests/test_project_layout.py -q`

Expected: PASS.

- [x] **Step 2: Run all tests**

Run: `pytest -q`

Expected: PASS.

- [x] **Step 3: Verify worktree status**

Run: `git status --short`

Expected: clean before plan checkbox update.

- [x] **Step 4: Mark this plan complete**

Edit `docs/superpowers/plans/2026-05-08-bv-review-mode-ui-implementation-plan.md` so completed checkbox steps use `- [x]`.

- [x] **Step 5: Commit plan progress**

```bash
git add docs/superpowers/plans/2026-05-08-bv-review-mode-ui-implementation-plan.md
git commit -m "docs: update bv review ui implementation plan progress"
```

## Phase 2 Completion Criteria

- App first screen clearly identifies `BV PV Design Review Workbench`.
- A `BV Review` tab renders without Streamlit exceptions.
- BV review intake controls allow project scope, standards, review objects, client requirements, and document status changes.
- BV tab displays decision, blockers, basis, review paths, risk/nonconformity register, ITP/review plan, and report preview.
- Existing portal-frame screening tabs still render and existing export behavior remains untouched.
- Focused UI tests and full `pytest -q` pass.

## Follow-Up Plans After Phase 2

- Phase 3: BV Markdown / Word / PDF export integration.
- Phase 4: README, showcase docs, and screenshot refresh for BV positioning.
