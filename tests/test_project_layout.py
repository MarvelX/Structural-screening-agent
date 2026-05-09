import py_compile
from pathlib import Path

import pytest


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
    assert "BV Review" in source
    assert "Risk & Nonconformity Register" in source
    assert "Portal-Frame Scenario Module" in source
    assert "st.tabs(" in source
    assert 'translate(ui_language, "assessment_tab")' in source
    assert 'translate(ui_language, "project_input_tab")' in source
    assert 'translate(ui_language, "basis_traceability_tab")' in source
    assert 'translate(ui_language, "report_export_tab")' in source
    assert 'translate(ui_language, "calculation_extension_tab")' in source
    assert "view.traceability_cards" in source
    assert "view.assessment_metric_cards" in source
    assert "view.conclusion_overview_card" in source
    assert "view.evidence_overview_cards" in source
    assert "Select at least one standards system" in source
    assert "Select at least one review object" in source
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
    assert "bv_markdown_download" in source
    assert "bv_word_download" in source
    assert "bv_pdf_download" in source
    assert "st.file_uploader(" in source


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
    assert "评估结论" in demo_guide
    assert "项目一句话" in brief
    assert "不是一个通用 AI demo" in brief


def test_showcase_docs_link_to_assets_and_each_other() -> None:
    root = project_root()
    readme = (root / "README.md").read_text()
    demo_guide = (root / "docs" / "showcase" / "demo-guide.md").read_text()
    brief = (root / "docs" / "showcase" / "project-brief.md").read_text()
    assert "docs/showcase/assets/assessment-overview.png" in readme
    assert "docs/showcase/project-brief.md" in readme
    assert "docs/showcase/assets/report-export.png" in demo_guide
    assert "docs/showcase/demo-guide.md" in brief


def test_showcase_screenshot_assets_exist() -> None:
    root = project_root()
    assert (root / "docs" / "showcase" / "assets" / "assessment-overview.png").exists()
    assert (root / "docs" / "showcase" / "assets" / "basis-traceability.png").exists()
    assert (root / "docs" / "showcase" / "assets" / "report-export.png").exists()
