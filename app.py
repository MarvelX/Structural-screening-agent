from copy import deepcopy
from pathlib import Path
from typing import Optional

import streamlit as st
from pydantic import ValidationError

from structural_screening_agent.app_state import (
    default_package_options,
    demo_case_catalog,
    demo_case_options,
    evaluate_case,
    ordered_demo_keys,
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
from structural_screening_agent.report_export import build_docx_report_bytes, build_pdf_report_bytes
from structural_screening_agent.report_generator import build_report_filename, build_report_preview


st.set_page_config(page_title="Portal-Frame Rooftop PV Screening", layout="wide")

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


st.title(translate(ui_language, "portal_frame_screening_title"))
st.caption(translate(ui_language, "portal_frame_screening_subtitle"))

assessment_tab, input_tab, basis_tab, export_tab, extension_tab = st.tabs(
    [
        translate(ui_language, "assessment_tab"),
        translate(ui_language, "project_input_tab"),
        translate(ui_language, "basis_traceability_tab"),
        translate(ui_language, "report_export_tab"),
        translate(ui_language, "calculation_extension_tab"),
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
