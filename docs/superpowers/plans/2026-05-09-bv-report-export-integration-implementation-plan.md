# BV Report Export Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add BV Markdown / Word / PDF export to the new BV Review Mode while keeping the existing portal-frame export flow unchanged.

**Architecture:** Reuse the existing `report_export.py` Word/PDF pipeline because it only depends on preview-shaped data (`title`, `sections`, `items`). Add BV-specific Markdown generation and filename helpers in `structural_screening_agent.bv_review.report`, then wire BV download buttons into the `BV Review` tab without changing the legacy export tab semantics.

**Tech Stack:** Streamlit, Pydantic v2, pytest, `python-docx`, `reportlab`, existing `bv_review` workflow/report preview.

---

## File Structure

- Modify: `src/structural_screening_agent/bv_review/report.py`
  - Add BV Markdown export and filename helper.
- Modify: `app.py`
  - Add BV export buttons and BV preview rendering in the `BV Review` tab.
- Modify: `tests/test_bv_review_report.py`
  - Add tests for BV Markdown export content and workflow-attached preview.
- Modify: `tests/test_report_export_files.py`
  - Add tests proving existing DOCX/PDF exporters work with BV preview objects.

## Task 1: BV Markdown Export

**Files:**
- Modify: `src/structural_screening_agent/bv_review/report.py`
- Modify: `tests/test_bv_review_report.py`

- [ ] **Step 1: Write the failing BV export tests**

Add to `tests/test_bv_review_report.py`:

```python
from datetime import date

from structural_screening_agent.bv_review.report import (
    build_bv_markdown_report,
    build_bv_report_filename,
)


def test_bv_markdown_report_contains_required_sections_and_boundary_statement() -> None:
    result = evaluate_bv_review(_sample_intake())
    report = build_bv_markdown_report(_sample_intake(), result)

    assert report.startswith("# BV 光伏结构设计审查报告")
    assert "## 项目与审核范围" in report
    assert "## 审核依据" in report
    assert "## 提交资料清单与完整性状态" in report
    assert "## 审核路径与方法" in report
    assert "## 不符合项与阻塞项" in report
    assert "## 技术风险与优化建议" in report
    assert "## 后续行动" in report
    assert "## 审核边界声明" in report
    assert "不替代正式设计" in report
    assert "不代表 BV 官方签发流程" in report


def test_bv_report_filename_uses_date_and_scope_key() -> None:
    filename = build_bv_report_filename("rooftop_pv_review", report_date=date(2026, 5, 9))

    assert filename == "2026-05-09-rooftop_pv_review-bv-review-report.md"
```

- [ ] **Step 2: Run the BV export tests to verify they fail**

Run: `pytest tests/test_bv_review_report.py::test_bv_markdown_report_contains_required_sections_and_boundary_statement tests/test_bv_review_report.py::test_bv_report_filename_uses_date_and_scope_key -q`

Expected: FAIL because `build_bv_markdown_report` and `build_bv_report_filename` do not exist yet.

- [ ] **Step 3: Implement BV Markdown export**

Update `src/structural_screening_agent/bv_review/report.py` by adding:

```python
from datetime import date

from structural_screening_agent.bv_review.models import BVReportPreview, BVReportSection, BVReviewIntake, BVReviewResult


def build_bv_markdown_report(intake: BVReviewIntake, result: BVReviewResult) -> str:
    preview = result.report_preview or build_bv_report_preview(intake, result)
    lines = [f"# {preview.title}", ""]
    for section in preview.sections:
        lines.append(f"## {section.heading}")
        for item in section.items:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_bv_report_filename(scope_key: str, report_date: date | None = None) -> str:
    current_date = report_date or date.today()
    return f"{current_date.isoformat()}-{scope_key}-bv-review-report.md"
```

- [ ] **Step 4: Run the BV export tests to verify they pass**

Run: `pytest tests/test_bv_review_report.py::test_bv_markdown_report_contains_required_sections_and_boundary_statement tests/test_bv_review_report.py::test_bv_report_filename_uses_date_and_scope_key -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/bv_review/report.py tests/test_bv_review_report.py
git commit -m "feat: add bv markdown export helpers"
```

## Task 2: Reuse Word/PDF Export For BV Preview

**Files:**
- Modify: `tests/test_report_export_files.py`

- [ ] **Step 1: Write the failing BV DOCX/PDF export test**

Add to `tests/test_report_export_files.py`:

```python
from structural_screening_agent.bv_review.report import build_bv_report_preview
from structural_screening_agent.bv_review.workflow import evaluate_bv_review
from structural_screening_agent.bv_review.models import BVReviewIntake


def _sample_bv_intake() -> BVReviewIntake:
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


def test_report_export_generates_docx_and_pdf_bytes_for_bv_preview() -> None:
    intake = _sample_bv_intake()
    result = evaluate_bv_review(intake)
    preview = build_bv_report_preview(intake, result)

    docx_bytes = build_docx_report_bytes(preview)
    pdf_bytes = build_pdf_report_bytes(preview)

    assert docx_bytes[:2] == b"PK"
    assert pdf_bytes[:4] == b"%PDF"
    assert len(docx_bytes) > 3000
    assert len(pdf_bytes) > 1500
```

- [ ] **Step 2: Run the BV DOCX/PDF export test**

Run: `pytest tests/test_report_export_files.py::test_report_export_generates_docx_and_pdf_bytes_for_bv_preview -q`

Expected: PASS or FAIL only if current export helpers are too tightly typed. If it fails, capture the exact mismatch before editing code.

- [ ] **Step 3: If needed, minimally generalize export helpers**

If the test fails because `report_export.py` is too tightly coupled to `report_generator.ReportPreview`, update only the type hints and local helper signatures to accept preview-shaped objects without changing runtime behavior. A safe pattern is:

```python
from typing import Protocol, Iterable


class PreviewSectionLike(Protocol):
    heading: str
    items: list[str]


class PreviewLike(Protocol):
    title: str
    sections: list[PreviewSectionLike]
```

Then use `PreviewLike` in `build_docx_report_bytes`, `build_pdf_report_bytes`, `_iter_preview_items`, `_key_export_sections`, and `_cover_metadata_line`.

- [ ] **Step 4: Run the BV DOCX/PDF export test to verify it passes**

Run: `pytest tests/test_report_export_files.py::test_report_export_generates_docx_and_pdf_bytes_for_bv_preview -q`

Expected: PASS.

- [ ] **Step 5: Commit**

If `report_export.py` changed:

```bash
git add src/structural_screening_agent/report_export.py tests/test_report_export_files.py
git commit -m "feat: support bv preview in docx and pdf export"
```

If only the test was added:

```bash
git add tests/test_report_export_files.py
git commit -m "test: cover bv docx and pdf export"
```

## Task 3: BV Download Buttons In Streamlit

**Files:**
- Modify: `app.py`
- Modify: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing layout test for BV export controls**

Add to `tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture`:

```python
    assert "build_bv_markdown_report" in source
    assert "build_bv_report_filename" in source
    assert "download_bv_markdown_report" in source or "Download BV Markdown Report" in source
    assert "download_bv_word_report" in source or "Download BV Word Report" in source
    assert "download_bv_pdf_report" in source or "Download BV PDF Report" in source
```

- [ ] **Step 2: Run the layout test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture -q`

Expected: FAIL because BV export functions/buttons are not referenced yet.

- [ ] **Step 3: Add BV export wiring in app**

Update `app.py` imports:

```python
from structural_screening_agent.bv_review.report import (
    build_bv_markdown_report,
    build_bv_report_filename,
)
```

Inside `with bv_review_tab:`, after `bv_result = evaluate_bv_review(bv_intake)` and before the metrics, add:

```python
    bv_scope_key = "_".join(bv_intake.review_objects[:2]) or "bv_review"
    bv_report_filename = build_bv_report_filename(bv_scope_key)
    bv_report_docx_filename = bv_report_filename.replace(".md", ".docx")
    bv_report_pdf_filename = bv_report_filename.replace(".md", ".pdf")
    bv_markdown_report = build_bv_markdown_report(bv_intake, bv_result)
```

After the ITP / risk sections and before the existing preview loop, add BV export buttons:

```python
        export_col_1, export_col_2, export_col_3 = st.columns(3)
        with export_col_1:
            st.download_button(
                "Download BV Markdown Report" if ui_language == "en" else "下载 BV Markdown 报告",
                data=bv_markdown_report,
                file_name=bv_report_filename,
                mime="text/markdown",
                use_container_width=True,
                key="download_bv_markdown_report",
            )
        with export_col_2:
            st.download_button(
                "Download BV Word Report" if ui_language == "en" else "下载 BV Word 报告",
                data=build_docx_report_bytes(bv_result.report_preview),
                file_name=bv_report_docx_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key="download_bv_word_report",
            )
        with export_col_3:
            st.download_button(
                "Download BV PDF Report" if ui_language == "en" else "下载 BV PDF 报告",
                data=build_pdf_report_bytes(bv_result.report_preview),
                file_name=bv_report_pdf_filename,
                mime="application/pdf",
                use_container_width=True,
                key="download_bv_pdf_report",
            )
```

Use `bv_result.report_preview` directly only after confirming it is not `None`; if needed, keep it guarded under the same `if bv_result.report_preview is not None:` block as the preview rendering.

- [ ] **Step 4: Run the layout test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture -q`

Expected: PASS.

- [ ] **Step 5: Run AppTest smoke**

Run: `pytest tests/test_project_layout.py::test_app_runs_without_streamlit_exceptions -q`

Expected: PASS or SKIP if `streamlit.testing.v1` is unavailable.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_project_layout.py
git commit -m "feat: add bv report downloads to streamlit app"
```

## Task 4: Regression And Plan Closure

**Files:**
- Modify: `docs/superpowers/plans/2026-05-09-bv-report-export-integration-implementation-plan.md`

- [ ] **Step 1: Run focused BV export tests**

Run: `pytest tests/test_bv_review_report.py tests/test_report_export_files.py tests/test_project_layout.py -q`

Expected: PASS.

- [ ] **Step 2: Run all tests**

Run: `pytest -q`

Expected: PASS.

- [ ] **Step 3: Verify worktree status**

Run: `git status --short`

Expected: clean before plan checkbox update.

- [ ] **Step 4: Mark this plan complete**

Edit `docs/superpowers/plans/2026-05-09-bv-report-export-integration-implementation-plan.md` so completed checkbox steps use `- [x]`.

- [ ] **Step 5: Commit plan progress**

```bash
git add docs/superpowers/plans/2026-05-09-bv-report-export-integration-implementation-plan.md
git commit -m "docs: update bv report export integration plan progress"
```

## Phase 3 Completion Criteria

- BV Markdown export exists and contains required sections and boundary statement.
- Existing DOCX/PDF exporters can serialize BV preview content.
- BV Review tab exposes Markdown / Word / PDF download buttons.
- Existing portal-frame export behavior remains intact.
- Focused export tests and `pytest -q` pass.

## Follow-Up Plan After Phase 3

- Phase 4: README, showcase docs, and screenshot refresh for BV positioning.
