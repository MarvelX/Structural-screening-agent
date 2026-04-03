import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel, Field

from structural_screening_agent.core.basis_registry import load_basis_registry
from structural_screening_agent.core.domain import PortalFrameScreeningCase
from structural_screening_agent.core.kernel import KernelOutcome


class StoredRun(BaseModel):
    run_id: int
    case: PortalFrameScreeningCase
    outcome: KernelOutcome


class StoredEvaluation(BaseModel):
    result_id: int
    case_id: int
    evidence_snapshot_id: int
    report_id: int
    case: PortalFrameScreeningCase
    outcome: KernelOutcome
    report_markdown: str = Field(min_length=1)
    explanation_payload: Dict[str, Any] = Field(default_factory=dict)
    language: str = Field(min_length=1)


class ScreeningRepository:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY,
                    project_type TEXT NOT NULL,
                    building_type TEXT NOT NULL,
                    case_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_snapshots (
                    id INTEGER PRIMARY KEY,
                    case_id INTEGER NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    FOREIGN KEY(case_id) REFERENCES cases(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS standards_basis_records (
                    basis_id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    title_en TEXT NOT NULL,
                    title_zh TEXT NOT NULL,
                    citation_en TEXT NOT NULL,
                    citation_zh TEXT NOT NULL,
                    applicable_standards TEXT NOT NULL DEFAULT '[]',
                    trigger_conditions TEXT NOT NULL DEFAULT '[]',
                    review_requirements TEXT NOT NULL DEFAULT '[]',
                    evidence_requirements TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS screening_results (
                    id INTEGER PRIMARY KEY,
                    run_id INTEGER,
                    case_id INTEGER NOT NULL,
                    evidence_snapshot_id INTEGER NOT NULL,
                    outcome_json TEXT NOT NULL,
                    decision_status TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    traceability_count INTEGER NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES screening_runs(id),
                    FOREIGN KEY(case_id) REFERENCES cases(id),
                    FOREIGN KEY(evidence_snapshot_id) REFERENCES evidence_snapshots(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS screening_result_rules (
                    id INTEGER PRIMARY KEY,
                    screening_result_id INTEGER NOT NULL,
                    rule_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    summary_en TEXT NOT NULL,
                    summary_zh TEXT NOT NULL,
                    basis_ids_json TEXT NOT NULL,
                    traces_json TEXT NOT NULL,
                    FOREIGN KEY(screening_result_id) REFERENCES screening_results(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS screening_result_calculations (
                    id INTEGER PRIMARY KEY,
                    screening_result_id INTEGER NOT NULL,
                    calc_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    value_text TEXT NOT NULL,
                    numeric_value REAL,
                    summary_en TEXT NOT NULL,
                    summary_zh TEXT NOT NULL,
                    FOREIGN KEY(screening_result_id) REFERENCES screening_results(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS screening_result_actions (
                    id INTEGER PRIMARY KEY,
                    screening_result_id INTEGER NOT NULL,
                    title_en TEXT NOT NULL,
                    title_zh TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    FOREIGN KEY(screening_result_id) REFERENCES screening_results(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS screening_result_basis_links (
                    screening_result_id INTEGER NOT NULL,
                    basis_id TEXT NOT NULL,
                    PRIMARY KEY(screening_result_id, basis_id),
                    FOREIGN KEY(screening_result_id) REFERENCES screening_results(id),
                    FOREIGN KEY(basis_id) REFERENCES standards_basis_records(basis_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS exported_reports (
                    id INTEGER PRIMARY KEY,
                    screening_result_id INTEGER NOT NULL,
                    report_markdown TEXT NOT NULL,
                    explanation_json TEXT NOT NULL,
                    language TEXT NOT NULL,
                    FOREIGN KEY(screening_result_id) REFERENCES screening_results(id)
                )
                """
            )
            self._ensure_column(connection, "standards_basis_records", "applicable_standards", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "standards_basis_records", "trigger_conditions", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "standards_basis_records", "review_requirements", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "standards_basis_records", "evidence_requirements", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(connection, "screening_results", "run_id", "INTEGER")
        self._sync_basis_registry()

    def _ensure_column(self, connection: sqlite3.Connection, table_name: str, column_name: str, column_definition: str) -> None:
        columns = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        if column_name not in columns:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            )

    def _sync_basis_registry(self) -> None:
        registry = load_basis_registry()
        with self._connect() as connection:
            for item in registry.references.values():
                connection.execute(
                    """
                    INSERT INTO standards_basis_records(
                        basis_id, source_type, title_en, title_zh, citation_en, citation_zh,
                        applicable_standards, trigger_conditions, review_requirements, evidence_requirements
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(basis_id) DO UPDATE SET
                        source_type=excluded.source_type,
                        title_en=excluded.title_en,
                        title_zh=excluded.title_zh,
                        citation_en=excluded.citation_en,
                        citation_zh=excluded.citation_zh,
                        applicable_standards=excluded.applicable_standards,
                        trigger_conditions=excluded.trigger_conditions,
                        review_requirements=excluded.review_requirements,
                        evidence_requirements=excluded.evidence_requirements
                    """,
                    (
                        item.basis_id,
                        item.source_type,
                        item.title_en,
                        item.title_zh,
                        item.citation_en,
                        item.citation_zh,
                        json.dumps(item.applicable_standards),
                        json.dumps(item.trigger_conditions),
                        json.dumps(item.review_requirements),
                        json.dumps(item.evidence_requirements),
                    ),
                )

    def save_run(self, case: PortalFrameScreeningCase, outcome: KernelOutcome) -> int:
        with self._connect() as connection:
            return self._insert_run(connection, case, outcome)

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
            case=PortalFrameScreeningCase.model_validate_json(row[1]),
            outcome=KernelOutcome.model_validate_json(row[2]),
        )

    def save_evaluation(
        self,
        case: PortalFrameScreeningCase,
        outcome: KernelOutcome,
        report_markdown: str,
        explanation_payload: Optional[Dict[str, Any]] = None,
        language: str = "zh",
    ) -> int:
        explanation_payload = explanation_payload or {}
        with self._connect() as connection:
            return self._insert_evaluation(
                connection=connection,
                case=case,
                outcome=outcome,
                run_id=None,
                report_markdown=report_markdown,
                explanation_payload=explanation_payload,
                language=language,
            )

    def save_run_and_evaluation(
        self,
        case: PortalFrameScreeningCase,
        outcome: KernelOutcome,
        report_markdown: str,
        explanation_payload: Optional[Dict[str, Any]] = None,
        language: str = "zh",
    ) -> Tuple[int, int]:
        explanation_payload = explanation_payload or {}
        with self._connect() as connection:
            run_id = self._insert_run(connection, case, outcome)
            result_id = self._insert_evaluation(
                connection=connection,
                case=case,
                outcome=outcome,
                run_id=run_id,
                report_markdown=report_markdown,
                explanation_payload=explanation_payload,
                language=language,
            )
            return run_id, result_id

    def _insert_run(
        self,
        connection: sqlite3.Connection,
        case: PortalFrameScreeningCase,
        outcome: KernelOutcome,
    ) -> int:
        cursor = connection.execute(
            "INSERT INTO screening_runs(case_json, outcome_json) VALUES (?, ?)",
            (case.model_dump_json(), outcome.model_dump_json()),
        )
        return int(cursor.lastrowid)

    def _insert_evaluation(
        self,
        connection: sqlite3.Connection,
        case: PortalFrameScreeningCase,
        outcome: KernelOutcome,
        run_id: Optional[int],
        report_markdown: str,
        explanation_payload: Dict[str, Any],
        language: str,
    ) -> int:
        case_id = self._insert_case(connection, case)
        evidence_snapshot_id = self._insert_evidence_snapshot(connection, case_id, case)
        result_id = self._insert_screening_result(
            connection=connection,
            run_id=run_id,
            case_id=case_id,
            evidence_snapshot_id=evidence_snapshot_id,
            outcome=outcome,
        )
        self._insert_calculations(connection, result_id, outcome)
        self._insert_actions(connection, result_id, outcome)
        self._insert_rules(connection, result_id, outcome)
        self._insert_basis_links(connection, result_id, outcome)
        self._insert_exported_report(
            connection=connection,
            result_id=result_id,
            report_markdown=report_markdown,
            explanation_payload=explanation_payload,
            language=language,
        )
        return result_id

    def _insert_case(self, connection: sqlite3.Connection, case: PortalFrameScreeningCase) -> int:
        case_cursor = connection.execute(
            "INSERT INTO cases(project_type, building_type, case_json) VALUES (?, ?, ?)",
            (
                case.building.project_type,
                case.building.building_type,
                case.model_dump_json(),
            ),
        )
        return int(case_cursor.lastrowid)

    def _insert_evidence_snapshot(
        self,
        connection: sqlite3.Connection,
        case_id: int,
        case: PortalFrameScreeningCase,
    ) -> int:
        evidence_snapshot = {
            "code_context": case.code_context.model_dump(mode="json"),
            "geometry": case.geometry.model_dump(mode="json"),
            "primary_frame": case.primary_frame.model_dump(mode="json"),
            "secondary_members": case.secondary_members.model_dump(mode="json"),
            "pv_load": case.pv_load.model_dump(mode="json"),
            "evidence": case.evidence.model_dump(mode="json"),
            "member_evidence": case.member_evidence.model_dump(mode="json"),
            "connection_evidence": case.connection_evidence.model_dump(mode="json"),
            "roof_system": case.roof_system.model_dump(mode="json"),
            "load_assumptions": case.load_assumptions.model_dump(mode="json"),
        }
        evidence_cursor = connection.execute(
            "INSERT INTO evidence_snapshots(case_id, snapshot_json) VALUES (?, ?)",
            (case_id, json.dumps(evidence_snapshot)),
        )
        return int(evidence_cursor.lastrowid)

    def _insert_screening_result(
        self,
        connection: sqlite3.Connection,
        run_id: Optional[int],
        case_id: int,
        evidence_snapshot_id: int,
        outcome: KernelOutcome,
    ) -> int:
        result_cursor = connection.execute(
            """
            INSERT INTO screening_results(
                run_id, case_id, evidence_snapshot_id, outcome_json, decision_status, confidence, traceability_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                case_id,
                evidence_snapshot_id,
                outcome.model_dump_json(),
                outcome.decision.status,
                outcome.decision.confidence,
                len(outcome.findings),
            ),
        )
        return int(result_cursor.lastrowid)

    def _insert_calculations(
        self,
        connection: sqlite3.Connection,
        result_id: int,
        outcome: KernelOutcome,
    ) -> None:
        for calc in outcome.calc_outputs:
            connection.execute(
                """
                INSERT INTO screening_result_calculations(
                    screening_result_id,
                    calc_id,
                    category,
                    value_text,
                    numeric_value,
                    summary_en,
                    summary_zh
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    calc.calc_id,
                    calc.category,
                    calc.value_text,
                    calc.numeric_value,
                    calc.summary_en,
                    calc.summary_zh,
                ),
            )

    def _insert_actions(
        self,
        connection: sqlite3.Connection,
        result_id: int,
        outcome: KernelOutcome,
    ) -> None:
        for action in outcome.recommended_actions:
            connection.execute(
                """
                INSERT INTO screening_result_actions(
                    screening_result_id, title_en, title_zh, phase
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    result_id,
                    action.title_en,
                    action.title_zh,
                    action.phase,
                ),
            )

    def _insert_rules(
        self,
        connection: sqlite3.Connection,
        result_id: int,
        outcome: KernelOutcome,
    ) -> None:
        for rule in outcome.triggered_rules:
            connection.execute(
                """
                INSERT INTO screening_result_rules(
                    screening_result_id,
                    rule_id,
                    severity,
                    summary_en,
                    summary_zh,
                    basis_ids_json,
                    traces_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    rule.rule_id,
                    rule.severity,
                    rule.summary_en,
                    rule.summary_zh,
                    json.dumps(rule.basis_ids),
                    json.dumps(
                        [trace.model_dump(mode="json") for trace in rule.traces]
                    ),
                ),
            )

    def _insert_basis_links(
        self,
        connection: sqlite3.Connection,
        result_id: int,
        outcome: KernelOutcome,
    ) -> None:
        for basis in outcome.basis_references:
            connection.execute(
                """
                INSERT OR REPLACE INTO screening_result_basis_links(
                    screening_result_id, basis_id
                ) VALUES (?, ?)
                """,
                (result_id, basis.basis_id),
            )

    def _insert_exported_report(
        self,
        connection: sqlite3.Connection,
        result_id: int,
        report_markdown: str,
        explanation_payload: Dict[str, Any],
        language: str,
    ) -> int:
        report_cursor = connection.execute(
            """
            INSERT INTO exported_reports(screening_result_id, report_markdown, explanation_json, language)
            VALUES (?, ?, ?, ?)
            """,
            (
                result_id,
                report_markdown,
                json.dumps(explanation_payload),
                language,
            ),
        )
        return int(report_cursor.lastrowid)

    def load_evaluation(self, result_id: int) -> StoredEvaluation:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    sr.id,
                    c.id,
                    es.id,
                    er.id,
                    c.case_json,
                    sr.outcome_json,
                    er.report_markdown,
                    er.explanation_json,
                    er.language
                FROM screening_results sr
                JOIN cases c ON c.id = sr.case_id
                JOIN evidence_snapshots es ON es.id = sr.evidence_snapshot_id
                JOIN exported_reports er ON er.screening_result_id = sr.id
                WHERE sr.id = ?
                """,
                (result_id,),
            ).fetchone()

        if row is None:
            raise KeyError(f"screening evaluation {result_id} not found")

        return StoredEvaluation(
            result_id=int(row[0]),
            case_id=int(row[1]),
            evidence_snapshot_id=int(row[2]),
            report_id=int(row[3]),
            case=PortalFrameScreeningCase.model_validate_json(row[4]),
            outcome=KernelOutcome.model_validate_json(row[5]),
            report_markdown=row[6],
            explanation_payload=json.loads(row[7]),
            language=row[8],
        )
