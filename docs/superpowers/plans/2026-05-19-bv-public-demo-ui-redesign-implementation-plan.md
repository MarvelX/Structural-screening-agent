# BV Public Demo UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the public Streamlit demo and the job-application showcase into one restrained light visual system, while fixing mixed Chinese/English UI rendering in the demo.

**Architecture:** Keep the existing workflows, tabs, and engineering outputs intact. Concentrate the change set in the UI shell (`app.py`), centralized translation keys (`src/structural_screening_agent/localization.py`), and the static showcase (`docs/job-application/`). Use tests to lock the single-language rule and the continued presence of the BV/portal-frame workbench structure.

**Tech Stack:** Streamlit, existing localization helpers, static HTML/CSS, pytest, `py_compile`, Streamlit AppTest.

---

## File Structure

- Modify: `src/structural_screening_agent/localization.py`
  - Add translation keys for public-demo headings, tab labels, section labels, metrics, and warnings now hardcoded in `app.py`.
- Modify: `app.py`
  - Replace hardcoded bilingual strings with translation lookups, add a restrained light visual shell, and restyle the BV Review/public demo presentation without changing workflows.
- Modify: `docs/job-application/index.html`
  - Rework the application showcase information hierarchy to match the new light engineering-workbench visual direction.
- Modify: `docs/job-application/styles.css`
  - Replace the current landing-page treatment with a cleaner, more editorial product-style system.
- Modify: `tests/test_project_layout.py`
  - Update source assertions to check centralized translation usage and the continued workbench/tab structure.
- Modify: `tests/test_job_application_package.py`
  - Update static assertions for the refreshed showcase wording and CTA structure.

## Task 1: Lock the single-language UI contract in tests

**Files:**
- Modify: `tests/test_project_layout.py`
- Modify: `tests/test_job_application_package.py`

- [ ] **Step 1: Write the failing layout assertions for the language contract**

Add to `tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture`:

```python
    assert 'translate(ui_language, "public_demo_banner")' in source
    assert 'translate(ui_language, "public_demo_caption")' in source
    assert 'translate(ui_language, "bv_review_tab")' in source
    assert 'translate(ui_language, "portal_frame_tab")' in source
    assert 'translate(ui_language, "bv_review_intake_heading")' in source
    assert 'translate(ui_language, "bv_review_checklist_heading")' in source
    assert 'translate(ui_language, "bv_review_basis_heading")' in source
    assert 'translate(ui_language, "bv_review_path_heading")' in source
    assert 'translate(ui_language, "bv_review_risk_heading")' in source
    assert 'translate(ui_language, "bv_review_plan_heading")' in source
    assert 'translate(ui_language, "bv_review_warning_standards")' in source
    assert 'translate(ui_language, "bv_review_warning_objects")' in source
```

Add to `tests/test_job_application_package.py`:

```python
def test_job_application_page_uses_online_demo_cta_and_engineering_positioning() -> None:
    root = project_root()
    source = (root / "docs" / "job-application" / "index.html").read_text()

    assert "打开在线演示" in source
    assert "工程化作品证明" in source
    assert "BV PV Design Review Workbench" in source
    assert "Role Fit" not in source
    assert "Workbench" not in source
```

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `pytest tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture tests/test_job_application_package.py::test_job_application_page_uses_online_demo_cta_and_engineering_positioning -q`

Expected: FAIL because the new translation keys and updated showcase wording do not exist yet.

- [ ] **Step 3: Commit the failing-test checkpoint only if your workflow requires it**

No commit required here. Proceed directly to the implementation tasks so the diff stays reviewable.

## Task 2: Centralize the public demo and BV Review language keys

**Files:**
- Modify: `src/structural_screening_agent/localization.py`
- Modify: `tests/test_project_layout.py`

- [ ] **Step 1: Write a focused translation-coverage test**

Add to `tests/test_project_layout.py`:

```python
from structural_screening_agent.localization import TRANSLATIONS


def test_public_demo_translation_keys_exist_for_both_languages() -> None:
    required_keys = [
        "public_demo_banner",
        "public_demo_caption",
        "bv_review_tab",
        "portal_frame_tab",
        "bv_review_intake_heading",
        "bv_review_checklist_heading",
        "bv_review_basis_heading",
        "bv_review_path_heading",
        "bv_review_risk_heading",
        "bv_review_plan_heading",
        "bv_review_warning_standards",
        "bv_review_warning_objects",
    ]

    for key in required_keys:
        assert TRANSLATIONS[key]["zh"]
        assert TRANSLATIONS[key]["en"]
```

- [ ] **Step 2: Run the translation test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_public_demo_translation_keys_exist_for_both_languages -q`

Expected: FAIL with `KeyError` or missing-key assertions because the public-demo keys are not defined yet.

- [ ] **Step 3: Add the minimal translation keys**

Update `src/structural_screening_agent/localization.py` by extending `TRANSLATIONS` with keys in this shape:

```python
    "public_demo_banner": {
        "zh": "公开演示版本：仅用于 screening-level 审核支持展示，不替代正式设计、法定审批或签章计算。",
        "en": "Public demo build: for screening-level review support only; it does not replace formal design, statutory approval, or stamped calculations.",
    },
    "public_demo_caption": {
        "zh": "当前版本用于作品集展示与演示浏览，重点展示 BV 审核工作流、依据追溯和报告导出。",
        "en": "This build is intended for portfolio review and walkthroughs, focusing on BV review workflow, traceability, and report export.",
    },
    "bv_review_tab": {"zh": "BV 审核总览", "en": "BV Review"},
    "portal_frame_tab": {"zh": "门刚场景模块", "en": "Portal-Frame Scenario Module"},
    "bv_review_intake_heading": {"zh": "项目设计审核输入", "en": "Project Review Intake"},
    "bv_review_checklist_heading": {"zh": "设计资料完整性", "en": "Design Document Checklist"},
    "bv_review_basis_heading": {"zh": "审核依据", "en": "Review Basis"},
    "bv_review_path_heading": {"zh": "结构审核路径", "en": "Structural Review Path"},
    "bv_review_risk_heading": {"zh": "风险与不符合项清单", "en": "Risk & Nonconformity Register"},
    "bv_review_plan_heading": {"zh": "ITP 与审核计划", "en": "ITP & Review Plan"},
    "bv_review_warning_standards": {"zh": "请至少选择一个标准体系。", "en": "Select at least one standards system."},
    "bv_review_warning_objects": {"zh": "请至少选择一个审核对象。", "en": "Select at least one review object."},
```

If `app.py` still needs more labels during implementation, add them in the same centralized pattern rather than reintroducing inline ternaries.

- [ ] **Step 4: Run the translation test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_public_demo_translation_keys_exist_for_both_languages -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/localization.py tests/test_project_layout.py
git commit -m "feat: centralize public demo translation labels"
```

## Task 3: Rebuild the Streamlit demo shell as a restrained light workbench

**Files:**
- Modify: `app.py`
- Modify: `tests/test_project_layout.py`

- [ ] **Step 1: Extend the source assertions before editing the UI shell**

Update `tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture` with these additional assertions:

```python
    assert "st.set_page_config(page_title=\"BV PV Design Review Workbench\", layout=\"wide\")" in source
    assert 'translate(ui_language, "bv_review_tab")' in source
    assert 'translate(ui_language, "portal_frame_tab")' in source
    assert 'translate(ui_language, "public_demo_banner")' in source
    assert 'translate(ui_language, "public_demo_caption")' in source
    assert 'translate(ui_language, "bv_review_intake_heading")' in source
```

- [ ] **Step 2: Run the layout assertion test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture -q`

Expected: FAIL because `app.py` still contains hardcoded BV/public-demo strings.

- [ ] **Step 3: Replace the hardcoded public-demo shell and tab labels**

Update `app.py` to:

1. Keep the title as the product name
2. Replace top-level hardcoded captions/info banners with translation lookups
3. Replace tab labels with translation lookups
4. Replace the BV Review warnings and headings with translation lookups

Use this pattern:

```python
st.title("BV PV Design Review Workbench")
st.caption(
    "面向第三方审核工程师的光伏土建、钢结构、支架、基础与既有屋面增载设计审核工作台。"
    if ui_language == "zh"
    else "Third-party PV civil, structural, mounting, foundation, and existing-rooftop design review workbench."
)
st.info(translate(ui_language, "public_demo_banner"))
st.caption(translate(ui_language, "public_demo_caption"))

bv_review_tab, assessment_tab, input_tab, basis_tab, export_tab, extension_tab = st.tabs(
    [
        translate(ui_language, "bv_review_tab"),
        translate(ui_language, "assessment_tab"),
        translate(ui_language, "project_input_tab"),
        translate(ui_language, "basis_traceability_tab"),
        translate(ui_language, "report_export_tab"),
        translate(ui_language, "portal_frame_tab"),
    ]
)
```

Replace the BV Review section headings and warnings similarly:

```python
    st.subheader(translate(ui_language, "bv_review_intake_heading"))
    st.markdown(f"#### {translate(ui_language, 'bv_review_checklist_heading')}")
    ...
        st.warning(translate(ui_language, "bv_review_warning_standards"))
    ...
        st.warning(translate(ui_language, "bv_review_warning_objects"))
```

- [ ] **Step 4: Add a light visual shell with minimal CSS in `app.py`**

Add a scoped `st.markdown(..., unsafe_allow_html=True)` style block near the top of `app.py` that:

- softens the page background
- normalizes card radius to 8px
- lightens borders/shadows
- gives tabs a cleaner light selected state
- avoids large gradients or decorative blocks

A safe starting block:

```python
st.markdown(
    """
    <style>
    .stApp {
        background: #f5f7fa;
        color: #15202b;
    }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dde5ec;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    [data-testid="stTabs"] button[role="tab"] {
        border-radius: 8px;
        border: 1px solid #dde5ec;
        background: #ffffff;
        padding: 0.5rem 0.9rem;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #0b63ce;
        border-color: #b7d0ee;
        box-shadow: inset 0 0 0 1px rgba(11, 99, 206, 0.08);
    }
    div[data-testid="stVerticalBlock"] div[data-testid="stMarkdownContainer"] h4 {
        margin-top: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
```

Do not chase pixel-perfect custom components. Keep the shell declarative and small.

- [ ] **Step 5: Refine the BV Review panel hierarchy without changing workflow**

In `app.py`, keep the current form and evaluation flow, but tighten the BV Review section presentation:

- use stable `st.columns` for metrics
- keep basis / path / risk / plan in a consistent two-column panel rhythm
- keep report preview below the summary blocks
- avoid repeating boundary captions in every subsection

Use existing helpers such as `_render_bv_section` rather than inventing a new component stack.

- [ ] **Step 6: Run the fast verification**

Run: `pytest tests/test_project_layout.py::test_app_py_compiles tests/test_project_layout.py::test_app_py_uses_tabbed_information_architecture -q`

Expected: PASS.

- [ ] **Step 7: Run the Streamlit smoke test**

Run: `pytest tests/test_project_layout.py::test_app_runs_without_streamlit_exceptions -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add app.py tests/test_project_layout.py
git commit -m "feat: restyle public streamlit demo shell"
```

## Task 4: Refresh the job-application showcase into the same visual system

**Files:**
- Modify: `docs/job-application/index.html`
- Modify: `docs/job-application/styles.css`
- Modify: `tests/test_job_application_package.py`

- [ ] **Step 1: Add the failing static assertions for the refreshed showcase**

Extend `tests/test_job_application_package.py` with:

```python
def test_job_application_page_uses_chinese_section_labels_and_no_english_kickers() -> None:
    root = project_root()
    source = (root / "docs" / "job-application" / "index.html").read_text()

    assert "岗位匹配" in source
    assert "产品证明" in source
    assert "为什么这不是一个普通 AI demo" in source
    assert "Role Fit" not in source
    assert "Workbench" not in source
    assert "Engineering Boundary" not in source
```

- [ ] **Step 2: Run the job-application static tests to verify they fail**

Run: `pytest tests/test_job_application_package.py::test_job_application_page_uses_chinese_section_labels_and_no_english_kickers -q`

Expected: FAIL because the current page still includes English kickers like `Role Fit`, `Workbench`, and `Engineering Boundary`.

- [ ] **Step 3: Rewrite the showcase HTML hierarchy**

Update `docs/job-application/index.html` to:

- keep the same sections and links
- remove English section kickers used as visible UI labels
- make the hero more restrained and product-like
- keep the primary CTA as `打开在线演示`

Use section heading markup like:

```html
<div class="section-heading">
  <p class="section-kicker">岗位匹配</p>
  <h2>我如何对应这个岗位</h2>
</div>
```

And for the product proof section:

```html
<div class="section-heading">
  <p class="section-kicker">产品证明</p>
  <h2>这不是口头理解，而是可运行工作台</h2>
</div>
```

If any English helper phrase remains visible, it must be deliberate product naming, not generic UI filler.

- [ ] **Step 4: Replace the CSS with a lighter, more restrained system**

Update `docs/job-application/styles.css` so it uses:

- lighter page background
- smaller, cleaner hero
- restrained blue accent
- lighter borders and smaller shadows
- tighter tables and panels

Keep a simple CSS variable palette in this shape:

```css
:root {
  --bg: #f5f7fa;
  --surface: #ffffff;
  --surface-soft: #f8fafc;
  --text: #16202a;
  --muted: #5e6b77;
  --line: #dde5ec;
  --accent: #0b63ce;
  --shadow: 0 16px 36px rgba(15, 23, 42, 0.05);
}
```

Do not add dark hero bands, large gradients, or oversized editorial typography.

- [ ] **Step 5: Run the job-application tests**

Run: `pytest tests/test_job_application_package.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/job-application/index.html docs/job-application/styles.css tests/test_job_application_package.py
git commit -m "feat: refresh bv job application showcase ui"
```

## Task 5: Final verification and cleanup

**Files:**
- Verify only; no intentional new file edits

- [ ] **Step 1: Run the targeted regression suite**

Run: `pytest tests/test_project_layout.py tests/test_job_application_package.py -q`

Expected: PASS.

- [ ] **Step 2: Run the broader safe suite used in this repo**

Run: `pytest tests --ignore-glob='* 2.py' -q`

Expected: PASS, with the existing duplicate-file workaround still required.

- [ ] **Step 3: Manually open the local demo and check language behavior**

Run the app locally if it is not already running:

```bash
python3 -m streamlit run app.py --server.port 8505 --server.headless true
```

Then verify:

- Chinese mode shows no English UI fragments in the public-demo banner, tabs, headings, and warnings
- English mode shows no fixed Chinese UI text in those same areas
- BV Review, Assessment, Basis, Report Export, and Portal-Frame tabs still render

- [ ] **Step 4: Commit the final verification checkpoint if no code changed in this task**

No commit is required if verification does not change files. If a tiny regression fix is needed, commit it with a focused message such as:

```bash
git add app.py src/structural_screening_agent/localization.py tests/test_project_layout.py tests/test_job_application_package.py
git commit -m "fix: polish public demo language and ui details"
```

## Self-Review

- Spec coverage:
  - unified light visual system: covered by Tasks 3 and 4
  - single-language UI rule: covered by Tasks 1, 2, and 5
  - no core logic changes: enforced in file structure and task scope
  - continued BV/portal-frame workflows: covered by Task 5 verification
- Placeholder scan:
  - no `TODO`/`TBD` placeholders remain
  - all tasks include file paths, commands, and expected outcomes
- Type and naming consistency:
  - translation keys referenced in Task 3 are introduced in Task 2
  - static showcase assertions in Task 4 match the intended Chinese-facing page copy

