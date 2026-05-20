from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from structural_screening_agent.bv_review.models import (
    BVDocumentStatus,
    BVReviewIntake,
    BVRiskItem,
)


ReviewPhase = Literal[
    "intake",
    "document_check",
    "basis_build",
    "review_plan",
    "engineer_data_lock",
    "calculation_check",
    "risk_register",
    "report_draft",
    "engineer_approval",
    "issue_rfi_closeout",
]
ReviewPhaseStatus = Literal[
    "pending",
    "running",
    "blocked",
    "waiting_for_client",
    "waiting_for_engineer",
    "approved",
    "rejected",
]
REVIEW_PHASES: tuple[ReviewPhase, ...] = (
    "intake",
    "document_check",
    "basis_build",
    "review_plan",
    "engineer_data_lock",
    "calculation_check",
    "risk_register",
    "report_draft",
    "engineer_approval",
    "issue_rfi_closeout",
)

FieldValue = str | float | int | bool


class DocumentVersion(BaseModel):
    document_id: str = Field(min_length=1)
    document_type: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    source_name: str = Field(min_length=1)
    status: BVDocumentStatus
    received_date: Optional[str] = None
    supersedes: Optional[str] = None
    notes: Optional[str] = None


class ExtractedField(BaseModel):
    field_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    candidate_value: FieldValue
    unit: Optional[str] = None
    source_document_id: str = Field(min_length=1)
    page_or_section: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    is_confirmed: bool = False
    confirmed_value: Optional[FieldValue] = None
    confirmed_unit: Optional[str] = None
    include_in_calculation: bool = False
    reviewer_note: Optional[str] = None

    @model_validator(mode="after")
    def require_confirmation_for_calculation(self) -> "ExtractedField":
        if self.include_in_calculation and (
            not self.is_confirmed or self.confirmed_value in (None, "")
        ):
            raise ValueError(
                "Fields included in calculation must be engineer-confirmed with a confirmed value."
            )
        return self


class PVStructuralSpec(BaseModel):
    support_type: Literal["ground_fixed"] = "ground_fixed"
    tilt_angle_deg: Optional[float] = None
    pile_diameter_mm: Optional[float] = None
    pile_length_m: Optional[float] = None
    pile_spacing_m: Optional[float] = None
    steel_grade: Optional[str] = None
    post_section: Optional[str] = None
    beam_section: Optional[str] = None
    purlin_section: Optional[str] = None
    basic_wind_pressure_kpa: Optional[float] = None
    snow_load_kpa: Optional[float] = None
    bearing_capacity_characteristic_kpa: Optional[float] = None
    side_resistance_standard_kpa: Optional[float] = None
    worst_axial_force_kn: Optional[float] = None
    worst_bending_moment_knm: Optional[float] = None
    worst_shear_force_kn: Optional[float] = None


class EngineerApproval(BaseModel):
    approval_id: str = Field(min_length=1)
    target_type: Literal["field", "basis", "calculation", "report", "gate"]
    target_id: str = Field(min_length=1)
    status: Literal["pending", "approved", "rejected"]
    reviewer: Optional[str] = None
    approved_at: Optional[str] = None
    comment: Optional[str] = None
    locked: bool = False

    @model_validator(mode="after")
    def require_approval_before_lock(self) -> "EngineerApproval":
        if self.locked and self.status != "approved":
            raise ValueError("Locked approvals must be approved.")
        return self


class CalculationRun(BaseModel):
    run_id: str = Field(min_length=1)
    engine_name: Literal["foundation", "superstructure"]
    engine_version: str = Field(min_length=1)
    input_field_ids: List[str] = Field(default_factory=list)
    input_locked: bool
    status: Literal["ready", "blocked", "completed", "failed"]
    structured_errors: List[str] = Field(default_factory=list)
    result_summary: Dict[str, FieldValue] = Field(default_factory=dict)
    created_at: Optional[str] = None

    @model_validator(mode="after")
    def require_locked_inputs_for_executable_states(self) -> "CalculationRun":
        if self.status in {"ready", "completed"} and not self.input_locked:
            raise ValueError("Ready or completed calculation runs require locked inputs.")
        return self


class RFIItem(BaseModel):
    rfi_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    responsible_party: str = Field(min_length=1)
    trigger_basis: str = Field(min_length=1)
    required_document_or_field: str = Field(min_length=1)
    status: Literal["open", "responded", "closed", "reopened"]
    client_response: Optional[str] = None
    reopen_review_items: List[str] = Field(default_factory=list)
    triggers_incremental_recheck: bool = False

    @model_validator(mode="after")
    def require_response_before_close(self) -> "RFIItem":
        if self.status == "closed" and not self.client_response:
            raise ValueError("Closed RFI items require a client response.")
        return self


def _default_phase_statuses() -> dict[ReviewPhase, ReviewPhaseStatus]:
    return {phase: "pending" for phase in REVIEW_PHASES}


class ProjectReviewState(BaseModel):
    project_id: str = Field(min_length=1)
    intake: BVReviewIntake
    current_phase: ReviewPhase = "intake"
    phase_statuses: Dict[ReviewPhase, ReviewPhaseStatus] = Field(
        default_factory=_default_phase_statuses
    )
    document_versions: List[DocumentVersion] = Field(default_factory=list)
    extracted_fields: List[ExtractedField] = Field(default_factory=list)
    structural_spec: PVStructuralSpec = Field(default_factory=PVStructuralSpec)
    approvals: List[EngineerApproval] = Field(default_factory=list)
    calculation_runs: List[CalculationRun] = Field(default_factory=list)
    rfi_items: List[RFIItem] = Field(default_factory=list)
    risks: List[BVRiskItem] = Field(default_factory=list)

    def locked_calculation_fields(self) -> list[ExtractedField]:
        return [
            field
            for field in self.extracted_fields
            if field.is_confirmed and field.include_in_calculation
        ]

    def is_gate_locked(self, target_id: str) -> bool:
        return any(
            approval.target_id == target_id
            and approval.status == "approved"
            and approval.locked
            for approval in self.approvals
        )
