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
    ui_source = (
        root / "src" / "structural_screening_agent" / "bv_review" / "ui.py"
    ).read_text()
    gitignore = (root / ".gitignore").read_text()

    assert "def _label(" in app_source
    assert "JsonProjectReviewStateRepository" in app_source
    assert "run_persisted_local_agent_workflow_with_summary" in app_source
    assert "build_persisted_workflow_run_summary_rows" in app_source
    assert 'Path(".local_data") / "bv_review_states"' in app_source
    assert ".local_data/" in gitignore
    assert '"Save Current Review State"' in app_source
    assert '"保存当前审核状态"' in app_source
    assert '"Resume Saved Workflow"' in app_source
    assert '"恢复已保存工作流"' in app_source
    assert '"Saved Project ID"' in app_source
    assert '"已保存项目 ID"' in app_source
    assert '"Resume Selected Saved Project"' in app_source
    assert '"恢复所选已保存项目"' in app_source
    assert '"Use Current Form State"' in app_source
    assert '"使用当前表单状态"' in app_source
    assert "store_persisted_workflow_result" in app_source
    assert "clear_persisted_workflow_session" in app_source
    assert "get_active_persisted_project_id" in app_source
    assert "active_persisted_project_id" in app_source
    assert "get_active_persisted_workflow_state" in app_source
    assert "get_active_persisted_workflow_summary" in app_source
    assert "record_persisted_agent_review_decision" in app_source
    assert "record_persisted_report_revision" in app_source
    assert "record_persisted_rfi_client_response" in app_source
    assert "close_persisted_rfi_after_engineer_review" in app_source
    assert "run_persisted_rfi_incremental_calculation_recheck" in app_source
    assert "apply_persisted_authorized_agent_response" in app_source
    assert "store_persisted_workflow_state" in app_source
    assert "build_bv_review_result_from_project_state" in app_source
    assert "record_report_revision" in app_source
    assert '"Approve Report Gate"' in app_source
    assert '"批准报告门禁"' in app_source
    assert '"Record Report Revision Snapshot"' in app_source
    assert '"记录报告修订快照"' in app_source
    assert "Report Revision History" in app_source
    assert "报告修订历史" in app_source
    assert '"Persisted RFI Register"' in app_source
    assert '"持久化 RFI 台账"' in app_source
    assert '"Record RFI Client Response"' in app_source
    assert '"记录 RFI 客户回复"' in app_source
    assert '"Run Deterministic Recheck"' in app_source
    assert '"运行确定性增量复核"' in app_source
    assert "Run deterministic incremental recheck before closing this RFI." in app_source
    assert "关闭该 RFI 前，需要先运行确定性增量复核。" in app_source
    assert "Deterministic incremental recheck completed and saved." in app_source
    assert "确定性增量复核已完成并保存。" in app_source
    assert "Deterministic recheck was saved but remains blocked" in app_source
    assert "确定性复核已保存但仍处于阻塞状态" in app_source
    assert "rechecked_complete" in app_source
    assert "selected_persisted_rfi.completed_recheck_items" in app_source
    assert '"Close RFI After Engineer Review"' in app_source
    assert '"工程师复核后关闭 RFI"' in app_source
    assert 'f"bv_persisted_rfi_client_response_{selected_persisted_rfi_id}"' in app_source
    assert 'f"bv_persisted_rfi_closeout_note_{selected_persisted_rfi_id}"' in app_source
    assert "build_service_scope_recommendations" in app_source
    assert '"BV Service Scope Recommendations"' in app_source
    assert '"BV 服务范围建议"' in app_source
    assert "build_project_management_actions" in app_source
    assert "build_bv_project_management_dashboard_view" in app_source
    assert "build_project_management_action_summary" in ui_source
    assert "build_project_management_action_summary_rows" in ui_source
    assert "build_project_management_action_rows" in ui_source
    assert '"Project Management Action Dashboard"' in ui_source
    assert '"项目管理行动看板"' in ui_source
    assert "build_agent_prompt_packages" in app_source
    assert "build_agent_prompt_package_rows" in app_source
    assert "build_agent_provider_invocation_request" in app_source
    assert "build_agent_provider_invocation_rows" in app_source
    assert '"Agent Contract Prompt Preview"' in app_source
    assert '"Agent 契约提示词预览"' in app_source
    assert '"Agent Provider Invocation Preview"' in app_source
    assert '"Agent 供应商调用预览"' in app_source
    assert "Invocation preview only; no network request is sent" in app_source
    assert "resolve_provider" not in app_source[
        app_source.index('"Agent Contract Prompt Preview"') :
        app_source.index('"Agent JSON Response Validation Sandbox"')
    ]
    assert '"JSON Schema Preview"' in app_source
    assert '"JSON Schema 预览"' in app_source
    assert "build_agent_response_impact_rows" in app_source
    assert "build_agent_response_sandbox_result" in app_source
    assert "build_agent_response_sandbox_rows" in app_source
    assert "build_agent_response_engineer_handoff" in app_source
    assert "build_agent_response_engineer_handoff_rows" in app_source
    assert "build_agent_response_application_plan" in app_source
    assert "build_agent_response_application_plan_rows" in app_source
    assert "AgentResponseApplicationAuthorization" in app_source
    assert "apply_authorized_agent_response_to_state" in app_source
    assert "build_sample_agent_response_json" in app_source
    assert '"Agent JSON Response Validation Sandbox"' in app_source
    assert '"Agent JSON 响应验证沙盒"' in app_source
    assert '"Agent Response Sandbox Summary"' in app_source
    assert '"Agent 响应沙盒摘要"' in app_source
    assert '"Agent Engineer Review Handoff"' in app_source
    assert '"Agent 工程师复核移交"' in app_source
    assert '"Agent Controlled Application Plan"' in app_source
    assert '"Agent 受控应用计划"' in app_source
    assert '"Authorize and Apply Agent Response"' in app_source
    assert '"授权并应用 Agent 响应"' in app_source
    assert '"Agent response applied to workflow state."' in app_source
    assert '"Agent 响应已应用到工作流状态。"' in app_source
    assert "AgentResponseApplicationPacket" in app_source
    assert "build_agent_response_application_packet" in app_source
    assert "is_agent_response_application_packet_current" in app_source
    assert "build_agent_application_authorization_rows" in app_source
    assert "Agent Application Authorization Ledger" in app_source
    assert "Agent 应用授权记录" in app_source
    assert (
        "Revalidate the agent response before applying it to the updated workflow state."
        in app_source
    )
    assert "Sandbox result only; no network request is sent" in app_source
    assert "Application plan only; no agent output is applied" in app_source
    assert "response_digest=application_plan.response_digest" in app_source
    assert '"Agent Response Impact Preview"' in app_source
    assert '"Agent 响应影响预览"' in app_source
    assert "Preview only; engineer approval is still required" in app_source
    assert '"Validate Agent JSON Response"' in app_source
    assert '"验证 Agent JSON 响应"' in app_source
    assert "effective_bv_result" in app_source
    assert "list_project_inventory" in app_source
    assert "invalid_project_ids" in app_source
    assert "build_project_review_state_summary_rows" in app_source
    assert "build_blocked_calculation_review_draft_rows" in app_source
    assert '"Blocked Calculation Draft RFI"' in app_source
    assert '"计算阻塞草稿 RFI"' in app_source
    assert "issue_persisted_blocked_calculation_draft_rfi" in app_source
    assert '"Issue Draft RFI After Engineer Review"' in app_source
    assert '"工程师复核后签发草稿 RFI"' in app_source
    assert "Draft RFI issued after engineer review." in app_source
    assert "草稿 RFI 已经工程师复核并签发。" in app_source
    assert "available_draft_rfi_ids" in app_source
    assert "already been issued into the persisted RFI register" in app_source
    assert "已进入持久化 RFI 台账" in app_source
    assert "issuing an RFI moves the persisted workflow to issue/RFI closeout" in app_source
    assert "Saved Project Inventory" in app_source
    assert '"已保存项目清单"' in app_source
    assert "Some saved project files could not be loaded" in app_source
    assert "部分已保存项目文件无法加载" in app_source
    assert "if persisted_workflow_is_active" in app_source
    assert '"bv_persisted_workflow_summary_rows"' not in app_source
    assert "只有点击按钮时才会保存或恢复本地 JSON 状态" in app_source
