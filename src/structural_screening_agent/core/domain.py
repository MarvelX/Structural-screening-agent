from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.models import BuildingIntake


class ProjectProfile(BaseModel):
    project_type: Literal["rooftop_pv", "load_upgrade", "retrofit", "mixed"]
    design_standard: Literal["gb", "aisc", "eurocode"]
    building_type: str = Field(min_length=1)
    structural_system: str = Field(min_length=1)
    roof_type: str = Field(min_length=1)


class ModificationScope(BaseModel):
    intended_modification: str = Field(min_length=1)
    estimated_added_load_kpa: Optional[float] = None


class GeometryProfile(BaseModel):
    building_span_m: Optional[float] = None
    column_spacing_m: Optional[float] = None
    purlin_type: Optional[str] = None


class RoofProfile(BaseModel):
    panel_type: Optional[str] = None
    panel_thickness_mm: Optional[float] = None
    rib_height_mm: Optional[float] = None
    attachment_preference: Literal["clamp_based", "penetrating", "undecided"] = "undecided"
    waterproofing_sensitivity: Literal["low", "medium", "high"] = "medium"
    restricted_installation_zones: Optional[str] = None


class EvidenceProfile(BaseModel):
    drawing_availability: Literal["complete", "partial", "missing"]
    survey_available: bool = False
    member_schedule_status: Literal["available", "partial", "missing"] = "missing"
    connection_detail_status: Literal["available", "partial", "missing"] = "missing"
    roof_vendor_data_status: Literal["available", "partial", "missing"] = "missing"


class VerificationContext(BaseModel):
    corrosion_condition: Literal["low", "moderate", "high", "unknown"] = "unknown"
    shutdown_constraint: Literal["none", "limited", "strict"]
    available_path: Literal["drawings_only", "survey_only", "drawings_plus_survey", "no_viable_path_yet"]


class ScreeningCase(BaseModel):
    project: ProjectProfile
    modification: ModificationScope
    geometry: GeometryProfile
    roof: RoofProfile
    evidence: EvidenceProfile
    verification: VerificationContext


def from_building_intake(intake: BuildingIntake) -> ScreeningCase:
    return ScreeningCase(
        project=ProjectProfile(
            project_type=intake.project_type,
            design_standard=intake.design_standard_context,
            building_type=intake.building_type,
            structural_system=intake.structural_system,
            roof_type=intake.roof_type,
        ),
        modification=ModificationScope(
            intended_modification=intake.intended_modification,
            estimated_added_load_kpa=intake.estimated_added_load_kpa,
        ),
        geometry=GeometryProfile(
            building_span_m=intake.building_span_m,
            column_spacing_m=intake.column_spacing_m,
            purlin_type=intake.purlin_type,
        ),
        roof=RoofProfile(
            panel_type=intake.roof_panel_type,
            panel_thickness_mm=intake.roof_panel_thickness_mm,
            rib_height_mm=intake.roof_rib_height_mm,
            attachment_preference=intake.roof_attachment_preference,
            waterproofing_sensitivity=intake.waterproofing_sensitivity,
            restricted_installation_zones=intake.restricted_installation_zones,
        ),
        evidence=EvidenceProfile(
            drawing_availability=intake.drawing_availability,
            survey_available=intake.survey_available,
            member_schedule_status=intake.existing_member_schedule_status,
            connection_detail_status=intake.connection_detail_status,
            roof_vendor_data_status=intake.roof_vendor_data_status,
        ),
        verification=VerificationContext(
            corrosion_condition=intake.corrosion_condition,
            shutdown_constraint=intake.shutdown_constraint,
            available_path=intake.available_verification_path,
        ),
    )
