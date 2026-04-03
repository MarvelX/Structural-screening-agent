from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field

from structural_screening_agent.core.basis_registry import load_basis_registry
from structural_screening_agent.core.domain import PortalFrameScreeningCase, ScreeningCase
from structural_screening_agent.core.portal_frame import run_portal_frame_screening
from structural_screening_agent.localization import translate_option


class TraceRef(BaseModel):
    input_path: str = Field(min_length=1)
    observed_value: str


class KernelFinding(BaseModel):
    finding_id: str = Field(min_length=1)
    severity: Literal["info", "caution", "blocking"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    basis_ids: List[str] = Field(default_factory=list)
    traces: List[TraceRef] = Field(default_factory=list)


class KernelDecision(BaseModel):
    status: Literal["go", "conditional_go", "no_go"]
    confidence: Literal["high", "medium", "low"]


class ScreeningCheckOutput(BaseModel):
    status: Literal["screen_pass", "review", "undetermined"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class KernelItem(BaseModel):
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)


class VerificationReadinessOutput(BaseModel):
    level: Literal["ready", "partial", "not_ready"]
    score: int = Field(ge=0, le=100)
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    blockers: List[KernelItem] = Field(default_factory=list)


class UncertaintyComponent(BaseModel):
    component: Literal["load_demand", "evidence_completeness", "condition_state", "attachment_definition"]
    severity: Literal["low", "medium", "high"]
    score: int = Field(ge=0, le=100)
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class UncertaintyAssessment(BaseModel):
    overall: Literal["low", "medium", "high"]
    score: int = Field(ge=0, le=100)
    components: List[UncertaintyComponent] = Field(default_factory=list)


class ReserveUncertaintyOutput(BaseModel):
    component: Literal["load_demand", "evidence_completeness", "framing_module", "condition_state"]
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    severity: Literal["low", "medium", "high"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class AttachmentPathwayOutput(BaseModel):
    pathway: Literal["clamp_based", "penetrating", "vendor_confirmed", "defendability"]
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    status: Literal["screen_pass", "review", "undetermined"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class ReviewTriggerOutput(BaseModel):
    category: Literal["member", "connection"]
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class EngineeringCheckOutput(BaseModel):
    check_id: Literal["reserve_screening", "attachment_screening"]
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    status: Literal["screen_pass", "review", "undetermined"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class ActionOutput(BaseModel):
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    phase: Literal["must_do", "parallel", "later"]


class EvidenceSnapshotOutput(BaseModel):
    evidence_id: str = Field(min_length=1)
    category: Literal["member", "connection", "roof", "verification"]
    status: Literal["available", "partial", "missing", "undetermined"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    source_paths: List[str] = Field(default_factory=list)


class CalculationOutput(BaseModel):
    calc_id: str = Field(min_length=1)
    category: Literal["reserve", "attachment", "readiness", "uncertainty", "load"]
    value_text: str = Field(min_length=1)
    numeric_value: Optional[Union[int, float]] = None
    unit: Optional[str] = None
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    formula_en: Optional[str] = None
    formula_zh: Optional[str] = None


class TriggeredRuleOutput(BaseModel):
    rule_id: str = Field(min_length=1)
    severity: Literal["info", "caution", "blocking"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    basis_ids: List[str] = Field(default_factory=list)
    traces: List[TraceRef] = Field(default_factory=list)


class BasisReferenceOutput(BaseModel):
    basis_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    citation_en: str = Field(min_length=1)
    citation_zh: str = Field(min_length=1)
    applicable_standards: List[str] = Field(default_factory=list)
    trigger_conditions: List[str] = Field(default_factory=list)
    review_requirements: List[str] = Field(default_factory=list)
    evidence_requirements: List[str] = Field(default_factory=list)


class ResourceRecommendationOutput(BaseModel):
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class ControllingPathOutput(BaseModel):
    category: Literal["member", "connection"]
    component: Literal["purlin", "primary_frame", "connection"]
    path_id: Literal[
        "purlin_strength",
        "purlin_deflection",
        "primary_frame_rafter",
        "primary_frame_column",
        "connection_path",
    ]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)


class LoadCombinationSensitivityOutput(BaseModel):
    sensitivity_id: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    source_paths: List[str] = Field(default_factory=list)


class AssumptionLedgerItem(BaseModel):
    assumption_id: str = Field(min_length=1)
    status: Literal["active", "resolved"] = "active"
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    source_paths: List[str] = Field(default_factory=list)
    basis_ids: List[str] = Field(default_factory=list)


class KernelOutcome(BaseModel):
    decision: KernelDecision
    controlling_path: Optional[ControllingPathOutput] = None
    load_combination_sensitivities: List[LoadCombinationSensitivityOutput] = Field(default_factory=list)
    assumption_ledger: List[AssumptionLedgerItem] = Field(default_factory=list)
    evidence_snapshot: List[EvidenceSnapshotOutput] = Field(default_factory=list)
    calc_outputs: List[CalculationOutput] = Field(default_factory=list)
    triggered_rules: List[TriggeredRuleOutput] = Field(default_factory=list)
    basis_references: List[BasisReferenceOutput] = Field(default_factory=list)
    reserve_screening: ScreeningCheckOutput
    attachment_screening: ScreeningCheckOutput
    verification_readiness: VerificationReadinessOutput
    uncertainty_assessment: UncertaintyAssessment
    member_reserve_uncertainties: List[ReserveUncertaintyOutput] = Field(default_factory=list)
    attachment_pathways: List[AttachmentPathwayOutput] = Field(default_factory=list)
    review_triggers: List[ReviewTriggerOutput] = Field(default_factory=list)
    engineering_checks: List[EngineeringCheckOutput] = Field(default_factory=list)
    recommended_actions: List[ActionOutput] = Field(default_factory=list)
    resource_recommendations: List[ResourceRecommendationOutput] = Field(default_factory=list)
    findings: List[KernelFinding] = Field(default_factory=list)


def _trace(path: str, value: object) -> TraceRef:
    return TraceRef(input_path=path, observed_value=str(value))


def _severity_score(severity: str) -> int:
    return {"low": 20, "medium": 55, "high": 85}[severity]


def _append_kernel_item(items: List[KernelItem], title_en: str, title_zh: str) -> None:
    if any(item.title_en == title_en for item in items):
        return
    items.append(KernelItem(title_en=title_en, title_zh=title_zh))


def _append_review_trigger(
    triggers: List[ReviewTriggerOutput],
    category: Literal["member", "connection"],
    title_en: str,
    title_zh: str,
    summary_en: str,
    summary_zh: str,
) -> None:
    if any(item.title_en == title_en for item in triggers):
        return
    triggers.append(
        ReviewTriggerOutput(
            category=category,
            title_en=title_en,
            title_zh=title_zh,
            summary_en=summary_en,
            summary_zh=summary_zh,
        )
    )


def _find_calc_output(
    calc_outputs: List[CalculationOutput],
    calc_id: str,
) -> Optional[CalculationOutput]:
    return next((item for item in calc_outputs if item.calc_id == calc_id), None)


def _controlling_ratio_calc_id(
    controlling_path: Optional[ControllingPathOutput],
) -> Optional[str]:
    if controlling_path is None:
        return None
    return {
        "purlin_strength": "purlin_strength_ratio",
        "purlin_deflection": "purlin_deflection_ratio",
        "primary_frame_rafter": "primary_frame_rafter_screening_ratio",
        "primary_frame_column": "primary_frame_column_screening_ratio",
    }.get(controlling_path.path_id)


def _build_added_load_sensitivity_outputs(
    case: ScreeningCase,
    controlling_path: Optional[ControllingPathOutput],
    calc_outputs: List[CalculationOutput],
) -> List[CalculationOutput]:
    if not isinstance(case, PortalFrameScreeningCase):
        return []

    added_load = case.load_assumptions.estimated_added_load_kpa or 0.0
    if added_load <= 0:
        return []

    ratio_calc_id = _controlling_ratio_calc_id(controlling_path)
    if ratio_calc_id is None:
        return []

    governing_ratio_item = _find_calc_output(calc_outputs, ratio_calc_id)
    if governing_ratio_item is None or governing_ratio_item.numeric_value is None:
        return []

    governing_ratio = float(governing_ratio_item.numeric_value)
    if governing_ratio <= 0:
        return []

    critical_added_load = round(added_load / governing_ratio, 2)
    remaining_margin = round(critical_added_load - added_load, 2)
    path_summary_en = controlling_path.summary_en if controlling_path is not None else "Current governing path is not available."
    path_summary_zh = controlling_path.summary_zh if controlling_path is not None else "当前控制路径不可用。"
    return [
        CalculationOutput(
            calc_id="critical_added_load_kpa",
            category="load",
            value_text=f"{critical_added_load:.2f}",
            numeric_value=critical_added_load,
            unit="kPa",
            summary_en=(
                f"Estimated critical added load at which the current governing screening ratio reaches 1.00. {path_summary_en}"
            ),
            summary_zh=(
                f"按当前控制路径反推、使控制筛查比值达到 1.00 时的临界新增荷载估算。{path_summary_zh}"
            ),
            formula_en="q_crit = q_add / eta_gov",
            formula_zh="q_临界 = q_新增 / η_控制",
        ),
        CalculationOutput(
            calc_id="remaining_added_load_margin_kpa",
            category="load",
            value_text=f"{remaining_margin:.2f}",
            numeric_value=remaining_margin,
            unit="kPa",
            summary_en=(
                "Estimated remaining added-load margin relative to the current governing screening path."
                if remaining_margin >= 0
                else "Current added load already exceeds the estimated governing-path threshold."
            ),
            summary_zh=(
                "相对当前控制路径的剩余新增荷载余量估算。"
                if remaining_margin >= 0
                else "当前新增荷载已超过按控制路径反推的临界阈值。"
            ),
            formula_en="q_margin = q_crit - q_add",
            formula_zh="q_余量 = q_临界 - q_新增",
        ),
    ]


def _build_load_combination_sensitivities(
    case: ScreeningCase,
    controlling_path: Optional[ControllingPathOutput],
    calc_outputs: List[CalculationOutput],
) -> List[LoadCombinationSensitivityOutput]:
    if case.building.project_type != "rooftop_pv" or case.load_assumptions.estimated_added_load_kpa is None:
        return []

    standard_label_en = {
        "gb": "GB",
        "aisc": "AISC / ASCE",
        "eurocode": "Eurocode",
    }.get(case.standards_context.design_standard, case.standards_context.design_standard.upper())
    standard_label_zh = {
        "gb": "国标 GB",
        "aisc": "AISC / ASCE",
        "eurocode": "Eurocode",
    }.get(case.standards_context.design_standard, case.standards_context.design_standard.upper())
    added_load = case.load_assumptions.estimated_added_load_kpa
    source_paths = ["pv_load.added_dead_load_kpa"]
    if controlling_path is not None:
        source_paths.append("portal_frame.controlling_path")

    if controlling_path is not None and controlling_path.path_id in {"purlin_deflection", "primary_frame_rafter"}:
        summary_en = (
            f"Current screening remains sensitive to load combinations under the {standard_label_en} route. "
            "Because the governing path is deflection-sensitive, wind and snow combinations may tighten the current conclusion once full code combinations are checked."
        )
        summary_zh = (
            f"当前初筛结论对 {standard_label_zh} 路径下的荷载组合仍较敏感。"
            "由于当前控制路径偏向挠度控制，后续一旦展开风荷载或雪荷载组合核查，当前结论可能进一步收紧。"
        )
    elif controlling_path is not None and controlling_path.path_id == "primary_frame_column":
        summary_en = (
            f"Current screening remains sensitive to load combinations under the {standard_label_en} route. "
            "Because the governing path sits at the primary-frame column, wind-governed combinations may amplify column moment and stability demand."
        )
        summary_zh = (
            f"当前初筛结论对 {standard_label_zh} 路径下的荷载组合仍较敏感。"
            "由于当前控制路径落在主门架柱，后续若出现风荷载控制组合，柱的附加弯矩与稳定需求可能进一步放大。"
        )
    else:
        summary_en = (
            f"Current screening remains sensitive to load combinations under the {standard_label_en} route. "
            f"The added PV dead load of {added_load:.2f} kPa should still be checked against wind, snow, and maintenance combinations before any final release."
        )
        summary_zh = (
            f"当前初筛结论对 {standard_label_zh} 路径下的荷载组合仍较敏感。"
            f"当前新增光伏恒载为 {added_load:.2f} kPa，后续仍应结合风荷载、雪荷载及检修荷载组合再确认一次，才能形成最终放行结论。"
        )

    items = [
        LoadCombinationSensitivityOutput(
            sensitivity_id="portal_frame_load_combination_sensitivity",
            title_en="Load Combination Sensitivity",
            title_zh="荷载组合敏感性提示",
            summary_en=summary_en,
            summary_zh=summary_zh,
            source_paths=source_paths,
        )
    ]

    critical_added_load = _find_calc_output(calc_outputs, "critical_added_load_kpa")
    remaining_margin = _find_calc_output(calc_outputs, "remaining_added_load_margin_kpa")
    if critical_added_load is not None and remaining_margin is not None:
        critical_text = f"{critical_added_load.value_text} {critical_added_load.unit or ''}".strip()
        margin_value = float(remaining_margin.numeric_value or 0)
        margin_text = f"{abs(margin_value):.2f} {remaining_margin.unit or ''}".strip()
        if margin_value >= 0:
            summary_en = (
                f"Estimated critical added load is about {critical_text}; the current screening path still leaves roughly {margin_text} of added-load margin."
            )
            summary_zh = (
                f"按当前控制路径反推，临界新增荷载约为 {critical_text}，当前仍可再增加约 {margin_text} 的新增荷载。"
            )
        else:
            summary_en = (
                f"Estimated critical added load is about {critical_text}; the current added load already exceeds this screening threshold by about {margin_text}."
            )
            summary_zh = (
                f"按当前控制路径反推，临界新增荷载约为 {critical_text}；当前新增荷载已超过该筛查阈值约 {margin_text}。"
            )
        items.append(
            LoadCombinationSensitivityOutput(
                sensitivity_id="portal_frame_added_load_sensitivity",
                title_en="Estimated Critical Added Load",
                title_zh="临界新增荷载估算",
                summary_en=summary_en,
                summary_zh=summary_zh,
                source_paths=["load_assumptions.estimated_added_load_kpa", "portal_frame.controlling_path"],
            )
        )

    return items


def _append_action(actions: List[ActionOutput], title_en: str, title_zh: str, phase: Literal["must_do", "parallel", "later"]) -> None:
    if any(item.title_en == title_en for item in actions):
        return
    actions.append(ActionOutput(title_en=title_en, title_zh=title_zh, phase=phase))


def _append_resource_recommendation(
    items: List[ResourceRecommendationOutput],
    title_en: str,
    title_zh: str,
    summary_en: str,
    summary_zh: str,
) -> None:
    if any(item.title_en == title_en for item in items):
        return
    items.append(
        ResourceRecommendationOutput(
            title_en=title_en,
            title_zh=title_zh,
            summary_en=summary_en,
            summary_zh=summary_zh,
        )
    )


def _default_basis_ids(case: ScreeningCase) -> List[str]:
    registry = load_basis_registry()
    basis_id = {
        "gb": "gb_50017_general",
        "aisc": "aisc_360_general",
        "eurocode": "eurocode_3_general",
    }[case.standards_context.design_standard]
    return [basis_id] if registry.get(basis_id) else []


def _map_status(value: str) -> Literal["available", "partial", "missing", "undetermined"]:
    return {
        "complete": "available",
        "available": "available",
        "partial": "partial",
        "missing": "missing",
        "drawings_only": "partial",
        "survey_only": "partial",
        "drawings_plus_survey": "available",
        "no_viable_path_yet": "missing",
    }.get(value, "undetermined")


def _build_evidence_snapshot(case: ScreeningCase) -> List[EvidenceSnapshotOutput]:
    verification_status = _map_status(case.connection_evidence.available_verification_path)
    items = [
        EvidenceSnapshotOutput(
            evidence_id="member_drawings",
            category="member",
            status=_map_status(case.member_evidence.drawing_availability),
            summary_en=f"Member drawings are currently {case.member_evidence.drawing_availability}.",
            summary_zh=(
                f"当前构件图纸状态为 "
                f"{translate_option('zh', 'drawing_availability', case.member_evidence.drawing_availability)}。"
            ),
            source_paths=["member_evidence.drawing_availability"],
        ),
        EvidenceSnapshotOutput(
            evidence_id="member_schedule",
            category="member",
            status=_map_status(case.member_evidence.member_schedule_status),
            summary_en=f"Member schedule status is {case.member_evidence.member_schedule_status}.",
            summary_zh=(
                f"当前构件表状态为 "
                f"{translate_option('zh', 'document_status', case.member_evidence.member_schedule_status)}。"
            ),
            source_paths=["member_evidence.member_schedule_status"],
        ),
        EvidenceSnapshotOutput(
            evidence_id="site_survey",
            category="member",
            status="available" if case.member_evidence.survey_available else "missing",
            summary_en="Targeted site survey is available." if case.member_evidence.survey_available else "Targeted site survey is still missing.",
            summary_zh="针对性现场调查已具备。" if case.member_evidence.survey_available else "针对性现场调查仍缺失。",
            source_paths=["member_evidence.survey_available"],
        ),
        EvidenceSnapshotOutput(
            evidence_id="connection_details",
            category="connection",
            status=_map_status(case.connection_evidence.connection_detail_status),
            summary_en=f"Connection detail status is {case.connection_evidence.connection_detail_status}.",
            summary_zh=(
                f"当前连接做法资料状态为 "
                f"{translate_option('zh', 'document_status', case.connection_evidence.connection_detail_status)}。"
            ),
            source_paths=["connection_evidence.connection_detail_status"],
        ),
        EvidenceSnapshotOutput(
            evidence_id="roof_vendor_data",
            category="roof",
            status=_map_status(case.connection_evidence.roof_vendor_data_status),
            summary_en=f"Roof vendor data status is {case.connection_evidence.roof_vendor_data_status}.",
            summary_zh=(
                f"当前屋面厂家资料状态为 "
                f"{translate_option('zh', 'document_status', case.connection_evidence.roof_vendor_data_status)}。"
            ),
            source_paths=["connection_evidence.roof_vendor_data_status"],
        ),
        EvidenceSnapshotOutput(
            evidence_id="verification_path",
            category="verification",
            status=verification_status,
            summary_en=f"Verification path is {case.connection_evidence.available_verification_path}.",
            summary_zh=(
                f"当前复核路径为 "
                f"{translate_option('zh', 'available_verification_path', case.connection_evidence.available_verification_path)}。"
            ),
            source_paths=["connection_evidence.available_verification_path"],
        ),
    ]

    if case.building.project_type == "rooftop_pv":
        items.append(
            EvidenceSnapshotOutput(
                evidence_id="roof_panel_geometry",
                category="roof",
                status=(
                    "available"
                    if case.roof_system.panel_thickness_mm is not None and case.roof_system.rib_height_mm is not None
                    else "missing"
                ),
                summary_en=(
                    "Roof panel thickness and rib height are available."
                    if case.roof_system.panel_thickness_mm is not None and case.roof_system.rib_height_mm is not None
                    else "Roof panel thickness and/or rib height are still missing."
                ),
                summary_zh=(
                    "屋面板厚与波高已具备。"
                    if case.roof_system.panel_thickness_mm is not None and case.roof_system.rib_height_mm is not None
                    else "屋面板厚和/或波高仍缺失。"
                ),
                source_paths=["roof_system.panel_thickness_mm", "roof_system.rib_height_mm"],
            )
        )
    return items


def _build_calc_outputs(
    case: ScreeningCase,
    reserve_screening: ScreeningCheckOutput,
    attachment_screening: ScreeningCheckOutput,
    verification_readiness: VerificationReadinessOutput,
    uncertainty_assessment: UncertaintyAssessment,
) -> List[CalculationOutput]:
    added_load = case.load_assumptions.estimated_added_load_kpa or 0.0
    return [
        CalculationOutput(
            calc_id="added_load_kpa",
            category="load",
            value_text=f"{added_load:.2f}",
            numeric_value=round(added_load, 2),
            unit="kPa",
            summary_en="Screening-level added load assumption.",
            summary_zh="筛查层面的新增荷载假定。",
            formula_en="q_add = q_pv",
            formula_zh="q_新增 = q_光伏",
        ),
        CalculationOutput(
            calc_id="reserve_screening_status",
            category="reserve",
            value_text=reserve_screening.status,
            summary_en="Reserve screening module status.",
            summary_zh="承载储备筛查模块状态。",
        ),
        CalculationOutput(
            calc_id="attachment_screening_status",
            category="attachment",
            value_text=attachment_screening.status,
            summary_en="Attachment screening module status.",
            summary_zh="连接路径筛查模块状态。",
        ),
        CalculationOutput(
            calc_id="verification_readiness_score",
            category="readiness",
            value_text=str(verification_readiness.score),
            numeric_value=verification_readiness.score,
            unit="score",
            summary_en="Verification readiness score derived from evidence completeness and path viability.",
            summary_zh="由证据完整度与复核路径可行性得到的复核准备度分数。",
            formula_en="Readiness = evidence/path screening score",
            formula_zh="准备度 = 证据与复核路径综合评分",
        ),
        CalculationOutput(
            calc_id="uncertainty_score",
            category="uncertainty",
            value_text=str(uncertainty_assessment.score),
            numeric_value=uncertainty_assessment.score,
            unit="score",
            summary_en="Overall uncertainty score for the screening case.",
            summary_zh="当前筛查案例的总体不确定性分数。",
            formula_en="Uncertainty = component-weighted screening score",
            formula_zh="不确定性 = 分项加权后的筛查评分",
        ),
    ]


def _build_triggered_rules(findings: List[KernelFinding]) -> List[TriggeredRuleOutput]:
    return [
        TriggeredRuleOutput(
            rule_id=finding.finding_id,
            severity=finding.severity,
            summary_en=finding.summary_en,
            summary_zh=finding.summary_zh,
            basis_ids=list(finding.basis_ids),
            traces=list(finding.traces),
        )
        for finding in findings
    ]


def _build_basis_references(findings: List[KernelFinding]) -> List[BasisReferenceOutput]:
    registry = load_basis_registry()
    basis_ids = []
    for finding in findings:
        for basis_id in finding.basis_ids:
            if basis_id not in basis_ids:
                basis_ids.append(basis_id)

    items: List[BasisReferenceOutput] = []
    for basis_id in basis_ids:
        reference = registry.get(basis_id)
        if reference is None:
            continue
        items.append(
            BasisReferenceOutput(
                basis_id=reference.basis_id,
                source_type=reference.source_type,
                title_en=reference.title_en,
                title_zh=reference.title_zh,
                citation_en=reference.citation_en,
                citation_zh=reference.citation_zh,
                applicable_standards=list(reference.applicable_standards),
                trigger_conditions=list(reference.trigger_conditions),
                review_requirements=list(reference.review_requirements),
                evidence_requirements=list(reference.evidence_requirements),
            )
        )
    return items


def _build_portal_frame_controlling_path(path_id: Optional[str]) -> Optional[ControllingPathOutput]:
    mapping = {
        "purlin_strength": (
            "purlin",
            "Current controlling factor is the purlin strength screening.",
            "当前控制因素主要落在檩条强度筛查。",
        ),
        "purlin_deflection": (
            "purlin",
            "Current controlling factor is the purlin deflection screening.",
            "当前控制因素主要落在檩条挠度筛查。",
        ),
        "primary_frame_rafter": (
            "primary_frame",
            "Current controlling factor is the primary-frame rafter added-moment screening.",
            "当前控制因素主要落在主门架梁的附加弯矩筛查。",
        ),
        "primary_frame_column": (
            "primary_frame",
            "Current controlling factor is the primary-frame column added-moment screening.",
            "当前控制因素主要落在主门架柱的附加弯矩筛查。",
        ),
    }
    if path_id not in mapping:
        return None
    component, summary_en, summary_zh = mapping[path_id]
    return ControllingPathOutput(
        category="member",
        component=component,  # type: ignore[arg-type]
        path_id=path_id,  # type: ignore[arg-type]
        summary_en=summary_en,
        summary_zh=summary_zh,
    )


def _conservative_steel_grade_label(case: PortalFrameScreeningCase) -> tuple[str, str]:
    return {
        "gb": ("Q235", "Q235"),
        "aisc": ("A36", "A36"),
        "eurocode": ("S275", "S275"),
    }.get(case.code_context.standard, ("Q235", "Q235"))


def _append_assumption(
    items: List[AssumptionLedgerItem],
    assumption_id: str,
    summary_en: str,
    summary_zh: str,
    source_paths: Optional[List[str]] = None,
    basis_ids: Optional[List[str]] = None,
) -> None:
    if any(item.assumption_id == assumption_id for item in items):
        return
    items.append(
        AssumptionLedgerItem(
            assumption_id=assumption_id,
            summary_en=summary_en,
            summary_zh=summary_zh,
            source_paths=source_paths or [],
            basis_ids=basis_ids or [],
        )
    )


def _build_assumption_ledger(
    case: ScreeningCase,
    verification_readiness: VerificationReadinessOutput,
) -> List[AssumptionLedgerItem]:
    items: List[AssumptionLedgerItem] = []
    default_basis_ids = _default_basis_ids(case)

    _append_assumption(
        items,
        "screening_scope_boundary",
        "Current output is for early-stage structural screening and path selection only. It does not replace formal design, code calculations, or signed conclusions.",
        "当前输出仅用于前期结构筛查与路径判断，不替代正式结构设计、规范计算或签字结论。",
        basis_ids=default_basis_ids,
    )

    if case.member_evidence.drawing_availability != "complete":
        _append_assumption(
            items,
            "drawing_information_incomplete",
            "The current decision assumes missing drawing information may still change the governing member, connection, or global stability checks in formal review.",
            "当前判断默认缺失图纸信息可能在后续正式复核中改变构件、连接或整体稳定控制条件。",
            source_paths=["member_evidence.drawing_availability"],
            basis_ids=default_basis_ids,
        )
    if not case.member_evidence.survey_available:
        _append_assumption(
            items,
            "site_survey_unverified",
            "Corrosion, connection detailing, and as-built deviations remain unverified until the site survey is completed.",
            "当前尚未通过现场调查验证腐蚀、节点做法与实际构造偏差。",
            source_paths=["member_evidence.survey_available"],
            basis_ids=default_basis_ids,
        )
    if case.member_evidence.member_schedule_status != "available":
        _append_assumption(
            items,
            "member_schedule_incomplete",
            "The existing member schedule / section schedule is still incomplete, so the controlling members identified in formal review may change.",
            "既有构件表/截面表尚未完整掌握，正式复核时关键构件识别仍可能调整。",
            source_paths=["member_evidence.member_schedule_status"],
            basis_ids=default_basis_ids,
        )
    if case.connection_evidence.connection_detail_status != "available":
        _append_assumption(
            items,
            "connection_detail_incomplete",
            "Connection detailing records remain incomplete, so the current connection judgement may still shift during detailed review.",
            "节点连接做法资料尚未完整掌握，连接判断仍可能在后续详细复核中变化。",
            source_paths=["connection_evidence.connection_detail_status"],
            basis_ids=default_basis_ids,
        )
    if case.connection_evidence.roof_vendor_data_status != "available":
        _append_assumption(
            items,
            "roof_vendor_data_incomplete",
            "Roof-system vendor data is still incomplete, so attachment and waterproofing boundaries remain subject to later confirmation.",
            "屋面系统厂家资料尚未完整掌握，屋面连接与防水构造边界仍需后续确认。",
            source_paths=["connection_evidence.roof_vendor_data_status"],
            basis_ids=default_basis_ids,
        )
    if case.roof_system.panel_type == "profiled_sheet" and (
        case.roof_system.panel_thickness_mm is None or case.roof_system.rib_height_mm is None
    ):
        _append_assumption(
            items,
            "roof_panel_geometry_missing",
            "Attachment feasibility for the profiled roof still depends on confirmation of key panel properties such as thickness and rib height.",
            "压型钢板的连接可行性仍依赖板厚和波高等关键参数确认。",
            source_paths=["roof_system.panel_thickness_mm", "roof_system.rib_height_mm"],
            basis_ids=default_basis_ids,
        )
    if verification_readiness.level != "ready":
        _append_assumption(
            items,
            "verification_readiness_not_ready",
            "Until verification readiness reaches 'Ready', the current conclusion should not be used for broad rollout or construction commitment.",
            "在结构复核准备度未达到“已具备”前，当前结论不应作为大范围铺开或施工承诺依据。",
            source_paths=["connection_evidence.available_verification_path", "member_evidence.survey_available"],
            basis_ids=default_basis_ids,
        )

    if isinstance(case, PortalFrameScreeningCase):
        if not case.primary_frame.steel_grade:
            label_en, label_zh = _conservative_steel_grade_label(case)
            _append_assumption(
                items,
                "steel_grade_conservative_default",
                f"Steel grade is still unconfirmed, so the screening keeps a conservative default of {label_en} for the primary-frame member check.",
                f"由于钢材标号缺失，当前主门架筛查按保守的 {label_zh} 材质进行。",
                source_paths=["primary_frame.steel_grade"],
                basis_ids=default_basis_ids,
            )
        if case.secondary_members.purlin_spacing_m is None:
            _append_assumption(
                items,
                "purlin_spacing_default",
                "Purlin spacing is unconfirmed, so the screening uses a provisional default of 1.5 m for tributary-load estimation.",
                "由于檩条间距缺失，当前筛查暂按 1.5 m 的经验默认值估算分担荷载。",
                source_paths=["secondary_members.purlin_spacing_m"],
                basis_ids=default_basis_ids,
            )

    return items


def _extend_with_portal_frame_result(
    case: ScreeningCase,
    calc_outputs: List[CalculationOutput],
    findings: List[KernelFinding],
) -> Optional[ControllingPathOutput]:
    if not isinstance(case, PortalFrameScreeningCase):
        return None

    result = run_portal_frame_screening(case)
    controlling_path = _build_portal_frame_controlling_path(result.controlling_path)
    if result.conclusion_status == "insufficient_evidence":
        return controlling_path

    existing_calc_ids = {item.calc_id for item in calc_outputs}
    for row in result.calculation_rows:
        if row.row_id in existing_calc_ids:
            continue
        calc_outputs.append(
            CalculationOutput(
                calc_id=row.row_id,
                category="reserve",
                value_text=row.value_text,
                numeric_value=row.numeric_value,
                unit=row.unit,
                summary_en=row.label_en,
                summary_zh=row.label_zh,
                formula_en=row.formula_en,
                formula_zh=row.formula_zh,
            )
        )

    portal_frame_basis_id = next(
        (
            basis_id
            for basis_id in result.code_reference_ids
            if basis_id in {
                "gb_portal_frame_purlin_screening",
                "aisc_portal_frame_purlin_screening",
                "eurocode_portal_frame_purlin_screening",
            }
        ),
        None,
    )
    if portal_frame_basis_id is None:
        return controlling_path
    if any(item.finding_id == portal_frame_basis_id for item in findings):
        return controlling_path

    strength_ratio = next(
        (row.numeric_value for row in result.calculation_rows if row.row_id == "purlin_strength_ratio"),
        None,
    )
    deflection_ratio = next(
        (row.numeric_value for row in result.calculation_rows if row.row_id == "purlin_deflection_ratio"),
        None,
    )
    primary_frame_ratio = next(
        (row.numeric_value for row in result.calculation_rows if row.row_id == "primary_frame_screening_ratio"),
        None,
    )
    primary_frame_rafter_ratio = next(
        (row.numeric_value for row in result.calculation_rows if row.row_id == "primary_frame_rafter_screening_ratio"),
        None,
    )
    primary_frame_column_ratio = next(
        (row.numeric_value for row in result.calculation_rows if row.row_id == "primary_frame_column_screening_ratio"),
        None,
    )
    numeric_ratios = [
        value
        for value in (
            strength_ratio,
            deflection_ratio,
            primary_frame_ratio,
            primary_frame_rafter_ratio,
            primary_frame_column_ratio,
        )
        if value is not None
    ]
    if not numeric_ratios:
        return
    governing_ratio = max(numeric_ratios)
    severity = "caution" if governing_ratio >= 0.85 else "info"
    findings.append(
        KernelFinding(
            finding_id=portal_frame_basis_id,
            severity=severity,
            summary_en=result.calculation_summary,
            summary_zh=(
                "门式刚架第一轮筛查已按檩条与主门架附加荷载代理值完成初步判断。"
            ),
            basis_ids=list(result.code_reference_ids),
            traces=[
                _trace("pv_load.added_dead_load_kpa", case.pv_load.added_dead_load_kpa),
                _trace("secondary_members.purlin_spacing_m", case.secondary_members.purlin_spacing_m or 1.5),
                _trace("portal_frame.purlin_strength_ratio", strength_ratio),
                _trace("portal_frame.purlin_deflection_ratio", deflection_ratio),
                _trace("portal_frame.primary_frame_rafter_screening_ratio", primary_frame_rafter_ratio),
                _trace("portal_frame.primary_frame_column_screening_ratio", primary_frame_column_ratio),
                _trace("portal_frame.primary_frame_screening_ratio", primary_frame_ratio),
                _trace("portal_frame.controlling_path", result.controlling_path),
            ],
        )
    )
    return controlling_path


def _build_reserve_screening(case: ScreeningCase) -> ScreeningCheckOutput:
    if case.connection_evidence.available_verification_path == "no_viable_path_yet":
        return ScreeningCheckOutput(
            status="undetermined",
            summary_en="Reserve screening cannot proceed because no defendable verification path is available.",
            summary_zh="由于当前没有可辩护的复核路径，承载储备筛查暂时无法推进。",
        )

    if (
        (case.load_assumptions.estimated_added_load_kpa or 0.0) <= 0.12
        and case.member_evidence.drawing_availability == "complete"
        and case.member_evidence.survey_available
        and case.member_evidence.member_schedule_status == "available"
        and case.member_evidence.corrosion_condition == "low"
        and case.connection_evidence.available_verification_path == "drawings_plus_survey"
    ):
        return ScreeningCheckOutput(
            status="screen_pass",
            summary_en="Reserve screening is favorable under the current load, evidence, and verification path inputs.",
            summary_zh="在当前荷载、证据链和复核路径条件下，承载储备筛查结果较为有利。",
        )

    return ScreeningCheckOutput(
        status="review",
        summary_en="Reserve screening still needs targeted member review because evidence or demand conditions remain open.",
        summary_zh="由于证据链或荷载条件仍未闭合，承载储备筛查仍需进入针对性构件复核。",
    )


def _build_attachment_screening(case: ScreeningCase) -> ScreeningCheckOutput:
    if case.connection_evidence.available_verification_path == "no_viable_path_yet":
        return ScreeningCheckOutput(
            status="undetermined",
            summary_en="Attachment pathway screening cannot proceed because no defendable verification path is available.",
            summary_zh="由于当前没有可辩护的复核路径，连接路径筛查暂时无法推进。",
        )

    if case.roof_system.panel_type == "profiled_sheet" and (
        case.roof_system.panel_thickness_mm is None or case.roof_system.rib_height_mm is None
    ):
        return ScreeningCheckOutput(
            status="undetermined",
            summary_en="Attachment pathway remains undetermined because roof panel geometry is incomplete.",
            summary_zh="由于屋面板几何信息不完整，连接路径当前仍不可判定。",
        )

    if case.connection_evidence.available_verification_path in ("drawings_only", "drawings_plus_survey"):
        return ScreeningCheckOutput(
            status="screen_pass",
            summary_en="Attachment pathway is screenable under the current roof geometry and verification path.",
            summary_zh="在当前屋面几何和复核路径条件下，连接路径已具备筛查条件。",
        )

    return ScreeningCheckOutput(
        status="review",
        summary_en="Attachment pathway still needs targeted connection review.",
        summary_zh="连接路径仍需进入针对性连接复核。",
    )


def _build_verification_readiness(case: ScreeningCase) -> VerificationReadinessOutput:
    blockers: List[KernelItem] = []
    if case.connection_evidence.available_verification_path == "no_viable_path_yet":
        _append_kernel_item(blockers, "No defendable verification route has been established yet", "当前尚未建立可辩护的复核路径")
    if case.member_evidence.drawing_availability == "missing":
        _append_kernel_item(blockers, "Original structural drawings are still missing", "原结构图纸仍然缺失")
    if not case.member_evidence.survey_available:
        _append_kernel_item(blockers, "Targeted site survey has not been completed", "针对性现场调查尚未完成")
    if case.roof_system.panel_type == "profiled_sheet":
        if case.roof_system.panel_thickness_mm is None:
            _append_kernel_item(blockers, "Roof panel thickness is still unconfirmed", "屋面板厚仍未确认")
        if case.roof_system.rib_height_mm is None:
            _append_kernel_item(blockers, "Roof rib height is still unconfirmed", "屋面波高仍未确认")
    if case.member_evidence.member_schedule_status != "available":
        _append_kernel_item(blockers, "Existing member schedule / section schedule is incomplete", "既有构件表/截面表尚不完整")
    if case.connection_evidence.connection_detail_status != "available":
        _append_kernel_item(blockers, "Connection detail record is incomplete", "节点连接做法资料尚不完整")
    if case.connection_evidence.roof_vendor_data_status != "available":
        _append_kernel_item(blockers, "Roof vendor data is incomplete", "屋面系统厂家资料尚不完整")

    if case.connection_evidence.available_verification_path == "no_viable_path_yet":
        return VerificationReadinessOutput(
            level="not_ready",
            score=20,
            summary_en="The case is not ready for a defendable verification package yet.",
            summary_zh="当前案例尚不具备形成可辩护复核包的条件。",
            blockers=blockers,
        )

    if (
        case.member_evidence.drawing_availability == "complete"
        and case.member_evidence.survey_available
        and case.member_evidence.member_schedule_status == "available"
        and case.connection_evidence.connection_detail_status == "available"
        and case.connection_evidence.roof_vendor_data_status == "available"
        and case.connection_evidence.available_verification_path == "drawings_plus_survey"
    ):
        return VerificationReadinessOutput(
            level="ready",
            score=85,
            summary_en="The case is ready to proceed into a targeted verification package.",
            summary_zh="当前案例已具备进入针对性复核包的基本条件。",
            blockers=blockers,
        )

    return VerificationReadinessOutput(
        level="partial",
        score=55,
        summary_en="The case is partially ready, but key evidence and review tasks remain open.",
        summary_zh="当前案例部分具备条件，但仍有关键证据和复核任务未闭合。",
        blockers=blockers,
    )


def _build_uncertainty_assessment(case: ScreeningCase) -> UncertaintyAssessment:
    added_load = case.load_assumptions.estimated_added_load_kpa or 0.0
    load_severity = "high" if added_load >= 0.18 else ("medium" if added_load >= 0.12 else "low")
    evidence_severity = "high" if (
        case.member_evidence.drawing_availability != "complete"
        or case.member_evidence.member_schedule_status != "available"
    ) else "low"
    condition_severity = "high" if case.member_evidence.corrosion_condition == "high" else (
        "medium" if case.member_evidence.corrosion_condition in ("moderate", "unknown") or not case.member_evidence.survey_available else "low"
    )
    attachment_severity = "high" if (
        case.roof_system.panel_type == "profiled_sheet"
        and (case.roof_system.panel_thickness_mm is None or case.roof_system.rib_height_mm is None)
    ) else "low"

    components = [
        UncertaintyComponent(
            component="load_demand",
            severity=load_severity,
            score=_severity_score(load_severity),
            summary_en=f"Added load assumption is {added_load:.2f} kPa at screening stage.",
            summary_zh=f"当前筛查阶段的新增荷载假设为 {added_load:.2f} kPa。",
        ),
        UncertaintyComponent(
            component="evidence_completeness",
            severity=evidence_severity,
            score=_severity_score(evidence_severity),
            summary_en="Drawings and member evidence remain incomplete." if evidence_severity != "low" else "Drawings and member evidence are comparatively complete.",
            summary_zh="图纸和构件证据链仍不完整。" if evidence_severity != "low" else "图纸和构件证据链相对完整。",
        ),
        UncertaintyComponent(
            component="condition_state",
            severity=condition_severity,
            score=_severity_score(condition_severity),
            summary_en="Condition-state confidence remains limited." if condition_severity != "low" else "Condition-state confidence is comparatively stable.",
            summary_zh="现状条件判断信心仍然有限。" if condition_severity != "low" else "现状条件判断相对稳定。",
        ),
        UncertaintyComponent(
            component="attachment_definition",
            severity=attachment_severity,
            score=_severity_score(attachment_severity),
            summary_en="Attachment definition remains incomplete." if attachment_severity != "low" else "Attachment definition is comparatively complete.",
            summary_zh="连接路径定义仍不完整。" if attachment_severity != "low" else "连接路径定义相对完整。",
        ),
    ]
    score = max(component.score for component in components)
    overall = "high" if score >= 80 else ("medium" if score >= 50 else "low")
    return UncertaintyAssessment(overall=overall, score=score, components=components)


def _build_member_reserve_uncertainties(case: ScreeningCase) -> List[ReserveUncertaintyOutput]:
    items: List[ReserveUncertaintyOutput] = []
    added_load = case.load_assumptions.estimated_added_load_kpa or 0.0
    load_severity = "high" if added_load >= 0.18 else ("medium" if added_load >= 0.12 else "low")
    items.append(
        ReserveUncertaintyOutput(
            component="load_demand",
            title_en="Member Reserve Uncertainty: Load Demand",
            title_zh="构件承载储备不确定性：新增荷载需求",
            severity=load_severity,
            summary_en=(
                f"Added load is currently {added_load:.2f} kPa, which keeps the demand-side uncertainty elevated until governing member checks are closed."
                if load_severity != "low"
                else f"Added load is currently {added_load:.2f} kPa, so demand-side uncertainty is comparatively limited at screening level."
            ),
            summary_zh=(
                f"当前新增荷载为 {added_load:.2f} kPa，在控制构件复核闭合前，需求侧不确定性仍然偏高。"
                if load_severity != "low"
                else f"当前新增荷载为 {added_load:.2f} kPa，因此在筛查层面需求侧不确定性相对可控。"
            ),
        )
    )

    evidence_severity = "high" if (
        case.member_evidence.drawing_availability == "missing"
        or case.member_evidence.member_schedule_status == "missing"
    ) else ("medium" if (
        case.member_evidence.drawing_availability != "complete"
        or case.member_evidence.member_schedule_status != "available"
    ) else "low")
    items.append(
        ReserveUncertaintyOutput(
            component="evidence_completeness",
            title_en="Member Reserve Uncertainty: Evidence Completeness",
            title_zh="构件承载储备不确定性：证据链完整度",
            severity=evidence_severity,
            summary_en=(
                "Drawings and member schedules are sufficiently complete for a first-pass member reserve screen."
                if evidence_severity == "low"
                else "Drawings and/or member schedules remain incomplete, so reserve-capacity screening still rests on a partial evidence chain."
            ),
            summary_zh=(
                "图纸和构件表已基本完整，可支持一轮构件承载储备初筛。"
                if evidence_severity == "low"
                else "当前图纸和/或构件表仍不完整，因此承载储备筛查仍建立在部分证据链之上。"
            ),
        )
    )

    span = case.building.building_span_m or 0.0
    spacing = case.building.column_spacing_m or 0.0
    framing_severity = "high" if span >= 33.0 or spacing >= 8.5 else ("medium" if span >= 27.0 or spacing >= 8.0 else "low")
    items.append(
        ReserveUncertaintyOutput(
            component="framing_module",
            title_en="Member Reserve Uncertainty: Framing Module",
            title_zh="构件承载储备不确定性：框架模块",
            severity=framing_severity,
            summary_en=(
                f"Span {span:.1f} m and column spacing {spacing:.1f} m place the framing module in a range that should be treated as a governing uncertainty driver."
                if framing_severity != "low"
                else f"Span {span:.1f} m and column spacing {spacing:.1f} m keep the framing module within a relatively manageable screening range."
            ),
            summary_zh=(
                f"当前跨度 {span:.1f} m、柱距 {spacing:.1f} m，使框架模块进入应重点关注的不确定性区间。"
                if framing_severity != "low"
                else f"当前跨度 {span:.1f} m、柱距 {spacing:.1f} m，使框架模块仍处于相对可控的筛查区间。"
            ),
        )
    )

    condition_severity = "high" if case.member_evidence.corrosion_condition == "high" else "low"
    if condition_severity != "high" and (
        case.member_evidence.corrosion_condition == "moderate" or not case.member_evidence.survey_available
    ):
        condition_severity = "medium"
    items.append(
        ReserveUncertaintyOutput(
            component="condition_state",
            title_en="Member Reserve Uncertainty: Condition State",
            title_zh="构件承载储备不确定性：现状条件",
            severity=condition_severity,
            summary_en=(
                "Corrosion exposure and current-survey evidence still leave the as-is condition state uncertain for reserve screening."
                if condition_severity != "low"
                else "Observed condition inputs are comparatively stable for screening-level reserve judgement."
            ),
            summary_zh=(
                "当前腐蚀暴露与现场调查证据仍使既有状态对承载储备筛查构成不确定性。"
                if condition_severity != "low"
                else "当前现状条件输入相对稳定，可支持筛查层面的承载储备判断。"
            ),
        )
    )
    return items


def _build_attachment_pathways(case: ScreeningCase) -> List[AttachmentPathwayOutput]:
    items: List[AttachmentPathwayOutput] = []
    if case.building.project_type != "rooftop_pv":
        return [
            AttachmentPathwayOutput(
                pathway="defendability",
                title_en="Attachment Pathway: Scenario-Specific Connection Route",
                title_zh="连接路径：场景相关连接路径",
                status="review",
                summary_en="Attachment pathways in this scenario should be resolved in the next-stage engineering package.",
                summary_zh="当前场景下的连接路径应在下一阶段工程包中继续明确。",
            )
        ]

    clamp_status = "review"
    clamp_summary_en = "Clamp-based attachment is a plausible first route, but it still needs roof geometry and detailing confirmation."
    clamp_summary_zh = "夹持式连接是一个可优先考虑的路径，但仍需补齐屋面几何与构造确认。"
    if case.connection_evidence.available_verification_path == "no_viable_path_yet":
        clamp_status = "undetermined"
        clamp_summary_en = "No defendable review route exists yet, so a clamp-based pathway cannot be screened credibly."
        clamp_summary_zh = "当前尚无可辩护复核路径，因此夹持式连接路径暂无法可信筛查。"
    elif case.roof_system.panel_type == "profiled_sheet" and (
        case.roof_system.panel_thickness_mm is None or case.roof_system.rib_height_mm is None
    ):
        clamp_status = "undetermined"
        clamp_summary_en = "Clamp-based attachment remains undetermined because roof panel thickness and/or rib height are still missing."
        clamp_summary_zh = "由于屋面板厚和/或波高仍缺失，夹持式连接路径当前仍不可判定。"
    elif (
        case.roof_system.attachment_preference == "clamp_based"
        and case.connection_evidence.available_verification_path == "drawings_plus_survey"
        and case.connection_evidence.connection_detail_status == "available"
    ):
        clamp_status = "screen_pass"
        clamp_summary_en = "Clamp-based attachment is the current best-screened route and can proceed into formal detailing review."
        clamp_summary_zh = "夹持式连接是当前证据链最完整的路径，可进入正式构造复核。"
    items.append(
        AttachmentPathwayOutput(
            pathway="clamp_based",
            title_en="Attachment Pathway: Clamp-Based Roof Connection",
            title_zh="连接路径：夹持式屋面连接",
            status=clamp_status,
            summary_en=clamp_summary_en,
            summary_zh=clamp_summary_zh,
        )
    )

    penetrating_status = "review"
    penetrating_summary_en = "Penetrating attachment remains possible but should be escalated through targeted connection and waterproofing review."
    penetrating_summary_zh = "穿透式连接并非不可选，但应先进入针对性的连接与防水复核。"
    if case.connection_evidence.available_verification_path == "no_viable_path_yet":
        penetrating_status = "undetermined"
        penetrating_summary_en = "Penetrating attachment cannot be screened responsibly until a defendable review route is established."
        penetrating_summary_zh = "在建立可辩护复核路径前，穿透式连接无法负责任地进行筛查。"
    elif case.roof_system.waterproofing_sensitivity == "high":
        penetrating_status = "review"
        penetrating_summary_en = "High waterproofing sensitivity keeps penetrating attachment in a review-required state even if the route remains technically possible."
        penetrating_summary_zh = "高防水敏感性使穿透式连接即便技术上可行，也应保持在需复核状态。"
    elif (
        case.roof_system.attachment_preference == "penetrating"
        and case.connection_evidence.connection_detail_status == "available"
        and case.connection_evidence.available_verification_path == "drawings_plus_survey"
    ):
        penetrating_status = "screen_pass"
        penetrating_summary_en = "Penetrating attachment can be screened forward under the current evidence set, subject to formal detailing review."
        penetrating_summary_zh = "在当前证据链下，穿透式连接可进入下一步筛查放行，但仍需正式构造复核。"
    items.append(
        AttachmentPathwayOutput(
            pathway="penetrating",
            title_en="Attachment Pathway: Penetrating Roof Connection",
            title_zh="连接路径：穿透式屋面连接",
            status=penetrating_status,
            summary_en=penetrating_summary_en,
            summary_zh=penetrating_summary_zh,
        )
    )

    vendor_status = "review"
    vendor_summary_en = "A vendor-confirmed roof-system route remains worth reviewing if supplier data can anchor the attachment pathway."
    vendor_summary_zh = "如果厂家资料能够锚定连接做法，则厂家确认路径仍值得继续复核。"
    if case.connection_evidence.available_verification_path == "no_viable_path_yet":
        vendor_status = "undetermined"
        vendor_summary_en = "Without a defendable review route, a vendor-confirmed pathway cannot be established yet."
        vendor_summary_zh = "在缺少可辩护复核路径时，当前无法建立厂家确认路径。"
    elif case.connection_evidence.roof_vendor_data_status == "missing":
        vendor_status = "undetermined"
        vendor_summary_en = "Roof-system vendor data is still missing, so a vendor-confirmed pathway is currently undetermined."
        vendor_summary_zh = "当前屋面系统厂家资料仍缺失，因此厂家确认路径暂不可判定。"
    elif case.connection_evidence.roof_vendor_data_status == "available" and case.connection_evidence.available_verification_path == "drawings_plus_survey":
        vendor_status = "screen_pass"
        vendor_summary_en = "Vendor data is available and can support a more defendable roof-system-specific pathway."
        vendor_summary_zh = "厂家资料已具备，可支撑更可辩护的屋面系统专项路径。"
    items.append(
        AttachmentPathwayOutput(
            pathway="vendor_confirmed",
            title_en="Attachment Pathway: Vendor-Confirmed Roof-System Route",
            title_zh="连接路径：厂家确认的屋面系统路径",
            status=vendor_status,
            summary_en=vendor_summary_en,
            summary_zh=vendor_summary_zh,
        )
    )

    defendability_status = "review"
    defendability_summary_en = "A defendable attachment route is forming, but one or more evidence gaps still need to close before scheme commitment."
    defendability_summary_zh = "当前正在形成可辩护的连接路径，但在承诺方案前仍需补齐若干证据缺口。"
    if case.connection_evidence.available_verification_path == "no_viable_path_yet" or (
        case.roof_system.panel_type == "profiled_sheet"
        and (case.roof_system.panel_thickness_mm is None or case.roof_system.rib_height_mm is None)
    ):
        defendability_status = "undetermined"
        defendability_summary_en = "The current evidence set does not yet support a defendable attachment route."
        defendability_summary_zh = "当前证据链尚不足以支撑一条可辩护的连接路径。"
    elif case.connection_evidence.available_verification_path == "drawings_plus_survey" and (
        clamp_status == "screen_pass" or vendor_status == "screen_pass"
    ):
        defendability_status = "screen_pass"
        defendability_summary_en = "The current evidence set supports a defendable attachment route for the next-stage design review."
        defendability_summary_zh = "当前证据链已可支撑进入下一阶段设计复核的可辩护连接路径。"
    items.append(
        AttachmentPathwayOutput(
            pathway="defendability",
            title_en="Attachment Pathway: Current Defendability",
            title_zh="连接路径：当前可辩护性",
            status=defendability_status,
            summary_en=defendability_summary_en,
            summary_zh=defendability_summary_zh,
        )
    )
    return items


def _build_review_triggers(case: ScreeningCase) -> List[ReviewTriggerOutput]:
    triggers: List[ReviewTriggerOutput] = []
    if (
        case.load_assumptions.estimated_added_load_kpa is not None
        and case.load_assumptions.estimated_added_load_kpa >= 0.15
        and case.member_evidence.drawing_availability != "complete"
    ):
        _append_review_trigger(
            triggers,
            "member",
            "Member Review Trigger: added load and incomplete framing evidence",
            "构件复核触发项：新增荷载与构件证据链不完整",
            "Added load is already material while drawings / member schedules remain incomplete, so member-level reserve review should be escalated.",
            "当前新增荷载已经具有影响，且图纸/构件表证据链仍不完整，因此应升级进入构件层面的承载复核。",
        )
    if (
        case.building.building_span_m is not None
        and case.building.column_spacing_m is not None
        and case.building.building_span_m >= 33.0
        and case.building.column_spacing_m >= 8.5
    ):
        _append_review_trigger(
            triggers,
            "member",
            "Member Review Trigger: long-span framing module",
            "构件复核触发项：大跨度框架模块",
            "The framing module is already in a longer-span range, so formal member review should confirm the governing members and reserve path.",
            "当前框架模块已进入较大跨度范围，因此应通过正式构件复核确认控制构件与承载储备路径。",
        )
    if case.roof_system.panel_type == "profiled_sheet" and (
        case.roof_system.panel_thickness_mm is None or case.roof_system.rib_height_mm is None
    ):
        _append_review_trigger(
            triggers,
            "connection",
            "Connection Review Trigger: missing panel thickness / rib height",
            "连接复核触发项：板厚 / 波高缺失",
            "Panel thickness and/or rib height are still missing, so the attachment pathway cannot enter a defendable connection review package yet.",
            "当前板厚和/或波高仍缺失，因此连接路径尚不能进入可辩护的连接复核包。",
        )
    if (
        case.connection_evidence.connection_detail_status != "available"
        or case.connection_evidence.roof_vendor_data_status != "available"
    ):
        _append_review_trigger(
            triggers,
            "connection",
            "Connection Review Trigger: incomplete connection detail or vendor data",
            "连接复核触发项：连接做法或厂家资料不完整",
            "Connection detailing records and/or roof vendor data remain incomplete, so connection and roof detailing review should continue.",
            "当前节点做法资料和/或屋面厂家资料仍不完整，因此应继续开展连接与屋面构造复核。",
        )
    if case.roof_system.waterproofing_sensitivity == "high" and case.roof_system.attachment_preference == "penetrating":
        _append_review_trigger(
            triggers,
            "connection",
            "Connection Review Trigger: penetrating attachment under high waterproofing sensitivity",
            "连接复核触发项：高防水敏感下的穿透式连接",
            "A penetrating attachment path under high waterproofing sensitivity should be escalated to a dedicated connection and waterproofing review.",
            "在高防水敏感条件下采用穿透式连接，应升级为专项连接与防水复核。",
        )
    return triggers


def _build_engineering_checks(
    reserve_screening: ScreeningCheckOutput,
    attachment_screening: ScreeningCheckOutput,
) -> List[EngineeringCheckOutput]:
    return [
        EngineeringCheckOutput(
            check_id="reserve_screening",
            title_en="Reserve Capacity Screening",
            title_zh="承载储备筛查",
            status=reserve_screening.status,
            summary_en=reserve_screening.summary_en,
            summary_zh=reserve_screening.summary_zh,
        ),
        EngineeringCheckOutput(
            check_id="attachment_screening",
            title_en="Attachment Feasibility Screening",
            title_zh="连接可行性筛查",
            status=attachment_screening.status,
            summary_en=attachment_screening.summary_en,
            summary_zh=attachment_screening.summary_zh,
        ),
    ]


def _build_recommended_actions(case: ScreeningCase, findings: List[KernelFinding]) -> List[ActionOutput]:
    actions: List[ActionOutput] = []
    if any(finding.finding_id == "verification_path_blocked" for finding in findings):
        _append_action(actions, "Pause progression and establish a defendable verification route", "暂停推进并先建立可辩护的复核路径", "must_do")
    if any(finding.finding_id == "roof_attachment_uncertainty" for finding in findings):
        _append_action(actions, "Confirm panel profile, rib geometry, and attachment path before scheme lock", "在锁定方案前确认板型、波形参数及支架连接路径", "must_do")
    if (
        case.load_assumptions.estimated_added_load_kpa is not None
        and case.load_assumptions.estimated_added_load_kpa >= 0.15
        and case.member_evidence.drawing_availability != "complete"
    ):
        _append_action(actions, "Perform targeted structural verification", "开展针对性结构复核", "must_do")
    if (
        case.member_evidence.corrosion_condition in ("moderate", "high")
        and case.member_evidence.drawing_availability != "complete"
        and not case.member_evidence.survey_available
    ):
        _append_action(actions, "Use survey findings to confirm corrosion severity before broad rollout", "在大范围铺设前结合现场调查确认腐蚀程度", "parallel")
    if (
        case.building.building_span_m is not None
        and case.building.column_spacing_m is not None
        and case.building.building_span_m >= 33.0
        and case.building.column_spacing_m >= 8.5
        and case.member_evidence.drawing_availability != "complete"
    ):
        _append_action(actions, "Use a framing module check to target the first verification package", "先按框架模数梳理首轮复核范围", "parallel")
    if case.standards_context.shutdown_constraint in ("limited", "strict") and not (case.roof_system.restricted_installation_zones or "").strip():
        _append_action(actions, "Define a restricted-zone installation plan before broad rollout", "在大范围推进前先明确分区安装策略", "parallel")
    if not any(finding.finding_id == "verification_path_blocked" for finding in findings):
        _append_action(actions, "Re-rank full-roof rollout after the first verification package closes", "在首轮复核完成后重新排序整屋面推进范围", "later")
    return actions


def _build_resource_recommendations(
    case: ScreeningCase,
    engineering_checks: List[EngineeringCheckOutput],
    review_triggers: List[ReviewTriggerOutput],
    attachment_pathways: List[AttachmentPathwayOutput],
) -> List[ResourceRecommendationOutput]:
    items: List[ResourceRecommendationOutput] = []
    member_triggered = any(item.category == "member" for item in review_triggers)
    reserve_check = next((item for item in engineering_checks if item.check_id == "reserve_screening"), None)
    if member_triggered or (reserve_check and reserve_check.status != "screen_pass"):
        _append_resource_recommendation(
            items,
            "Structural Engineer for Member Review",
            "结构复核工程师",
            "Assign a steel/structural review engineer to close the governing member path, reserve checks, and framing assumptions.",
            "建议配置钢结构/结构复核工程师，用于闭合控制构件路径、承载储备检查与框架假定。",
        )
    connection_triggered = any(item.category == "connection" for item in review_triggers)
    connection_path_uncertain = any(item.status != "screen_pass" for item in attachment_pathways)
    if connection_triggered or connection_path_uncertain:
        _append_resource_recommendation(
            items,
            "Roof System and Attachment Specialist",
            "屋面系统与连接专项支持",
            "Bring in roof-system/vendor and connection-detail support to confirm attachment geometry, detailing, and waterproofing boundaries.",
            "建议配置屋面系统厂家/连接专项支持，用于确认连接几何、构造做法与防水边界。",
        )
    if not case.member_evidence.survey_available or case.member_evidence.corrosion_condition in ("moderate", "high", "unknown"):
        _append_resource_recommendation(
            items,
            "Targeted Site Survey and Roof Inspection",
            "现场调查与屋面检查",
            "Use a targeted site survey and roof inspection team to confirm the as-is condition, corrosion state, and field access assumptions.",
            "建议配置针对性现场调查与屋面检查资源，用于确认既有状态、腐蚀等级和现场进入条件。",
        )
    if (
        case.member_evidence.drawing_availability != "complete"
        or case.member_evidence.member_schedule_status != "available"
        or case.connection_evidence.connection_detail_status != "available"
    ):
        _append_resource_recommendation(
            items,
            "As-Built Document Recovery Support",
            "既有资料补齐支持",
            "Coordinate drawing recovery and as-built document collation so the next review package does not rely on fragmented evidence.",
            "建议配置既有图纸与资料补齐支持，避免下一轮复核继续依赖碎片化证据链。",
        )
    return items


def evaluate_screening_case(case: ScreeningCase) -> KernelOutcome:
    registry = load_basis_registry()
    findings: List[KernelFinding] = []
    default_basis_ids = _default_basis_ids(case)
    reserve_screening = _build_reserve_screening(case)
    attachment_screening = _build_attachment_screening(case)
    verification_readiness = _build_verification_readiness(case)
    uncertainty_assessment = _build_uncertainty_assessment(case)
    member_reserve_uncertainties = _build_member_reserve_uncertainties(case)
    attachment_pathways = _build_attachment_pathways(case)
    review_triggers = _build_review_triggers(case)
    assumption_ledger = _build_assumption_ledger(case, verification_readiness)

    if case.verification.available_path == "no_viable_path_yet":
        findings.append(
            KernelFinding(
                finding_id="verification_path_blocked",
                severity="blocking",
                summary_en="No defendable verification path is available at the current project stage.",
                summary_zh="当前项目阶段尚无可辩护的复核路径。",
                basis_ids=default_basis_ids,
                traces=[
                    _trace("verification.available_path", case.verification.available_path),
                    _trace("evidence.drawing_availability", case.evidence.drawing_availability),
                    _trace("evidence.survey_available", case.evidence.survey_available),
                ],
            )
        )

    if case.roof.panel_type == "profiled_sheet" and (
        case.roof.panel_thickness_mm is None or case.roof.rib_height_mm is None
    ):
        findings.append(
            KernelFinding(
                finding_id="roof_attachment_uncertainty",
                severity="caution",
                summary_en="Roof attachment pathway remains uncertain because panel geometry is incomplete.",
                summary_zh="由于屋面板几何信息不完整，当前连接路径仍不确定。",
                basis_ids=default_basis_ids,
                traces=[
                    _trace("roof.panel_type", case.roof.panel_type),
                    _trace("roof.panel_thickness_mm", case.roof.panel_thickness_mm),
                    _trace("roof.rib_height_mm", case.roof.rib_height_mm),
                ],
            )
        )

    engineering_checks = _build_engineering_checks(reserve_screening, attachment_screening)
    recommended_actions = _build_recommended_actions(case, findings)
    resource_recommendations = _build_resource_recommendations(
        case,
        engineering_checks,
        review_triggers,
        attachment_pathways,
    )
    evidence_snapshot = _build_evidence_snapshot(case)
    calc_outputs = _build_calc_outputs(
        case,
        reserve_screening,
        attachment_screening,
        verification_readiness,
        uncertainty_assessment,
    )
    controlling_path = _extend_with_portal_frame_result(case, calc_outputs, findings)
    calc_outputs.extend(_build_added_load_sensitivity_outputs(case, controlling_path, calc_outputs))
    load_combination_sensitivities = _build_load_combination_sensitivities(case, controlling_path, calc_outputs)
    triggered_rules = _build_triggered_rules(findings)
    basis_references = _build_basis_references(findings)

    if any(finding.severity == "blocking" for finding in findings):
        return KernelOutcome(
            decision=KernelDecision(status="no_go", confidence="low"),
            controlling_path=controlling_path,
            load_combination_sensitivities=load_combination_sensitivities,
            assumption_ledger=assumption_ledger,
            evidence_snapshot=evidence_snapshot,
            calc_outputs=calc_outputs,
            triggered_rules=triggered_rules,
            basis_references=basis_references,
            reserve_screening=reserve_screening,
            attachment_screening=attachment_screening,
            verification_readiness=verification_readiness,
            uncertainty_assessment=uncertainty_assessment,
            member_reserve_uncertainties=member_reserve_uncertainties,
            attachment_pathways=attachment_pathways,
            review_triggers=review_triggers,
            engineering_checks=engineering_checks,
            recommended_actions=recommended_actions,
            resource_recommendations=resource_recommendations,
            findings=findings,
        )

    if any(finding.severity == "caution" for finding in findings):
        return KernelOutcome(
            decision=KernelDecision(status="conditional_go", confidence="medium"),
            controlling_path=controlling_path,
            load_combination_sensitivities=load_combination_sensitivities,
            assumption_ledger=assumption_ledger,
            evidence_snapshot=evidence_snapshot,
            calc_outputs=calc_outputs,
            triggered_rules=triggered_rules,
            basis_references=basis_references,
            reserve_screening=reserve_screening,
            attachment_screening=attachment_screening,
            verification_readiness=verification_readiness,
            uncertainty_assessment=uncertainty_assessment,
            member_reserve_uncertainties=member_reserve_uncertainties,
            attachment_pathways=attachment_pathways,
            review_triggers=review_triggers,
            engineering_checks=engineering_checks,
            recommended_actions=recommended_actions,
            resource_recommendations=resource_recommendations,
            findings=findings,
        )

    return KernelOutcome(
        decision=KernelDecision(status="go", confidence="high"),
        controlling_path=controlling_path,
        load_combination_sensitivities=load_combination_sensitivities,
        assumption_ledger=assumption_ledger,
        evidence_snapshot=evidence_snapshot,
        calc_outputs=calc_outputs,
        triggered_rules=triggered_rules,
        basis_references=basis_references,
        reserve_screening=reserve_screening,
        attachment_screening=attachment_screening,
        verification_readiness=verification_readiness,
        uncertainty_assessment=uncertainty_assessment,
        member_reserve_uncertainties=member_reserve_uncertainties,
        attachment_pathways=attachment_pathways,
        review_triggers=review_triggers,
        engineering_checks=engineering_checks,
        recommended_actions=recommended_actions,
        resource_recommendations=resource_recommendations,
        findings=[],
    )
