from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_serializer, model_validator

from structural_screening_agent.models import BuildingIntake


class Building(BaseModel):
    project_type: Literal["rooftop_pv", "load_upgrade", "retrofit", "mixed"]
    building_type: str = Field(min_length=1)
    structural_system: str = Field(min_length=1)
    roof_type: str = Field(min_length=1)
    building_span_m: Optional[float] = None
    column_spacing_m: Optional[float] = None
    purlin_type: Optional[str] = None


class RoofSystem(BaseModel):
    panel_type: Optional[str] = None
    panel_thickness_mm: Optional[float] = None
    rib_height_mm: Optional[float] = None
    attachment_preference: Literal["clamp_based", "penetrating", "undecided"] = "undecided"
    waterproofing_sensitivity: Literal["low", "medium", "high"] = "medium"
    restricted_installation_zones: Optional[str] = None


class MemberEvidence(BaseModel):
    drawing_availability: Literal["complete", "partial", "missing"]
    survey_available: bool = False
    member_schedule_status: Literal["available", "partial", "missing"] = "missing"
    corrosion_condition: Literal["low", "moderate", "high", "unknown"] = "unknown"


class ConnectionEvidence(BaseModel):
    connection_detail_status: Literal["available", "partial", "missing"] = "missing"
    roof_vendor_data_status: Literal["available", "partial", "missing"] = "missing"
    available_verification_path: Literal[
        "drawings_only", "survey_only", "drawings_plus_survey", "no_viable_path_yet"
    ] = "drawings_only"


class LoadAssumptions(BaseModel):
    intended_modification: str = Field(min_length=1)
    estimated_added_load_kpa: Optional[float] = None


class StandardsContext(BaseModel):
    design_standard: Literal["gb", "aisc", "eurocode"]
    shutdown_constraint: Literal["none", "limited", "strict"]
    screening_stage: Literal["screening"] = "screening"


class ReviewTask(BaseModel):
    task_id: str = Field(min_length=1)
    task_type: Literal["member_review", "connection_review", "site_survey", "document_recovery"]
    objective: str = Field(min_length=1)
    required_evidence: List[str] = Field(default_factory=list)
    status: Literal["pending", "active", "blocked", "complete"] = "pending"


class ProjectProfile(BaseModel):
    project_type: Literal["rooftop_pv", "load_upgrade", "retrofit", "mixed"]
    design_standard: Literal["gb", "aisc", "eurocode"]
    building_type: str = Field(min_length=1)
    structural_system: str = Field(min_length=1)
    roof_type: str = Field(min_length=1)


class ModificationScope(LoadAssumptions):
    pass


class GeometryProfile(BaseModel):
    building_span_m: Optional[float] = None
    column_spacing_m: Optional[float] = None
    purlin_type: Optional[str] = None


class RoofProfile(RoofSystem):
    pass


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
    building: Building
    roof_system: RoofSystem
    member_evidence: MemberEvidence
    connection_evidence: ConnectionEvidence
    load_assumptions: LoadAssumptions
    standards_context: StandardsContext
    review_tasks: List[ReviewTask] = Field(default_factory=list)

    @property
    def project(self) -> ProjectProfile:
        return ProjectProfile(
            project_type=self.building.project_type,
            design_standard=self.standards_context.design_standard,
            building_type=self.building.building_type,
            structural_system=self.building.structural_system,
            roof_type=self.building.roof_type,
        )

    @property
    def modification(self) -> ModificationScope:
        return ModificationScope.model_validate(self.load_assumptions.model_dump())

    @property
    def geometry(self) -> GeometryProfile:
        return GeometryProfile(
            building_span_m=self.building.building_span_m,
            column_spacing_m=self.building.column_spacing_m,
            purlin_type=self.building.purlin_type,
        )

    @property
    def roof(self) -> RoofProfile:
        return RoofProfile.model_validate(self.roof_system.model_dump())

    @property
    def evidence(self) -> EvidenceProfile:
        return EvidenceProfile(
            drawing_availability=self.member_evidence.drawing_availability,
            survey_available=self.member_evidence.survey_available,
            member_schedule_status=self.member_evidence.member_schedule_status,
            connection_detail_status=self.connection_evidence.connection_detail_status,
            roof_vendor_data_status=self.connection_evidence.roof_vendor_data_status,
        )

    @property
    def verification(self) -> VerificationContext:
        return VerificationContext(
            corrosion_condition=self.member_evidence.corrosion_condition,
            shutdown_constraint=self.standards_context.shutdown_constraint,
            available_path=self.connection_evidence.available_verification_path,
        )


class CodeContext(BaseModel):
    standard: Literal["gb", "aisc", "eurocode"]
    project_type: Literal["rooftop_pv", "load_upgrade", "retrofit", "mixed"]
    building_type: str = Field(min_length=1)
    structural_system: str = Field(min_length=1)
    roof_type: str = Field(min_length=1)
    intended_modification: str = Field(min_length=1)
    shutdown_constraint: Literal["none", "limited", "strict"] = "none"


class PortalFrameGeometry(BaseModel):
    span_m: Optional[float] = None
    bay_spacing_m: Optional[float] = None
    eave_height_m: Optional[float] = None

    @property
    def building_span_m(self) -> Optional[float]:
        return self.span_m

    @property
    def column_spacing_m(self) -> Optional[float]:
        return self.bay_spacing_m


class PrimaryFrameProfile(BaseModel):
    rafter_section: Optional[str] = None
    column_section: Optional[str] = None
    steel_grade: Optional[str] = None


class SecondaryMemberProfile(BaseModel):
    purlin_type: Optional[str] = None
    purlin_spacing_m: Optional[float] = None


class PVLoadProfile(BaseModel):
    added_dead_load_kpa: Optional[float] = None
    coverage: Literal["full_roof", "partial_zone"] = "full_roof"


class PortalFrameEvidence(BaseModel):
    original_drawings_available: bool
    original_calc_report_available: bool = False
    member_schedule_available: bool = False
    site_survey_completed: bool = False
    connection_detail_available: bool = False
    roof_vendor_data_available: bool = False
    drawing_availability: Literal["complete", "partial", "missing"] = "missing"
    survey_available: bool = False
    member_schedule_status: Literal["available", "partial", "missing"] = "missing"
    connection_detail_status: Literal["available", "partial", "missing"] = "missing"
    roof_vendor_data_status: Literal["available", "partial", "missing"] = "missing"
    available_verification_path: Literal[
        "drawings_only", "survey_only", "drawings_plus_survey", "no_viable_path_yet"
    ] = "drawings_only"
    corrosion_condition: Literal["low", "moderate", "high", "unknown"] = "unknown"
    screening_level: Literal["level_a", "level_b", "level_c"]
    missing_critical_data: List[str] = Field(default_factory=list)


class PortalFrameScreeningCase(BaseModel):
    code_context: CodeContext
    geometry: PortalFrameGeometry
    primary_frame: PrimaryFrameProfile
    secondary_members: SecondaryMemberProfile
    pv_load: PVLoadProfile
    evidence: PortalFrameEvidence
    roof_panel_type: Optional[str] = None
    roof_panel_thickness_mm: Optional[float] = None
    roof_rib_height_mm: Optional[float] = None
    roof_attachment_preference: Literal["clamp_based", "penetrating", "undecided"] = "undecided"
    waterproofing_sensitivity: Literal["low", "medium", "high"] = "medium"
    restricted_installation_zones: Optional[str] = None
    review_tasks: List[ReviewTask] = Field(default_factory=list)

    @property
    def project(self) -> ProjectProfile:
        return ProjectProfile(
            project_type=self.code_context.project_type,
            design_standard=self.code_context.standard,
            building_type=self.code_context.building_type,
            structural_system=self.code_context.structural_system,
            roof_type=self.code_context.roof_type,
        )

    @property
    def building(self) -> Building:
        return Building(
            project_type=self.code_context.project_type,
            building_type=self.code_context.building_type,
            structural_system=self.code_context.structural_system,
            roof_type=self.code_context.roof_type,
            building_span_m=self.geometry.span_m,
            column_spacing_m=self.geometry.bay_spacing_m,
            purlin_type=self.secondary_members.purlin_type,
        )

    @property
    def roof_system(self) -> RoofSystem:
        return RoofSystem(
            panel_type=self.roof_panel_type,
            panel_thickness_mm=self.roof_panel_thickness_mm,
            rib_height_mm=self.roof_rib_height_mm,
            attachment_preference=self.roof_attachment_preference,
            waterproofing_sensitivity=self.waterproofing_sensitivity,
            restricted_installation_zones=self.restricted_installation_zones,
        )

    @property
    def member_evidence(self) -> MemberEvidence:
        return MemberEvidence(
            drawing_availability=self.evidence.drawing_availability,
            survey_available=self.evidence.survey_available,
            member_schedule_status=self.evidence.member_schedule_status,
            corrosion_condition=self.evidence.corrosion_condition,
        )

    @property
    def connection_evidence(self) -> ConnectionEvidence:
        return ConnectionEvidence(
            connection_detail_status=self.evidence.connection_detail_status,
            roof_vendor_data_status=self.evidence.roof_vendor_data_status,
            available_verification_path=self.evidence.available_verification_path,
        )

    @property
    def load_assumptions(self) -> LoadAssumptions:
        return LoadAssumptions(
            intended_modification=self.code_context.intended_modification,
            estimated_added_load_kpa=self.pv_load.added_dead_load_kpa,
        )

    @property
    def modification(self) -> ModificationScope:
        return ModificationScope.model_validate(self.load_assumptions.model_dump())

    @property
    def standards_context(self) -> StandardsContext:
        return StandardsContext(
            design_standard=self.code_context.standard,
            shutdown_constraint=self.code_context.shutdown_constraint,
        )

    @property
    def roof(self) -> RoofProfile:
        return RoofProfile.model_validate(self.roof_system.model_dump())

    @property
    def verification(self) -> VerificationContext:
        return VerificationContext(
            corrosion_condition=self.evidence.corrosion_condition,
            shutdown_constraint=self.code_context.shutdown_constraint,
            available_path=self.evidence.available_verification_path,
        )

    @model_validator(mode="before")
    @classmethod
    def _normalize_serialized_input(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        if "code_context" in values:
            return values
        if "building" not in values:
            return values

        building = values.get("building") or {}
        roof_system = values.get("roof_system") or {}
        member_evidence = values.get("member_evidence") or {}
        connection_evidence = values.get("connection_evidence") or {}
        load_assumptions = values.get("load_assumptions") or {}
        standards_context = values.get("standards_context") or {}
        evidence = values.get("evidence") or {}

        normalized_evidence = evidence or _build_portal_frame_evidence_from_legacy_payload(
            building=building,
            member_evidence=member_evidence,
            connection_evidence=connection_evidence,
            load_assumptions=load_assumptions,
        ).model_dump(mode="json")

        return {
            "code_context": {
                "standard": standards_context.get("design_standard", values.get("design_standard_context", "gb")),
                "project_type": building.get("project_type", values.get("project_type")),
                "building_type": building.get("building_type", values.get("building_type")),
                "structural_system": building.get("structural_system", values.get("structural_system")),
                "roof_type": building.get("roof_type", values.get("roof_type")),
                "intended_modification": load_assumptions.get(
                    "intended_modification", values.get("intended_modification", "")
                ),
                "shutdown_constraint": standards_context.get(
                    "shutdown_constraint", values.get("shutdown_constraint", "none")
                ),
            },
            "geometry": {
                "span_m": building.get("building_span_m", values.get("building_span_m")),
                "bay_spacing_m": building.get("column_spacing_m", values.get("column_spacing_m")),
            },
            "primary_frame": {
                "rafter_section": values.get("primary_frame", {}).get(
                    "rafter_section", building.get("rafter_section", values.get("rafter_section"))
                )
                if isinstance(values.get("primary_frame"), dict)
                else building.get("rafter_section", values.get("rafter_section")),
                "column_section": values.get("primary_frame", {}).get(
                    "column_section", building.get("column_section", values.get("column_section"))
                )
                if isinstance(values.get("primary_frame"), dict)
                else building.get("column_section", values.get("column_section")),
                "steel_grade": values.get("primary_frame", {}).get("steel_grade") if isinstance(values.get("primary_frame"), dict) else values.get("steel_grade"),
            },
            "secondary_members": {
                "purlin_type": values.get("secondary_members", {}).get(
                    "purlin_type",
                    values.get("secondary_members", {}).get("purlin_section", building.get("purlin_type", values.get("purlin_type"))),
                )
                if isinstance(values.get("secondary_members"), dict)
                else building.get("purlin_type", values.get("purlin_type")),
                "purlin_spacing_m": values.get("secondary_members", {}).get(
                    "purlin_spacing_m", building.get("purlin_spacing_m", values.get("purlin_spacing_m"))
                )
                if isinstance(values.get("secondary_members"), dict)
                else building.get("purlin_spacing_m", values.get("purlin_spacing_m")),
            },
            "pv_load": {
                "added_dead_load_kpa": load_assumptions.get(
                    "estimated_added_load_kpa", values.get("estimated_added_load_kpa")
                ),
            },
            "evidence": normalized_evidence,
            "roof_panel_type": roof_system.get("panel_type", values.get("roof_panel_type")),
            "roof_panel_thickness_mm": roof_system.get("panel_thickness_mm", values.get("roof_panel_thickness_mm")),
            "roof_rib_height_mm": roof_system.get("rib_height_mm", values.get("roof_rib_height_mm")),
            "roof_attachment_preference": roof_system.get(
                "attachment_preference", values.get("roof_attachment_preference", "undecided")
            ),
            "waterproofing_sensitivity": roof_system.get(
                "waterproofing_sensitivity", values.get("waterproofing_sensitivity", "medium")
            ),
            "restricted_installation_zones": roof_system.get(
                "restricted_installation_zones", values.get("restricted_installation_zones")
            ),
            "review_tasks": values.get("review_tasks", []),
        }

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        data = handler(self)
        data.update(
            {
                "building": self.building.model_dump(mode="json"),
                "roof_system": self.roof_system.model_dump(mode="json"),
                "member_evidence": self.member_evidence.model_dump(mode="json"),
                "connection_evidence": self.connection_evidence.model_dump(mode="json"),
                "load_assumptions": self.load_assumptions.model_dump(mode="json"),
                "standards_context": self.standards_context.model_dump(mode="json"),
                "review_tasks": [task.model_dump(mode="json") for task in self.review_tasks],
            }
        )
        return data


def _derive_portal_frame_evidence(intake: BuildingIntake) -> PortalFrameEvidence:
    original_drawings_available = intake.drawing_availability == "complete"
    member_schedule_available = intake.existing_member_schedule_status == "available"
    site_survey_completed = intake.survey_available
    connection_detail_available = intake.connection_detail_status == "available"
    roof_vendor_data_available = intake.roof_vendor_data_status == "available"

    missing_critical_data: List[str] = []

    if not original_drawings_available:
        missing_critical_data.append("Original structural drawings")
    if not member_schedule_available:
        missing_critical_data.append("Existing member schedule")
    if not site_survey_completed:
        missing_critical_data.append("Targeted site survey")
    if not connection_detail_available:
        missing_critical_data.append("Connection detail records")
    if not roof_vendor_data_available:
        missing_critical_data.append("Roof vendor data")
    if intake.purlin_spacing_m is None:
        missing_critical_data.append("Purlin spacing")
    if intake.rafter_section is None:
        missing_critical_data.append("Primary frame rafter section")

    if not original_drawings_available or not member_schedule_available:
        screening_level = "level_c"
    elif not site_survey_completed or not connection_detail_available or not roof_vendor_data_available:
        screening_level = "level_b"
    else:
        screening_level = "level_a"

    return PortalFrameEvidence(
        original_drawings_available=original_drawings_available,
        original_calc_report_available=original_drawings_available and member_schedule_available,
        member_schedule_available=member_schedule_available,
        site_survey_completed=site_survey_completed,
        connection_detail_available=connection_detail_available,
        roof_vendor_data_available=roof_vendor_data_available,
        drawing_availability=intake.drawing_availability,
        survey_available=intake.survey_available,
        member_schedule_status=intake.existing_member_schedule_status,
        connection_detail_status=intake.connection_detail_status,
        roof_vendor_data_status=intake.roof_vendor_data_status,
        available_verification_path=intake.available_verification_path,
        corrosion_condition=intake.corrosion_condition,
        screening_level=screening_level,
        missing_critical_data=missing_critical_data,
    )


def _build_portal_frame_evidence_from_legacy_payload(
    building: Dict[str, Any],
    member_evidence: Dict[str, Any],
    connection_evidence: Dict[str, Any],
    load_assumptions: Dict[str, Any],
) -> PortalFrameEvidence:
    original_drawings_available = member_evidence.get("drawing_availability") == "complete"
    member_schedule_available = member_evidence.get("member_schedule_status") == "available"
    site_survey_completed = bool(member_evidence.get("survey_available", False))
    connection_detail_available = connection_evidence.get("connection_detail_status") == "available"
    roof_vendor_data_available = connection_evidence.get("roof_vendor_data_status") == "available"
    corrosion_condition = member_evidence.get("corrosion_condition", "unknown")
    available_verification_path = connection_evidence.get("available_verification_path", "drawings_only")
    rafter_section = building.get("rafter_section")
    purlin_spacing_m = building.get("purlin_spacing_m")
    if purlin_spacing_m is None:
        purlin_spacing_m = load_assumptions.get("purlin_spacing_m")

    missing_critical_data: List[str] = []
    if not original_drawings_available:
        missing_critical_data.append("Original structural drawings")
    if not member_schedule_available:
        missing_critical_data.append("Existing member schedule")
    if not site_survey_completed:
        missing_critical_data.append("Targeted site survey")
    if not connection_detail_available:
        missing_critical_data.append("Connection detail records")
    if not roof_vendor_data_available:
        missing_critical_data.append("Roof vendor data")
    if purlin_spacing_m is None:
        missing_critical_data.append("Purlin spacing")
    if rafter_section is None:
        missing_critical_data.append("Primary frame rafter section")

    if not original_drawings_available or not member_schedule_available:
        screening_level = "level_c"
    elif not site_survey_completed or not connection_detail_available or not roof_vendor_data_available:
        screening_level = "level_b"
    else:
        screening_level = "level_a"

    return PortalFrameEvidence(
        original_drawings_available=original_drawings_available,
        original_calc_report_available=original_drawings_available and member_schedule_available,
        member_schedule_available=member_schedule_available,
        site_survey_completed=site_survey_completed,
        connection_detail_available=connection_detail_available,
        roof_vendor_data_available=roof_vendor_data_available,
        drawing_availability=member_evidence.get(
            "drawing_availability",
            "complete" if original_drawings_available else "missing",
        ),
        survey_available=site_survey_completed,
        member_schedule_status=member_evidence.get(
            "member_schedule_status",
            "available" if member_schedule_available else "missing",
        ),
        connection_detail_status=connection_evidence.get(
            "connection_detail_status",
            "available" if connection_detail_available else "missing",
        ),
        roof_vendor_data_status=connection_evidence.get(
            "roof_vendor_data_status",
            "available" if roof_vendor_data_available else "missing",
        ),
        available_verification_path=available_verification_path,
        corrosion_condition=corrosion_condition,
        screening_level=screening_level,
        missing_critical_data=missing_critical_data,
    )


def _derive_review_tasks(intake: BuildingIntake) -> List[ReviewTask]:
    tasks: List[ReviewTask] = []

    if intake.drawing_availability != "complete" or intake.existing_member_schedule_status != "available":
        tasks.append(
            ReviewTask(
                task_id="member_review",
                task_type="member_review",
                objective="Close the governing member reserve path with drawings and member schedule evidence.",
                required_evidence=["structural drawings", "member schedule"],
                status="pending",
            )
        )

    if (
        intake.connection_detail_status != "available"
        or intake.roof_vendor_data_status != "available"
        or intake.roof_panel_thickness_mm is None
        or intake.roof_rib_height_mm is None
    ):
        tasks.append(
            ReviewTask(
                task_id="connection_review",
                task_type="connection_review",
                objective="Close the roof attachment pathway with connection details and roof system evidence.",
                required_evidence=["connection detail", "roof vendor data", "roof panel geometry"],
                status="pending",
            )
        )

    if not intake.survey_available:
        tasks.append(
            ReviewTask(
                task_id="site_survey",
                task_type="site_survey",
                objective="Confirm the as-built condition through a targeted site survey.",
                required_evidence=["site survey"],
                status="pending",
            )
        )

    if intake.drawing_availability != "complete":
        tasks.append(
            ReviewTask(
                task_id="document_recovery",
                task_type="document_recovery",
                objective="Recover missing as-built drawings and evidence records before deeper review.",
                required_evidence=["structural drawings"],
                status="pending",
            )
        )

    return tasks


def from_building_intake(intake: BuildingIntake) -> PortalFrameScreeningCase:
    return PortalFrameScreeningCase(
        code_context=CodeContext(
            standard=intake.design_standard_context,
            project_type=intake.project_type,
            building_type=intake.building_type,
            structural_system=intake.structural_system,
            roof_type=intake.roof_type,
            intended_modification=intake.intended_modification,
            shutdown_constraint=intake.shutdown_constraint,
        ),
        geometry=PortalFrameGeometry(
            span_m=intake.building_span_m,
            bay_spacing_m=intake.column_spacing_m,
            eave_height_m=intake.eave_height_m,
        ),
        primary_frame=PrimaryFrameProfile(
            rafter_section=intake.rafter_section,
            column_section=intake.column_section,
            steel_grade=intake.steel_grade,
        ),
        secondary_members=SecondaryMemberProfile(
            purlin_type=intake.purlin_type,
            purlin_spacing_m=intake.purlin_spacing_m,
        ),
        pv_load=PVLoadProfile(
            added_dead_load_kpa=intake.estimated_added_load_kpa,
        ),
        evidence=_derive_portal_frame_evidence(intake),
        roof_panel_type=intake.roof_panel_type,
        roof_panel_thickness_mm=intake.roof_panel_thickness_mm,
        roof_rib_height_mm=intake.roof_rib_height_mm,
        roof_attachment_preference=intake.roof_attachment_preference,
        waterproofing_sensitivity=intake.waterproofing_sensitivity,
        restricted_installation_zones=intake.restricted_installation_zones,
        review_tasks=_derive_review_tasks(intake),
    )
