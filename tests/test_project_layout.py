import py_compile
from pathlib import Path


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
