from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from structural_screening_agent.bv_review.models import (
    BVBasisReference,
    BVReportSection,
    BVReviewPathItem,
    BVReviewPlanItem,
    BVRiskItem,
)
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    DocumentVersion,
    ExtractedField,
    ProjectReviewState,
    RFIItem,
)


AgentRole = Literal[
    "document_intake",
    "basis_code",
    "review_plan",
    "structural_review",
    "calculation_check",
    "risk_ncr",
    "report_composer",
]
AGENT_ROLE_SEQUENCE: tuple[AgentRole, ...] = (
    "document_intake",
    "basis_code",
    "review_plan",
    "structural_review",
    "calculation_check",
    "risk_ncr",
    "report_composer",
)
AGENT_CONTRACT_SCHEMA_VERSION = "phase2-agent-contracts-v1"
DETERMINISTIC_SCREENING_BOUNDARY = "screening-level review support only"
_BOUNDARY_TERMS = ("screening-level", "review-support")
_PROHIBITED_SIGNING_TERMS = (
    "official bv issue",
    "official bv signing",
    "stamped",
    "正式签发",
    "正式签章",
    "签章",
)


class _EngineerReviewedAgentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1)
    schema_version: str = AGENT_CONTRACT_SCHEMA_VERSION
    requires_engineer_review: Literal[True] = True


class DocumentIntakeAgentOutput(_EngineerReviewedAgentOutput):
    agent_role: Literal["document_intake"] = "document_intake"
    extracted_fields: list[ExtractedField] = Field(default_factory=list)
    document_versions: list[DocumentVersion] = Field(default_factory=list)
    missing_document_keys: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BasisCodeAgentOutput(_EngineerReviewedAgentOutput):
    agent_role: Literal["basis_code"] = "basis_code"
    basis_references: list[BVBasisReference] = Field(min_length=1)


class ReviewPlanAgentOutput(_EngineerReviewedAgentOutput):
    agent_role: Literal["review_plan"] = "review_plan"
    review_plan: list[BVReviewPlanItem] = Field(min_length=1)


class StructuralReviewAgentOutput(_EngineerReviewedAgentOutput):
    agent_role: Literal["structural_review"] = "structural_review"
    review_paths: list[BVReviewPathItem] = Field(min_length=1)


class CalculationCheckAgentOutput(_EngineerReviewedAgentOutput):
    agent_role: Literal["calculation_check"] = "calculation_check"
    calculation_run_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_run_ids(self) -> "CalculationCheckAgentOutput":
        if len(set(self.calculation_run_ids)) != len(self.calculation_run_ids):
            raise ValueError("Calculation check output cannot contain duplicate run ids.")
        return self


class RiskNCRAgentOutput(_EngineerReviewedAgentOutput):
    agent_role: Literal["risk_ncr"] = "risk_ncr"
    risks: list[BVRiskItem] = Field(default_factory=list)
    source_calculation_run_ids: list[str] = Field(default_factory=list)


class ReportComposerAgentOutput(_EngineerReviewedAgentOutput):
    agent_role: Literal["report_composer"] = "report_composer"
    report_sections: list[BVReportSection] = Field(min_length=1)
    rfi_items: list[RFIItem] = Field(default_factory=list)
    boundary_statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_screening_boundary_statement(self) -> "ReportComposerAgentOutput":
        statement = self.boundary_statement.lower()
        if not any(term in statement for term in _BOUNDARY_TERMS):
            raise ValueError("Report boundary statement must state screening-level or review-support.")
        if _contains_prohibited_signing_term(self._all_report_text()):
            raise ValueError("Report composer output must not claim formal signing authority.")
        return self

    def _all_report_text(self) -> str:
        parts: list[str] = [self.boundary_statement]
        for section in self.report_sections:
            parts.append(section.heading)
            parts.extend(section.items)
        for rfi_item in self.rfi_items:
            parts.extend(
                [
                    rfi_item.rfi_id,
                    rfi_item.question,
                    rfi_item.responsible_party,
                    rfi_item.trigger_basis,
                    rfi_item.required_document_or_field,
                    rfi_item.status,
                    rfi_item.client_response or "",
                    " ".join(rfi_item.reopen_review_items),
                ]
            )
        return "\n".join(parts).lower()


def validate_calculation_check_output_against_state(
    output: CalculationCheckAgentOutput,
    state: ProjectReviewState,
) -> None:
    if output.project_id != state.project_id:
        raise ValueError("Calculation check output project_id must match project state.")

    resolve_calculation_check_output_against_state(output, state)


def resolve_calculation_check_output_against_state(
    output: CalculationCheckAgentOutput,
    state: ProjectReviewState,
) -> list[CalculationRun]:
    if output.project_id != state.project_id:
        raise ValueError("Calculation check output project_id must match project state.")

    resolved_runs: list[CalculationRun] = []
    state_runs_by_id = {run.run_id: run for run in state.calculation_runs}
    for run_id in output.calculation_run_ids:
        state_run = state_runs_by_id.get(run_id)
        if state_run is None:
            raise ValueError(f"Calculation run {run_id} does not exist in project state.")
        _validate_state_calculation_run(state_run)
        resolved_runs.append(state_run)
    return resolved_runs


def _validate_state_calculation_run(run: CalculationRun) -> None:
    if run.status != "completed":
        return
    if run.result_summary.get("screening_boundary") != DETERMINISTIC_SCREENING_BOUNDARY:
        raise ValueError("Completed calculation runs require deterministic screening boundary.")
    if "deterministic" not in run.engine_version:
        raise ValueError("Completed calculation runs must use deterministic engine output.")


def _contains_prohibited_signing_term(text: str) -> bool:
    return any(term in text for term in _PROHIBITED_SIGNING_TERMS)
