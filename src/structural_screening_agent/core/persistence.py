import sqlite3
from pathlib import Path

from pydantic import BaseModel

from structural_screening_agent.core.domain import ScreeningCase
from structural_screening_agent.core.kernel import KernelOutcome


class StoredRun(BaseModel):
    run_id: int
    case: ScreeningCase
    outcome: KernelOutcome


class ScreeningRepository:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS screening_runs (
                    id INTEGER PRIMARY KEY,
                    case_json TEXT NOT NULL,
                    outcome_json TEXT NOT NULL
                )
                """
            )

    def save_run(self, case: ScreeningCase, outcome: KernelOutcome) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO screening_runs(case_json, outcome_json) VALUES (?, ?)",
                (case.model_dump_json(), outcome.model_dump_json()),
            )
            return int(cursor.lastrowid)

    def load_run(self, run_id: int) -> StoredRun:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, case_json, outcome_json FROM screening_runs WHERE id = ?",
                (run_id,),
            ).fetchone()

        if row is None:
            raise KeyError(f"screening run {run_id} not found")

        return StoredRun(
            run_id=int(row[0]),
            case=ScreeningCase.model_validate_json(row[1]),
            outcome=KernelOutcome.model_validate_json(row[2]),
        )
