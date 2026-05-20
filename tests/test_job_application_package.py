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
    assert "为什么这不是一个普通演示页" in html
    assert "JD 条款 - 产品模块 - 当前覆盖度" in html
    assert "下载 PDF" in html
    assert "下载 PPT" in html


def test_pdf_attachment_exists_and_is_a_pdf() -> None:
    root = project_root()
    pdf_path = root / "docs" / "job-application" / "attachments" / "BV-job-application-one-pager.pdf"

    assert pdf_path.exists()
    assert pdf_path.read_bytes()[:4] == b"%PDF"
    assert pdf_path.stat().st_size > 20_000


def test_ppt_attachment_exists_and_is_a_pptx() -> None:
    root = project_root()
    pptx_path = root / "docs" / "job-application" / "attachments" / "BV-job-application-deck.pptx"

    assert pptx_path.exists()
    assert pptx_path.read_bytes()[:2] == b"PK"
    assert pptx_path.stat().st_size > 30_000


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
    assert "https://marvelx.github.io/Structural-screening-agent/job-application/" in email
    assert "./attachments/BV-job-application-one-pager.pdf" in html
    assert "./attachments/BV-job-application-deck.pptx" in html


def test_job_application_site_links_to_streamlit_demo() -> None:
    root = project_root()
    html_path = root / "docs" / "job-application" / "index.html"

    html = html_path.read_text()

    assert "打开在线演示" in html
    assert "https://" in html
    assert any(host in html for host in ["trycloudflare.com", "streamlit.app"])


def test_job_application_page_uses_chinese_section_labels_and_no_english_kickers() -> None:
    root = project_root()
    source = (root / "docs" / "job-application" / "index.html").read_text()

    assert "岗位匹配" in source
    assert "产品证明" in source
    assert "为什么这不是一个普通演示页" in source
    assert '<p class="section-kicker">Role Fit</p>' not in source
    assert '<p class="section-kicker">Workbench</p>' not in source
    assert '<p class="section-kicker">Engineering Boundary</p>' not in source
    assert "review basis" not in source
    assert "document completeness" not in source
    assert "deterministic kernel" not in source
    assert "screening-level" not in source


def test_streamlit_demo_deployment_files_exist() -> None:
    root = project_root()
    requirements_path = root / "requirements.txt"
    deploy_doc_path = root / "docs" / "job-application" / "streamlit-demo-deploy.md"

    assert requirements_path.exists()
    assert deploy_doc_path.exists()

    requirements = requirements_path.read_text()
    deploy_doc = deploy_doc_path.read_text()

    assert "-e ." in requirements
    assert "Streamlit Community Cloud" in deploy_doc
    assert "app.py" in deploy_doc


def test_readme_and_app_expose_public_demo_context() -> None:
    root = project_root()
    readme = (root / "README.md").read_text()
    app_source = (root / "app.py").read_text()

    assert "Public Demo" in readme
    assert any(host in readme for host in ["trycloudflare.com", "streamlit.app"])
    assert 'translate(ui_language, "public_demo_banner")' in app_source
    assert 'translate(ui_language, "public_demo_caption")' in app_source


def test_streamlit_bv_demo_exposes_explicit_persisted_workflow_resume_controls() -> None:
    root = project_root()
    app_source = (root / "app.py").read_text()
    gitignore = (root / ".gitignore").read_text()

    assert "JsonProjectReviewStateRepository" in app_source
    assert "run_persisted_local_agent_workflow_with_summary" in app_source
    assert "build_persisted_workflow_run_summary_rows" in app_source
    assert 'Path(".local_data") / "bv_review_states"' in app_source
    assert ".local_data/" in gitignore
    assert '"Save Current Review State"' in app_source
    assert '"保存当前审核状态"' in app_source
    assert '"Resume Saved Workflow"' in app_source
    assert '"恢复已保存工作流"' in app_source
    assert '"Use Current Form State"' in app_source
    assert '"使用当前表单状态"' in app_source
    assert "store_persisted_workflow_result" in app_source
    assert "clear_persisted_workflow_session" in app_source
    assert "get_active_persisted_workflow_state" in app_source
    assert "get_active_persisted_workflow_summary" in app_source
    assert '"bv_persisted_workflow_summary_rows"' not in app_source
    assert "只有点击按钮时才会保存或恢复本地 JSON 状态" in app_source
