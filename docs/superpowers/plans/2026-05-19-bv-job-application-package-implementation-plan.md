# BV Job Application Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public Chinese-first job-application package for the BV role, consisting of a public microsite, a one-page PDF, a 6-8 slide PPT, and a ready-to-send email draft that all prove strong fit to the structural design review position.

**Architecture:** Reuse the existing BV Workbench narrative and screenshot assets, but reorganize them into a job-application surface under `docs/job-application/`. Keep the site fully static so it can be previewed locally and published via GitHub Pages from the repo `docs/` folder. Treat the PDF, PPT, and email draft as first-class tracked artifacts under `docs/job-application/attachments/`.

**Tech Stack:** Static HTML/CSS, existing showcase PNG assets, pytest static-file assertions, GitHub Pages publishing via `gh api`, Documents skill for PDF/DOCX, Presentations skill for PPTX.

---

## File Structure

- Create: `docs/job-application/index.html`
  - Public microsite entrypoint served from GitHub Pages under `/job-application/`.
- Create: `docs/job-application/styles.css`
  - Professional engineering-review visual layer for the microsite.
- Create: `docs/job-application/content/application-copy.md`
  - Canonical Chinese-first source copy for site/PDF/PPT/email reuse.
- Create: `docs/job-application/attachments/BV-job-application-one-pager.docx`
  - Editable source for the one-page attachment.
- Create: `docs/job-application/attachments/BV-job-application-one-pager.pdf`
  - Final one-page attachment for HR.
- Create: `docs/job-application/attachments/BV-job-application-deck.pptx`
  - 6-8 page deck for technical review.
- Create: `docs/job-application/attachments/bv-application-email.md`
  - Ready-to-send email body in Chinese.
- Create: `tests/test_job_application_package.py`
  - Static regression tests for site, copy, and attachment presence.
- Modify: `README.md`
  - Add a short pointer to the job-application package once it exists.

## Task 1: Canonical Copy Source

**Files:**
- Create: `docs/job-application/content/application-copy.md`
- Create: `tests/test_job_application_package.py`

- [ ] **Step 1: Write the failing copy-source test**

Create `tests/test_job_application_package.py` with:

```python
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_application_copy_exists_and_contains_core_sections() -> None:
    root = project_root()
    copy_path = root / "docs" / "job-application" / "content" / "application-copy.md"

    assert copy_path.exists()

    content = copy_path.read_text()
    assert "# BV Job Application Package Copy" in content
    assert "目标岗位" in content
    assert "岗位匹配" in content
    assert "产品证明" in content
    assert "当前边界" in content
    assert "附件清单" in content
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run: `pytest tests/test_job_application_package.py::test_application_copy_exists_and_contains_core_sections -q`

Expected: FAIL because the file does not exist yet.

- [ ] **Step 3: Create the canonical copy file**

Create `docs/job-application/content/application-copy.md` with:

```md
# BV Job Application Package Copy

## 目标岗位

- 第三方光伏结构设计审核岗位
- 重点职责：独立审核、规范应用、risk register、ITP/review plan、design review report

## 候选人定位

- 我不仅理解光伏结构设计审核的工作流，也已经把它做成了可运行的工程审核工作台

## 岗位匹配

- 独立审核图纸、计算书和技术规格书
- 应用 GB / IEC / AS/NZS / Eurocode
- 组织 review scope、basis、document completeness、risk register、ITP、report

## 产品证明

- BV 审核总览
- 评估结论
- 依据与追溯
- 报告导出

## 当前边界

- screening / review-support level
- 首个场景模块聚焦门式刚架屋面光伏增载
- 质量体系流转、项目协同、外部软件接口仍需补强

## 附件清单

- 公开展示页
- 1 页 PDF
- 6-8 页 PPT
- 邮件正文
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run: `pytest tests/test_job_application_package.py::test_application_copy_exists_and_contains_core_sections -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/job-application/content/application-copy.md tests/test_job_application_package.py
git commit -m "docs: add application package copy source"
```

## Task 2: Public Microsite

**Files:**
- Create: `docs/job-application/index.html`
- Create: `docs/job-application/styles.css`
- Modify: `tests/test_job_application_package.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing microsite test**

Append to `tests/test_job_application_package.py`:

```python
def test_job_application_site_exists_and_contains_required_sections() -> None:
    root = project_root()
    html_path = root / "docs" / "job-application" / "index.html"
    css_path = root / "docs" / "job-application" / "styles.css"

    assert html_path.exists()
    assert css_path.exists()

    html = html_path.read_text()
    assert "第三方光伏结构设计审核岗位的工程化作品证明" in html
    assert "岗位匹配" in html
    assert "产品证明" in html
    assert "为什么这不是一个普通 AI demo" in html
    assert "JD 条款 - 产品模块 - 当前覆盖度" in html
    assert "下载 PDF" in html
    assert "下载 PPT" in html
```

- [ ] **Step 2: Run the targeted site test to verify it fails**

Run: `pytest tests/test_job_application_package.py::test_job_application_site_exists_and_contains_required_sections -q`

Expected: FAIL because the site files do not exist yet.

- [ ] **Step 3: Create the public site**

Create `docs/job-application/index.html` with a single-page structure that includes:

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>BV 光伏结构设计审核岗位作品证明</title>
    <link rel="stylesheet" href="./styles.css" />
  </head>
  <body>
    <header class="hero">
      <p class="eyebrow">Job Application Package</p>
      <h1>第三方光伏结构设计审核岗位的工程化作品证明</h1>
      <p class="lede">
        我不仅理解光伏结构设计审核的真实职责，也已经把这套审核工作流做成了可运行的 BV PV Design Review Workbench。
      </p>
      <div class="actions">
        <a href="#product-proof" class="button primary">查看产品展示</a>
        <a href="./attachments/BV-job-application-one-pager.pdf" class="button">下载 PDF</a>
        <a href="./attachments/BV-job-application-deck.pptx" class="button">下载 PPT</a>
      </div>
    </header>

    <main>
      <section id="fit">
        <h2>岗位匹配</h2>
      </section>
      <section id="product-proof">
        <h2>产品证明</h2>
      </section>
      <section id="why-not-ai-demo">
        <h2>为什么这不是一个普通 AI demo</h2>
      </section>
      <section id="jd-mapping">
        <h2>JD 条款 - 产品模块 - 当前覆盖度</h2>
      </section>
    </main>
  </body>
</html>
```

Create `docs/job-application/styles.css` with:

```css
:root {
  color-scheme: light;
  --bg: #f4f6f8;
  --surface: #ffffff;
  --text: #16202a;
  --muted: #5e6b78;
  --line: #d9e1e7;
  --accent: #114b8b;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--text);
}

.hero,
main section {
  max-width: 1120px;
  margin: 0 auto;
  padding: 48px 24px;
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 18px;
  border: 1px solid var(--line);
  color: var(--text);
  text-decoration: none;
  background: var(--surface);
}

.button.primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
```

Update `README.md` near the showcase links with:

```md
- [Job Application Package](docs/job-application/index.html)
```

- [ ] **Step 4: Run the targeted site test to verify it passes**

Run: `pytest tests/test_job_application_package.py::test_job_application_site_exists_and_contains_required_sections -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/job-application/index.html docs/job-application/styles.css README.md tests/test_job_application_package.py
git commit -m "feat: add bv job application microsite"
```

## Task 3: One-Page PDF Attachment

**Files:**
- Create: `docs/job-application/attachments/BV-job-application-one-pager.docx`
- Create: `docs/job-application/attachments/BV-job-application-one-pager.pdf`
- Modify: `tests/test_job_application_package.py`

- [ ] **Step 1: Write the failing PDF artifact test**

Append to `tests/test_job_application_package.py`:

```python
def test_pdf_attachment_exists_and_is_a_pdf() -> None:
    root = project_root()
    pdf_path = root / "docs" / "job-application" / "attachments" / "BV-job-application-one-pager.pdf"

    assert pdf_path.exists()
    assert pdf_path.read_bytes()[:4] == b"%PDF"
    assert pdf_path.stat().st_size > 20_000
```

- [ ] **Step 2: Run the targeted PDF test to verify it fails**

Run: `pytest tests/test_job_application_package.py::test_pdf_attachment_exists_and_is_a_pdf -q`

Expected: FAIL because the PDF does not exist yet.

- [ ] **Step 3: Create the one-page attachment**

Use the Documents skill to create `docs/job-application/attachments/BV-job-application-one-pager.docx` and export `docs/job-application/attachments/BV-job-application-one-pager.pdf` with this exact content structure:

```text
Title:
BV 光伏结构设计审核岗位作品证明

Header strip:
- 姓名
- 目标岗位
- 公开链接

Section 1: 为什么我适合这个岗位
- 独立审核图纸、计算书、规格书
- 规范应用：GB / IEC / AS/NZS / Eurocode
- 审核计划、ITP、risk register、design review report

Section 2: 我做出的产品证明
- BV 审核总览
- 评估结论
- 依据与追溯
- 报告导出

Section 3: 当前边界与判断
- screening/review-support level
- 首个场景模块聚焦门刚屋面增载
- 下一步补强：质量体系流转 / 项目协同 / 软件接口

Footer:
- GitHub
- Demo
- 邮箱 / 电话
```

Render and visually verify the PDF before treating it as final.

- [ ] **Step 4: Run the targeted PDF test to verify it passes**

Run: `pytest tests/test_job_application_package.py::test_pdf_attachment_exists_and_is_a_pdf -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/job-application/attachments/BV-job-application-one-pager.docx docs/job-application/attachments/BV-job-application-one-pager.pdf tests/test_job_application_package.py
git commit -m "docs: add bv application one-pager"
```

## Task 4: PPT Attachment

**Files:**
- Create: `docs/job-application/attachments/BV-job-application-deck.pptx`
- Modify: `tests/test_job_application_package.py`

- [ ] **Step 1: Write the failing PPT artifact test**

Append to `tests/test_job_application_package.py`:

```python
def test_ppt_attachment_exists_and_is_a_pptx() -> None:
    root = project_root()
    pptx_path = root / "docs" / "job-application" / "attachments" / "BV-job-application-deck.pptx"

    assert pptx_path.exists()
    assert pptx_path.read_bytes()[:2] == b"PK"
    assert pptx_path.stat().st_size > 30_000
```

- [ ] **Step 2: Run the targeted PPT test to verify it fails**

Run: `pytest tests/test_job_application_package.py::test_ppt_attachment_exists_and_is_a_pptx -q`

Expected: FAIL because the PPTX does not exist yet.

- [ ] **Step 3: Create the slide deck**

Use the Presentations skill to create `docs/job-application/attachments/BV-job-application-deck.pptx` with these slides:

```text
1. 我是谁 / 我为什么投这个岗位
2. 我对 BV 第三方设计审核工作流的理解
3. 我做的产品：BV PV Design Review Workbench
4. 产品模块与 JD 职责映射
5. 关键界面：BV 审核总览 / 评估结论
6. 关键界面：依据与追溯 / 报告导出
7. 当前边界与下一步补强
8. 联系方式 / 公开链接 / GitHub
```

Design rules:

- 中文为主
- 工程审核风格
- 每页一个主结论
- 使用现有 showcase PNG 作为视觉证据

- [ ] **Step 4: Run the targeted PPT test to verify it passes**

Run: `pytest tests/test_job_application_package.py::test_ppt_attachment_exists_and_is_a_pptx -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/job-application/attachments/BV-job-application-deck.pptx tests/test_job_application_package.py
git commit -m "docs: add bv application deck"
```

## Task 5: Email Draft And Download Wiring

**Files:**
- Create: `docs/job-application/attachments/bv-application-email.md`
- Modify: `docs/job-application/index.html`
- Modify: `tests/test_job_application_package.py`

- [ ] **Step 1: Write the failing email/download test**

Append to `tests/test_job_application_package.py`:

```python
def test_email_template_exists_and_site_links_to_attachments() -> None:
    root = project_root()
    email_path = root / "docs" / "job-application" / "attachments" / "bv-application-email.md"
    html_path = root / "docs" / "job-application" / "index.html"

    assert email_path.exists()
    email = email_path.read_text()
    html = html_path.read_text()

    assert "BV PV Design Review Workbench" in email
    assert "公开展示页" in email
    assert "PDF" in email
    assert "PPT" in email
    assert "./attachments/BV-job-application-one-pager.pdf" in html
    assert "./attachments/BV-job-application-deck.pptx" in html
```

- [ ] **Step 2: Run the targeted email/download test to verify it fails**

Run: `pytest tests/test_job_application_package.py::test_email_template_exists_and_site_links_to_attachments -q`

Expected: FAIL because the email file does not exist yet.

- [ ] **Step 3: Create the email draft and finalize site links**

Create `docs/job-application/attachments/bv-application-email.md` with:

```md
主题：应聘光伏结构设计审核岗位 - 附产品作品证明

您好，

我正在应聘贵司的光伏结构设计审核岗位。结合岗位描述，我将自己对第三方光伏结构设计审核工作流的理解，做成了一个可运行的 `BV PV Design Review Workbench / BV 光伏结构设计审核工作台` 原型，并整理成了一套简短的岗位投递展示包。

公开展示页：
- https://marvelx.github.io/Structural-screening-agent/job-application/

附件包括：
- 1 页 PDF：岗位匹配与产品证明摘要
- 6-8 页 PPT：产品与审核职责映射说明

如果您愿意，我也很希望在面试中进一步介绍我对设计审核、风险识别、ITP / review plan 和设计审查报告的理解。

谢谢。
```

Keep the public-link line exactly as:

```text
https://marvelx.github.io/Structural-screening-agent/job-application/
```

- [ ] **Step 4: Run the targeted email/download test to verify it passes**

Run: `pytest tests/test_job_application_package.py::test_email_template_exists_and_site_links_to_attachments -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/job-application/attachments/bv-application-email.md docs/job-application/index.html tests/test_job_application_package.py
git commit -m "docs: add bv application email draft"
```

## Task 6: Local Preview And Public Publish

**Files:**
- Modify: `docs/job-application/attachments/bv-application-email.md`
- Modify: `README.md` (only if adding the final public-link pointer is useful)

- [ ] **Step 1: Preview the microsite locally**

Run: `python3 -m http.server 8787 -d docs`

Expected: local preview available at `http://localhost:8787/job-application/`

- [ ] **Step 2: Verify the local site content**

Check manually that:

- Hero reads as a job-application proof page, not a generic portfolio
- PDF and PPT download buttons resolve
- BV 审核总览 / 评估结论 / 依据与追溯 / 报告导出 visuals appear correctly

- [ ] **Step 3: Publish to GitHub Pages from `/docs`**

Run:

```bash
gh api repos/MarvelX/Structural-screening-agent/pages \
  --method POST \
  -f source[branch]=main \
  -f source[path]=/docs
```

If the Pages site already exists, run:

```bash
gh api repos/MarvelX/Structural-screening-agent/pages \
  --method PUT \
  -f source[branch]=main \
  -f source[path]=/docs
```

Expected: GitHub Pages configured to serve the repo `docs/` folder.

- [ ] **Step 4: Verify the public URL**

Run: `curl -I https://marvelx.github.io/Structural-screening-agent/job-application/`

Expected: `HTTP/2 200` or a temporary `HTTP/2 404` that resolves after Pages finishes building.

- [ ] **Step 5: Verify the email draft still points to the final public link**

Confirm that `docs/job-application/attachments/bv-application-email.md` contains:

```text
https://marvelx.github.io/Structural-screening-agent/job-application/
```

- [ ] **Step 6: Run the full test suite**

Run: `pytest -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add README.md docs/job-application tests/test_job_application_package.py
git commit -m "docs: publish bv job application package"
```
