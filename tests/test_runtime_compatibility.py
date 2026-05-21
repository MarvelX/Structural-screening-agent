import os
import subprocess
from pathlib import Path


def test_core_kernel_imports_under_system_python3() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    result = subprocess.run(
        ["python3", "-c", "import structural_screening_agent.core.kernel"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_bv_review_workbench_imports_under_system_python3() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{repo_root / 'src'}:{repo_root}"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    result = subprocess.run(
        [
            "python3",
            "-c",
            "import structural_screening_agent.bv_review; import app",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
