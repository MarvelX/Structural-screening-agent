# Portal Frame UI Information Architecture Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Streamlit UI into a tab-based structural screening interface that emphasizes conclusion-first review, separates traceability from the main decision screen, and reserves a future calculation-extension interface.

**Architecture:** Keep the current screening engine, persistence, and report generation pipeline, but replace the single-page stacked UI with a five-tab interface. Introduce smaller presentation builders for each tab while keeping the legacy `WorkbenchView` contract only as long as needed for a safe migration. Use strict single-language UI rendering and demote formulas, traceability, and report text out of the default decision screen.

**Tech Stack:** Python 3.9+, Streamlit, Pydantic v2, pytest, existing `structural_screening_agent` presentation/report pipeline

---

## File Structure

- Modify: `app.py`
- Modify: `src/structural_screening_agent/presentation.py`
- Modify: `src/structural_screening_agent/localization.py`
- Modify: `src/structural_screening_agent/intake_snapshot.py`
- Modify: `src/structural_screening_agent/app_state.py`
- Modify: `src/structural_screening_agent/report_generator.py`
- Modify: `src/structural_screening_agent/demo_data.py`
- Modify: `tests/test_project_layout.py`
- Modify: `tests/test_presentation.py`
- Modify: `tests/test_report_preview.py`
- Modify: `tests/test_report_generator.py`
- Modify: `tests/test_demo_experience.py`
- Modify: `tests/test_localization.py`

## Task 1: Introduce Tab-Oriented Presentation Contracts

**Files:**
- Modify: `src/structural_screening_agent/presentation.py`
- Test: `tests/test_presentation.py`

- [ ] **Step 1: Write the failing presentation tests**

```python
def test_build_ui_tabs_exposes_five_tab_sections() -> None:
    evaluation = evaluate_case(main_demo_case().model_dump())

    view = build_tabbed_ui_view(evaluation, language="zh")

    assert view.default_tab == "assessment"
    assert view.tab_labels == ["项目输入", "评估结论", "依据与追溯", "报告导出", "计算扩展"]


def test_assessment_tab_prioritizes_conclusion_controls_and_calculations() -> None:
    evaluation = evaluate_case(main_demo_case().model_dump())

    view = build_tabbed_ui_view(evaluation, language="zh")

    assert view.assessment_tab.conclusion_cards
    assert view.assessment_tab.control_cards
    assert view.assessment_tab.key_calculation_cards
    assert view.assessment_tab.evidence_cards
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_presentation.py -q`
Expected: FAIL because `build_tabbed_ui_view` and tab-scoped contracts do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
class AssessmentTabView(BaseModel):
    conclusion_cards: List[ContentCard]
    control_cards: List[ContentCard]
    key_calculation_cards: List[ContentCard]
    evidence_cards: List[ContentCard]


class BasisTraceabilityTabView(BaseModel):
    basis_cards: List[ContentCard]
    trace_cards: List[ContentCard]


class ExportTabView(BaseModel):
    title: str
    export_note: str
    preview_sections: List[ContentCard]


class ExtensionTabView(BaseModel):
    overview_cards: List[ContentCard]


class TabbedUIView(BaseModel):
    default_tab: Literal["assessment"]
    tab_labels: List[str]
    input_summary: List[str]
    assessment_tab: AssessmentTabView
    basis_traceability_tab: BasisTraceabilityTabView
    export_tab: ExportTabView
    extension_tab: ExtensionTabView
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_presentation.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/presentation.py tests/test_presentation.py
git commit -m "feat: add tab-oriented presentation contract"
```

## Task 2: Rebuild the Streamlit Layout Around Five Tabs

**Files:**
- Modify: `app.py`
- Test: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing layout tests**

```python
def test_app_uses_streamlit_tabs_for_primary_navigation() -> None:
    source = Path("app.py").read_text()

    assert "st.tabs(" in source
    assert "项目输入" in source or 'translate(ui_language, "project_intake")' in source


def test_app_no_longer_renders_single_page_report_grid_on_main_surface() -> None:
    source = Path("app.py").read_text()

    assert "ssa-report-grid" not in source
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_layout.py -q`
Expected: FAIL because the current app still renders the single-page stacked layout.

- [ ] **Step 3: Write minimal implementation**

```python
input_tab, assessment_tab, basis_tab, export_tab, extension_tab = st.tabs(
    [
        translate(ui_language, "project_input_tab"),
        translate(ui_language, "assessment_tab"),
        translate(ui_language, "basis_traceability_tab"),
        translate(ui_language, "report_export_tab"),
        translate(ui_language, "calculation_extension_tab"),
    ]
)
```

Then move:

- the form into `input_tab`
- the conclusion-first cards into `assessment_tab`
- the basis and traces into `basis_tab`
- export button and short preview into `export_tab`
- placeholders into `extension_tab`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_layout.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_project_layout.py
git commit -m "feat: replace stacked page with tabbed UI"
```

## Task 3: Simplify the Assessment Tab and Demote Formulas

**Files:**
- Modify: `src/structural_screening_agent/presentation.py`
- Modify: `app.py`
- Test: `tests/test_presentation.py`

- [ ] **Step 1: Write the failing assessment-tab tests**

```python
def test_assessment_tab_uses_key_calculation_cards_without_full_formula_priority() -> None:
    evaluation = evaluate_case(main_demo_case().model_dump())

    view = build_tabbed_ui_view(evaluation, language="zh")

    assert any("檩条强度比" in card.title for card in view.assessment_tab.key_calculation_cards)
    assert all("计算式" not in card.title for card in view.assessment_tab.key_calculation_cards)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_presentation.py -q`
Expected: FAIL because formulas and values are still mixed in the same top-level card emphasis.

- [ ] **Step 3: Write minimal implementation**

```python
def _build_key_calculation_cards(...):
    return [
        ContentCard(
            title="檩条强度比",
            detail="0.90\n结论：当前未成为最不利控制项",
            tone="amber",
        )
    ]
```

Keep formulas either:

- in a lower-emphasis line inside the detail body, or
- in a separate expandable section in `app.py`

but not as equal-weight card content.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_presentation.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/presentation.py app.py tests/test_presentation.py
git commit -m "feat: simplify assessment tab calculation hierarchy"
```

## Task 4: Make the Main UI Strictly Single-Language

**Files:**
- Modify: `src/structural_screening_agent/localization.py`
- Modify: `src/structural_screening_agent/report_generator.py`
- Test: `tests/test_localization.py`
- Test: `tests/test_report_preview.py`

- [ ] **Step 1: Write the failing localization tests**

```python
def test_ui_tab_labels_are_single_language_only() -> None:
    assert translate("zh", "assessment_tab") == "评估结论"
    assert translate("en", "assessment_tab") == "Assessment"


def test_report_preview_export_center_uses_single_language_title() -> None:
    preview = build_report_preview(...)
    assert preview.title == "复核摘要"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_localization.py tests/test_report_preview.py -q`
Expected: FAIL because current labels still reflect old memo/workbench structures.

- [ ] **Step 3: Write minimal implementation**

```python
TRANSLATIONS.update(
    {
        "project_input_tab": {"zh": "项目输入", "en": "Project Input"},
        "assessment_tab": {"zh": "评估结论", "en": "Assessment"},
        "basis_traceability_tab": {"zh": "依据与追溯", "en": "Basis & Traceability"},
        "report_export_tab": {"zh": "报告导出", "en": "Report Export"},
        "calculation_extension_tab": {"zh": "计算扩展", "en": "Calculation Extension"},
    }
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_localization.py tests/test_report_preview.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/localization.py src/structural_screening_agent/report_generator.py tests/test_localization.py tests/test_report_preview.py
git commit -m "feat: enforce single-language main UI labels"
```

## Task 5: Turn Report Preview Into a Lightweight Export Center

**Files:**
- Modify: `app.py`
- Modify: `src/structural_screening_agent/report_generator.py`
- Test: `tests/test_report_generator.py`

- [ ] **Step 1: Write the failing export-center tests**

```python
def test_report_export_tab_uses_short_preview_sections() -> None:
    preview = build_report_preview(...)

    assert len(preview.sections) <= 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_report_generator.py -q`
Expected: FAIL because the current preview still mirrors many full report sections.

- [ ] **Step 3: Write minimal implementation**

```python
sections = [
    ReportPreviewSection(heading="导出摘要", items=[...]),
    ReportPreviewSection(heading="结论摘录", items=[...]),
    ReportPreviewSection(heading="关键计算摘录", items=[...]),
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_report_generator.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app.py src/structural_screening_agent/report_generator.py tests/test_report_generator.py
git commit -m "feat: convert report preview into export center"
```

## Task 6: Add Calculation Extension Placeholder Interface

**Files:**
- Modify: `app.py`
- Modify: `src/structural_screening_agent/presentation.py`
- Test: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing extension-tab tests**

```python
def test_app_renders_calculation_extension_tab_with_future_interfaces() -> None:
    source = Path("app.py").read_text()

    assert "计算扩展" in source
    assert "Midas" in source
    assert "SAP" in source
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_layout.py -q`
Expected: FAIL because no extension tab exists yet.

- [ ] **Step 3: Write minimal implementation**

```python
st.markdown("### 计算扩展")
st.info("后续将接入计算简图、Midas / SAP 以及外部计算接口。")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_layout.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app.py src/structural_screening_agent/presentation.py tests/test_project_layout.py
git commit -m "feat: add calculation extension placeholder tab"
```

## Task 7: Full Verification

**Files:**
- Modify as needed: any files touched in Tasks 1-6

- [ ] **Step 1: Run targeted regression**

Run: `pytest tests/test_presentation.py tests/test_project_layout.py tests/test_report_preview.py tests/test_report_generator.py tests/test_localization.py tests/test_demo_experience.py -q`
Expected: PASS

- [ ] **Step 2: Run full suite**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 3: Run syntax verification**

Run: `python3 -m py_compile app.py src/structural_screening_agent/presentation.py src/structural_screening_agent/localization.py src/structural_screening_agent/report_generator.py`
Expected: no output

- [ ] **Step 4: Run Streamlit page smoke test**

Run:

```bash
python3 - <<'PY'
from streamlit.testing.v1 import AppTest
at = AppTest.from_file("app.py").run(timeout=60)
print("EXCEPTION_COUNT=", len(at.exception))
PY
```

Expected: `EXCEPTION_COUNT= 0`

- [ ] **Step 5: Commit**

```bash
git add app.py src/structural_screening_agent/presentation.py src/structural_screening_agent/localization.py src/structural_screening_agent/report_generator.py src/structural_screening_agent/intake_snapshot.py tests/test_presentation.py tests/test_project_layout.py tests/test_report_preview.py tests/test_report_generator.py tests/test_localization.py tests/test_demo_experience.py
git commit -m "feat: redesign portal frame screening UI information architecture"
```
