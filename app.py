from copy import deepcopy
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
    build_bv_review_intake,
    default_bv_review_intake,
)
from structural_screening_agent.bv_review.models import BVReportSection
from structural_screening_agent.bv_review.report import build_bv_markdown_report, build_bv_report_filename
from structural_screening_agent.bv_review.workflow import evaluate_bv_review
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


def _label(label_map: dict[str, dict[str, str]], value: str, language: Language) -> str:
    return label_map.get(value, {}).get(language, value)


def _render_bv_section(title: str, items: list[str], limit: Optional[int] = None) -> None:
    st.markdown(f"#### {title}")
    visible_items = items if limit is None else items[:limit]
    for item in visible_items:
        st.write(f"- {item}")


def _bv_object_labels(values: list[str], language: Language) -> str:
    return ", ".join(_label(BV_REVIEW_OBJECT_LABELS, value, language) for value in values)


def _bv_basis_items(bv_result, language: Language) -> list[str]:
    if language == "zh":
        return [f"{item.title}: {'; '.join(item.review_actions)}" for item in bv_result.basis_references]
    return [
        f"{item.basis_id}: {item.source_type}; objects: {_bv_object_labels(item.review_objects, language)}"
        for item in bv_result.basis_references
    ]


def _bv_path_items(bv_result, language: Language) -> list[str]:
    if language == "zh":
        return [f"{item.title}: {item.status} | {item.method}" for item in bv_result.review_paths]
    return [
        f"{_label(BV_REVIEW_OBJECT_LABELS, item.review_object, language)}: {item.status}; deliverables: {len(item.deliverables)}"
        for item in bv_result.review_paths
    ]


def _bv_risk_items(bv_result, language: Language) -> list[str]:
    if language == "zh":
        return [f"{item.severity} | {item.title}: {item.recommendation}" for item in bv_result.risks]
    return [
        f"{item.severity} | {item.category}: {item.risk_id}; blocks report: {item.blocks_report_issue}"
        for item in bv_result.risks
    ]


def _bv_plan_items(bv_result, language: Language) -> list[str]:
    if language == "zh":
        return [f"{item.phase}: {item.method} | {item.deliverable}" for item in bv_result.review_plan]
    return [f"{item.phase}: {item.responsible_role}; item: {item.item_id}" for item in bv_result.review_plan]


def _bv_report_preview_sections(bv_intake, bv_result, language: Language) -> list[BVReportSection]:
    if language == "zh" and bv_result.report_preview is not None:
        return bv_result.report_preview.sections[:4]

    blockers = [item for item in bv_result.risks if item.blocks_report_issue]
    return [
        BVReportSection(
            heading="Project and Review Scope",
            items=[
                f"Project name: {bv_intake.project_name}",
                f"Country / region: {bv_intake.country_or_region}",
                f"Design stage: {bv_intake.design_stage}",
                f"Decision: {bv_result.decision}",
            ],
        ),
        BVReportSection(
            heading="Review Basis",
            items=_bv_basis_items(bv_result, language)[:4],
        ),
        BVReportSection(
            heading="Document Completeness",
            items=[f"{item.document_key}: {item.status}" for item in bv_result.checklist_items[:4]],
        ),
        BVReportSection(
            heading="Findings",
            items=[
                f"Blocking items: {len(blockers)}",
                f"Risks and nonconformities: {len(bv_result.risks)}",
                f"Review plan items: {len(bv_result.review_plan)}",
            ],
        ),
    ]


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
            format_func=lambda value: _label(BV_PROJECT_TYPE_LABELS, value, ui_language),
            key="bv_project_type",
        )
        bv_design_stage = st.selectbox(
            "Design Stage" if ui_language == "en" else "设计阶段",
            list(BV_DESIGN_STAGE_LABELS),
            index=list(BV_DESIGN_STAGE_LABELS).index(default_bv_intake.design_stage),
            format_func=lambda value: _label(BV_DESIGN_STAGE_LABELS, value, ui_language),
            key="bv_design_stage",
        )
    with bv_col_2:
        bv_standards = st.multiselect(
            "Standards Systems" if ui_language == "en" else "标准体系",
            list(BV_STANDARD_LABELS),
            default=list(default_bv_intake.standards_systems),
            format_func=lambda value: _label(BV_STANDARD_LABELS, value, ui_language),
            key="bv_standards",
        )
        bv_review_objects = st.multiselect(
            "Review Objects" if ui_language == "en" else "审核对象",
            list(BV_REVIEW_OBJECT_LABELS),
            default=list(default_bv_intake.review_objects),
            format_func=lambda value: _label(BV_REVIEW_OBJECT_LABELS, value, ui_language),
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
                format_func=lambda value: _label(BV_DOCUMENT_STATUS_LABELS, value, ui_language),
                key=f"bv_doc_{document_key}",
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
        blockers = [item for item in bv_result.risks if item.blocks_report_issue]

        metric_1, metric_2, metric_3 = st.columns(3)
        metric_1.metric("Decision" if ui_language == "en" else "审核结论", bv_result.decision)
        metric_2.metric("Blocking Items" if ui_language == "en" else "阻塞项", len(blockers))
        metric_3.metric("Review Paths" if ui_language == "en" else "审核路径", len(bv_result.review_paths))

        overview_col, risk_col = st.columns([1.0, 1.0])
        with overview_col:
            _render_bv_section(
                translate(ui_language, "bv_review_basis_heading"),
                _bv_basis_items(bv_result, ui_language),
                limit=4,
            )
            _render_bv_section(
                translate(ui_language, "bv_review_path_heading"),
                _bv_path_items(bv_result, ui_language),
                limit=5,
            )
        with risk_col:
            _render_bv_section(
                translate(ui_language, "bv_review_risk_heading"),
                _bv_risk_items(bv_result, ui_language),
                limit=6,
            )
            _render_bv_section(
                translate(ui_language, "bv_review_plan_heading"),
                _bv_plan_items(bv_result, ui_language),
                limit=5,
            )

        bv_report_preview = bv_result.report_preview
        bv_markdown_payload = build_bv_markdown_report(bv_intake, bv_result)
        bv_markdown_filename = build_bv_report_filename(bv_intake.project_type)
        bv_word_filename = bv_markdown_filename.replace(".md", ".docx")
        bv_pdf_filename = bv_markdown_filename.replace(".md", ".pdf")
        bv_docx_payload = build_docx_report_bytes(bv_report_preview)
        bv_pdf_payload = build_pdf_report_bytes(bv_report_preview)

        st.markdown("#### Design Review Report Preview" if ui_language == "en" else "设计审查报告预览")
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
        for section in _bv_report_preview_sections(bv_intake, bv_result, ui_language):
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
