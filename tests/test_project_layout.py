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
