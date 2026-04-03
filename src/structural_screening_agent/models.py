from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class DecisionStatus(str, Enum):
    GO = "go"
    CONDITIONAL_GO = "conditional_go"
    NO_GO = "no_go"


class BuildingIntake(BaseModel):
    project_type: Literal["rooftop_pv", "load_upgrade", "retrofit", "mixed"]
    design_standard_context: Literal["gb", "aisc", "eurocode"] = "gb"
    building_type: str = Field(min_length=1)
    structural_system: str = Field(min_length=1)
    roof_type: str = Field(min_length=1)
    intended_modification: str = Field(min_length=1)
    estimated_added_load_kpa: Optional[float] = None
    building_span_m: Optional[float] = None
    column_spacing_m: Optional[float] = None
    eave_height_m: Optional[float] = None
    rafter_section: Optional[str] = None
    column_section: Optional[str] = None
    steel_grade: Optional[str] = None
    purlin_spacing_m: Optional[float] = None
    purlin_type: Optional[str] = None
    roof_panel_type: Optional[str] = None
    roof_panel_thickness_mm: Optional[float] = None
    roof_rib_height_mm: Optional[float] = None
    roof_attachment_preference: Literal["clamp_based", "penetrating", "undecided"] = "undecided"
    existing_member_schedule_status: Literal["available", "partial", "missing"] = "missing"
    connection_detail_status: Literal["available", "partial", "missing"] = "missing"
    roof_vendor_data_status: Literal["available", "partial", "missing"] = "missing"
    corrosion_condition: Literal["low", "moderate", "high", "unknown"] = "unknown"
    waterproofing_sensitivity: Literal["low", "medium", "high"] = "medium"
    restricted_installation_zones: Optional[str] = None
    available_verification_path: Literal[
        "drawings_only", "survey_only", "drawings_plus_survey", "no_viable_path_yet"
    ] = "drawings_only"
    shutdown_constraint: Literal["none", "limited", "strict"]
    drawing_availability: Literal["complete", "partial", "missing"]
    survey_available: bool = False

    @field_validator("estimated_added_load_kpa")
    @classmethod
    def validate_estimated_added_load_kpa(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if value <= 0 or value > 5.0:
            raise ValueError("estimated_added_load_kpa must remain within a realistic screening range (0, 5].")
        return value

    @field_validator("building_span_m")
    @classmethod
    def validate_building_span_m(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if value <= 0 or value > 120.0:
            raise ValueError("building_span_m must remain within a realistic screening range (0, 120].")
        return value

    @field_validator("column_spacing_m")
    @classmethod
    def validate_column_spacing_m(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if value <= 0 or value > 20.0:
            raise ValueError("column_spacing_m must remain within a realistic screening range (0, 20].")
        return value

    @field_validator("eave_height_m")
    @classmethod
    def validate_eave_height_m(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if value <= 0 or value > 30.0:
            raise ValueError("eave_height_m must remain within a realistic screening range (0, 30].")
        return value


class BilingualItem(BaseModel):
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    detail_en: Optional[str] = None
    detail_zh: Optional[str] = None


class ScreeningAction(BilingualItem):
    phase: Literal["must_do", "parallel", "later"]


class ScreeningOption(BaseModel):
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    priority_rationale_en: Optional[str] = None
    priority_rationale_zh: Optional[str] = None
    fit_when_en: str = Field(min_length=1)
    fit_when_zh: str = Field(min_length=1)
    main_constraint_en: str = Field(min_length=1)
    main_constraint_zh: str = Field(min_length=1)
    operational_impact_en: str = Field(min_length=1)
    operational_impact_zh: str = Field(min_length=1)
    cost_level_en: str = Field(min_length=1)
    cost_level_zh: str = Field(min_length=1)
    screening_cost_range_en: str = Field(min_length=1)
    screening_cost_range_zh: str = Field(min_length=1)
    schedule_impact_en: str = Field(min_length=1)
    schedule_impact_zh: str = Field(min_length=1)
    recommendation_note_en: str = Field(min_length=1)
    recommendation_note_zh: str = Field(min_length=1)


class VerificationReadiness(BaseModel):
    level: Literal["ready", "partial", "not_ready"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    blockers: List[BilingualItem] = Field(default_factory=list)


class EngineeringCheck(BaseModel):
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    status: Literal["screen_pass", "review", "undetermined"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class ReserveUncertainty(BaseModel):
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    severity: Literal["low", "medium", "high"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class AttachmentPathway(BaseModel):
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    status: Literal["screen_pass", "review", "undetermined"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class ResourceRecommendation(BaseModel):
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class ReviewTrigger(BaseModel):
    category: Literal["member", "connection"]
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class TraceabilityTrace(BaseModel):
    input_path: str = Field(min_length=1)
    observed_value: str


class TraceabilityFinding(BaseModel):
    finding_id: str = Field(min_length=1)
    severity: Literal["info", "caution", "blocking"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    basis_ids: List[str] = Field(default_factory=list)
    traces: List[TraceabilityTrace] = Field(default_factory=list)


class ScreeningResult(BaseModel):
    status: DecisionStatus
    confidence: Literal["high", "medium", "low"]
    risks: List[BilingualItem] = Field(default_factory=list)
    missing_data: List[BilingualItem] = Field(default_factory=list)
    recommended_actions: List[ScreeningAction] = Field(default_factory=list)
    review_required: List[BilingualItem] = Field(default_factory=list)
    options: List[ScreeningOption] = Field(default_factory=list)
    verification_readiness: VerificationReadiness
    engineering_checks: List[EngineeringCheck] = Field(default_factory=list)
    member_reserve_uncertainties: List[ReserveUncertainty] = Field(default_factory=list)
    attachment_pathways: List[AttachmentPathway] = Field(default_factory=list)
    resource_recommendations: List[ResourceRecommendation] = Field(default_factory=list)
    review_triggers: List[ReviewTrigger] = Field(default_factory=list)
    traceability: List[TraceabilityFinding] = Field(default_factory=list)


class LLMExplanation(BaseModel):
    provider: Literal["mock", "openai", "minimax", "gemini"]
    model: str
    mode: Literal["fallback", "live"]
    requested_provider: Optional[str] = None
    fallback_reason: Optional[str] = None
    summary: str = Field(min_length=1)
