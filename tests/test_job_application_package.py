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


def test_pdf_attachment_exists_and_is_a_pdf() -> None:
    root = project_root()
    pdf_path = root / "docs" / "job-application" / "attachments" / "BV-job-application-one-pager.pdf"

    assert pdf_path.exists()
    assert pdf_path.read_bytes()[:4] == b"%PDF"
    assert pdf_path.stat().st_size > 20_000
