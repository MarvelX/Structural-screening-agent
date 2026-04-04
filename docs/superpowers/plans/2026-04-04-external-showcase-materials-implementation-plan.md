# External Showcase Materials Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a Chinese-first external showcase package consisting of an updated README, three stable screenshots, a short demo guide, and a one-page project brief.

**Architecture:** Keep the code changes minimal and isolate showcase work into documentation and asset-generation paths. Reuse the existing Streamlit app as the screenshot source, and generate assets in a dedicated `docs/showcase/` tree so the repository front door and external materials stay organized.

**Tech Stack:** Markdown, Streamlit, lightweight browser automation for screenshots, pytest for regression checks

---

### Task 1: Create showcase document structure

**Files:**
- Create: `docs/showcase/demo-guide.md`
- Create: `docs/showcase/project-brief.md`
- Create: `docs/showcase/assets/.gitkeep`
- Test: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing test**

Add assertions to `tests/test_project_layout.py` that the showcase docs and assets directory exist:

```python
from pathlib import Path

def test_showcase_docs_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs/showcase/demo-guide.md").exists()
    assert (root / "docs/showcase/project-brief.md").exists()
    assert (root / "docs/showcase/assets").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_showcase_docs_exist -q`
Expected: FAIL because the showcase files do not exist yet

- [ ] **Step 3: Write minimal implementation**

Create the files:

- `docs/showcase/demo-guide.md` with temporary top-level headings:

```md
# Demo Guide
```

- `docs/showcase/project-brief.md` with temporary top-level headings:

```md
# Project Brief
```

- `docs/showcase/assets/.gitkeep`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_showcase_docs_exist -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_project_layout.py docs/showcase/demo-guide.md docs/showcase/project-brief.md docs/showcase/assets/.gitkeep
git commit -m "docs: add showcase document structure"
```

### Task 2: Rewrite README for external viewers

**Files:**
- Modify: `README.md`
- Test: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing test**

Add a focused README content test:

```python
def test_readme_mentions_showcase_positioning() -> None:
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text()
    assert "门式刚架屋面光伏增载" in readme
    assert "不是聊天机器人" in readme
    assert "docs/showcase/demo-guide.md" in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_readme_mentions_showcase_positioning -q`
Expected: FAIL because the current README does not match the new outward-facing copy

- [ ] **Step 3: Write minimal implementation**

Rewrite `README.md` into these sections:

- title
- one-sentence positioning
- problem statement
- core capabilities
- why this is not a generic AI demo
- screenshots section linking to three asset files
- quick start
- project boundary
- links to showcase docs

Use Chinese-first copy and keep it concise.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_readme_mentions_showcase_positioning -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_project_layout.py
git commit -m "docs: rewrite readme for external showcase"
```

### Task 3: Add the demo guide and project brief content

**Files:**
- Modify: `docs/showcase/demo-guide.md`
- Modify: `docs/showcase/project-brief.md`
- Test: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing test**

Add content assertions:

```python
def test_showcase_docs_contain_expected_sections() -> None:
    root = Path(__file__).resolve().parents[1]
    demo_guide = (root / "docs/showcase/demo-guide.md").read_text()
    brief = (root / "docs/showcase/project-brief.md").read_text()
    assert "3 分钟跑起来" in demo_guide
    assert "评估结论" in demo_guide
    assert "项目一句话" in brief
    assert "不是一个通用 AI demo" in brief
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_showcase_docs_contain_expected_sections -q`
Expected: FAIL because the content is still placeholder-level

- [ ] **Step 3: Write minimal implementation**

Populate:

- `docs/showcase/demo-guide.md` with:
  - what the demo is
  - quick start commands
  - suggested viewing order
  - current boundary

- `docs/showcase/project-brief.md` with:
  - one-sentence positioning
  - problem
  - core capabilities
  - why it is not a generic AI demo
  - boundary
  - why the project is representative

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_showcase_docs_contain_expected_sections -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/showcase/demo-guide.md docs/showcase/project-brief.md tests/test_project_layout.py
git commit -m "docs: add external demo guide and project brief"
```

### Task 4: Generate stable screenshot assets

**Files:**
- Create: `scripts/capture_showcase_screenshots.py`
- Create: `docs/showcase/assets/assessment-overview.png`
- Create: `docs/showcase/assets/basis-traceability.png`
- Create: `docs/showcase/assets/report-export.png`
- Test: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing test**

Add a file-existence test:

```python
def test_showcase_screenshot_assets_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "docs/showcase/assets/assessment-overview.png").exists()
    assert (root / "docs/showcase/assets/basis-traceability.png").exists()
    assert (root / "docs/showcase/assets/report-export.png").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_showcase_screenshot_assets_exist -q`
Expected: FAIL because the assets do not exist yet

- [ ] **Step 3: Write minimal implementation**

Create `scripts/capture_showcase_screenshots.py` that:

- opens `http://localhost:8503`
- captures the default assessment tab
- switches to the basis tab and captures
- switches to the export tab and captures
- writes files under `docs/showcase/assets/`

If a browser automation dependency is already available, reuse it. Otherwise use the smallest available option in the environment.

Run the script and generate the three PNG files.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_showcase_screenshot_assets_exist -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/capture_showcase_screenshots.py docs/showcase/assets/assessment-overview.png docs/showcase/assets/basis-traceability.png docs/showcase/assets/report-export.png tests/test_project_layout.py
git commit -m "docs: add showcase screenshots"
```

### Task 5: Link screenshots and docs together

**Files:**
- Modify: `README.md`
- Modify: `docs/showcase/demo-guide.md`
- Modify: `docs/showcase/project-brief.md`
- Test: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing test**

Add an integration-level doc test:

```python
def test_showcase_docs_link_to_assets_and_each_other() -> None:
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text()
    demo_guide = (root / "docs/showcase/demo-guide.md").read_text()
    brief = (root / "docs/showcase/project-brief.md").read_text()
    assert "docs/showcase/assets/assessment-overview.png" in readme
    assert "docs/showcase/project-brief.md" in readme
    assert "docs/showcase/assets/report-export.png" in demo_guide
    assert "docs/showcase/demo-guide.md" in brief
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_showcase_docs_link_to_assets_and_each_other -q`
Expected: FAIL until links are fully wired in

- [ ] **Step 3: Write minimal implementation**

Add:

- screenshot embeds and doc links in `README.md`
- at least one screenshot reference in `docs/showcase/demo-guide.md`
- a link back to the demo guide from `docs/showcase/project-brief.md`

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_showcase_docs_link_to_assets_and_each_other -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md docs/showcase/demo-guide.md docs/showcase/project-brief.md tests/test_project_layout.py
git commit -m "docs: wire showcase materials together"
```

### Task 6: Final verification

**Files:**
- Verify only

- [ ] **Step 1: Run focused docs/layout tests**

Run: `pytest tests/test_project_layout.py -q`
Expected: PASS

- [ ] **Step 2: Run the screenshot script again**

Run: `python3 scripts/capture_showcase_screenshots.py`
Expected: screenshot files updated without errors

- [ ] **Step 3: Run full regression**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 4: Manual smoke check**

Open:

- `README.md`
- `docs/showcase/demo-guide.md`
- `docs/showcase/project-brief.md`
- screenshot PNG files

Confirm the outward-facing story is coherent and Chinese-first.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/showcase scripts/capture_showcase_screenshots.py tests/test_project_layout.py
git commit -m "docs: finalize external showcase package"
```
