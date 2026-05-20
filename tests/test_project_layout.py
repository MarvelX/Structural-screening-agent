import py_compile
from pathlib import Path

import pytest

from structural_screening_agent.localization import TRANSLATIONS
from structural_screening_agent.pv_3d_studio import build_pv_3d_studio_html


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_project_layout_exists() -> None:
    root = project_root()
    assert (root / "app.py").exists()
    assert (root / "pyproject.toml").exists()
    assert (root / "src" / "structural_screening_agent").exists()


def test_app_py_compiles() -> None:
    root = project_root()
    py_compile.compile(str(root / "app.py"), doraise=True)


def test_app_py_uses_tabbed_information_architecture() -> None:
    root = project_root()
    source = (root / "app.py").read_text()

    assert "BV PV Design Review Workbench" in source
    assert "evaluate_bv_review" in source
    assert "default_bv_review_intake" in source
    assert "build_bv_review_intake" in source
    assert "bv_review_tab" in source
    assert "st.tabs(" in source
    assert 'translate(ui_language, "bv_review_tab")' in source
    assert 'translate(ui_language, "portal_frame_tab")' in source
    assert 'translate(ui_language, "assessment_tab")' in source
    assert 'translate(ui_language, "project_input_tab")' in source
    assert 'translate(ui_language, "basis_traceability_tab")' in source
    assert 'translate(ui_language, "report_export_tab")' in source
    assert 'translate(ui_language, "pv_3d_studio_tab")' in source
    assert 'translate(ui_language, "calculation_extension_tab")' in source
    assert 'translate(ui_language, "public_demo_banner")' in source
    assert 'translate(ui_language, "public_demo_caption")' in source
    assert 'translate(ui_language, "bv_review_intake_heading")' in source
    assert 'translate(ui_language, "bv_review_checklist_heading")' in source
    assert 'translate(ui_language, "bv_review_basis_heading")' in source
    assert 'translate(ui_language, "bv_review_path_heading")' in source
    assert 'translate(ui_language, "bv_review_risk_heading")' in source
    assert 'translate(ui_language, "bv_review_plan_heading")' in source
    assert 'translate(ui_language, "multi_agent_workflow_heading")' in source
    assert 'translate(ui_language, "human_gate_heading")' in source
    assert 'translate(ui_language, "data_lock_button")' in source
    assert 'translate(ui_language, "report_draft_gate_heading")' in source
    assert 'translate(ui_language, "version_diff_heading")' in source
    assert "build_foundation_calculation_run_from_fields" in source
    assert "build_superstructure_calculation_run_from_fields" in source
    assert "diff_extracted_fields" in source
    assert 'row["field_id"] == "pile_length_m"' in source
    assert 'previous_human_gate_rows[1]' not in source
    assert "build_incremental_recheck_plan" in source
    assert "build_incremental_recheck_summary_rows" in source
    assert "record_agent_review_decision" in source
    assert "run_local_agent_workflow_until_blocked" in source
    assert "build_agent_workflow_phase_rows" in source
    assert "build_agent_workflow_artifact_rows" in source
    assert "build_agent_engineer_review_queue_rows" in source
    assert "build_agent_workflow_event_rows" in source
    assert "workflow_state" in source
    assert "本地 Agent 工作流状态" in source
    assert "工程师复核队列" in source
    assert "Engineer Review Queue" in source
    assert "bv_agent_review_decisions" in source
    assert "bv_agent_review_signature" in source
    assert "批准所选复核项" in source
    assert "Approve Selected Review Item" in source
    assert "驳回所选复核项" in source
    assert "Reject Selected Review Item" in source
    assert "reviewed_workflow_state" in source
    assert "st.rerun()" in source
    assert "本地 Agent 事件追踪" in source
    assert 'translate(ui_language, "bv_review_warning_standards")' in source
    assert 'translate(ui_language, "bv_review_warning_objects")' in source
    assert "view.traceability_cards" in source
    assert "view.assessment_metric_cards" in source
    assert "view.conclusion_overview_card" in source
    assert "view.evidence_overview_cards" in source
    assert "_bv_basis_items" in source
    assert "_bv_report_preview_sections" in source
    assert 'translate(ui_language, "critical_calculation_results")' in source
    assert 'translate(ui_language, "detailed_calculation_results")' in source
    assert 'translate(ui_language, "detailed_evidence_status")' in source
    assert 'translate(ui_language, "photo_assist_entry")' in source
    assert 'translate(ui_language, "photo_assist_targets")' in source
    assert 'translate(ui_language, "photo_assist_backfill_boundary")' in source
    assert 'translate(ui_language, "steel_grade_preset")' in source
    assert 'translate(ui_language, "rafter_section_preset")' in source
    assert 'translate(ui_language, "column_section_preset")' in source
    assert 'translate(ui_language, "download_word_report")' in source
    assert 'translate(ui_language, "download_pdf_report")' in source
    assert "build_bv_markdown_report" in source
    assert "build_bv_report_filename" in source
    assert "build_pv_3d_studio_html" in source
    assert "components.html" in source
    assert "bv_markdown_download" in source
    assert "bv_word_download" in source
    assert "bv_pdf_download" in source
    assert "bv_calculation_gate_locked" in source
    assert "report_draft_ready" in source
    assert "if report_draft_ready:" in source
    assert 'row.get("quote")' in source
    assert 'row.get("confidence")' in source
    assert "st.file_uploader(" in source


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
        "multi_agent_workflow_heading",
        "human_gate_heading",
        "human_gate_caption",
        "data_lock_button",
        "calculation_gate_ready",
        "calculation_gate_blocked",
        "report_draft_gate_heading",
        "report_draft_gate_ready",
        "report_draft_gate_blocked",
        "version_diff_heading",
        "version_diff_caption",
        "incremental_recheck_heading",
        "bv_review_warning_standards",
        "bv_review_warning_objects",
        "pv_3d_studio_tab",
        "pv_3d_studio_heading",
        "pv_3d_studio_boundary",
    ]

    for key in required_keys:
        assert TRANSLATIONS[key]["zh"]
        assert TRANSLATIONS[key]["en"]


def test_pv_3d_studio_html_supports_chinese_and_english() -> None:
    zh_html = build_pv_3d_studio_html("zh")
    en_html = build_pv_3d_studio_html("en")

    assert "data-pv-structure-studio" in zh_html
    assert "pv-structure-canvas" in zh_html
    assert "光伏组件" in zh_html
    assert "暂停旋转" in zh_html
    assert "Component List" in en_html
    assert "Pause Rotation" in en_html
    assert "光伏组件" not in en_html


def test_app_py_no_longer_renders_legacy_report_grid_on_main_surface() -> None:
    root = project_root()
    source = (root / "app.py").read_text()

    assert "ssa-report-grid" not in source


def test_app_runs_without_streamlit_exceptions() -> None:
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
    root = project_root()
    at = AppTest.from_file(str(root / "app.py"))
    at.run(timeout=20)
    assert len(at.exception) == 0


def test_showcase_docs_exist() -> None:
    root = project_root()
    assert (root / "docs" / "showcase" / "demo-guide.md").exists()
    assert (root / "docs" / "showcase" / "project-brief.md").exists()
    assert (root / "docs" / "showcase" / "assets").exists()


def test_readme_mentions_showcase_positioning() -> None:
    root = project_root()
    readme = (root / "README.md").read_text()
    assert "BV PV Design Review Workbench" in readme
    assert "BV 光伏结构设计审核工作台" in readme
    assert "门式刚架屋面光伏增载场景模块" in readme
    assert "docs/showcase/demo-guide.md" in readme
    assert "门式刚架屋面光伏增载" in readme
    assert "不是聊天机器人" in readme


def test_showcase_docs_contain_expected_sections() -> None:
    root = project_root()
    demo_guide = (root / "docs" / "showcase" / "demo-guide.md").read_text()
    brief = (root / "docs" / "showcase" / "project-brief.md").read_text()
    assert "3 分钟跑起来" in demo_guide
    assert "BV 审核总览" in demo_guide
    assert "评估结论" in demo_guide
    assert "设计审查报告预览" in demo_guide
    assert "门刚场景模块" in demo_guide
    assert "BV PV Design Review Workbench" in brief
    assert "第三方审核工程师" in brief
    assert "门式刚架屋面光伏增载场景模块" in brief
    assert "项目一句话" in brief
    assert "不是一个通用 AI demo" in brief


def test_showcase_docs_link_to_assets_and_each_other() -> None:
    root = project_root()
    readme = (root / "README.md").read_text()
    demo_guide = (root / "docs" / "showcase" / "demo-guide.md").read_text()
    brief = (root / "docs" / "showcase" / "project-brief.md").read_text()
    assert "docs/showcase/assets/bv-review-overview.png" in readme
    assert "docs/showcase/assets/assessment-overview.png" in readme
    assert "docs/showcase/project-brief.md" in readme
    assert "docs/showcase/assets/bv-review-overview.png" in demo_guide
    assert "docs/showcase/assets/report-export.png" in demo_guide
    assert "docs/showcase/demo-guide.md" in brief


def test_showcase_screenshot_assets_exist() -> None:
    root = project_root()
    assert (root / "docs" / "showcase" / "assets" / "bv-review-overview.png").exists()
    assert (root / "docs" / "showcase" / "assets" / "assessment-overview.png").exists()
    assert (root / "docs" / "showcase" / "assets" / "basis-traceability.png").exists()
    assert (root / "docs" / "showcase" / "assets" / "report-export.png").exists()
