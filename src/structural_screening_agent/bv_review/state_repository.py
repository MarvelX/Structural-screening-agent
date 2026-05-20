from __future__ import annotations

import json
from pathlib import Path
from re import fullmatch

from structural_screening_agent.bv_review.field_diff import (
    IncrementalRecheckPlan,
    build_incremental_recheck_plan_from_closed_rfis,
)
from structural_screening_agent.bv_review.project_state import ProjectReviewState


class JsonProjectReviewStateRepository:
    def __init__(self, root: Path | str):
        self.root = Path(root)

    def _path_for(self, project_id: str) -> Path:
        if fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", project_id) is None:
            raise ValueError("Project id must be a safe file name.")
        return self.root / f"{project_id}.json"

    def save(self, state: ProjectReviewState) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._path_for(state.project_id)
        path.write_text(
            json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load(self, project_id: str) -> ProjectReviewState:
        path = self._path_for(project_id)
        if not path.exists():
            raise FileNotFoundError(f"No project review state found for {project_id!r}.")
        return ProjectReviewState.model_validate_json(path.read_text(encoding="utf-8"))

    def load_closed_rfi_recheck_plan(self, project_id: str) -> IncrementalRecheckPlan:
        state = self.load(project_id)
        return build_incremental_recheck_plan_from_closed_rfis(
            state.rfi_items,
            calculation_runs=state.calculation_runs,
        )

    def list_project_ids(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(path.stem for path in self.root.glob("*.json") if path.is_file())
