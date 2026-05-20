from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


BVStandardSystem = Literal["gb", "iec", "as_nzs", "eurocode"]
BVReviewObject = Literal[
    "mounting_structure",
    "steel_structure",
    "concrete_structure",
    "foundation",
    "connection",
    "load_calculation",
    "existing_rooftop_added_load",
]
BVDocumentStatus = Literal["available", "partial", "missing", "not_applicable"]
BVReviewDecision = Literal["ready_for_review", "review_with_holds", "not_ready"]
BVSeverity = Literal["low", "medium", "high", "critical"]


class BVReviewIntake(BaseModel):
    project_name: str = Field(min_length=1)
    country_or_region: str = Field(min_length=1)
    project_type: Literal["utility_pv", "rooftop_pv", "distributed_pv", "mixed"]
    design_stage: Literal["concept", "tender", "detailed_design", "construction_drawing", "as_built"]
    standards_systems: List[BVStandardSystem] = Field(min_length=1)
    review_objects: List[BVReviewObject] = Field(min_length=1)
    client_requirements: List[str] = Field(default_factory=list)
    documents: Dict[str, BVDocumentStatus] = Field(default_factory=dict)


class BVBasisReference(BaseModel):
    basis_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: Literal["code", "iec_standard", "project_specification", "contract", "screening_method"]
    standards_systems: List[BVStandardSystem] = Field(default_factory=list)
    review_objects: List[BVReviewObject] = Field(default_factory=list)
    trigger_conditions: List[str] = Field(default_factory=list)
    evidence_requirements: List[str] = Field(default_factory=list)
    review_actions: List[str] = Field(default_factory=list)


class BVChecklistItem(BaseModel):
    document_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: BVDocumentStatus
    affected_review_objects: List[BVReviewObject] = Field(default_factory=list)
    review_blocked: bool = False
    required_action: str = Field(min_length=1)


class BVReviewPathItem(BaseModel):
    path_id: str = Field(min_length=1)
    review_object: BVReviewObject
    title: str = Field(min_length=1)
    method: str = Field(min_length=1)
    required_inputs: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)
    status: Literal["ready", "hold", "manual_confirmation_required"]


class BVRiskItem(BaseModel):
    risk_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    severity: BVSeverity
    trigger_basis: str = Field(min_length=1)
    linked_field_ids: List[str] = Field(default_factory=list)
    impact_scope: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    blocks_report_issue: bool = False
    category: Literal["risk", "nonconformity", "optimization"]


class BVReviewPlanItem(BaseModel):
    item_id: str = Field(min_length=1)
    phase: Literal["intake", "document_review", "technical_check", "reporting"]
    review_object: Optional[BVReviewObject] = None
    input_documents: List[str] = Field(default_factory=list)
    method: str = Field(min_length=1)
    responsible_role: str = Field(min_length=1)
    blocking_condition: Optional[str] = None
    deliverable: str = Field(min_length=1)


class BVReportSection(BaseModel):
    heading: str = Field(min_length=1)
    items: List[str] = Field(default_factory=list)


class BVReportPreview(BaseModel):
    title: str = Field(min_length=1)
    sections: List[BVReportSection] = Field(default_factory=list)


class BVReviewResult(BaseModel):
    decision: BVReviewDecision
    basis_references: List[BVBasisReference] = Field(default_factory=list)
    checklist_items: List[BVChecklistItem] = Field(default_factory=list)
    review_paths: List[BVReviewPathItem] = Field(default_factory=list)
    risks: List[BVRiskItem] = Field(default_factory=list)
    review_plan: List[BVReviewPlanItem] = Field(default_factory=list)
    report_preview: Optional[BVReportPreview] = None
