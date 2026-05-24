from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components
from pydantic import ValidationError

from structural_screening_agent.app_state import (
    default_package_options,
    demo_case_catalog,
    demo_case_options,
    evaluate_case,
    ordered_demo_keys,
)
from structural_screening_agent.bv_review.ui_state import (
    BV_DESIGN_STAGE_LABELS,
    BV_DOCUMENT_LABELS,
    BV_DOCUMENT_STATUS_LABELS,
    BV_PROJECT_TYPE_LABELS,
    BV_REVIEW_OBJECT_LABELS,
    BV_STANDARD_LABELS,
    build_agent_application_authorization_rows,
    build_agent_engineer_review_decision_rows,
    build_agent_workflow_artifact_rows,
    build_agent_engineer_review_queue_rows,
    build_agent_workflow_event_rows,
    build_agent_workflow_phase_rows,
    build_blocked_calculation_review_draft_rows,
    build_calculation_result_summary_rows,
    build_closed_rfi_incremental_recheck_rows,
    build_evidence_matrix_rows,
    build_extracted_fields_from_human_gate_rows,
    build_bv_review_intake,
    build_field_diff_summary_rows,
    build_ground_fixed_human_gate_rows,
    build_incremental_recheck_summary_rows,
    build_persisted_workflow_run_summary_rows,
    build_project_review_state_summary_rows,
    build_project_timeline_rows,
    build_quality_gate_status_rows,
    build_report_gate_evidence_rows,
    build_report_revision_history_rows,
    default_bv_review_intake,
)
from structural_screening_agent.bv_review.field_diff import (
    build_incremental_recheck_plan,
    diff_extracted_fields,
)
from structural_screening_agent.bv_review.calculation_engines import (
    build_foundation_calculation_run_from_fields,
    build_superstructure_calculation_run_from_fields,
)
from structural_screening_agent.bv_review.human_gate import (
    build_engineer_approval,
    build_report_draft_gate_result,
    record_report_revision,
)
from structural_screening_agent.bv_review.persisted_workflow_session import (
    close_persisted_rfi_after_engineer_review,
    clear_persisted_workflow_session,
    get_active_persisted_project_id,
    get_active_persisted_workflow_state,
    get_active_persisted_workflow_summary,
    apply_persisted_authorized_agent_response,
    issue_persisted_blocked_calculation_draft_rfi,
    record_persisted_agent_review_decision,
    record_persisted_report_revision,
    record_persisted_rfi_client_response,
    run_persisted_rfi_incremental_calculation_recheck,
    store_persisted_workflow_state,
    store_persisted_workflow_result,
)
from structural_screening_agent.bv_review.project_state import ProjectReviewState, RFIItem
from structural_screening_agent.bv_review.project_management import (
    build_finding_lifecycle_summary,
    build_finding_lifecycle_summary_rows,
    build_project_management_actions,
    build_responsible_party_status_rows,
)
from structural_screening_agent.bv_review.ui import (
    build_bv_project_management_dashboard_view,
    build_bv_report_revision_history_view,
)
from structural_screening_agent.bv_review.agent_application import (
    AgentResponseApplicationPacket,
    apply_authorized_agent_response_to_state,
    build_agent_response_application_packet,
    is_agent_response_application_packet_current,
)
from structural_screening_agent.bv_review.agent_prompting import (
    AgentResponseApplicationAuthorization,
    build_agent_provider_invocation_request,
    build_agent_provider_invocation_rows,
    build_agent_response_application_plan,
    build_agent_response_application_plan_rows,
    build_agent_response_engineer_handoff,
    build_agent_response_engineer_handoff_rows,
    build_agent_prompt_package_rows,
    build_agent_prompt_packages,
    build_agent_response_impact_rows,
    build_agent_response_sandbox_result,
    build_agent_response_sandbox_rows,
    build_sample_agent_response_json,
    default_agent_provider_model,
)
from structural_screening_agent.bv_review.report import (
    build_bv_markdown_report,
    build_bv_report_filename,
    build_bv_report_preview,
)
from structural_screening_agent.bv_review.service_scope import (
    build_service_scope_display_rows,
    build_service_scope_recommendations,
)
from structural_screening_agent.bv_review.ui import (
    build_bv_basis_items,
    build_bv_evidence_table_text,
    build_bv_gate_panel_text,
    build_foundation_evidence_display_rows,
    build_bv_path_items,
    build_bv_plan_items,
    build_bv_report_preview_sections,
    build_bv_risk_items,
    format_bv_label,
    render_bv_report_gate_status,
    render_bv_section,
)
from structural_screening_agent.bv_review import (
    JsonProjectReviewStateRepository,
    resume_local_agent_workflow_after_review_decisions,
    run_local_agent_workflow_until_blocked,
    run_persisted_local_agent_workflow_with_summary,
)
from structural_screening_agent.bv_review.workflow import (
    build_bv_review_result_from_project_state,
    evaluate_bv_review,
)
from structural_screening_agent.core.persistence import ScreeningRepository
from structural_screening_agent.localization import (
    Language,
    canonicalize_preset_text,
    language_label,
    localize_preset_text,
    translate,
    translate_option,
)
from structural_screening_agent.photo_assist import build_photo_assist_interface
from structural_screening_agent.presentation import ContentCard, build_workbench_view
from structural_screening_agent.pv_3d_studio import build_pv_3d_studio_html
from structural_screening_agent.report_export import build_docx_report_bytes, build_pdf_report_bytes
from structural_screening_agent.report_generator import build_report_filename, build_report_preview


st.set_page_config(page_title="BV PV Design Review Workbench", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: #f5f7fa;
        color: #15202b;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1220px;
    }
    [data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #dde5ec;
    }
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dde5ec;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    [data-testid="stTabs"] button[role="tab"] {
        border-radius: 8px;
        border: 1px solid #dde5ec;
        background: #ffffff;
        padding: 0.5rem 0.9rem;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #0b63ce;
        border-color: #b7d0ee;
        box-shadow: inset 0 0 0 1px rgba(11, 99, 206, 0.08);
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 8px;
        border-color: #dde5ec;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
        background: #ffffff;
    }
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stMarkdownContainer"] h4 {
        letter-spacing: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

repository = ScreeningRepository(Path(".local_data") / "screening.db")
demo_cases = demo_case_options()
default_packages = default_package_options()

if "ui_language" not in st.session_state:
    st.session_state.ui_language = "zh"

current_language_label: Language = st.session_state.get("ui_language", "zh")
ui_language: Language = st.sidebar.selectbox(
    translate(current_language_label, "language"),
    ["zh", "en"],
    format_func=lambda value: language_label(current_language_label, value),
    key="ui_language",
)

demo_catalog = demo_case_catalog(ui_language)
selected_demo_key = ordered_demo_keys()[0]
defaults = deepcopy(demo_cases[selected_demo_key].model_dump())
selected_demo = demo_catalog[selected_demo_key]
CUSTOM_INPUT_OPTION = "__custom__"
STEEL_GRADE_PRESETS = ["Q235", "Q355", "A36", "A572 Gr50", "S275", "S355"]
RAFTER_SECTION_PRESETS = [
    "310x150x8x12 welded rafter",
    "300x150x6x10 welded rafter",
    "250x125x6x8 welded rafter",
]
COLUMN_SECTION_PRESETS = [
    "305x305x10x15 welded column",
    "300x200x8x12 welded column",
    "250x250x9x14 welded column",
]


def _split_calc_detail(detail: str) -> tuple[str, str, Optional[str]]:
    lines = detail.splitlines()
    main_line = lines[0] if lines else detail
    formula_line = "\n".join(lines[1:]).strip() or None
    if " | " in main_line:
        value, summary = main_line.split(" | ", 1)
        return value.strip(), summary.strip(), formula_line
    return main_line.strip(), "", formula_line


def _render_card(card: ContentCard) -> None:
    with st.container(border=True):
        st.markdown(f"**{card.title}**")
        if card.detail:
            st.write(card.detail)


def _render_cards(cards: list[ContentCard], limit: Optional[int] = None) -> None:
    items = cards if limit is None else cards[:limit]
    for card in items:
        _render_card(card)


def _render_key_calculation_cards(cards: list[ContentCard], language: Language, limit: Optional[int] = None) -> None:
    items = cards if limit is None else cards[:limit]
    for card in items:
        value_text, summary_text, formula_text = _split_calc_detail(card.detail)
        with st.container(border=True):
            st.markdown(f"**{card.title}**")
            st.markdown(f"### {value_text}")
            if summary_text:
                st.caption(summary_text)
            if formula_text:
                with st.expander("计算式" if language == "zh" else "Formula"):
                    for line in formula_text.splitlines():
                        st.write(line)


def _preset_or_custom_value(
    *,
    preset_label: str,
    text_label: str,
    options: list[str],
    current_value: Optional[str],
    widget_prefix: str,
) -> str:
    initial_value = current_value or ""
    select_options = [*options, CUSTOM_INPUT_OPTION]
    default_value = initial_value if initial_value in options else CUSTOM_INPUT_OPTION
    selected_value = st.selectbox(
        preset_label,
        select_options,
        index=select_options.index(default_value),
        format_func=lambda value: translate(ui_language, "custom_input") if value == CUSTOM_INPUT_OPTION else value,
        key=f"{widget_prefix}_preset",
    )
    if selected_value == CUSTOM_INPUT_OPTION:
        return st.text_input(
            text_label,
            value=initial_value,
            key=f"{widget_prefix}_custom",
    )
    return selected_value


with st.container(border=True):
    overview_col, focus_col = st.columns([1.8, 1.0])
    with overview_col:
        st.title("BV PV Design Review Workbench" if ui_language == "en" else "BV 光伏结构设计审核工作台")
        st.caption(
            "Third-party PV civil, structural, mounting, foundation, and existing-rooftop design review workbench."
            if ui_language == "en"
            else "面向第三方审核工程师的光伏土建、钢结构、支架、基础与既有屋面增载设计审核工作台。"
        )
        st.caption(translate(ui_language, "public_demo_caption"))
    with focus_col:
        st.markdown(f"**{'Demo Focus' if ui_language == 'en' else '当前演示焦点'}**")
        st.write(
            "- Review workflow, basis traceability, risk register, and report export"
            if ui_language == "en"
            else "- 审核工作流、依据追溯、风险台账与报告导出"
        )
        st.write(
            "- Existing portal-frame rooftop PV screening module remains available"
            if ui_language == "en"
            else "- 既有门式刚架屋面光伏增载筛查模块继续保留"
        )
        st.write(
            "- Uses example inputs for public walkthroughs"
            if ui_language == "en"
            else "- 使用示例输入进行公开演示"
        )
st.info(translate(ui_language, "public_demo_banner"))

bv_review_tab, assessment_tab, input_tab, basis_tab, export_tab, pv_3d_tab, extension_tab = st.tabs(
    [
        translate(ui_language, "bv_review_tab"),
        translate(ui_language, "assessment_tab"),
        translate(ui_language, "project_input_tab"),
        translate(ui_language, "basis_traceability_tab"),
        translate(ui_language, "report_export_tab"),
        translate(ui_language, "pv_3d_studio_tab"),
        translate(ui_language, "portal_frame_tab"),
    ]
)

with input_tab:
    st.subheader(translate(ui_language, "project_input_tab"))
    st.caption(selected_demo["label"])
    st.caption(selected_demo["note"])

    with st.form("project_input_form"):
        st.markdown(f"### {translate(ui_language, 'input_group_project_basics')}")
        project_type = "rooftop_pv"
        default_package_key = st.selectbox(
            translate(ui_language, "default_package"),
            ["none", *default_packages.keys()],
            format_func=lambda value: translate_option(ui_language, "default_package_key", value),
        )
        st.caption(translate(ui_language, "default_package_hint"))
        design_standard_context = st.selectbox(
            translate(ui_language, "design_standard_context"),
            ["gb", "aisc", "eurocode"],
            index=["gb", "aisc", "eurocode"].index(defaults.get("design_standard_context", "gb")),
            format_func=lambda value: translate_option(ui_language, "design_standard_context", value),
        )
        building_type = st.text_input(
            translate(ui_language, "building_type"),
            value=localize_preset_text(ui_language, "building_type", defaults["building_type"]),
        )
        structural_system = st.text_input(
            translate(ui_language, "structural_system"),
            value=localize_preset_text(ui_language, "structural_system", defaults["structural_system"]),
        )
        roof_type = st.text_input(
            translate(ui_language, "roof_type"),
            value=localize_preset_text(ui_language, "roof_type", defaults["roof_type"]),
        )
        intended_modification = st.text_input(
            translate(ui_language, "modification"),
            value=localize_preset_text(ui_language, "modification", defaults["intended_modification"]),
        )
        estimated_added_load_kpa = st.number_input(
            translate(ui_language, "added_load"),
            min_value=0.0,
            value=float(defaults["estimated_added_load_kpa"] or 0.0),
            step=0.01,
            format="%.2f",
        )

        st.markdown(f"### {translate(ui_language, 'main_case_screening_inputs')}")
        building_span_m = st.number_input(
            translate(ui_language, "building_span"),
            min_value=0.0,
            value=float(defaults.get("building_span_m") or 0.0),
            step=0.5,
            format="%.1f",
        )
        column_spacing_m = st.number_input(
            translate(ui_language, "column_spacing"),
            min_value=0.0,
            value=float(defaults.get("column_spacing_m") or 0.0),
            step=0.5,
            format="%.1f",
        )
        eave_height_m = st.number_input(
            translate(ui_language, "eave_height"),
            min_value=0.0,
            value=float(defaults.get("eave_height_m") or 0.0),
            step=0.5,
            format="%.1f",
        )
        steel_grade = _preset_or_custom_value(
            preset_label=translate(ui_language, "steel_grade_preset"),
            text_label=translate(ui_language, "steel_grade"),
            options=STEEL_GRADE_PRESETS,
            current_value=defaults.get("steel_grade"),
            widget_prefix="steel_grade",
        )
        rafter_section = _preset_or_custom_value(
            preset_label=translate(ui_language, "rafter_section_preset"),
            text_label=translate(ui_language, "rafter_section"),
            options=RAFTER_SECTION_PRESETS,
            current_value=defaults.get("rafter_section"),
            widget_prefix="rafter_section",
        )
        column_section = _preset_or_custom_value(
            preset_label=translate(ui_language, "column_section_preset"),
            text_label=translate(ui_language, "column_section"),
            options=COLUMN_SECTION_PRESETS,
            current_value=defaults.get("column_section"),
            widget_prefix="column_section",
        )
        purlin_spacing_m = st.number_input(
            translate(ui_language, "purlin_spacing"),
            min_value=0.0,
            value=float(defaults.get("purlin_spacing_m") or 0.0),
            step=0.1,
            format="%.2f",
        )
        purlin_type = st.selectbox(
            translate(ui_language, "purlin_type"),
            ["cold_formed_z", "cold_formed_c", "hot_rolled", "unknown"],
            index=["cold_formed_z", "cold_formed_c", "hot_rolled", "unknown"].index(
                defaults.get("purlin_type") or "unknown"
            ),
            format_func=lambda value: translate_option(ui_language, "purlin_type", value),
        )

        st.markdown(f"### {translate(ui_language, 'input_group_roof_connection')}")
        roof_panel_type = st.selectbox(
            translate(ui_language, "roof_panel_type"),
            ["profiled_sheet", "sandwich_panel", "standing_seam", "unknown"],
            index=["profiled_sheet", "sandwich_panel", "standing_seam", "unknown"].index(
                defaults.get("roof_panel_type") or "unknown"
            ),
            format_func=lambda value: translate_option(ui_language, "roof_panel_type", value),
        )
        roof_panel_thickness_mm_raw = st.text_input(
            translate(ui_language, "roof_panel_thickness"),
            value="" if defaults["roof_panel_thickness_mm"] is None else str(defaults["roof_panel_thickness_mm"]),
        )
        roof_rib_height_mm_raw = st.text_input(
            translate(ui_language, "roof_rib_height"),
            value="" if defaults["roof_rib_height_mm"] is None else str(defaults["roof_rib_height_mm"]),
        )
        roof_attachment_preference = st.selectbox(
            translate(ui_language, "attachment_preference"),
            ["clamp_based", "penetrating", "undecided"],
            index=["clamp_based", "penetrating", "undecided"].index(
                defaults.get("roof_attachment_preference", "undecided")
            ),
            format_func=lambda value: translate_option(ui_language, "roof_attachment_preference", value),
        )
        waterproofing_sensitivity = st.selectbox(
            translate(ui_language, "waterproofing_sensitivity"),
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(defaults.get("waterproofing_sensitivity", "medium")),
            format_func=lambda value: translate_option(ui_language, "waterproofing_sensitivity", value),
        )
        restricted_installation_zones = st.text_area(
            translate(ui_language, "restricted_installation_zones"),
            value=defaults.get("restricted_installation_zones") or "",
            height=90,
        )

        st.markdown(f"### {translate(ui_language, 'input_group_structural_evidence')}")
        existing_member_schedule_status = st.selectbox(
            translate(ui_language, "existing_member_schedule_status"),
            ["available", "partial", "missing"],
            index=["available", "partial", "missing"].index(defaults.get("existing_member_schedule_status", "missing")),
            format_func=lambda value: translate_option(ui_language, "document_status", value),
        )
        connection_detail_status = st.selectbox(
            translate(ui_language, "connection_detail_status"),
            ["available", "partial", "missing"],
            index=["available", "partial", "missing"].index(defaults.get("connection_detail_status", "missing")),
            format_func=lambda value: translate_option(ui_language, "document_status", value),
        )
        roof_vendor_data_status = st.selectbox(
            translate(ui_language, "roof_vendor_data_status"),
            ["available", "partial", "missing"],
            index=["available", "partial", "missing"].index(defaults.get("roof_vendor_data_status", "missing")),
            format_func=lambda value: translate_option(ui_language, "document_status", value),
        )
        corrosion_condition = st.selectbox(
            translate(ui_language, "corrosion_condition"),
            ["low", "moderate", "high", "unknown"],
            index=["low", "moderate", "high", "unknown"].index(defaults.get("corrosion_condition", "unknown")),
            format_func=lambda value: translate_option(ui_language, "corrosion_condition", value),
        )
        drawing_availability = st.selectbox(
            translate(ui_language, "drawing_availability"),
            ["complete", "partial", "missing"],
            index=["complete", "partial", "missing"].index(defaults["drawing_availability"]),
            format_func=lambda value: translate_option(ui_language, "drawing_availability", value),
        )
        survey_available = st.checkbox(
            translate(ui_language, "survey_available"),
            value=bool(defaults["survey_available"]),
        )
        available_verification_path = st.selectbox(
            translate(ui_language, "verification_path"),
            ["drawings_only", "survey_only", "drawings_plus_survey", "no_viable_path_yet"],
            index=["drawings_only", "survey_only", "drawings_plus_survey", "no_viable_path_yet"].index(
                defaults.get("available_verification_path", "drawings_only")
            ),
            format_func=lambda value: translate_option(ui_language, "available_verification_path", value),
        )
        shutdown_constraint = st.selectbox(
            translate(ui_language, "shutdown_constraint"),
            ["none", "limited", "strict"],
            index=["none", "limited", "strict"].index(defaults["shutdown_constraint"]),
            format_func=lambda value: translate_option(ui_language, "shutdown_constraint", value),
        )

        st.form_submit_button(translate(ui_language, "update_assessment"), use_container_width=True)

form_data = {
    "default_package_key": None if default_package_key == "none" else default_package_key,
    "project_type": project_type,
    "design_standard_context": design_standard_context,
    "building_type": canonicalize_preset_text("building_type", building_type),
    "structural_system": canonicalize_preset_text("structural_system", structural_system),
    "roof_type": canonicalize_preset_text("roof_type", roof_type),
    "intended_modification": canonicalize_preset_text("modification", intended_modification),
    "estimated_added_load_kpa": estimated_added_load_kpa,
    "building_span_m": building_span_m if building_span_m else None,
    "column_spacing_m": column_spacing_m if column_spacing_m else None,
    "eave_height_m": eave_height_m if eave_height_m else None,
    "steel_grade": steel_grade.strip() or None,
    "rafter_section": rafter_section.strip() or None,
    "column_section": column_section.strip() or None,
    "purlin_spacing_m": purlin_spacing_m if purlin_spacing_m else None,
    "purlin_type": purlin_type,
    "roof_panel_type": roof_panel_type,
    "roof_panel_thickness_mm": float(roof_panel_thickness_mm_raw) if roof_panel_thickness_mm_raw.strip() else None,
    "roof_rib_height_mm": float(roof_rib_height_mm_raw) if roof_rib_height_mm_raw.strip() else None,
    "roof_attachment_preference": roof_attachment_preference,
    "existing_member_schedule_status": existing_member_schedule_status,
    "connection_detail_status": connection_detail_status,
    "roof_vendor_data_status": roof_vendor_data_status,
    "corrosion_condition": corrosion_condition,
    "waterproofing_sensitivity": waterproofing_sensitivity,
    "restricted_installation_zones": restricted_installation_zones,
    "available_verification_path": available_verification_path,
    "shutdown_constraint": shutdown_constraint,
    "drawing_availability": drawing_availability,
    "survey_available": survey_available,
}

try:
    evaluation = evaluate_case(form_data, language=ui_language, repository=repository)
except ValidationError as exc:
    st.error(
        "输入参数超出当前工程筛查的合理区间，请先修正新增荷载或几何参数后再继续。"
        if ui_language == "zh"
        else "One or more inputs fall outside the current engineering screening range. Please correct the load or geometry values and try again."
    )
    st.caption(str(exc))
    st.stop()

result = evaluation["result"]
explanation = evaluation["explanation"]
view = build_workbench_view(evaluation, language=ui_language)
report_preview = build_report_preview(
    evaluation["intake"],
    result,
    explanation,
    language=ui_language,
    kernel_outcome=evaluation.get("kernel_outcome"),
)
report_filename = build_report_filename(selected_demo_key)
report_docx_filename = report_filename.replace(".md", ".docx")
report_pdf_filename = report_filename.replace(".md", ".pdf")

with bv_review_tab:
    default_bv_intake = default_bv_review_intake()
    st.subheader(translate(ui_language, "bv_review_intake_heading"))
    st.caption(
        "BV Review Mode organizes scope, basis, document completeness, ITP, risks, and report preview."
        if ui_language == "en"
        else "BV 审核模式用于组织审核范围、依据、资料完整性、ITP、风险清单和报告预览。"
    )

    bv_col_1, bv_col_2 = st.columns(2)
    with bv_col_1:
        bv_project_name = st.text_input(
            "Project Name" if ui_language == "en" else "项目名称",
            value=default_bv_intake.project_name,
            key="bv_project_name",
        )
        bv_country_or_region = st.text_input(
            "Country / Region" if ui_language == "en" else "国家 / 地区",
            value=default_bv_intake.country_or_region,
            key="bv_country_or_region",
        )
        bv_project_type = st.selectbox(
            "Project Type" if ui_language == "en" else "项目类型",
            list(BV_PROJECT_TYPE_LABELS),
            index=list(BV_PROJECT_TYPE_LABELS).index(default_bv_intake.project_type),
            format_func=lambda value: format_bv_label(
                BV_PROJECT_TYPE_LABELS,
                value,
                ui_language,
            ),
            key="bv_project_type",
        )
        bv_design_stage = st.selectbox(
            "Design Stage" if ui_language == "en" else "设计阶段",
            list(BV_DESIGN_STAGE_LABELS),
            index=list(BV_DESIGN_STAGE_LABELS).index(default_bv_intake.design_stage),
            format_func=lambda value: format_bv_label(
                BV_DESIGN_STAGE_LABELS,
                value,
                ui_language,
            ),
            key="bv_design_stage",
        )
    with bv_col_2:
        bv_standards = st.multiselect(
            "Standards Systems" if ui_language == "en" else "标准体系",
            list(BV_STANDARD_LABELS),
            default=list(default_bv_intake.standards_systems),
            format_func=lambda value: format_bv_label(
                BV_STANDARD_LABELS,
                value,
                ui_language,
            ),
            key="bv_standards",
        )
        bv_review_objects = st.multiselect(
            "Review Objects" if ui_language == "en" else "审核对象",
            list(BV_REVIEW_OBJECT_LABELS),
            default=list(default_bv_intake.review_objects),
            format_func=lambda value: format_bv_label(
                BV_REVIEW_OBJECT_LABELS,
                value,
                ui_language,
            ),
            key="bv_review_objects",
        )
        bv_client_requirements_text = st.text_area(
            "Client Requirements" if ui_language == "en" else "客户要求",
            value="\n".join(default_bv_intake.client_requirements),
            height=90,
            key="bv_client_requirements",
        )

    st.markdown(f'#### {translate(ui_language, "bv_review_checklist_heading")}')
    document_statuses = {}
    doc_cols = st.columns(3)
    for index, (document_key, labels) in enumerate(BV_DOCUMENT_LABELS.items()):
        with doc_cols[index % 3]:
            document_statuses[document_key] = st.selectbox(
                labels[ui_language],
                list(BV_DOCUMENT_STATUS_LABELS),
                index=list(BV_DOCUMENT_STATUS_LABELS).index(default_bv_intake.documents[document_key]),
                format_func=lambda value: format_bv_label(
                    BV_DOCUMENT_STATUS_LABELS,
                    value,
                    ui_language,
                ),
                key=f"bv_doc_{document_key}",
            )

    st.markdown(f'#### {translate(ui_language, "multi_agent_workflow_heading")}')
    st.caption(translate(ui_language, "human_gate_caption"))
    st.markdown(f'##### {translate(ui_language, "human_gate_heading")}')
    human_gate_rows = st.data_editor(
        build_ground_fixed_human_gate_rows(ui_language),
        column_config={
            "field_id": None,
            "field_name": st.column_config.TextColumn("字段" if ui_language == "zh" else "Field"),
            "candidate_value": st.column_config.TextColumn("候选值" if ui_language == "zh" else "Candidate Value"),
            "unit": st.column_config.TextColumn("单位" if ui_language == "zh" else "Unit"),
            "source_document_id": st.column_config.TextColumn("来源文件 ID" if ui_language == "zh" else "Source Document ID"),
            "page_or_section": st.column_config.TextColumn("页码 / 章节" if ui_language == "zh" else "Page / Section"),
            "quote": st.column_config.TextColumn("原文片段" if ui_language == "zh" else "Evidence Quote"),
            "confidence": st.column_config.NumberColumn("置信度" if ui_language == "zh" else "Confidence", min_value=0.0, max_value=1.0),
            "is_confirmed": st.column_config.CheckboxColumn("工程师确认" if ui_language == "zh" else "Engineer Confirmed"),
            "include_in_calculation": st.column_config.CheckboxColumn("进入计算接口" if ui_language == "zh" else "Enter Calculation Interface"),
        },
        disabled=["source_document_id"],
        hide_index=True,
        num_rows="fixed",
        use_container_width=True,
        key="bv_human_gate_rows",
    )
    human_gate_records = (
        human_gate_rows.to_dict("records")
        if hasattr(human_gate_rows, "to_dict")
        else list(human_gate_rows)
    )
    human_gate_signature = repr(
        [
            (
                row.get("field_id"),
                row.get("candidate_value"),
                row.get("unit"),
                row.get("source_document_id"),
                row.get("page_or_section"),
                row.get("quote"),
                row.get("confidence"),
                row.get("is_confirmed"),
                row.get("include_in_calculation"),
            )
            for row in human_gate_records
        ]
    )
    try:
        human_gate_fields = build_extracted_fields_from_human_gate_rows(human_gate_records)
        foundation_calculation_run = build_foundation_calculation_run_from_fields(
            run_id="phase1-ground-fixed-gate",
            fields=human_gate_fields,
        )
        superstructure_calculation_run = build_superstructure_calculation_run_from_fields(
            run_id="phase1-ground-fixed-superstructure-gate",
            fields=human_gate_fields,
            member_id="post-P1",
            member_type="post",
        )
        calculation_gate_runs = [
            foundation_calculation_run,
            superstructure_calculation_run,
        ]
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        human_gate_fields = []
        calculation_gate_runs = []
        st.warning(str(exc))

    gate_is_still_locked = (
        st.session_state.get("bv_calculation_gate_locked") is True
        and st.session_state.get("bv_calculation_gate_signature") == human_gate_signature
    )
    calculation_gate_ready = bool(calculation_gate_runs) and all(
        run.status in {"ready", "completed"} for run in calculation_gate_runs
    )
    calculation_gate_checked = st.button(translate(ui_language, "data_lock_button"), use_container_width=True)
    if calculation_gate_checked:
        if calculation_gate_ready:
            st.session_state["bv_calculation_gate_locked"] = True
            st.session_state["bv_calculation_gate_signature"] = human_gate_signature
            st.success(translate(ui_language, "calculation_gate_ready"))
            field_name_by_id = {
                str(row["field_id"]): str(row["field_name"])
                for row in human_gate_records
            }
            st.caption(
                ", ".join(
                    field_name_by_id.get(field_id, field_id)
                    for run in calculation_gate_runs
                    for field_id in run.input_field_ids
                )
            )
            for run in calculation_gate_runs:
                if run.result_summary:
                    engine_labels = {
                        "foundation": {
                            "zh": "基础验算",
                            "en": "Foundation",
                        },
                        "superstructure": {
                            "zh": "上部构件验算",
                            "en": "Superstructure",
                        },
                    }
                    st.markdown(
                        f"**{run.engine_name.title()}**"
                        if ui_language == "en"
                        else f"**{format_bv_label(engine_labels, run.engine_name, ui_language)}**"
                    )
                    st.dataframe(
                        build_calculation_result_summary_rows(
                            run.result_summary, ui_language
                        ),
                        hide_index=True,
                        use_container_width=True,
                    )
        else:
            st.session_state["bv_calculation_gate_locked"] = False
            st.session_state["bv_calculation_gate_signature"] = None
            st.warning(translate(ui_language, "calculation_gate_blocked"))
            for run in calculation_gate_runs:
                for error in run.structured_errors:
                    st.write(f"- {error}")

    st.markdown(f'#### {translate(ui_language, "version_diff_heading")}')
    st.caption(translate(ui_language, "version_diff_caption"))
    previous_human_gate_rows = build_ground_fixed_human_gate_rows(ui_language)
    next(row for row in previous_human_gate_rows if row["field_id"] == "pile_length_m")[
        "candidate_value"
    ] = "3.5"
    current_human_gate_rows = list(human_gate_records)
    field_diffs = diff_extracted_fields(
        build_extracted_fields_from_human_gate_rows(previous_human_gate_rows),
        build_extracted_fields_from_human_gate_rows(current_human_gate_rows),
        calculation_runs=calculation_gate_runs,
    )
    incremental_recheck_plan = build_incremental_recheck_plan(field_diffs)
    if field_diffs:
        st.dataframe(
            build_field_diff_summary_rows(field_diffs, ui_language),
            hide_index=True,
            use_container_width=True,
        )
    st.markdown(f'##### {translate(ui_language, "incremental_recheck_heading")}')
    incremental_recheck_rows = build_incremental_recheck_summary_rows(incremental_recheck_plan, ui_language)
    if incremental_recheck_rows:
        st.dataframe(incremental_recheck_rows, hide_index=True, use_container_width=True)
    else:
        st.caption("当前没有增量复核项。" if ui_language == "zh" else "No incremental recheck items at this point.")
    registered_incremental_rfis: list[RFIItem] = []
    if incremental_recheck_plan.rfi_items:
        rfi_source_by_id = {item.rfi_id: item for item in incremental_recheck_plan.rfi_items}
        rfi_status_labels = (
            {"open": "待回复", "responded": "已回复", "closed": "已关闭", "reopened": "已重开"}
            if ui_language == "zh"
            else {"open": "open", "responded": "responded", "closed": "closed", "reopened": "reopened"}
        )
        rfi_status_values = {
            **{label: value for value, label in rfi_status_labels.items()},
            "open": "open",
            "responded": "responded",
            "closed": "closed",
            "reopened": "reopened",
            "待回复": "open",
            "已回复": "responded",
            "已关闭": "closed",
            "已重开": "reopened",
        }
        rfi_closeout_rows = st.data_editor(
            [
                {
                    "rfi_id": item.rfi_id,
                    "question": (
                        f"请确认字段 {item.required_document_or_field} 的更新输入。"
                        if ui_language == "zh"
                        else item.question
                    ),
                    "status": rfi_status_labels[item.status],
                    "client_response": item.client_response or "",
                    "required_document_or_field": item.required_document_or_field,
                }
                for item in incremental_recheck_plan.rfi_items
            ],
            column_config={
                "rfi_id": st.column_config.TextColumn("RFI ID"),
                "question": st.column_config.TextColumn("问题" if ui_language == "zh" else "Question"),
                "status": st.column_config.SelectboxColumn(
                    "状态" if ui_language == "zh" else "Status",
                    options=list(rfi_status_labels.values()),
                ),
                "client_response": st.column_config.TextColumn(
                    "客户回复" if ui_language == "zh" else "Client Response"
                ),
                "required_document_or_field": st.column_config.TextColumn(
                    "所需资料 / 字段" if ui_language == "zh" else "Required Document / Field"
                ),
            },
            disabled=["rfi_id", "question", "required_document_or_field"],
            hide_index=True,
            num_rows="fixed",
            use_container_width=True,
            key=f"bv_incremental_rfi_closeout_rows_{ui_language}",
        )
        rfi_closeout_records = (
            rfi_closeout_rows.to_dict("records")
            if hasattr(rfi_closeout_rows, "to_dict")
            else list(rfi_closeout_rows)
        )
        for row in rfi_closeout_records:
            source_rfi = rfi_source_by_id[str(row["rfi_id"])]
            try:
                registered_incremental_rfis.append(
                    RFIItem(
                        rfi_id=source_rfi.rfi_id,
                        question=source_rfi.question,
                        responsible_party=source_rfi.responsible_party,
                        trigger_basis=source_rfi.trigger_basis,
                        required_document_or_field=source_rfi.required_document_or_field,
                        status=rfi_status_values[str(row["status"])],
                        client_response=str(row.get("client_response") or "") or None,
                        reopen_review_items=source_rfi.reopen_review_items,
                        completed_recheck_items=(
                            source_rfi.reopen_review_items
                            if rfi_status_values[str(row["status"])] == "closed"
                            else []
                        ),
                        triggers_incremental_recheck=source_rfi.triggers_incremental_recheck,
                    )
                )
            except ValidationError as exc:
                registered_incremental_rfis.append(source_rfi)
                st.warning(
                    "将 RFI 标记为已回复或已关闭前必须填写客户回复。"
                    if ui_language == "zh"
                    else str(exc)
                )

    if not bv_standards:
        st.warning(translate(ui_language, "bv_review_warning_standards"))
    elif not bv_review_objects:
        st.warning(translate(ui_language, "bv_review_warning_objects"))
    else:
        bv_intake = build_bv_review_intake(
            project_name=bv_project_name,
            country_or_region=bv_country_or_region,
            project_type=bv_project_type,
            design_stage=bv_design_stage,
            standards_systems=bv_standards,
            review_objects=bv_review_objects,
            client_requirements_text=bv_client_requirements_text,
            documents=document_statuses,
        )
        bv_result = evaluate_bv_review(bv_intake)
        phase1_approvals = []
        if (
            (calculation_gate_checked or gate_is_still_locked)
            and calculation_gate_ready
        ):
            phase1_approvals.append(
                build_engineer_approval(
                    approval_id="phase1-calculation-gate-approval",
                    target_id="calculation",
                    reviewer="demo-review-engineer",
                    comment="Phase 1 demo data lock for report draft gate.",
                )
            )
        phase1_state = ProjectReviewState(
            project_id="phase1-ground-fixed-demo",
            intake=bv_intake,
            extracted_fields=human_gate_fields,
            approvals=phase1_approvals,
            calculation_runs=calculation_gate_runs,
            rfi_items=registered_incremental_rfis,
            risks=bv_result.risks,
        )
        st.markdown(
            "#### Project Persistence / Resume"
            if ui_language == "en"
            else "项目持久化 / 恢复运行"
        )
        st.caption(
            "Explicit buttons save or resume local JSON state; normal page rendering does not write files."
            if ui_language == "en"
            else "只有点击按钮时才会保存或恢复本地 JSON 状态，普通页面渲染不会写入文件。"
        )
        persisted_repository = JsonProjectReviewStateRepository(
            Path(".local_data") / "bv_review_states"
        )
        persisted_project_id = st.text_input(
            "Persisted Project ID" if ui_language == "en" else "持久化项目 ID",
            value=phase1_state.project_id,
            key="bv_persisted_project_id",
        ).strip()
        persisted_project_id = persisted_project_id or phase1_state.project_id
        project_inventory = persisted_repository.list_project_inventory()
        if project_inventory.invalid_project_ids:
            st.warning(
                (
                    "Some saved project files could not be loaded: "
                    if ui_language == "en"
                    else "部分已保存项目文件无法加载："
                )
                + ", ".join(project_inventory.invalid_project_ids)
            )
        if project_inventory.summaries:
            st.markdown(
                "##### Saved Project Inventory"
                if ui_language == "en"
                else "已保存项目清单"
            )
            st.dataframe(
                build_project_review_state_summary_rows(
                    project_inventory.summaries,
                    ui_language,
                ),
                hide_index=True,
                use_container_width=True,
            )
            saved_project_ids = [
                summary.project_id for summary in project_inventory.summaries
            ]
            selected_saved_project_id = st.selectbox(
                "Saved Project ID" if ui_language == "en" else "已保存项目 ID",
                saved_project_ids,
                key="bv_selected_saved_project_id",
            )
        else:
            selected_saved_project_id = None
        persisted_workflow_result = None
        (
            save_state_col,
            resume_state_col,
            resume_selected_col,
            current_state_col,
        ) = st.columns(4)
        with save_state_col:
            if st.button(
                "Save Current Review State"
                if ui_language == "en"
                else "保存当前审核状态",
                key="bv_save_current_review_state",
                use_container_width=True,
            ):
                try:
                    persisted_repository.save(
                        phase1_state.model_copy(update={"project_id": persisted_project_id})
                    )
                    clear_persisted_workflow_session(st.session_state)
                    st.success(
                        f"Saved {persisted_project_id}."
                        if ui_language == "en"
                        else f"已保存 {persisted_project_id}。"
                    )
                except ValueError as exc:
                    st.warning(str(exc))
        with resume_state_col:
            if st.button(
                "Resume Saved Workflow"
                if ui_language == "en"
                else "恢复已保存工作流",
                key="bv_resume_saved_workflow",
                use_container_width=True,
            ):
                try:
                    persisted_workflow_result = (
                        run_persisted_local_agent_workflow_with_summary(
                            persisted_repository,
                            persisted_project_id,
                        )
                    )
                    store_persisted_workflow_result(
                        st.session_state,
                        persisted_workflow_result,
                    )
                    st.success(
                        f"Resumed {persisted_project_id}."
                        if ui_language == "en"
                        else f"已恢复 {persisted_project_id}。"
                    )
                except FileNotFoundError:
                    st.warning(
                        "Save this project before resuming a persisted workflow."
                        if ui_language == "en"
                        else "请先保存该项目，再恢复持久化工作流。"
                    )
                except ValueError as exc:
                    st.warning(str(exc))
        with resume_selected_col:
            if st.button(
                "Resume Selected Saved Project"
                if ui_language == "en"
                else "恢复所选已保存项目",
                key="bv_resume_selected_saved_project",
                use_container_width=True,
                disabled=selected_saved_project_id is None,
            ):
                try:
                    persisted_workflow_result = (
                        run_persisted_local_agent_workflow_with_summary(
                            persisted_repository,
                            str(selected_saved_project_id),
                        )
                    )
                    store_persisted_workflow_result(
                        st.session_state,
                        persisted_workflow_result,
                    )
                    st.success(
                        f"Resumed {selected_saved_project_id}."
                        if ui_language == "en"
                        else f"已恢复 {selected_saved_project_id}。"
                    )
                except FileNotFoundError:
                    st.warning(
                        "Save this project before resuming a persisted workflow."
                        if ui_language == "en"
                        else "请先保存该项目，再恢复持久化工作流。"
                    )
                except ValueError as exc:
                    st.warning(str(exc))
        with current_state_col:
            if st.button(
                "Use Current Form State"
                if ui_language == "en"
                else "使用当前表单状态",
                key="bv_use_current_form_state",
                use_container_width=True,
            ):
                clear_persisted_workflow_session(st.session_state)
                st.success(
                    "Using the current form state."
                    if ui_language == "en"
                    else "已切换为使用当前表单状态。"
                )
        active_persisted_project_id = (
            get_active_persisted_project_id(st.session_state)
            or persisted_project_id
        )
        persisted_summary = get_active_persisted_workflow_summary(
            st.session_state,
            active_persisted_project_id,
        )
        if persisted_summary:
            st.dataframe(
                build_persisted_workflow_run_summary_rows(
                    persisted_summary,
                    ui_language,
                ),
                hide_index=True,
                use_container_width=True,
            )
        persisted_session_state = get_active_persisted_workflow_state(
            st.session_state,
            active_persisted_project_id,
        )
        persisted_workflow_is_active = persisted_session_state is not None
        workflow_signature = f"{bv_intake.model_dump_json()}|{human_gate_signature}"
        if st.session_state.get("bv_agent_review_signature") != workflow_signature:
            st.session_state["bv_agent_review_signature"] = workflow_signature
            st.session_state["bv_agent_review_decisions"] = {}
            st.session_state["bv_report_gate_approved"] = False
            st.session_state["bv_report_revisions"] = []
            st.session_state.pop("bv_agent_application_state", None)
            st.session_state.pop("bv_agent_response_application_packet", None)
        session_agent_application_state = st.session_state.get(
            "bv_agent_application_state"
        )
        workflow_state = (
            persisted_workflow_result.state
            if persisted_workflow_result is not None
            else persisted_session_state
            if persisted_session_state is not None
            else session_agent_application_state
            if isinstance(session_agent_application_state, ProjectReviewState)
            else run_local_agent_workflow_until_blocked(phase1_state)
        )
        stored_agent_review_decisions = (
            {}
            if persisted_workflow_is_active
            else st.session_state.get(
                "bv_agent_review_decisions",
                {},
            )
        )
        reviewed_workflow_state = (
            workflow_state
            if persisted_workflow_is_active
            else resume_local_agent_workflow_after_review_decisions(
                workflow_state,
                stored_agent_review_decisions,
                reviewer="demo-review-engineer",
            )
        )
        if not persisted_workflow_is_active:
            if (
                st.session_state.get("bv_report_gate_approved") is True
                and not reviewed_workflow_state.is_gate_locked("report")
            ):
                reviewed_workflow_state = reviewed_workflow_state.model_copy(
                    update={
                        "approvals": [
                            *reviewed_workflow_state.approvals,
                            build_engineer_approval(
                                approval_id="phase1-report-gate-approval",
                                target_id="report",
                                reviewer="demo-review-engineer",
                                comment="Report gate approved in demo workbench.",
                            ),
                        ]
                    }
                )
            session_report_revisions = st.session_state.get("bv_report_revisions", [])
            if isinstance(session_report_revisions, list) and session_report_revisions:
                reviewed_workflow_state = reviewed_workflow_state.model_copy(
                    update={"report_revisions": session_report_revisions}
                )
        effective_bv_intake = (
            reviewed_workflow_state.intake
            if persisted_workflow_is_active
            else bv_intake
        )
        effective_bv_result = (
            build_bv_review_result_from_project_state(reviewed_workflow_state)
            if persisted_workflow_is_active
            else bv_result
        )
        effective_blockers = [
            item for item in effective_bv_result.risks if item.blocks_report_issue
        ]
        report_draft_gate = build_report_draft_gate_result(
            reviewed_workflow_state,
            effective_bv_result,
        )

        metric_1, metric_2, metric_3 = st.columns(3)
        metric_1.metric(
            "Decision" if ui_language == "en" else "审核结论",
            effective_bv_result.decision,
        )
        metric_2.metric(
            "Blocking Items" if ui_language == "en" else "阻塞项",
            len(effective_blockers),
        )
        metric_3.metric(
            "Review Paths" if ui_language == "en" else "审核路径",
            len(effective_bv_result.review_paths),
        )

        st.markdown("#### Local Agent Workflow State" if ui_language == "en" else "本地 Agent 工作流状态")
        workflow_phase_col, workflow_artifact_col = st.columns([1.2, 1.0])
        with workflow_phase_col:
            st.dataframe(
                build_agent_workflow_phase_rows(reviewed_workflow_state, ui_language),
                hide_index=True,
                use_container_width=True,
            )
        with workflow_artifact_col:
            st.dataframe(
                build_agent_workflow_artifact_rows(reviewed_workflow_state, ui_language),
                hide_index=True,
                use_container_width=True,
            )
        st.caption(
            "Local deterministic runner stops at engineer data lock until the calculation gate is approved."
            if ui_language == "en"
            else "本地确定性 runner 会在工程师数据锁定阶段等待计算门禁批准。"
        )
        blocked_calculation_draft_rows = build_blocked_calculation_review_draft_rows(
            reviewed_workflow_state,
            ui_language,
        )
        if blocked_calculation_draft_rows:
            blocked_calculation_draft_heading = (
                "Blocked Calculation Draft RFI"
                if ui_language == "en"
                else "计算阻塞草稿 RFI"
            )
            st.markdown(f"##### {blocked_calculation_draft_heading}")
            st.dataframe(
                blocked_calculation_draft_rows,
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                "Draft only; issuing an RFI moves the persisted workflow to issue/RFI closeout while calculation remains blocked until inputs are corrected."
                if ui_language == "en"
                else "仅作为草稿展示；签发 RFI 会将持久化工作流转入签发 / RFI 关闭阶段，计算仍需等待输入修正。"
            )
            draft_rfi_id_key = "Draft RFI ID" if ui_language == "en" else "草稿 RFI ID"
            existing_rfi_ids = {item.rfi_id for item in reviewed_workflow_state.rfi_items}
            draft_rfi_ids = [
                str(row[draft_rfi_id_key])
                for row in blocked_calculation_draft_rows
                if row.get(draft_rfi_id_key)
            ]
            available_draft_rfi_ids = [
                rfi_id for rfi_id in draft_rfi_ids if rfi_id not in existing_rfi_ids
            ]
            if persisted_workflow_is_active and available_draft_rfi_ids:
                selected_draft_rfi_id = st.selectbox(
                    "Draft RFI ID" if ui_language == "en" else "草稿 RFI ID",
                    available_draft_rfi_ids,
                    key="bv_blocked_calculation_draft_rfi_id",
                )
                draft_rfi_issue_comment = st.text_area(
                    "Draft RFI Issue Comment"
                    if ui_language == "en"
                    else "草稿 RFI 签发意见",
                    value=(
                        "Engineer reviewed the blocked calculation draft and issued an RFI."
                        if ui_language == "en"
                        else "工程师已复核计算阻塞草稿并签发 RFI。"
                    ),
                    key="bv_blocked_calculation_draft_rfi_issue_comment",
                    height=80,
                )
                if st.button(
                    "Issue Draft RFI After Engineer Review"
                    if ui_language == "en"
                    else "工程师复核后签发草稿 RFI",
                    key="bv_issue_blocked_calculation_draft_rfi",
                    use_container_width=True,
                ):
                    try:
                        issue_persisted_blocked_calculation_draft_rfi(
                            st.session_state,
                            persisted_repository,
                            project_id=active_persisted_project_id,
                            rfi_id=selected_draft_rfi_id,
                            reviewer="demo-review-engineer",
                            comment=draft_rfi_issue_comment,
                            approved_at=datetime.now(timezone.utc).isoformat(),
                        )
                    except ValueError as exc:
                        st.warning(str(exc))
                    else:
                        st.success(
                            "Draft RFI issued after engineer review."
                            if ui_language == "en"
                            else "草稿 RFI 已经工程师复核并签发。"
                        )
                        st.rerun()
            elif persisted_workflow_is_active:
                st.caption(
                    "All blocked calculation draft RFIs have already been issued into the persisted RFI register."
                    if ui_language == "en"
                    else "所有计算阻塞草稿 RFI 均已进入持久化 RFI 台账。"
                )
            else:
                st.caption(
                    "Save or resume a persisted project before issuing a draft RFI."
                    if ui_language == "en"
                    else "签发草稿 RFI 前，请先保存或恢复持久化项目。"
                )
        agent_prompt_packages = build_agent_prompt_packages(reviewed_workflow_state)
        agent_contract_heading = (
            "Agent Contract Prompt Preview"
            if ui_language == "en"
            else "Agent 契约提示词预览"
        )
        st.markdown(f"##### {agent_contract_heading}")
        st.dataframe(
            build_agent_prompt_package_rows(
                agent_prompt_packages,
                ui_language,
            ),
            hide_index=True,
            use_container_width=True,
        )
        selected_agent_contract = st.selectbox(
            "Agent Contract" if ui_language == "en" else "Agent 契约",
            [package.agent_role for package in agent_prompt_packages],
            key="bv_agent_contract_prompt_preview",
        )
        selected_agent_prompt_package = next(
            package
            for package in agent_prompt_packages
            if package.agent_role == selected_agent_contract
        )
        agent_application_notice = st.session_state.pop(
            "bv_agent_application_notice",
            None,
        )
        if isinstance(agent_application_notice, str):
            st.success(agent_application_notice)
        with st.expander(
            "System and User Prompt"
            if ui_language == "en"
            else "系统提示词与用户上下文",
            expanded=False,
        ):
            st.code(selected_agent_prompt_package.system_prompt)
            st.code(selected_agent_prompt_package.user_prompt)
        provider_col, model_col = st.columns(2)
        with provider_col:
            agent_provider_name = st.selectbox(
                "Agent Provider" if ui_language == "en" else "Agent 供应商",
                ["minimax", "openai", "mock"],
                key="bv_agent_invocation_provider",
            )
        with model_col:
            agent_model_name = st.text_input(
                "Agent Model" if ui_language == "en" else "Agent 模型",
                value=default_agent_provider_model(agent_provider_name),
                key=f"bv_agent_invocation_model_{agent_provider_name}",
            )
        agent_invocation_request = build_agent_provider_invocation_request(
            selected_agent_prompt_package,
            provider_name=agent_provider_name,
            model_name=agent_model_name,
        )
        agent_invocation_heading = (
            "Agent Provider Invocation Preview"
            if ui_language == "en"
            else "Agent 供应商调用预览"
        )
        st.markdown(f"##### {agent_invocation_heading}")
        st.dataframe(
            build_agent_provider_invocation_rows(
                agent_invocation_request,
                ui_language,
            ),
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            "Invocation preview only; no network request is sent and no API key is stored."
            if ui_language == "en"
            else "仅调用预览；不发送网络请求，也不保存密钥。"
        )
        with st.expander(
            "JSON Schema Preview" if ui_language == "en" else "JSON Schema 预览",
            expanded=False,
        ):
            st.json(selected_agent_prompt_package.output_schema)
        validation_sandbox_heading = (
            "Agent JSON Response Validation Sandbox"
            if ui_language == "en"
            else "Agent JSON 响应验证沙盒"
        )
        st.markdown(f"##### {validation_sandbox_heading}")
        sample_agent_response_json = build_sample_agent_response_json(
            selected_agent_prompt_package.agent_role,
            reviewed_workflow_state,
        )
        agent_response_json = st.text_area(
            "Agent JSON Response"
            if ui_language == "en"
            else "Agent JSON 响应",
            value=sample_agent_response_json,
            height=180,
            key=f"bv_agent_response_validation_{selected_agent_contract}",
        )
        if st.button(
            "Validate Agent JSON Response"
            if ui_language == "en"
            else "验证 Agent JSON 响应",
            key="bv_validate_agent_json_response",
            use_container_width=True,
        ):
            sandbox_result = build_agent_response_sandbox_result(
                selected_agent_prompt_package,
                agent_response_json,
                state=reviewed_workflow_state,
                provider_name=agent_provider_name,
                model_name=agent_model_name,
            )
            validation_result = sandbox_result.validation_result
            sandbox_summary_heading = (
                "Agent Response Sandbox Summary"
                if ui_language == "en"
                else "Agent 响应沙盒摘要"
            )
            st.markdown(f"##### {sandbox_summary_heading}")
            st.dataframe(
                build_agent_response_sandbox_rows(sandbox_result, ui_language),
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                "Sandbox result only; no network request is sent and project state is unchanged."
                if ui_language == "en"
                else "仅沙盒结果；不发送网络请求，项目状态不变。"
            )
            engineer_handoff = build_agent_response_engineer_handoff(sandbox_result)
            engineer_handoff_heading = (
                "Agent Engineer Review Handoff"
                if ui_language == "en"
                else "Agent 工程师复核移交"
            )
            st.markdown(f"##### {engineer_handoff_heading}")
            st.dataframe(
                build_agent_response_engineer_handoff_rows(
                    engineer_handoff,
                    ui_language,
                ),
                hide_index=True,
                use_container_width=True,
            )
            application_plan = build_agent_response_application_plan(engineer_handoff)
            application_plan_heading = (
                "Agent Controlled Application Plan"
                if ui_language == "en"
                else "Agent 受控应用计划"
            )
            st.markdown(f"##### {application_plan_heading}")
            st.dataframe(
                build_agent_response_application_plan_rows(
                    application_plan,
                    ui_language,
                ),
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                "Application plan only; no agent output is applied until an engineer authorizes the controlled workflow step."
                if ui_language == "en"
                else "仅应用计划；工程师授权前不应用 Agent 输出。"
            )
            st.session_state["bv_agent_response_application_packet"] = (
                build_agent_response_application_packet(
                    workflow_signature=workflow_signature,
                    state=reviewed_workflow_state,
                    sandbox=sandbox_result,
                    plan=application_plan,
                )
            )
            if validation_result.ok:
                st.success(
                    validation_result.summary
                    if ui_language == "en"
                    else "Agent JSON 响应已通过结构化契约校验。"
                )
                impact_preview = sandbox_result.impact_preview
                impact_preview_heading = (
                    "Agent Response Impact Preview"
                    if ui_language == "en"
                    else "Agent 响应影响预览"
                )
                st.markdown(f"##### {impact_preview_heading}")
                if impact_preview is not None:
                    st.dataframe(
                        build_agent_response_impact_rows(impact_preview, ui_language),
                        hide_index=True,
                        use_container_width=True,
                    )
                st.caption(
                    "Preview only; engineer approval is still required before applying agent output."
                    if ui_language == "en"
                    else "仅预览；应用 Agent 输出前仍需工程师批准。"
                )
            else:
                st.warning(
                    validation_result.error
                    if ui_language == "en"
                    else f"Agent JSON 响应未通过校验：{validation_result.error}"
                )
        agent_application_packet = st.session_state.get(
            "bv_agent_response_application_packet"
        )
        if isinstance(agent_application_packet, AgentResponseApplicationPacket):
            if not is_agent_response_application_packet_current(
                agent_application_packet,
                workflow_signature=workflow_signature,
                state=reviewed_workflow_state,
            ):
                st.session_state.pop("bv_agent_response_application_packet", None)
                st.info(
                    "Revalidate the agent response before applying it to the updated workflow state."
                    if ui_language == "en"
                    else "工作流状态已更新，请重新校验 Agent 响应后再应用。"
                )
            else:
                sandbox_for_application = agent_application_packet.sandbox_result
                application_plan = agent_application_packet.application_plan
                st.markdown(
                    "##### Engineer Authorization for Controlled Application"
                    if ui_language == "en"
                    else "##### 工程师授权受控应用"
                )
                application_reviewer = st.text_input(
                    "Authorizing Engineer"
                    if ui_language == "en"
                    else "授权工程师",
                    value=(
                        "demo-review-engineer"
                        if ui_language == "en"
                        else "演示审核工程师"
                    ),
                    key="bv_agent_application_reviewer",
                )
                application_comment = st.text_area(
                    "Authorization Comment"
                    if ui_language == "en"
                    else "授权意见",
                    value=(
                        "Engineer authorized controlled application of validated agent output."
                        if ui_language == "en"
                        else "工程师已授权受控应用已校验的 Agent 产物。"
                    ),
                    height=80,
                    key="bv_agent_application_comment",
                )
                application_is_ready = (
                    application_plan.plan_status == "ready_for_controlled_application"
                )
                if not application_is_ready:
                    st.warning(
                        "Resolve application plan blockers before authorizing application."
                        if ui_language == "en"
                        else "请先处理应用计划阻断项，再授权应用。"
                    )
                if st.button(
                    "Authorize and Apply Agent Response"
                    if ui_language == "en"
                    else "授权并应用 Agent 响应",
                    key="bv_authorize_apply_agent_response",
                    disabled=not application_is_ready,
                    use_container_width=True,
                ):
                    authorization = AgentResponseApplicationAuthorization(
                        plan_id=application_plan.plan_id,
                        response_digest=application_plan.response_digest,
                        reviewer=application_reviewer,
                        decision="authorized",
                        comment=application_comment,
                    )
                    try:
                        if persisted_workflow_is_active:
                            apply_persisted_authorized_agent_response(
                                st.session_state,
                                persisted_repository,
                                project_id=active_persisted_project_id,
                                sandbox=sandbox_for_application,
                                plan=application_plan,
                                authorization=authorization,
                            )
                        else:
                            updated_workflow_state = (
                                apply_authorized_agent_response_to_state(
                                    reviewed_workflow_state,
                                    sandbox_for_application,
                                    application_plan,
                                    authorization,
                                )
                            )
                            st.session_state["bv_agent_application_state"] = (
                                updated_workflow_state
                            )
                    except ValueError as exc:
                        st.warning(str(exc))
                    else:
                        st.session_state.pop(
                            "bv_agent_response_application_packet",
                            None,
                        )
                        st.session_state["bv_agent_application_notice"] = (
                            "Agent response applied to workflow state."
                            if ui_language == "en"
                            else "Agent 响应已应用到工作流状态。"
                        )
                        st.rerun()
        elif agent_application_packet is not None:
            st.session_state.pop("bv_agent_response_application_packet", None)
        lifecycle_summary = build_finding_lifecycle_summary(reviewed_workflow_state)
        lifecycle_rows = build_finding_lifecycle_summary_rows(
            lifecycle_summary,
            ui_language,
        )
        st.markdown(
            "##### Finding / RFI Lifecycle"
            if ui_language == "en"
            else "发现项与澄清问题生命周期"
        )
        st.dataframe(
            lifecycle_rows,
            hide_index=True,
            use_container_width=True,
        )
        project_management_actions = build_project_management_actions(
            reviewed_workflow_state
        )
        responsible_party_rows = build_responsible_party_status_rows(
            project_management_actions,
            ui_language,
        )
        st.markdown(
            "##### Responsible Party Status and SLA"
            if ui_language == "en"
            else "责任方待办与时限状态"
        )
        if responsible_party_rows:
            st.dataframe(
                responsible_party_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption(
                "No responsible-party actions are currently open."
                if ui_language == "en"
                else "当前没有责任方待办。"
            )
        project_management_view = build_bv_project_management_dashboard_view(
            project_management_actions,
            ui_language,
        )
        st.markdown(f"##### {project_management_view.heading}")
        if project_management_view.action_rows:
            st.dataframe(
                project_management_view.summary_rows,
                hide_index=True,
                use_container_width=True,
            )
            st.dataframe(
                project_management_view.action_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption(project_management_view.empty_caption)
        revision_history_view = build_bv_report_revision_history_view(
            reviewed_workflow_state,
            ui_language,
        )
        st.markdown(f"##### {revision_history_view.heading}")
        if revision_history_view.revision_rows:
            st.dataframe(
                revision_history_view.summary_rows,
                hide_index=True,
                use_container_width=True,
            )
            st.dataframe(
                revision_history_view.revision_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption(revision_history_view.empty_caption)
        project_timeline_rows = build_project_timeline_rows(
            reviewed_workflow_state,
            ui_language,
        )
        st.markdown(
            "##### Project Timeline"
            if ui_language == "en"
            else "项目时间线"
        )
        if project_timeline_rows:
            st.dataframe(
                project_timeline_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption(
                "No RFI, finding closeout, or report revision timeline events are available."
                if ui_language == "en"
                else "当前没有 RFI、发现项关闭或报告修订时间线记录。"
            )
        st.markdown("##### Engineer Review Queue" if ui_language == "en" else "工程师复核队列")
        engineer_review_queue_rows = build_agent_engineer_review_queue_rows(
            reviewed_workflow_state,
            ui_language,
        )
        st.dataframe(
            engineer_review_queue_rows,
            hide_index=True,
            use_container_width=True,
        )
        if engineer_review_queue_rows:
            review_item_column = "Review Item" if ui_language == "en" else "复核项"
            selected_agent_review_item = st.selectbox(
                "Review Item" if ui_language == "en" else "复核项",
                [str(row[review_item_column]) for row in engineer_review_queue_rows],
            )
            agent_review_comment = st.text_input(
                "Engineer Review Comment" if ui_language == "en" else "工程师复核意见",
                value=(
                    "Reviewed in demo workbench."
                    if ui_language == "en"
                    else "已在演示工作台复核。"
                ),
            )
            approve_review_col, reject_review_col = st.columns(2)
            with approve_review_col:
                if st.button(
                    "Approve Selected Review Item"
                    if ui_language == "en"
                    else "批准所选复核项",
                    use_container_width=True,
                ):
                    if persisted_workflow_is_active:
                        try:
                            record_persisted_agent_review_decision(
                                st.session_state,
                                persisted_repository,
                                project_id=active_persisted_project_id,
                                event_id=selected_agent_review_item,
                                decision="approved",
                                reviewer="demo-review-engineer",
                                comment=agent_review_comment,
                            )
                        except ValueError as exc:
                            st.warning(str(exc))
                        else:
                            st.rerun()
                    else:
                        st.session_state["bv_agent_review_decisions"] = {
                            **stored_agent_review_decisions,
                            selected_agent_review_item: {
                                "decision": "approved",
                                "comment": agent_review_comment,
                            },
                        }
                        st.rerun()
            with reject_review_col:
                if st.button(
                    "Reject Selected Review Item"
                    if ui_language == "en"
                    else "驳回所选复核项",
                    use_container_width=True,
                ):
                    if persisted_workflow_is_active:
                        try:
                            record_persisted_agent_review_decision(
                                st.session_state,
                                persisted_repository,
                                project_id=active_persisted_project_id,
                                event_id=selected_agent_review_item,
                                decision="rejected",
                                reviewer="demo-review-engineer",
                                comment=agent_review_comment,
                            )
                        except ValueError as exc:
                            st.warning(str(exc))
                        else:
                            st.rerun()
                    else:
                        st.session_state["bv_agent_review_decisions"] = {
                            **stored_agent_review_decisions,
                            selected_agent_review_item: {
                                "decision": "rejected",
                                "comment": agent_review_comment,
                            },
                        }
                        st.rerun()
        else:
            st.caption(
                "No pending agent outputs require engineer review."
                if ui_language == "en"
                else "当前没有待工程师复核的 Agent 产物。"
            )
        st.markdown(
            "##### Agent Application Authorization Ledger"
            if ui_language == "en"
            else "Agent 应用授权记录"
        )
        agent_application_authorization_rows = (
            build_agent_application_authorization_rows(
                reviewed_workflow_state,
                ui_language,
            )
        )
        if agent_application_authorization_rows:
            st.dataframe(
                agent_application_authorization_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption(
                "No agent application authorizations have been recorded in this session."
                if ui_language == "en"
                else "当前会话尚未记录 Agent 应用授权。"
            )
        st.markdown(
            "##### Engineer Review Decision Ledger"
            if ui_language == "en"
            else "工程师复核决策记录"
        )
        engineer_review_decision_rows = build_agent_engineer_review_decision_rows(
            reviewed_workflow_state,
            ui_language,
        )
        if engineer_review_decision_rows:
            st.dataframe(
                engineer_review_decision_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption(
                "No engineer review decisions have been recorded in this session."
                if ui_language == "en"
                else "当前会话尚未记录工程师复核决策。"
            )
        with st.expander(
            "Local Agent Event Trace" if ui_language == "en" else "本地 Agent 事件追踪",
            expanded=False,
        ):
            st.dataframe(
                build_agent_workflow_event_rows(reviewed_workflow_state, ui_language),
                hide_index=True,
                use_container_width=True,
            )

        overview_col, risk_col = st.columns([1.0, 1.0])
        with overview_col:
            render_bv_section(
                st,
                translate(ui_language, "bv_review_basis_heading"),
                build_bv_basis_items(effective_bv_result, ui_language),
                limit=4,
            )
            render_bv_section(
                st,
                translate(ui_language, "bv_review_path_heading"),
                build_bv_path_items(effective_bv_result, ui_language),
                limit=5,
            )
        with risk_col:
            render_bv_section(
                st,
                translate(ui_language, "bv_review_risk_heading"),
                build_bv_risk_items(effective_bv_result, ui_language),
                limit=6,
            )
            render_bv_section(
                st,
                translate(ui_language, "bv_review_plan_heading"),
                build_bv_plan_items(effective_bv_result, ui_language),
                limit=5,
            )

        st.markdown(f'#### {translate(ui_language, "report_draft_gate_heading")}')
        gate_panel_text = build_bv_gate_panel_text(ui_language)
        st.markdown(f"##### {gate_panel_text.quality_gate_heading}")
        st.dataframe(
            build_quality_gate_status_rows(
                effective_bv_intake,
                has_review_basis=bool(effective_bv_result.basis_references),
                calculation_gate_locked=reviewed_workflow_state.is_gate_locked(
                    "calculation"
                ),
                report_gate=report_draft_gate,
                language=ui_language,
            ),
            hide_index=True,
            use_container_width=True,
        )
        render_bv_report_gate_status(
            st,
            report_draft_gate,
            ui_language,
            ready_message=translate(ui_language, "report_draft_gate_ready"),
            blocked_message=translate(ui_language, "report_draft_gate_blocked"),
        )
        foundation_evidence_rows = build_foundation_evidence_display_rows(
            reviewed_workflow_state,
            ui_language,
        )
        evidence_table_text = build_bv_evidence_table_text(ui_language)
        st.markdown(f"##### {evidence_table_text.foundation_heading}")
        if foundation_evidence_rows:
            st.dataframe(
                foundation_evidence_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption(evidence_table_text.foundation_empty_caption)
        report_gate_evidence_rows = build_report_gate_evidence_rows(
            report_draft_gate,
            ui_language,
        )
        st.markdown(f"##### {evidence_table_text.report_gate_heading}")
        if report_gate_evidence_rows:
            st.dataframe(
                report_gate_evidence_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption(evidence_table_text.report_gate_empty_caption)
        evidence_matrix_rows = build_evidence_matrix_rows(
            reviewed_workflow_state,
            ui_language,
            report_risks=effective_bv_result.risks,
        )
        st.markdown(f"##### {evidence_table_text.evidence_matrix_heading}")
        if evidence_matrix_rows:
            st.dataframe(
                evidence_matrix_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption(evidence_table_text.evidence_matrix_empty_caption)
        closed_rfi_recheck_rows = build_closed_rfi_incremental_recheck_rows(
            reviewed_workflow_state,
            ui_language,
        )
        st.markdown(f"##### {evidence_table_text.closed_rfi_heading}")
        if closed_rfi_recheck_rows:
            st.dataframe(
                closed_rfi_recheck_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption(evidence_table_text.closed_rfi_empty_caption)

        if persisted_workflow_is_active and reviewed_workflow_state.rfi_items:
            persisted_rfi_register_heading = (
                "Persisted RFI Register"
                if ui_language == "en"
                else "持久化 RFI 台账"
            )
            st.markdown(f"##### {persisted_rfi_register_heading}")
            rfi_status_labels = {
                "open": "Open" if ui_language == "en" else "待回复",
                "responded": "Responded" if ui_language == "en" else "已回复",
                "closed": "Closed" if ui_language == "en" else "已关闭",
                "reopened": "Reopened" if ui_language == "en" else "重新打开",
            }
            st.dataframe(
                [
                    (
                        {
                            "RFI ID": item.rfi_id,
                            "问题": item.question,
                            "责任方": item.responsible_party,
                            "状态": rfi_status_labels[item.status],
                            "客户回复": item.client_response or "",
                            "待复核项": ", ".join(item.reopen_review_items),
                            "已完成复核": ", ".join(item.completed_recheck_items),
                        }
                        if ui_language == "zh"
                        else {
                            "RFI ID": item.rfi_id,
                            "Question": item.question,
                            "Responsible Party": item.responsible_party,
                            "Status": rfi_status_labels[item.status],
                            "Client Response": item.client_response or "",
                            "Pending Recheck Items": ", ".join(
                                item.reopen_review_items
                            ),
                            "Completed Recheck Items": ", ".join(
                                item.completed_recheck_items
                            ),
                        }
                    )
                    for item in reviewed_workflow_state.rfi_items
                ],
                hide_index=True,
                use_container_width=True,
            )
            actionable_rfi_items = [
                item
                for item in reviewed_workflow_state.rfi_items
                if item.status in {"open", "reopened", "responded"}
            ]
            if actionable_rfi_items:
                selected_persisted_rfi_id = st.selectbox(
                    "RFI ID",
                    [item.rfi_id for item in actionable_rfi_items],
                    key="bv_persisted_rfi_id",
                )
                selected_persisted_rfi = next(
                    item
                    for item in actionable_rfi_items
                    if item.rfi_id == selected_persisted_rfi_id
                )
                persisted_rfi_client_response_key = (
                    f"bv_persisted_rfi_client_response_{selected_persisted_rfi_id}"
                )
                persisted_rfi_closeout_note_key = (
                    f"bv_persisted_rfi_closeout_note_{selected_persisted_rfi_id}"
                )
                persisted_rfi_client_response = st.text_area(
                    "RFI Client Response"
                    if ui_language == "en"
                    else "RFI 客户回复",
                    value=selected_persisted_rfi.client_response or "",
                    key=persisted_rfi_client_response_key,
                    height=80,
                )
                persisted_rfi_closeout_note = st.text_area(
                    "RFI Closeout Note"
                    if ui_language == "en"
                    else "RFI 关闭备注",
                    value=(
                        "Engineer reviewed the client response and closed the RFI."
                        if ui_language == "en"
                        else "工程师已复核客户回复并关闭该 RFI。"
                    ),
                    key=persisted_rfi_closeout_note_key,
                    height=80,
                )
                recheck_required = selected_persisted_rfi.triggers_incremental_recheck
                recheck_complete = (
                    bool(selected_persisted_rfi.reopen_review_items)
                    and set(selected_persisted_rfi.completed_recheck_items)
                    == set(selected_persisted_rfi.reopen_review_items)
                )
                if (
                    selected_persisted_rfi.status == "responded"
                    and recheck_required
                    and not recheck_complete
                ):
                    st.caption(
                        "Run deterministic incremental recheck before closing this RFI."
                        if ui_language == "en"
                        else "关闭该 RFI 前，需要先运行确定性增量复核。"
                    )
                response_col, recheck_col, closeout_col = st.columns(3)
                with response_col:
                    response_disabled = selected_persisted_rfi.status not in {
                        "open",
                        "reopened",
                    }
                    if st.button(
                        "Record RFI Client Response"
                        if ui_language == "en"
                        else "记录 RFI 客户回复",
                        key="bv_record_persisted_rfi_client_response",
                        use_container_width=True,
                        disabled=response_disabled,
                    ):
                        try:
                            record_persisted_rfi_client_response(
                                st.session_state,
                                persisted_repository,
                                project_id=active_persisted_project_id,
                                rfi_id=selected_persisted_rfi_id,
                                client_response=persisted_rfi_client_response,
                            )
                        except ValueError as exc:
                            st.warning(str(exc))
                        else:
                            st.success(
                                "RFI client response recorded."
                                if ui_language == "en"
                                else "已记录 RFI 客户回复。"
                            )
                            st.rerun()
                with recheck_col:
                    recheck_disabled = (
                        selected_persisted_rfi.status != "responded"
                        or not recheck_required
                        or recheck_complete
                    )
                    if st.button(
                        "Run Deterministic Recheck"
                        if ui_language == "en"
                        else "运行确定性增量复核",
                        key="bv_run_persisted_rfi_incremental_recheck",
                        use_container_width=True,
                        disabled=recheck_disabled,
                    ):
                        try:
                            rechecked_state = run_persisted_rfi_incremental_calculation_recheck(
                                st.session_state,
                                persisted_repository,
                                project_id=active_persisted_project_id,
                                rfi_id=selected_persisted_rfi_id,
                            )
                        except ValueError as exc:
                            st.warning(str(exc))
                        else:
                            rechecked_rfi = next(
                                item
                                for item in rechecked_state.rfi_items
                                if item.rfi_id == selected_persisted_rfi_id
                            )
                            rechecked_complete = set(
                                rechecked_rfi.completed_recheck_items
                            ) == set(rechecked_rfi.reopen_review_items)
                            if rechecked_complete:
                                st.success(
                                    "Deterministic incremental recheck completed and saved."
                                    if ui_language == "en"
                                    else "确定性增量复核已完成并保存。"
                                )
                            else:
                                st.warning(
                                    "Deterministic recheck was saved but remains blocked; correct the inputs and rerun."
                                    if ui_language == "en"
                                    else "确定性复核已保存但仍处于阻塞状态；请修正输入后重新运行。"
                                )
                            st.rerun()
                with closeout_col:
                    closeout_disabled = selected_persisted_rfi.status != "responded" or (
                        recheck_required and not recheck_complete
                    )
                    if st.button(
                        "Close RFI After Engineer Review"
                        if ui_language == "en"
                        else "工程师复核后关闭 RFI",
                        key="bv_close_persisted_rfi_after_engineer_review",
                        use_container_width=True,
                        disabled=closeout_disabled,
                    ):
                        try:
                            close_persisted_rfi_after_engineer_review(
                                st.session_state,
                                persisted_repository,
                                project_id=active_persisted_project_id,
                                rfi_id=selected_persisted_rfi_id,
                                closeout_note=persisted_rfi_closeout_note,
                                completed_recheck_item_ids=(
                                    selected_persisted_rfi.completed_recheck_items
                                    if recheck_required
                                    else None
                                ),
                            )
                        except ValueError as exc:
                            st.warning(str(exc))
                        else:
                            st.success(
                                "RFI closed after engineer review."
                                if ui_language == "en"
                                else "工程师复核后已关闭 RFI。"
                            )
                            st.rerun()
            else:
                st.caption(
                    "No persisted RFI items are waiting for response or closeout."
                    if ui_language == "en"
                    else "当前没有等待回复或关闭的持久化 RFI。"
                )

        service_scope_recommendations = build_service_scope_recommendations(
            effective_bv_intake,
            effective_bv_result,
            project_state=reviewed_workflow_state,
        )
        if service_scope_recommendations:
            service_scope_heading = (
                "BV Service Scope Recommendations"
                if ui_language == "en"
                else "BV 服务范围建议"
            )
            st.markdown(f"##### {service_scope_heading}")
            st.dataframe(
                build_service_scope_display_rows(
                    service_scope_recommendations,
                    ui_language,
                ),
                hide_index=True,
                use_container_width=True,
            )

        bv_markdown_filename = build_bv_report_filename(effective_bv_intake.project_type)
        bv_word_filename = bv_markdown_filename.replace(".md", ".docx")
        bv_pdf_filename = bv_markdown_filename.replace(".md", ".pdf")

        st.markdown("#### Design Review Report Preview" if ui_language == "en" else "设计审查报告预览")
        report_draft_ready = report_draft_gate.status == "ready"
        if report_draft_ready:
            bv_report_preview = build_bv_report_preview(
                effective_bv_intake,
                effective_bv_result,
                project_state=reviewed_workflow_state,
            )
            bv_markdown_payload = build_bv_markdown_report(
                effective_bv_intake,
                effective_bv_result,
                project_state=reviewed_workflow_state,
            )
            bv_docx_payload = build_docx_report_bytes(bv_report_preview)
            bv_pdf_payload = build_pdf_report_bytes(bv_report_preview)

            st.markdown(
                "##### Report Revision History"
                if ui_language == "en"
                else "报告修订历史"
            )
            if reviewed_workflow_state.report_revisions:
                st.dataframe(
                    build_report_revision_history_rows(
                        reviewed_workflow_state,
                        ui_language,
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption(
                    "No report revision snapshots have been recorded."
                    if ui_language == "en"
                    else "当前尚未记录报告修订快照。"
                )

            report_gate_approved = reviewed_workflow_state.is_gate_locked("report")
            report_gate_col, report_revision_col = st.columns(2)
            with report_gate_col:
                if report_gate_approved:
                    st.success(
                        "Report gate approved by engineer."
                        if ui_language == "en"
                        else "报告门禁已由工程师批准。"
                    )
                elif st.button(
                    "Approve Report Gate"
                    if ui_language == "en"
                    else "批准报告门禁",
                    key="bv_approve_report_gate",
                    use_container_width=True,
                ):
                    report_reviewer = (
                        "demo-review-engineer"
                        if ui_language == "en"
                        else "演示审核工程师"
                    )
                    report_gate_approval = build_engineer_approval(
                        approval_id=(
                            "report-gate-approval-"
                            f"{len(reviewed_workflow_state.report_revisions) + 1:03d}"
                        ),
                        target_id="report",
                        reviewer=report_reviewer,
                        comment=(
                            "Report gate approved in Streamlit workbench."
                            if ui_language == "en"
                            else "已在 Streamlit 工作台批准报告门禁。"
                        ),
                    )
                    updated_workflow_state = reviewed_workflow_state.model_copy(
                        update={
                            "approvals": [
                                *reviewed_workflow_state.approvals,
                                report_gate_approval,
                            ]
                        }
                    )
                    if persisted_workflow_is_active:
                        persisted_repository.save(updated_workflow_state)
                        store_persisted_workflow_state(
                            st.session_state,
                            updated_workflow_state,
                        )
                    else:
                        st.session_state["bv_report_gate_approved"] = True
                    st.rerun()
            with report_revision_col:
                report_revision_note = st.text_input(
                    "Report Revision Note"
                    if ui_language == "en"
                    else "报告修订备注",
                    value=(
                        "Recorded after report gate evidence review."
                        if ui_language == "en"
                        else "已复核报告门禁证据后记录。"
                    ),
                    key="bv_report_revision_note",
                )
                if st.button(
                    "Record Report Revision Snapshot"
                    if ui_language == "en"
                    else "记录报告修订快照",
                    key="bv_record_report_revision_snapshot",
                    use_container_width=True,
                    disabled=not report_gate_approved,
                ):
                    revision_id = (
                        "report-rev-"
                        f"{len(reviewed_workflow_state.report_revisions) + 1:03d}"
                    )
                    report_reviewer = (
                        "demo-review-engineer"
                        if ui_language == "en"
                        else "演示审核工程师"
                    )
                    try:
                        if persisted_workflow_is_active:
                            updated_workflow_state = record_persisted_report_revision(
                                st.session_state,
                                persisted_repository,
                                project_id=active_persisted_project_id,
                                revision_id=revision_id,
                                report_preview=bv_report_preview,
                                gate_result=report_draft_gate,
                                reviewer=report_reviewer,
                                note=report_revision_note,
                                created_at=datetime.now(timezone.utc).isoformat(),
                            )
                        else:
                            updated_workflow_state = record_report_revision(
                                reviewed_workflow_state,
                                revision_id=revision_id,
                                report_preview=bv_report_preview,
                                gate_result=report_draft_gate,
                                reviewer=report_reviewer,
                                note=report_revision_note,
                                created_at=datetime.now(timezone.utc).isoformat(),
                            )
                            st.session_state["bv_report_revisions"] = (
                                updated_workflow_state.report_revisions
                            )
                        st.success(
                            f"Recorded {revision_id}."
                            if ui_language == "en"
                            else f"已记录 {revision_id}。"
                        )
                        st.rerun()
                    except ValueError as exc:
                        st.warning(str(exc))

            bv_export_col_1, bv_export_col_2, bv_export_col_3 = st.columns(3)
            with bv_export_col_1:
                bv_markdown_download = st.download_button(
                    translate(ui_language, "download_text_report"),
                    data=bv_markdown_payload,
                    file_name=bv_markdown_filename,
                    mime="text/markdown",
                    use_container_width=True,
                )
            with bv_export_col_2:
                bv_word_download = st.download_button(
                    translate(ui_language, "download_word_report"),
                    data=bv_docx_payload,
                    file_name=bv_word_filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            with bv_export_col_3:
                bv_pdf_download = st.download_button(
                    translate(ui_language, "download_pdf_report"),
                    data=bv_pdf_payload,
                    file_name=bv_pdf_filename,
                    mime="application/pdf",
                    use_container_width=True,
                )
            for section in build_bv_report_preview_sections(
                effective_bv_intake,
                effective_bv_result,
                ui_language,
            ):
                with st.container(border=True):
                    st.markdown(f"**{section.heading}**")
                    for item in section.items[:4]:
                        st.write(item)

with assessment_tab:
    metric_columns = st.columns(min(3, max(len(view.assessment_metric_cards), 1)))
    for index, card in enumerate(view.assessment_metric_cards[:3]):
        with metric_columns[index]:
            _render_card(card)

    st.subheader(translate(ui_language, "preliminary_structural_conclusion"))
    if view.conclusion_overview_card is not None:
        _render_card(view.conclusion_overview_card)

    calc_col, evidence_col = st.columns([1.3, 1.0])
    with calc_col:
        st.subheader(translate(ui_language, "critical_calculation_results"))
        _render_key_calculation_cards(view.calc_summary_cards, ui_language, limit=3)
        if len(view.calc_summary_cards) > 3:
            with st.expander(translate(ui_language, "detailed_calculation_results")):
                _render_key_calculation_cards(view.calc_summary_cards[3:], ui_language)
    with evidence_col:
        st.subheader(translate(ui_language, "evidence_status"))
        _render_cards(view.evidence_overview_cards, limit=1)
        _render_cards(view.evidence_status_cards, limit=3)
        if len(view.evidence_status_cards) > 3:
            with st.expander(translate(ui_language, "detailed_evidence_status")):
                _render_cards(view.evidence_status_cards[3:])

    if view.load_combination_sensitivity_cards:
        st.subheader(translate(ui_language, "load_combination_sensitivity"))
        _render_cards(view.load_combination_sensitivity_cards)

    if view.next_step_cards:
        st.subheader(translate(ui_language, "next_step_review_actions"))
        _render_cards(view.next_step_cards, limit=4)

with basis_tab:
    basis_col, trace_col = st.columns([1.0, 1.2])
    with basis_col:
        st.subheader(translate(ui_language, "basis_references"))
        _render_cards(view.basis_reference_cards)
    with trace_col:
        st.subheader(translate(ui_language, "traceability_basis"))
        _render_cards(view.traceability_cards)

with export_tab:
    st.subheader(translate(ui_language, "report_export_tab"))
    st.caption(translate(ui_language, "report_export_note"))
    export_col_1, export_col_2, export_col_3 = st.columns(3)
    with export_col_1:
        st.download_button(
            translate(ui_language, "download_bilingual_report"),
            data=evaluation["report"],
            file_name=report_filename,
            mime="text/markdown",
            use_container_width=True,
        )
    with export_col_2:
        st.download_button(
            translate(ui_language, "download_word_report"),
            data=build_docx_report_bytes(report_preview),
            file_name=report_docx_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with export_col_3:
        st.download_button(
            translate(ui_language, "download_pdf_report"),
            data=build_pdf_report_bytes(report_preview),
            file_name=report_pdf_filename,
            mime="application/pdf",
            use_container_width=True,
        )
    st.markdown(f"### {translate(ui_language, 'export_overview')}")
    preview_sections = report_preview.sections[:4]
    for section in preview_sections:
        with st.container(border=True):
            st.markdown(f"**{section.heading}**")
            for item in section.items[:4]:
                st.write(item)

with pv_3d_tab:
    st.subheader(translate(ui_language, "pv_3d_studio_heading"))
    st.caption(translate(ui_language, "pv_3d_studio_boundary"))
    components.html(
        build_pv_3d_studio_html(ui_language),
        height=920,
        scrolling=True,
    )

with extension_tab:
    st.subheader(translate(ui_language, "calculation_extension_tab"))
    st.caption(translate(ui_language, "extension_overview"))
    photo_assist = build_photo_assist_interface(ui_language)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("计算简图" if ui_language == "zh" else "Calculation Sketch")
        st.caption(
            "后续在此接入门架简图、控制构件标识和荷载示意。"
            if ui_language == "zh"
            else "Future slot for portal-frame sketches, controlling-member markers, and load diagrams."
        )
    with col2:
        st.info("Midas / SAP")
        st.caption(
            "后续在此接入外部结构分析软件调用接口。"
            if ui_language == "zh"
            else "Future slot for external structural analysis integrations."
        )
    with col3:
        st.info("IO Boundary" if ui_language == "en" else "输入输出边界")
        st.caption(
            "后续在此明确外部计算输入、输出和结果回填边界。"
            if ui_language == "zh"
            else "Future slot for external calculation input/output boundaries and result ingestion."
        )
    st.markdown(f"### {translate(ui_language, 'photo_assist_entry')}")
    st.caption(translate(ui_language, "photo_assist_upload_hint"))
    uploaded_photos = st.file_uploader(
        translate(ui_language, "photo_assist_entry"),
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    st.caption(photo_assist.intro)
    if uploaded_photos:
        st.caption(f"{translate(ui_language, 'photo_assist_received')}: {len(uploaded_photos)}")
    photo_assist_targets_heading = translate(ui_language, "photo_assist_targets")
    photo_assist_backfill_heading = translate(ui_language, "photo_assist_backfill_boundary")
    st.markdown(f"#### {photo_assist_targets_heading}")
    for item in photo_assist.targets:
        _render_card(
            ContentCard(
                title=item.title,
                detail=(
                    f"{item.detail}\n"
                    f"{translate(ui_language, 'candidate_backfill_fields')}: "
                    f"{', '.join(item.candidate_backfill_fields)}"
                ),
                tone="blue",
            )
        )
    st.markdown(f"#### {photo_assist_backfill_heading}")
    for note in photo_assist.boundary_notes:
        st.write(f"- {note}")
