from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml

from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import KernelOutcome, evaluate_screening_case
from structural_screening_agent.models import (
    AttachmentPathway,
    BilingualItem,
    BuildingIntake,
    DecisionStatus,
    EngineeringCheck,
    ReserveUncertainty,
    ResourceRecommendation,
    ReviewTrigger,
    ScreeningAction,
    ScreeningOption,
    ScreeningResult,
    TraceabilityFinding,
    TraceabilityTrace,
    VerificationReadiness,
)
from structural_screening_agent.scenario_classifier import classify_scenario


def _rules_root() -> Path:
    return Path(__file__).resolve().parents[2] / "rules"


def _load_yaml(filename: str):
    return yaml.safe_load((_rules_root() / filename).read_text())


def _merge_status(current: DecisionStatus, candidate: DecisionStatus) -> DecisionStatus:
    if current == DecisionStatus.NO_GO or candidate == DecisionStatus.GO:
        return current
    if candidate == DecisionStatus.NO_GO:
        return DecisionStatus.NO_GO
    if candidate == DecisionStatus.CONDITIONAL_GO:
        return DecisionStatus.CONDITIONAL_GO
    return current


def _append_item(
    items: List[BilingualItem],
    title_en: str,
    title_zh: str,
    detail_en: Optional[str] = None,
    detail_zh: Optional[str] = None,
) -> None:
    if any(item.title_en == title_en for item in items):
        return
    items.append(BilingualItem(title_en=title_en, title_zh=title_zh, detail_en=detail_en, detail_zh=detail_zh))


def _append_action(
    actions: List[ScreeningAction],
    title_en: str,
    title_zh: str,
    phase: str,
    detail_en: Optional[str] = None,
    detail_zh: Optional[str] = None,
) -> None:
    if any(item.title_en == title_en for item in actions):
        return
    actions.append(
        ScreeningAction(
            title_en=title_en,
            title_zh=title_zh,
            phase=phase,
            detail_en=detail_en,
            detail_zh=detail_zh,
        )
    )


def _append_option(options: List[ScreeningOption], option: Dict[str, Any]) -> None:
    if any(item.title_en == option["title_en"] for item in options):
        return
    options.append(ScreeningOption(**option))


def _build_option_lookup(option_rules: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {option["id"]: option for option in option_rules}


def _apply_flat_risk_rules(
    intake: BuildingIntake,
    scenario_slug: str,
    risk_rules: Iterable[Dict[str, Any]],
    matched_risks: List[BilingualItem],
    recommended_actions: List[ScreeningAction],
    current_status: DecisionStatus,
) -> DecisionStatus:
    status = current_status
    for rule in risk_rules:
        if scenario_slug not in rule["applies_to"]:
            continue
        triggers = rule.get("triggers", {})
        if not triggers:
            continue
        drawing_states = triggers.get("drawing_availability", [intake.drawing_availability])
        shutdown_states = triggers.get("shutdown_constraint", [intake.shutdown_constraint])
        if intake.drawing_availability not in drawing_states:
            continue
        if intake.shutdown_constraint not in shutdown_states:
            continue
        _append_item(matched_risks, rule["title_en"], rule["title_zh"])
        _append_action(recommended_actions, rule["recommended_action_en"], rule["recommended_action_zh"], "must_do")
        status = _merge_status(status, DecisionStatus(rule["decision_impact"]))
    return status


def _collect_missing_data(intake: BuildingIntake) -> List[BilingualItem]:
    missing_data: List[BilingualItem] = []
    if intake.drawing_availability != "complete":
        _append_item(missing_data, "Original structural drawings", "原结构图纸")
    if not intake.survey_available:
        _append_item(missing_data, "Targeted site survey", "针对性现场调查")
    if intake.project_type != "rooftop_pv":
        return missing_data
    if not intake.roof_panel_type:
        _append_item(missing_data, "Roof panel system confirmation", "屋面板体系确认")
    if intake.roof_panel_type == "profiled_sheet":
        if intake.roof_panel_thickness_mm is None:
            _append_item(missing_data, "Roof panel thickness", "屋面板厚")
        if intake.roof_rib_height_mm is None:
            _append_item(missing_data, "Roof rib height", "屋面波高")
    if not intake.purlin_type:
        _append_item(missing_data, "Purlin type and spacing", "檩条形式与布置")
    return missing_data


def _apply_main_demo_bundles(
    intake: BuildingIntake,
    risk_rules: Iterable[Dict[str, Any]],
    matched_risks: List[BilingualItem],
    recommended_actions: List[ScreeningAction],
    missing_data: List[BilingualItem],
    current_status: DecisionStatus,
) -> DecisionStatus:
    if intake.project_type != "rooftop_pv":
        return current_status

    status = current_status
    risk_lookup = {rule["id"]: rule for rule in risk_rules}

    if intake.available_verification_path == "no_viable_path_yet":
        _append_item(
            matched_risks,
            "No defendable verification path is available for this project stage",
            "当前阶段缺少可辩护的复核路径",
            detail_en=(
                "Available verification path is marked as 'No Viable Path Yet' while drawings and survey access are still unresolved."
            ),
            detail_zh="当前可用复核路径为“暂无可行路径”，且图纸与现场调查条件仍未落实。",
        )
        _append_action(
            recommended_actions,
            "Pause progression and establish a defendable verification route",
            "暂停推进并先建立可辩护的复核路径",
            "must_do",
        )
        status = _merge_status(status, DecisionStatus.NO_GO)

    if intake.roof_panel_type == "profiled_sheet" and (
        intake.roof_panel_thickness_mm is None or intake.roof_rib_height_mm is None
    ):
        rule = risk_lookup["roof_attachment_uncertainty"]
        _append_item(
            matched_risks,
            rule["title_en"],
            rule["title_zh"],
            detail_en=(
                f"Profiled steel sheet has missing rib height ({intake.roof_rib_height_mm}) and roof panel thickness ({intake.roof_panel_thickness_mm}), so the attachment path cannot be screened credibly yet."
            ),
            detail_zh=(
                f"当前压型钢板的波高（{intake.roof_rib_height_mm}）和板厚（{intake.roof_panel_thickness_mm}）缺失，暂无法可信地筛查支架连接路径。"
            ),
        )
        _append_action(recommended_actions, rule["recommended_action_en"], rule["recommended_action_zh"], "must_do")
        status = _merge_status(status, DecisionStatus(rule["decision_impact"]))

    if intake.waterproofing_sensitivity == "high" and intake.roof_attachment_preference == "penetrating":
        rule = risk_lookup["waterproofing_constraint"]
        _append_item(
            matched_risks,
            rule["title_en"],
            rule["title_zh"],
            detail_en="Waterproofing sensitivity is high and the preferred attachment path is penetrating.",
            detail_zh="当前防水敏感性为高，且拟采用穿透式连接。",
        )
        _append_action(recommended_actions, rule["recommended_action_en"], rule["recommended_action_zh"], "must_do")
        status = _merge_status(status, DecisionStatus(rule["decision_impact"]))

    if (
        intake.estimated_added_load_kpa is not None
        and intake.estimated_added_load_kpa >= 0.15
        and intake.drawing_availability != "complete"
    ):
        _append_item(
            matched_risks,
            "Insufficient reserve capacity in roof members",
            "屋面构件承载储备不足",
            detail_en=(
                f"Added load is {intake.estimated_added_load_kpa:.2f} kPa while drawings remain {intake.drawing_availability}, so reserve capacity cannot be released directly."
            ),
            detail_zh=f"当前新增荷载为 {intake.estimated_added_load_kpa:.2f} kPa，且图纸状态为{intake.drawing_availability}，因此不能直接放行承载储备。",
        )
        _append_action(recommended_actions, "Perform targeted structural verification", "开展针对性结构复核", "must_do")
        status = _merge_status(status, DecisionStatus.CONDITIONAL_GO)

    if (
        intake.corrosion_condition in ("moderate", "high")
        and intake.drawing_availability != "complete"
        and "Targeted site survey" in {item.title_en for item in missing_data}
    ):
        _append_item(
            matched_risks,
            "Corrosion condition increases uncertainty in reserve-capacity screening",
            "腐蚀状况提高了承载储备筛查的不确定性",
            detail_en="Corrosion is rated moderate or high while documentation is incomplete and survey data is still missing.",
            detail_zh="当前腐蚀等级为中等或偏高，且资料不完整、现场调查尚未补齐。",
        )
        _append_action(
            recommended_actions,
            "Use survey findings to confirm corrosion severity before broad rollout",
            "在大范围铺设前结合现场调查确认腐蚀程度",
            "parallel",
        )
        status = _merge_status(status, DecisionStatus.CONDITIONAL_GO)

    if (
        intake.building_span_m is not None
        and intake.column_spacing_m is not None
        and intake.building_span_m >= 33.0
        and intake.column_spacing_m >= 8.5
        and intake.drawing_availability != "complete"
    ):
        rule = risk_lookup["long_span_uncertainty"]
        _append_item(
            matched_risks,
            rule["title_en"],
            rule["title_zh"],
            detail_en=(
                f"Span is {intake.building_span_m:.1f} m and column spacing is {intake.column_spacing_m:.1f} m under partial documentation."
            ),
            detail_zh=f"当前跨度为 {intake.building_span_m:.1f} m、柱距为 {intake.column_spacing_m:.1f} m，且资料仅为部分完整。",
        )
        _append_action(recommended_actions, rule["recommended_action_en"], rule["recommended_action_zh"], "parallel")
        status = _merge_status(status, DecisionStatus(rule["decision_impact"]))

    if intake.shutdown_constraint in ("limited", "strict") and not (intake.restricted_installation_zones or "").strip():
        rule = risk_lookup["no_zone_strategy"]
        _append_item(
            matched_risks,
            rule["title_en"],
            rule["title_zh"],
            detail_en=(
                f"Shutdown constraint is {intake.shutdown_constraint}, but no restricted installation zones have been defined yet."
            ),
            detail_zh=f"当前停工约束为 {intake.shutdown_constraint}，但尚未定义限制安装区域。",
        )
        _append_action(recommended_actions, rule["recommended_action_en"], rule["recommended_action_zh"], "parallel")
        status = _merge_status(status, DecisionStatus(rule["decision_impact"]))

    if status != DecisionStatus.NO_GO:
        _append_action(
            recommended_actions,
            "Re-rank full-roof rollout after the first verification package closes",
            "在首轮复核完成后重新排序整屋面推进范围",
            "later",
        )

    return status


def _build_options(
    intake: BuildingIntake,
    option_rules: Iterable[Dict[str, Any]],
    status: DecisionStatus,
) -> List[ScreeningOption]:
    option_lookup = _build_option_lookup(option_rules)
    options: List[ScreeningOption] = []

    if intake.project_type == "rooftop_pv":
        primary_rationale_en = None
        primary_rationale_zh = None
        if status == DecisionStatus.NO_GO or intake.available_verification_path == "no_viable_path_yet":
            preferred_order = ["pause_and_verify", "restricted_installation", "local_strengthening"]
            primary_rationale_en = (
                "No defendable verification route is available yet, so scheme selection should pause before committing to installation."
            )
            primary_rationale_zh = "当前尚无可辩护的复核路径，因此在承诺安装方案前应先暂停并完成复核。"
        elif intake.shutdown_constraint in ("limited", "strict") or intake.waterproofing_sensitivity == "high":
            preferred_order = ["restricted_installation", "local_strengthening", "pause_and_verify"]
            primary_rationale_en = (
                "Limited shutdown tolerance and/or high waterproofing sensitivity favor a phased restricted-zone path first."
            )
            primary_rationale_zh = "当前有限停工容忍度和/或高防水敏感性，更适合先走分阶段的限定区域安装路径。"
        else:
            preferred_order = ["local_strengthening", "restricted_installation", "pause_and_verify"]
            primary_rationale_en = "Broader coverage is currently achievable, so local strengthening can unlock wider installation first."
            primary_rationale_zh = "当前更有机会争取较大铺设范围，因此可优先考虑通过局部加固释放更广安装面。"

        for index, option_id in enumerate(preferred_order):
            option = option_lookup.get(option_id)
            if option:
                option_payload = dict(option)
                if index == 0:
                    option_payload["priority_rationale_en"] = primary_rationale_en
                    option_payload["priority_rationale_zh"] = primary_rationale_zh
                _append_option(options, option_payload)
        return options

    scenario = classify_scenario(intake)
    for option in option_rules:
        if scenario.slug in option["applies_to"]:
            _append_option(options, option)
    return options


def _build_review_required(intake: BuildingIntake) -> List[BilingualItem]:
    review_required: List[BilingualItem] = []
    if intake.design_standard_context == "gb":
        _append_item(
            review_required,
            "Continue steel member and connection review under GB 50017 and local roof attachment detailing.",
            "后续应按 GB 50017 及屋面连接做法进入钢结构与连接复核。",
        )
    elif intake.design_standard_context == "aisc":
        _append_item(
            review_required,
            "Continue member stability, steel design, and connection review under AISC 360.",
            "后续应按 AISC 360 进入构件稳定、钢结构与连接复核。",
        )
    else:
        _append_item(
            review_required,
            "Continue steel member and connection review under Eurocode 3 and local execution rules.",
            "后续应按 Eurocode 3 及本地实施细则进入钢结构与连接复核。",
        )
    return review_required


def _build_verification_readiness(
    intake: BuildingIntake,
    status: DecisionStatus,
    missing_data: List[BilingualItem],
) -> VerificationReadiness:
    blockers: List[BilingualItem] = []
    blocker_titles = {item.title_en for item in missing_data}

    if intake.available_verification_path == "no_viable_path_yet":
        blockers.append(
            BilingualItem(
                title_en="No defendable verification route has been established yet",
                title_zh="当前尚未建立可辩护的复核路径",
            )
        )
    if intake.drawing_availability == "missing":
        blockers.append(BilingualItem(title_en="Original structural drawings are still missing", title_zh="原结构图纸仍然缺失"))
    if not intake.survey_available:
        blockers.append(BilingualItem(title_en="Targeted site survey has not been completed", title_zh="针对性现场调查尚未完成"))
    if intake.project_type == "rooftop_pv" and intake.roof_panel_type == "profiled_sheet":
        if intake.roof_panel_thickness_mm is None:
            blockers.append(BilingualItem(title_en="Roof panel thickness is still unconfirmed", title_zh="屋面板厚仍未确认"))
        if intake.roof_rib_height_mm is None:
            blockers.append(BilingualItem(title_en="Roof rib height is still unconfirmed", title_zh="屋面波高仍未确认"))
    if intake.project_type == "rooftop_pv" and intake.existing_member_schedule_status != "available":
        blockers.append(
            BilingualItem(
                title_en="Existing member schedule / section schedule is incomplete",
                title_zh="既有构件表/截面表尚不完整",
            )
        )
    if intake.project_type == "rooftop_pv" and intake.connection_detail_status != "available":
        blockers.append(
            BilingualItem(
                title_en="Connection detail record is incomplete",
                title_zh="节点连接做法资料尚不完整",
            )
        )
    if intake.project_type == "rooftop_pv" and intake.roof_vendor_data_status != "available":
        blockers.append(
            BilingualItem(
                title_en="Roof vendor data is incomplete",
                title_zh="屋面系统厂家资料尚不完整",
            )
        )

    if intake.available_verification_path == "no_viable_path_yet" or (
        intake.drawing_availability == "missing" and not intake.survey_available
    ):
        return VerificationReadiness(
            level="not_ready",
            summary_en="Not ready for a defendable structural review yet. The team should close basic access and evidence gaps first.",
            summary_zh="当前尚不具备开展可辩护结构复核的条件，应先补齐基础准入条件和证据链。",
            blockers=blockers,
        )

    if (
        status == DecisionStatus.CONDITIONAL_GO
        or intake.drawing_availability != "complete"
        or blocker_titles
        or intake.available_verification_path in ("drawings_only", "survey_only")
    ):
        return VerificationReadiness(
            level="partial",
            summary_en="Partially ready for structural review. A targeted verification package can start, but key gaps still need to be closed.",
            summary_zh="当前部分具备进入结构复核的条件，可以启动针对性复核包，但仍需先补齐若干关键缺口。",
            blockers=blockers,
        )

    return VerificationReadiness(
        level="ready",
        summary_en="Ready to proceed into targeted structural review under the selected standards context.",
        summary_zh="当前已具备进入所选规范体系下针对性结构复核的基础条件。",
        blockers=blockers,
    )


def _build_engineering_checks(intake: BuildingIntake, status: DecisionStatus) -> List[EngineeringCheck]:
    checks: List[EngineeringCheck] = []

    reserve_status = "review"
    reserve_summary_en = (
        "Current reserve-capacity screening still needs targeted structural review because the added load, as-built evidence, or governing framing checks are not fully closed."
    )
    reserve_summary_zh = "当前承载储备筛查仍需进入针对性结构复核，因为新增荷载、既有证据链或控制构件检查尚未闭合。"

    if intake.available_verification_path == "no_viable_path_yet":
        reserve_status = "undetermined"
        reserve_summary_en = "Reserve capacity cannot be screened credibly yet because no defendable verification route has been established."
        reserve_summary_zh = "当前尚无可辩护复核路径，因此承载储备暂无法进行可信筛查。"
    elif (
        intake.estimated_added_load_kpa is not None
        and intake.estimated_added_load_kpa <= 0.12
        and intake.drawing_availability == "complete"
        and intake.survey_available
        and intake.corrosion_condition == "low"
        and intake.available_verification_path == "drawings_plus_survey"
    ):
        reserve_status = "screen_pass"
        reserve_summary_en = "The current inputs support a favorable first-pass reserve-capacity screen, but formal design checks are still required before commitment."
        reserve_summary_zh = "当前输入条件支持承载储备的一轮初步放行判断，但在承诺实施前仍需完成正式设计复核。"

    checks.append(
        EngineeringCheck(
            title_en="Reserve Capacity Screening",
            title_zh="承载储备筛查",
            status=reserve_status,
            summary_en=reserve_summary_en,
            summary_zh=reserve_summary_zh,
        )
    )

    connection_status = "review"
    connection_summary_en = "Attachment feasibility still needs targeted connection review before system selection can be treated as defendable."
    connection_summary_zh = "在把连接方案视为可辩护之前，当前连接可行性仍需进入针对性连接复核。"

    if intake.project_type != "rooftop_pv":
        connection_status = "review"
        connection_summary_en = "Connection feasibility is scenario-dependent and should be reviewed in the next-stage engineering package."
        connection_summary_zh = "连接可行性依赖具体改造场景，应在下一阶段工程包中继续复核。"
    elif intake.available_verification_path == "no_viable_path_yet":
        connection_status = "undetermined"
        connection_summary_en = "Attachment feasibility cannot be judged yet because no defendable review route is available."
        connection_summary_zh = "当前尚无可辩护复核路径，因此连接可行性暂不可判定。"
    elif intake.roof_panel_type == "profiled_sheet" and (
        intake.roof_panel_thickness_mm is None or intake.roof_rib_height_mm is None
    ):
        connection_status = "undetermined"
        connection_summary_en = "Attachment feasibility remains undetermined because panel thickness and/or rib height are still missing."
        connection_summary_zh = "由于板厚和/或波高仍缺失，当前连接可行性仍不可判定。"
    elif intake.waterproofing_sensitivity == "high" and intake.roof_attachment_preference == "penetrating":
        connection_status = "review"
        connection_summary_en = "Penetrating attachment under high waterproofing sensitivity should be escalated to a targeted connection and waterproofing review."
        connection_summary_zh = "高防水敏感条件下采用穿透式连接，应升级为针对性连接与防水复核。"
    elif intake.roof_attachment_preference == "clamp_based" and intake.available_verification_path in (
        "drawings_plus_survey",
        "drawings_only",
    ):
        connection_status = "screen_pass"
        connection_summary_en = "A clamp-based attachment path is preliminarily screenable under the current roof system inputs, subject to formal detailing review."
        connection_summary_zh = "在当前屋面体系输入下，夹持式连接路径可做初步筛查放行，但仍需进入正式构造复核。"

    checks.append(
        EngineeringCheck(
            title_en="Attachment Feasibility Screening",
            title_zh="连接可行性筛查",
            status=connection_status,
            summary_en=connection_summary_en,
            summary_zh=connection_summary_zh,
        )
    )

    return checks


def _append_reserve_uncertainty(
    items: List[ReserveUncertainty],
    title_en: str,
    title_zh: str,
    severity: str,
    summary_en: str,
    summary_zh: str,
) -> None:
    if any(item.title_en == title_en for item in items):
        return
    items.append(
        ReserveUncertainty(
            title_en=title_en,
            title_zh=title_zh,
            severity=severity,
            summary_en=summary_en,
            summary_zh=summary_zh,
        )
    )


def _build_member_reserve_uncertainties(intake: BuildingIntake) -> List[ReserveUncertainty]:
    items: List[ReserveUncertainty] = []

    added_load = intake.estimated_added_load_kpa or 0.0
    load_severity = "high" if added_load >= 0.18 else ("medium" if added_load >= 0.12 else "low")
    _append_reserve_uncertainty(
        items,
        "Member Reserve Uncertainty: Load Demand",
        "构件承载储备不确定性：新增荷载需求",
        load_severity,
        (
            f"Added load is currently {added_load:.2f} kPa, which keeps the demand-side uncertainty elevated until governing member checks are closed."
            if load_severity != "low"
            else f"Added load is currently {added_load:.2f} kPa, so demand-side uncertainty is comparatively limited at screening level."
        ),
        (
            f"当前新增荷载为 {added_load:.2f} kPa，在控制构件复核闭合前，需求侧不确定性仍然偏高。"
            if load_severity != "low"
            else f"当前新增荷载为 {added_load:.2f} kPa，因此在筛查层面需求侧不确定性相对可控。"
        ),
    )

    evidence_severity = "low"
    if intake.drawing_availability == "missing" or intake.existing_member_schedule_status == "missing":
        evidence_severity = "high"
    elif intake.drawing_availability != "complete" or intake.existing_member_schedule_status != "available":
        evidence_severity = "medium"
    _append_reserve_uncertainty(
        items,
        "Member Reserve Uncertainty: Evidence Completeness",
        "构件承载储备不确定性：证据链完整度",
        evidence_severity,
        (
            "Drawings and member schedules are sufficiently complete for a first-pass member reserve screen."
            if evidence_severity == "low"
            else "Drawings and/or member schedules remain incomplete, so reserve-capacity screening still rests on a partial evidence chain."
        ),
        (
            "图纸和构件表已基本完整，可支持一轮构件承载储备初筛。"
            if evidence_severity == "low"
            else "当前图纸和/或构件表仍不完整，因此承载储备筛查仍建立在部分证据链之上。"
        ),
    )

    span = intake.building_span_m or 0.0
    spacing = intake.column_spacing_m or 0.0
    framing_severity = "high" if span >= 33.0 or spacing >= 8.5 else ("medium" if span >= 27.0 or spacing >= 8.0 else "low")
    _append_reserve_uncertainty(
        items,
        "Member Reserve Uncertainty: Framing Module",
        "构件承载储备不确定性：框架模块",
        framing_severity,
        (
            f"Span {span:.1f} m and column spacing {spacing:.1f} m place the framing module in a range that should be treated as a governing uncertainty driver."
            if framing_severity != "low"
            else f"Span {span:.1f} m and column spacing {spacing:.1f} m keep the framing module within a relatively manageable screening range."
        ),
        (
            f"当前跨度 {span:.1f} m、柱距 {spacing:.1f} m，使框架模块进入应重点关注的不确定性区间。"
            if framing_severity != "low"
            else f"当前跨度 {span:.1f} m、柱距 {spacing:.1f} m，使框架模块仍处于相对可控的筛查区间。"
        ),
    )

    condition_severity = "high" if intake.corrosion_condition == "high" else "low"
    if condition_severity != "high" and (intake.corrosion_condition == "moderate" or not intake.survey_available):
        condition_severity = "medium"
    _append_reserve_uncertainty(
        items,
        "Member Reserve Uncertainty: Condition State",
        "构件承载储备不确定性：现状条件",
        condition_severity,
        (
            "Corrosion exposure and current-survey evidence still leave the as-is condition state uncertain for reserve screening."
            if condition_severity != "low"
            else "Observed condition inputs are comparatively stable for screening-level reserve judgement."
        ),
        (
            "当前腐蚀暴露与现场调查证据仍使既有状态对承载储备筛查构成不确定性。"
            if condition_severity != "low"
            else "当前现状条件输入相对稳定，可支持筛查层面的承载储备判断。"
        ),
    )

    return items


def _append_attachment_pathway(
    items: List[AttachmentPathway],
    title_en: str,
    title_zh: str,
    status: str,
    summary_en: str,
    summary_zh: str,
) -> None:
    if any(item.title_en == title_en for item in items):
        return
    items.append(
        AttachmentPathway(
            title_en=title_en,
            title_zh=title_zh,
            status=status,
            summary_en=summary_en,
            summary_zh=summary_zh,
        )
    )


def _build_attachment_pathways(intake: BuildingIntake) -> List[AttachmentPathway]:
    items: List[AttachmentPathway] = []

    if intake.project_type != "rooftop_pv":
        _append_attachment_pathway(
            items,
            "Attachment Pathway: Scenario-Specific Connection Route",
            "连接路径：场景相关连接路径",
            "review",
            "Attachment pathways in this scenario should be resolved in the next-stage engineering package.",
            "当前场景下的连接路径应在下一阶段工程包中继续明确。",
        )
        return items

    clamp_status = "review"
    clamp_summary_en = "Clamp-based attachment is a plausible first route, but it still needs roof geometry and detailing confirmation."
    clamp_summary_zh = "夹持式连接是一个可优先考虑的路径，但仍需补齐屋面几何与构造确认。"
    if intake.available_verification_path == "no_viable_path_yet":
        clamp_status = "undetermined"
        clamp_summary_en = "No defendable review route exists yet, so a clamp-based pathway cannot be screened credibly."
        clamp_summary_zh = "当前尚无可辩护复核路径，因此夹持式连接路径暂无法可信筛查。"
    elif intake.roof_panel_type == "profiled_sheet" and (
        intake.roof_panel_thickness_mm is None or intake.roof_rib_height_mm is None
    ):
        clamp_status = "undetermined"
        clamp_summary_en = "Clamp-based attachment remains undetermined because roof panel thickness and/or rib height are still missing."
        clamp_summary_zh = "由于屋面板厚和/或波高仍缺失，夹持式连接路径当前仍不可判定。"
    elif (
        intake.roof_attachment_preference == "clamp_based"
        and intake.available_verification_path == "drawings_plus_survey"
        and intake.connection_detail_status == "available"
    ):
        clamp_status = "screen_pass"
        clamp_summary_en = "Clamp-based attachment is the current best-screened route and can proceed into formal detailing review."
        clamp_summary_zh = "夹持式连接是当前证据链最完整的路径，可进入正式构造复核。"
    _append_attachment_pathway(
        items,
        "Attachment Pathway: Clamp-Based Roof Connection",
        "连接路径：夹持式屋面连接",
        clamp_status,
        clamp_summary_en,
        clamp_summary_zh,
    )

    penetrating_status = "review"
    penetrating_summary_en = "Penetrating attachment remains possible but should be escalated through targeted connection and waterproofing review."
    penetrating_summary_zh = "穿透式连接并非不可选，但应先进入针对性的连接与防水复核。"
    if intake.available_verification_path == "no_viable_path_yet":
        penetrating_status = "undetermined"
        penetrating_summary_en = "Penetrating attachment cannot be screened responsibly until a defendable review route is established."
        penetrating_summary_zh = "在建立可辩护复核路径前，穿透式连接无法负责任地进行筛查。"
    elif intake.waterproofing_sensitivity == "high":
        penetrating_status = "review"
        penetrating_summary_en = "High waterproofing sensitivity keeps penetrating attachment in a review-required state even if the route remains technically possible."
        penetrating_summary_zh = "高防水敏感性使穿透式连接即便技术上可行，也应保持在需复核状态。"
    elif (
        intake.roof_attachment_preference == "penetrating"
        and intake.connection_detail_status == "available"
        and intake.available_verification_path == "drawings_plus_survey"
    ):
        penetrating_status = "screen_pass"
        penetrating_summary_en = "Penetrating attachment can be screened forward under the current evidence set, subject to formal detailing review."
        penetrating_summary_zh = "在当前证据链下，穿透式连接可进入下一步筛查放行，但仍需正式构造复核。"
    _append_attachment_pathway(
        items,
        "Attachment Pathway: Penetrating Roof Connection",
        "连接路径：穿透式屋面连接",
        penetrating_status,
        penetrating_summary_en,
        penetrating_summary_zh,
    )

    vendor_status = "review"
    vendor_summary_en = "A vendor-confirmed roof-system route remains worth reviewing if supplier data can anchor the attachment pathway."
    vendor_summary_zh = "如果厂家资料能够锚定连接做法，则厂家确认路径仍值得继续复核。"
    if intake.available_verification_path == "no_viable_path_yet":
        vendor_status = "undetermined"
        vendor_summary_en = "Without a defendable review route, a vendor-confirmed pathway cannot be established yet."
        vendor_summary_zh = "在缺少可辩护复核路径时，当前无法建立厂家确认路径。"
    elif intake.roof_vendor_data_status == "missing":
        vendor_status = "undetermined"
        vendor_summary_en = "Roof-system vendor data is still missing, so a vendor-confirmed pathway is currently undetermined."
        vendor_summary_zh = "当前屋面系统厂家资料仍缺失，因此厂家确认路径暂不可判定。"
    elif intake.roof_vendor_data_status == "available" and intake.available_verification_path == "drawings_plus_survey":
        vendor_status = "screen_pass"
        vendor_summary_en = "Vendor data is available and can support a more defendable roof-system-specific pathway."
        vendor_summary_zh = "厂家资料已具备，可支撑更可辩护的屋面系统专项路径。"
    _append_attachment_pathway(
        items,
        "Attachment Pathway: Vendor-Confirmed Roof-System Route",
        "连接路径：厂家确认的屋面系统路径",
        vendor_status,
        vendor_summary_en,
        vendor_summary_zh,
    )

    defendability_status = "review"
    defendability_summary_en = "A defendable attachment route is forming, but one or more evidence gaps still need to close before scheme commitment."
    defendability_summary_zh = "当前正在形成可辩护的连接路径，但在承诺方案前仍需补齐若干证据缺口。"
    if intake.available_verification_path == "no_viable_path_yet" or (
        intake.roof_panel_type == "profiled_sheet"
        and (intake.roof_panel_thickness_mm is None or intake.roof_rib_height_mm is None)
    ):
        defendability_status = "undetermined"
        defendability_summary_en = "The current evidence set does not yet support a defendable attachment route."
        defendability_summary_zh = "当前证据链尚不足以支撑一条可辩护的连接路径。"
    elif intake.available_verification_path == "drawings_plus_survey" and (
        clamp_status == "screen_pass" or vendor_status == "screen_pass"
    ):
        defendability_status = "screen_pass"
        defendability_summary_en = "The current evidence set supports a defendable attachment route for the next-stage design review."
        defendability_summary_zh = "当前证据链已可支撑进入下一阶段设计复核的可辩护连接路径。"
    _append_attachment_pathway(
        items,
        "Attachment Pathway: Current Defendability",
        "连接路径：当前可辩护性",
        defendability_status,
        defendability_summary_en,
        defendability_summary_zh,
    )

    return items


def _append_resource_recommendation(
    items: List[ResourceRecommendation],
    title_en: str,
    title_zh: str,
    summary_en: str,
    summary_zh: str,
) -> None:
    if any(item.title_en == title_en for item in items):
        return
    items.append(
        ResourceRecommendation(
            title_en=title_en,
            title_zh=title_zh,
            summary_en=summary_en,
            summary_zh=summary_zh,
        )
    )


def _build_resource_recommendations(
    intake: BuildingIntake,
    engineering_checks: List[EngineeringCheck],
    review_triggers: List[ReviewTrigger],
    attachment_pathways: List[AttachmentPathway],
) -> List[ResourceRecommendation]:
    items: List[ResourceRecommendation] = []

    member_triggered = any(item.category == "member" for item in review_triggers)
    reserve_check = next((item for item in engineering_checks if item.title_en == "Reserve Capacity Screening"), None)
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

    if not intake.survey_available or intake.corrosion_condition in ("moderate", "high", "unknown"):
        _append_resource_recommendation(
            items,
            "Targeted Site Survey and Roof Inspection",
            "现场调查与屋面检查",
            "Use a targeted site survey and roof inspection team to confirm the as-is condition, corrosion state, and field access assumptions.",
            "建议配置针对性现场调查与屋面检查资源，用于确认既有状态、腐蚀等级和现场进入条件。",
        )

    if (
        intake.drawing_availability != "complete"
        or intake.existing_member_schedule_status != "available"
        or intake.connection_detail_status != "available"
    ):
        _append_resource_recommendation(
            items,
            "As-Built Document Recovery Support",
            "既有资料补齐支持",
            "Coordinate drawing recovery and as-built document collation so the next review package does not rely on fragmented evidence.",
            "建议配置既有图纸与资料补齐支持，避免下一轮复核继续依赖碎片化证据链。",
        )

    return items


def _append_review_trigger(
    triggers: List[ReviewTrigger],
    category: str,
    title_en: str,
    title_zh: str,
    summary_en: str,
    summary_zh: str,
) -> None:
    if any(item.title_en == title_en for item in triggers):
        return
    triggers.append(
        ReviewTrigger(
            category=category,
            title_en=title_en,
            title_zh=title_zh,
            summary_en=summary_en,
            summary_zh=summary_zh,
        )
    )


def _build_review_triggers(intake: BuildingIntake) -> List[ReviewTrigger]:
    triggers: List[ReviewTrigger] = []

    if (
        intake.estimated_added_load_kpa is not None
        and intake.estimated_added_load_kpa >= 0.15
        and intake.drawing_availability != "complete"
    ):
        _append_review_trigger(
            triggers,
            "member",
            "Member Review Trigger: added load and incomplete framing evidence",
            "构件复核触发项：新增荷载与构件证据链不完整",
            "Added load is already material while drawings / member schedules remain incomplete, so member-level reserve review should be escalated.",
            "当前新增荷载已经具有影响，且图纸/构件表证据链仍不完整，因此应升级进入构件层面的承载复核。",
        )

    if intake.building_span_m is not None and intake.column_spacing_m is not None and intake.building_span_m >= 33.0 and intake.column_spacing_m >= 8.5:
        _append_review_trigger(
            triggers,
            "member",
            "Member Review Trigger: long-span framing module",
            "构件复核触发项：大跨度框架模块",
            "The framing module is already in a longer-span range, so formal member review should confirm the governing members and reserve path.",
            "当前框架模块已进入较大跨度范围，因此应通过正式构件复核确认控制构件与承载储备路径。",
        )

    if intake.roof_panel_type == "profiled_sheet" and (
        intake.roof_panel_thickness_mm is None or intake.roof_rib_height_mm is None
    ):
        _append_review_trigger(
            triggers,
            "connection",
            "Connection Review Trigger: missing panel thickness / rib height",
            "连接复核触发项：板厚 / 波高缺失",
            "Panel thickness and/or rib height are still missing, so the attachment pathway cannot enter a defendable connection review package yet.",
            "当前板厚和/或波高仍缺失，因此连接路径尚不能进入可辩护的连接复核包。",
        )

    if intake.connection_detail_status != "available" or intake.roof_vendor_data_status != "available":
        _append_review_trigger(
            triggers,
            "connection",
            "Connection Review Trigger: incomplete connection detail or vendor data",
            "连接复核触发项：连接做法或厂家资料不完整",
            "Connection detailing records and/or roof vendor data remain incomplete, so connection and roof detailing review should continue.",
            "当前节点做法资料和/或屋面厂家资料仍不完整，因此应继续开展连接与屋面构造复核。",
        )

    if intake.waterproofing_sensitivity == "high" and intake.roof_attachment_preference == "penetrating":
        _append_review_trigger(
            triggers,
            "connection",
            "Connection Review Trigger: penetrating attachment under high waterproofing sensitivity",
            "连接复核触发项：高防水敏感下的穿透式连接",
            "A penetrating attachment path under high waterproofing sensitivity should be escalated to a dedicated connection and waterproofing review.",
            "在高防水敏感条件下采用穿透式连接，应升级为专项连接与防水复核。",
        )

    return triggers


def _build_traceability(kernel_outcome: KernelOutcome) -> List[TraceabilityFinding]:
    return [
        TraceabilityFinding(
            finding_id=finding.finding_id,
            severity=finding.severity,
            summary_en=finding.summary_en,
            summary_zh=finding.summary_zh,
            basis_ids=list(finding.basis_ids),
            traces=[
                TraceabilityTrace(
                    input_path=trace.input_path,
                    observed_value=trace.observed_value,
                )
                for trace in finding.traces
            ],
        )
        for finding in kernel_outcome.findings
    ]


def evaluate_screening(intake: BuildingIntake) -> ScreeningResult:
    kernel_case = from_building_intake(intake)
    kernel_outcome = evaluate_screening_case(kernel_case)
    scenario = classify_scenario(intake)
    risk_rules = _load_yaml("risks.yaml")
    option_rules = _load_yaml("options.yaml")

    matched_risks: List[BilingualItem] = []
    recommended_actions: List[ScreeningAction] = []
    status = DecisionStatus(kernel_outcome.decision.status)
    status = _apply_flat_risk_rules(
        intake=intake,
        scenario_slug=scenario.slug,
        risk_rules=risk_rules,
        matched_risks=matched_risks,
        recommended_actions=recommended_actions,
        current_status=status,
    )
    missing_data = _collect_missing_data(intake)
    status = _apply_main_demo_bundles(
        intake=intake,
        risk_rules=risk_rules,
        matched_risks=matched_risks,
        recommended_actions=recommended_actions,
        missing_data=missing_data,
        current_status=status,
    )
    options = _build_options(intake, option_rules, status)
    review_required = _build_review_required(intake)
    verification_readiness = _build_verification_readiness(intake, status, missing_data)
    engineering_checks = _build_engineering_checks(intake, status)
    member_reserve_uncertainties = _build_member_reserve_uncertainties(intake)
    attachment_pathways = _build_attachment_pathways(intake)
    review_triggers = _build_review_triggers(intake)
    resource_recommendations = _build_resource_recommendations(
        intake,
        engineering_checks,
        review_triggers,
        attachment_pathways,
    )
    traceability = _build_traceability(kernel_outcome)

    confidence = kernel_outcome.decision.confidence
    if status == DecisionStatus.NO_GO:
        confidence = "low"
    elif matched_risks or len(missing_data) >= 2 or traceability:
        confidence = "medium"

    return ScreeningResult(
        status=status,
        confidence=confidence,
        risks=matched_risks,
        missing_data=missing_data,
        recommended_actions=recommended_actions,
        review_required=review_required,
        options=options,
        verification_readiness=verification_readiness,
        engineering_checks=engineering_checks,
        member_reserve_uncertainties=member_reserve_uncertainties,
        attachment_pathways=attachment_pathways,
        resource_recommendations=resource_recommendations,
        review_triggers=review_triggers,
        traceability=traceability,
    )
