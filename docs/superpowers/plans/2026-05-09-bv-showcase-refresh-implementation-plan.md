# BV Showcase Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the repository-facing README and showcase docs so they present the app as `BV PV Design Review Workbench` while preserving the portal-frame rooftop screening module as the first embedded scenario.

**Architecture:** Treat this phase as a documentation-only surface refresh. Reuse the current screenshots and app capabilities, update the product narrative to lead with BV design review, and keep explicit wording that the legacy portal-frame rooftop PV screening flow remains available as a scenario module inside the broader workbench.

**Tech Stack:** Markdown docs, pytest static doc/layout checks, existing showcase assets.

---

## File Structure

- Modify: `README.md`
  - Reposition the repo as BV PV Design Review Workbench, update capability framing, quick-run notes, and boundary statements.
- Modify: `docs/showcase/demo-guide.md`
  - Update the demo walkthrough to start from the BV Review tab and then show the retained portal-frame module.
- Modify: `docs/showcase/project-brief.md`
  - Replace the old single-scenario pitch with the BV design review positioning and explicitly mention the retained screening kernel.
- Modify: `tests/test_project_layout.py`
  - Update showcase text assertions so the test suite protects the new public-facing narrative.

## Task 1: Refresh README Positioning

**Files:**
- Modify: `README.md`
- Modify: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing README narrative test**

Add or update assertions in `tests/test_project_layout.py::test_readme_mentions_showcase_positioning`:

```python
    assert "BV PV Design Review Workbench" in readme
    assert "BV 光伏结构设计审核工作台" in readme
    assert "门式刚架屋面光伏增载场景模块" in readme
    assert "docs/showcase/demo-guide.md" in readme
```

- [ ] **Step 2: Run the targeted README test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_readme_mentions_showcase_positioning -q`

Expected: FAIL because the current README still opens with the old portal-frame-only positioning.

- [ ] **Step 3: Update README copy**

Revise `README.md` so it includes:

```md
# BV PV Design Review Workbench

`BV 光伏结构设计审核工作台`

面向第三方审核工程师的光伏土建、钢结构、支架与基础设计审核工具，用于组织审核范围、审核依据、资料完整性、风险清单、审核计划和设计审查报告输出。

当前仓库保留原有**门式刚架屋面光伏增载场景模块**，作为 BV 审核工作台中的第一个结构筛查场景。
```

Also update the surrounding sections so they reflect:

- BV Review tab as the lead workflow
- legacy portal-frame screening as an embedded scenario module
- Markdown / Word / PDF export for both workbench reporting and scenario reporting
- the product boundary remains screening/review support rather than formal stamped design

- [ ] **Step 4: Run the targeted README test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_readme_mentions_showcase_positioning -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_project_layout.py
git commit -m "docs: refresh readme for bv workbench"
```

## Task 2: Refresh Demo Guide Walkthrough

**Files:**
- Modify: `docs/showcase/demo-guide.md`
- Modify: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing demo-guide assertions**

Update `tests/test_project_layout.py::test_showcase_docs_contain_expected_sections`:

```python
    assert "BV 审核总览" in demo_guide
    assert "门刚场景模块" in demo_guide
    assert "设计审查报告预览" in demo_guide
```

- [ ] **Step 2: Run the targeted showcase-doc test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_showcase_docs_contain_expected_sections -q`

Expected: FAIL because the guide still describes only the old portal-frame screening flow.

- [ ] **Step 3: Update the demo guide**

Revise `docs/showcase/demo-guide.md` so the walkthrough becomes:

```md
## 这个 demo 是什么

这是一个面向第三方审核工程师的 `BV PV Design Review Workbench` demo。

你应该先看 `BV 审核总览`，理解项目范围、审核依据、资料缺口、风险与不符合项、ITP 和设计审查报告预览；然后再进入 `门刚场景模块`，查看已保留的屋面光伏增载 screening kernel。
```

Keep the quick-start commands and existing screenshot references, but reorganize the walkthrough in this order:

1. `BV 审核总览`
2. `评估结论`
3. `依据与追溯`
4. `报告导出`
5. `门刚场景模块`

- [ ] **Step 4: Run the targeted showcase-doc test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_showcase_docs_contain_expected_sections -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/showcase/demo-guide.md tests/test_project_layout.py
git commit -m "docs: refresh bv showcase demo guide"
```

## Task 3: Refresh Project Brief Narrative

**Files:**
- Modify: `docs/showcase/project-brief.md`
- Modify: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing project-brief assertions**

Update `tests/test_project_layout.py::test_showcase_docs_contain_expected_sections` and `tests/test_showcase_docs_link_to_assets_and_each_other` expectations as needed so they also require:

```python
    assert "BV PV Design Review Workbench" in brief
    assert "第三方审核工程师" in brief
    assert "门式刚架屋面光伏增载场景模块" in brief
```

- [ ] **Step 2: Run the targeted showcase-doc test to verify it fails**

Run: `pytest tests/test_project_layout.py::test_showcase_docs_contain_expected_sections -q`

Expected: FAIL because the brief still uses the old portal-frame-only product statement.

- [ ] **Step 3: Update the project brief**

Revise `docs/showcase/project-brief.md` so it opens with:

```md
## 项目一句话

这是一个面向第三方审核工程师的 `BV PV Design Review Workbench / BV 光伏结构设计审核工作台`，用于组织光伏土建、钢结构、支架、基础和既有屋面增载设计审核。
```

Ensure the brief also states:

- the existing structural screening kernel remains in the product as the first scenario module
- the workbench supports review scope, basis, document completeness, risk register, ITP/review plan, and report composition
- the boundary remains review support rather than formal design sign-off

- [ ] **Step 4: Run the targeted showcase-doc test to verify it passes**

Run: `pytest tests/test_project_layout.py::test_showcase_docs_contain_expected_sections -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/showcase/project-brief.md tests/test_project_layout.py
git commit -m "docs: refresh bv showcase brief"
```

## Task 4: Final Doc Regression

**Files:**
- Modify: `tests/test_project_layout.py` (only if the prior tasks reveal missing assertions)

- [ ] **Step 1: Run the showcase-focused regression**

Run: `pytest tests/test_project_layout.py -q`

Expected: PASS.

- [ ] **Step 2: Run the full test suite**

Run: `pytest -q`

Expected: PASS with the current global baseline or better.

- [ ] **Step 3: Commit any final test-only adjustments if needed**

If additional assertion cleanup was required:

```bash
git add tests/test_project_layout.py
git commit -m "test: align showcase narrative assertions"
```

If no further changes were needed, skip this commit.
