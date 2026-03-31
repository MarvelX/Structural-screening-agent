from copy import deepcopy

import streamlit as st

from structural_screening_agent.app_state import (
    default_form_values,
    demo_case_catalog,
    demo_case_options,
    evaluate_case,
    ordered_demo_keys,
)
from structural_screening_agent.localization import (
    Language,
    canonicalize_preset_text,
    language_label,
    localize_preset_text,
    translate,
    translate_option,
)
from structural_screening_agent.presentation import build_workbench_view
from structural_screening_agent.report_generator import build_report_filename, build_report_preview

st.set_page_config(page_title="Structural Screening Agent", layout="wide")

demo_cases = demo_case_options()

if "selected_demo_key" not in st.session_state:
    st.session_state.selected_demo_key = "main_warehouse_pv"
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
selected_demo_key = st.sidebar.selectbox(
    translate(ui_language, "demo_scenario"),
    ordered_demo_keys(),
    format_func=lambda key: demo_catalog[key]["label"],
    key="selected_demo_key",
)
defaults = deepcopy(demo_cases[selected_demo_key].model_dump())
selected_demo = demo_catalog[selected_demo_key]

st.title(translate(ui_language, "app_title"))
st.caption(
    "用于既有建筑改造前期结构筛查与方案预判的决策工作台。"
    if ui_language == "zh"
    else "A decision workbench for early-stage structural screening and path selection in retrofit projects."
)

with st.sidebar:
    st.subheader(translate(ui_language, "project_intake"))
    st.caption(selected_demo["label"])
    st.caption(selected_demo["note"])
    st.markdown(f"**{translate(ui_language, 'input_group_project_basics')}**")
    project_type = st.selectbox(
        translate(ui_language, "project_type"),
        ["rooftop_pv", "load_upgrade", "retrofit", "mixed"],
        index=["rooftop_pv", "load_upgrade", "retrofit", "mixed"].index(defaults["project_type"]),
        format_func=lambda value: translate_option(ui_language, "project_type", value),
    )
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
    building_span_m = defaults.get("building_span_m")
    column_spacing_m = defaults.get("column_spacing_m")
    purlin_type = defaults.get("purlin_type")
    roof_panel_type = defaults.get("roof_panel_type")
    roof_panel_thickness_mm_raw = (
        "" if defaults["roof_panel_thickness_mm"] is None else str(defaults["roof_panel_thickness_mm"])
    )
    roof_rib_height_mm_raw = "" if defaults["roof_rib_height_mm"] is None else str(defaults["roof_rib_height_mm"])
    roof_attachment_preference = defaults.get("roof_attachment_preference", "undecided")
    existing_member_schedule_status = defaults.get("existing_member_schedule_status", "missing")
    connection_detail_status = defaults.get("connection_detail_status", "missing")
    roof_vendor_data_status = defaults.get("roof_vendor_data_status", "missing")
    corrosion_condition = defaults.get("corrosion_condition", "unknown")
    waterproofing_sensitivity = defaults.get("waterproofing_sensitivity", "medium")
    restricted_installation_zones = defaults.get("restricted_installation_zones") or ""
    available_verification_path = defaults.get("available_verification_path", "drawings_only")

    if project_type == "rooftop_pv":
        st.markdown(f"**{translate(ui_language, 'main_case_screening_inputs')}**")
        building_span_m = st.number_input(
            translate(ui_language, "building_span"),
            min_value=0.0,
            value=float(building_span_m or 0.0),
            step=0.5,
            format="%.1f",
        )
        column_spacing_m = st.number_input(
            translate(ui_language, "column_spacing"),
            min_value=0.0,
            value=float(column_spacing_m or 0.0),
            step=0.5,
            format="%.1f",
        )
        purlin_type = st.selectbox(
            translate(ui_language, "purlin_type"),
            ["cold_formed_z", "cold_formed_c", "hot_rolled", "unknown"],
            index=["cold_formed_z", "cold_formed_c", "hot_rolled", "unknown"].index(purlin_type or "unknown"),
            format_func=lambda value: translate_option(ui_language, "purlin_type", value),
        )
        roof_panel_type = st.selectbox(
            translate(ui_language, "roof_panel_type"),
            ["profiled_sheet", "sandwich_panel", "standing_seam", "unknown"],
            index=["profiled_sheet", "sandwich_panel", "standing_seam", "unknown"].index(
                roof_panel_type or "unknown"
            ),
            format_func=lambda value: translate_option(ui_language, "roof_panel_type", value),
        )
        st.markdown(f"**{translate(ui_language, 'input_group_structural_evidence')}**")
        existing_member_schedule_status = st.selectbox(
            translate(ui_language, "existing_member_schedule_status"),
            ["available", "partial", "missing"],
            index=["available", "partial", "missing"].index(existing_member_schedule_status),
            format_func=lambda value: translate_option(ui_language, "document_status", value),
        )
        corrosion_condition = st.selectbox(
            translate(ui_language, "corrosion_condition"),
            ["low", "moderate", "high", "unknown"],
            index=["low", "moderate", "high", "unknown"].index(corrosion_condition),
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
        st.markdown(f"**{translate(ui_language, 'input_group_roof_connection')}**")
        if roof_panel_type == "profiled_sheet":
            roof_panel_thickness_mm_raw = st.text_input(
                translate(ui_language, "roof_panel_thickness"),
                value=roof_panel_thickness_mm_raw,
            )
            roof_rib_height_mm_raw = st.text_input(
                translate(ui_language, "roof_rib_height"),
                value=roof_rib_height_mm_raw,
            )
        roof_attachment_preference = st.selectbox(
            translate(ui_language, "attachment_preference"),
            ["clamp_based", "penetrating", "undecided"],
            index=["clamp_based", "penetrating", "undecided"].index(roof_attachment_preference),
            format_func=lambda value: translate_option(ui_language, "roof_attachment_preference", value),
        )
        connection_detail_status = st.selectbox(
            translate(ui_language, "connection_detail_status"),
            ["available", "partial", "missing"],
            index=["available", "partial", "missing"].index(connection_detail_status),
            format_func=lambda value: translate_option(ui_language, "document_status", value),
        )
        roof_vendor_data_status = st.selectbox(
            translate(ui_language, "roof_vendor_data_status"),
            ["available", "partial", "missing"],
            index=["available", "partial", "missing"].index(roof_vendor_data_status),
            format_func=lambda value: translate_option(ui_language, "document_status", value),
        )
        waterproofing_sensitivity = st.selectbox(
            translate(ui_language, "waterproofing_sensitivity"),
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(waterproofing_sensitivity),
            format_func=lambda value: translate_option(ui_language, "waterproofing_sensitivity", value),
        )
        st.markdown(f"**{translate(ui_language, 'input_group_execution_constraints')}**")
        shutdown_constraint = st.selectbox(
            translate(ui_language, "shutdown_constraint"),
            ["none", "limited", "strict"],
            index=["none", "limited", "strict"].index(defaults["shutdown_constraint"]),
            format_func=lambda value: translate_option(ui_language, "shutdown_constraint", value),
        )
        restricted_installation_zones = st.text_area(
            translate(ui_language, "restricted_installation_zones"),
            value=restricted_installation_zones,
            height=90,
        )
        st.markdown(f"**{translate(ui_language, 'input_group_verification_route')}**")
        available_verification_path = st.selectbox(
            translate(ui_language, "verification_path"),
            ["drawings_only", "survey_only", "drawings_plus_survey", "no_viable_path_yet"],
            index=["drawings_only", "survey_only", "drawings_plus_survey", "no_viable_path_yet"].index(
                available_verification_path
            ),
            format_func=lambda value: translate_option(ui_language, "available_verification_path", value),
        )
    else:
        st.markdown(f"**{translate(ui_language, 'input_group_execution_constraints')}**")
        shutdown_constraint = st.selectbox(
            translate(ui_language, "shutdown_constraint"),
            ["none", "limited", "strict"],
            index=["none", "limited", "strict"].index(defaults["shutdown_constraint"]),
            format_func=lambda value: translate_option(ui_language, "shutdown_constraint", value),
        )
        st.markdown(f"**{translate(ui_language, 'input_group_structural_evidence')}**")
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

form_data = {
    "project_type": project_type,
    "design_standard_context": design_standard_context,
    "building_type": canonicalize_preset_text("building_type", building_type),
    "structural_system": canonicalize_preset_text("structural_system", structural_system),
    "roof_type": canonicalize_preset_text("roof_type", roof_type),
    "intended_modification": canonicalize_preset_text("modification", intended_modification),
    "estimated_added_load_kpa": estimated_added_load_kpa,
    "building_span_m": building_span_m if project_type == "rooftop_pv" and building_span_m else None,
    "column_spacing_m": column_spacing_m if project_type == "rooftop_pv" and column_spacing_m else None,
    "purlin_type": purlin_type if project_type == "rooftop_pv" else defaults.get("purlin_type"),
    "roof_panel_type": roof_panel_type if project_type == "rooftop_pv" else defaults.get("roof_panel_type"),
    "roof_panel_thickness_mm": float(roof_panel_thickness_mm_raw) if roof_panel_thickness_mm_raw.strip() else None,
    "roof_rib_height_mm": float(roof_rib_height_mm_raw) if roof_rib_height_mm_raw.strip() else None,
    "roof_attachment_preference": (
        roof_attachment_preference if project_type == "rooftop_pv" else defaults.get("roof_attachment_preference")
    ),
    "existing_member_schedule_status": (
        existing_member_schedule_status
        if project_type == "rooftop_pv"
        else defaults.get("existing_member_schedule_status", "missing")
    ),
    "connection_detail_status": (
        connection_detail_status if project_type == "rooftop_pv" else defaults.get("connection_detail_status", "missing")
    ),
    "roof_vendor_data_status": (
        roof_vendor_data_status if project_type == "rooftop_pv" else defaults.get("roof_vendor_data_status", "missing")
    ),
    "corrosion_condition": (
        corrosion_condition if project_type == "rooftop_pv" else defaults.get("corrosion_condition", "unknown")
    ),
    "waterproofing_sensitivity": (
        waterproofing_sensitivity
        if project_type == "rooftop_pv"
        else defaults.get("waterproofing_sensitivity", "medium")
    ),
    "restricted_installation_zones": (
        restricted_installation_zones if project_type == "rooftop_pv" else defaults.get("restricted_installation_zones")
    ),
    "available_verification_path": (
        available_verification_path if project_type == "rooftop_pv" else defaults.get("available_verification_path")
    ),
    "shutdown_constraint": shutdown_constraint,
    "drawing_availability": drawing_availability,
    "survey_available": survey_available,
}

evaluation = evaluate_case(form_data, language=ui_language)
result = evaluation["result"]
explanation = evaluation["explanation"]
view = build_workbench_view(evaluation, language=ui_language)
report_preview = build_report_preview(evaluation["intake"], result, explanation, language=ui_language)
report_filename = build_report_filename(selected_demo_key)

st.markdown(
    """
    <style>
    .ssa-hero {
        padding: 1.4rem 1.5rem;
        border-radius: 20px;
        margin-bottom: 1rem;
        border: 1px solid rgba(15, 23, 42, 0.10);
        background: linear-gradient(135deg, #fff7ed 0%, #ffffff 55%, #f8fafc 100%);
    }
    .ssa-hero.green { background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 55%, #f8fafc 100%); }
    .ssa-hero.red { background: linear-gradient(135deg, #fef2f2 0%, #ffffff 55%, #f8fafc 100%); }
    .ssa-hero-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.25fr) minmax(260px, 0.75fr);
        gap: 1rem;
        align-items: end;
    }
    .ssa-kicker {
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 0.4rem;
    }
    .ssa-decision {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.35rem;
    }
    .ssa-meta {
        font-size: 0.95rem;
        color: #475569;
    }
    .ssa-meta-stack {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        justify-content: flex-end;
        align-content: flex-end;
    }
    .ssa-meta-pill {
        border-radius: 999px;
        padding: 0.45rem 0.75rem;
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(15, 23, 42, 0.08);
        color: #334155;
        font-size: 0.88rem;
        line-height: 1.35;
    }
    .ssa-info-strip {
        display: grid;
        grid-template-columns: 1fr 1.15fr;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .ssa-info-panel {
        border-radius: 18px;
        padding: 1rem 1.1rem;
        border: 1px solid rgba(15, 23, 42, 0.08);
        background: #ffffff;
    }
    .ssa-info-badge {
        display: inline-block;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        font-size: 0.73rem;
        font-weight: 600;
        color: #9a3412;
        background: #ffedd5;
        margin-bottom: 0.55rem;
    }
    .ssa-info-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.35rem;
    }
    .ssa-info-note {
        font-size: 0.93rem;
        color: #475569;
        line-height: 1.55;
    }
    .ssa-flow-step {
        padding: 0.45rem 0;
        border-top: 1px solid rgba(15, 23, 42, 0.08);
        font-size: 0.93rem;
        color: #0f172a;
        line-height: 1.5;
    }
    .ssa-section-title {
        font-size: 0.88rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #64748b;
        margin: 1rem 0 0.6rem 0;
    }
    .ssa-card {
        border-radius: 16px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.7rem;
        border: 1px solid rgba(15, 23, 42, 0.08);
        background: #ffffff;
    }
    .ssa-card.red { background: #fff5f5; }
    .ssa-card.green { background: #f0fdf4; }
    .ssa-card.amber { background: #fff7ed; }
    .ssa-card.blue { background: #eff6ff; }
    .ssa-card-title {
        font-size: 0.98rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .ssa-card-detail {
        font-size: 0.92rem;
        color: #475569;
        line-height: 1.55;
    }
    .ssa-cluster {
        border-radius: 18px;
        padding: 0.95rem 1rem 0.35rem 1rem;
        margin-bottom: 0.9rem;
        border: 1px solid rgba(15, 23, 42, 0.08);
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    }
    .ssa-cluster-head {
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 0.55rem;
    }
    .ssa-list-panel {
        border-radius: 16px;
        border: 1px solid rgba(15, 23, 42, 0.08);
        background: #ffffff;
        overflow: hidden;
        margin-bottom: 0.7rem;
    }
    .ssa-list-item {
        padding: 0.8rem 1rem;
        font-size: 0.94rem;
        color: #0f172a;
        line-height: 1.55;
        border-top: 1px solid rgba(15, 23, 42, 0.08);
    }
    .ssa-list-item:first-child {
        border-top: 0;
    }
    .ssa-option {
        border-radius: 18px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.8rem;
        border: 1px solid rgba(15, 23, 42, 0.08);
        background: #ffffff;
    }
    .ssa-option.primary {
        background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
        border: 1px solid rgba(234, 88, 12, 0.18);
        box-shadow: 0 12px 30px rgba(234, 88, 12, 0.08);
    }
    .ssa-option-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #9a3412;
        margin-bottom: 0.35rem;
    }
    .ssa-option-title {
        font-size: 1rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 0.45rem;
    }
    .ssa-option-detail {
        font-size: 0.9rem;
        color: #334155;
        line-height: 1.5;
        margin-bottom: 0.2rem;
    }
    .ssa-agent {
        border-radius: 20px;
        padding: 1rem 1.1rem;
        background: #0f172a;
        color: #e2e8f0;
        margin-top: 1rem;
    }
    .ssa-agent-meta {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 0.55rem;
    }
    .ssa-agent-summary {
        font-size: 0.98rem;
        line-height: 1.6;
        color: #f8fafc;
    }
    .ssa-agent-notice {
        border-radius: 12px;
        padding: 0.65rem 0.8rem;
        background: rgba(251, 191, 36, 0.12);
        border: 1px solid rgba(251, 191, 36, 0.32);
        color: #fde68a;
        font-size: 0.85rem;
        margin-bottom: 0.7rem;
    }
    .ssa-report {
        margin-top: 1rem;
        border-radius: 20px;
        padding: 1.1rem 1.15rem;
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(15, 23, 42, 0.08);
    }
    .ssa-report-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 0.8rem;
    }
    .ssa-report-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
    }
    .ssa-report-note {
        font-size: 0.84rem;
        color: #64748b;
    }
    .ssa-report-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.8rem;
    }
    .ssa-report-section {
        border-top: 1px solid rgba(15, 23, 42, 0.08);
        padding-top: 0.8rem;
    }
    .ssa-report-heading {
        font-size: 0.82rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 0.45rem;
    }
    .ssa-report-item {
        font-size: 0.93rem;
        color: #0f172a;
        line-height: 1.55;
        margin-bottom: 0.32rem;
    }
    @media (max-width: 960px) {
        .ssa-hero-grid {
            grid-template-columns: 1fr;
        }
        .ssa-meta-stack {
            justify-content: flex-start;
        }
        .ssa-info-strip {
            grid-template-columns: 1fr;
        }
        .ssa-report-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="ssa-hero {view.hero_tone}">
      <div class="ssa-hero-grid">
        <div>
          <div class="ssa-kicker">{translate(ui_language, "app_title")}</div>
          <div class="ssa-decision">{view.hero_decision}</div>
          <div class="ssa-meta">{view.scenario_label}</div>
        </div>
        <div class="ssa-meta-stack">
          <div class="ssa-meta-pill">{view.confidence_label}</div>
          <div class="ssa-meta-pill">{view.standards_context_label}</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

flow_markup = "".join(
    [f'<div class="ssa-flow-step">{index + 1}. {step}</div>' for index, step in enumerate(selected_demo["narrative_steps"])]
)
badge_markup = (
    f'<div class="ssa-info-badge">{translate(ui_language, "featured_demo")}</div>'
    if selected_demo["featured"]
    else ""
)
st.markdown(
    f"""
    <div class="ssa-info-strip">
      <div class="ssa-info-panel">
        {badge_markup}
        <div class="ssa-info-title">{translate(ui_language, "case_brief")}</div>
        <div class="ssa-info-note">{selected_demo["label"]}</div>
        <div class="ssa-info-note">{selected_demo["note"]}</div>
      </div>
      <div class="ssa-info-panel">
        <div class="ssa-section-title" style="margin-top:0;">{translate(ui_language, "demo_flow")}</div>
        {flow_markup or f'<div class="ssa-info-note">{selected_demo["note"]}</div>'}
        <div class="ssa-section-title">{translate(ui_language, "product_scope")}</div>
        <div class="ssa-info-note">{translate(ui_language, "scope_note")}</div>
        <div class="ssa-section-title">{translate(ui_language, "standards_context_note")}</div>
        <div class="ssa-info-note">{translate(ui_language, "standards_note")}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if view.management_summary:
    management_summary_markup = "".join(f'<div class="ssa-list-item">{item}</div>' for item in view.management_summary)
    st.markdown(
        f'<div class="ssa-section-title">{translate(ui_language, "management_summary")}</div><div class="ssa-list-panel">{management_summary_markup}</div>',
        unsafe_allow_html=True,
    )

if view.decision_chain:
    decision_chain_markup = "".join(f'<div class="ssa-list-item">{item}</div>' for item in view.decision_chain)
    st.markdown(
        f'<div class="ssa-section-title">{translate(ui_language, "decision_chain")}</div><div class="ssa-list-panel">{decision_chain_markup}</div>',
        unsafe_allow_html=True,
    )

decision_col, risk_col = st.columns([1.12, 0.88])

with decision_col:
    if view.screening_snapshot:
        screening_snapshot_markup = "".join(f'<div class="ssa-list-item">{item}</div>' for item in view.screening_snapshot)
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "main_case_screening_inputs")}</div><div class="ssa-list-panel">{screening_snapshot_markup}</div>',
            unsafe_allow_html=True,
        )

    if view.drawing_facts:
        drawing_facts_markup = "".join(f'<div class="ssa-list-item">{item}</div>' for item in view.drawing_facts)
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "drawing_facts_summary")}</div><div class="ssa-list-panel">{drawing_facts_markup}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="ssa-section-title">{translate(ui_language, "top_risks")}</div>',
        unsafe_allow_html=True,
    )
    for card in view.risk_cards:
        card_detail_markup = f'<div class="ssa-card-detail">{card.detail}</div>' if card.detail else ""
        st.markdown(
            f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div>{card_detail_markup}</div>',
            unsafe_allow_html=True,
        )

    if view.missing_data_cards:
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "missing_data")}</div>',
            unsafe_allow_html=True,
        )
        for card in view.missing_data_cards:
            st.markdown(
                f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f'<div class="ssa-section-title">{translate(ui_language, "follow_up_questions")}</div>',
        unsafe_allow_html=True,
    )
    for card in view.question_cards:
        st.markdown(
            f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div><div class="ssa-card-detail">{card.detail}</div></div>',
            unsafe_allow_html=True,
        )

with risk_col:
    st.markdown('<div class="ssa-cluster"><div class="ssa-cluster-head">Decision Support</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="ssa-section-title" style="margin-top:0;">{translate(ui_language, "verification_readiness")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ssa-card amber"><div class="ssa-card-title">{view.verification_readiness_title}</div><div class="ssa-card-detail">{view.verification_readiness_summary}</div></div>',
        unsafe_allow_html=True,
    )
    for card in view.verification_blockers:
        st.markdown(
            f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div></div>',
            unsafe_allow_html=True,
        )

    if view.engineering_check_cards:
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "engineering_checks")}</div>',
            unsafe_allow_html=True,
        )
        for card in view.engineering_check_cards:
            st.markdown(
                f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div><div class="ssa-card-detail">{card.detail}</div></div>',
                unsafe_allow_html=True,
            )

    if view.member_reserve_uncertainty_cards:
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "member_reserve_uncertainty_matrix")}</div>',
            unsafe_allow_html=True,
        )
        for card in view.member_reserve_uncertainty_cards:
            st.markdown(
                f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div><div class="ssa-card-detail">{card.detail}</div></div>',
                unsafe_allow_html=True,
            )

    if view.attachment_pathway_cards:
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "attachment_pathway_matrix")}</div>',
            unsafe_allow_html=True,
        )
        for card in view.attachment_pathway_cards:
            st.markdown(
                f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div><div class="ssa-card-detail">{card.detail}</div></div>',
                unsafe_allow_html=True,
            )

    if view.review_trigger_cards:
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "review_trigger_matrix")}</div>',
            unsafe_allow_html=True,
        )
        for card in view.review_trigger_cards:
            st.markdown(
                f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div><div class="ssa-card-detail">{card.detail}</div></div>',
                unsafe_allow_html=True,
            )

    if view.review_progression_summary:
        review_progression_markup = "".join(f'<div class="ssa-list-item">{item}</div>' for item in view.review_progression_summary)
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "review_progression")}</div><div class="ssa-list-panel">{review_progression_markup}</div>',
            unsafe_allow_html=True,
        )

    if view.resource_recommendation_cards:
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "resource_recommendations")}</div>',
            unsafe_allow_html=True,
        )
        for card in view.resource_recommendation_cards:
            st.markdown(
                f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div><div class="ssa-card-detail">{card.detail}</div></div>',
                unsafe_allow_html=True,
            )

    if view.check_action_links:
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "check_action_linkage")}</div>',
            unsafe_allow_html=True,
        )
        for card in view.check_action_links:
            st.markdown(
                f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div><div class="ssa-card-detail">{card.detail}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="ssa-section-title">{translate(ui_language, "recommended_action")}</div>',
        unsafe_allow_html=True,
    )
    for group in view.action_groups:
        st.markdown(
            f'<div class="ssa-card"><div class="ssa-card-title">{group.title}</div></div>',
            unsafe_allow_html=True,
        )
        for card in group.cards:
            st.markdown(
                f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f'<div class="ssa-section-title">{translate(ui_language, "options")}</div>',
        unsafe_allow_html=True,
    )
    for option in view.options:
        label = translate(ui_language, "primary_path") if option.emphasis == "primary" else translate(ui_language, "backup_path")
        option_details_markup = "".join(
            f'<div class="ssa-option-detail">{detail}</div>' for detail in option.details
        )
        st.markdown(
            f'<div class="ssa-option {option.emphasis}"><div class="ssa-option-label">{label}</div><div class="ssa-option-title">{option.title}</div>{option_details_markup}</div>',
            unsafe_allow_html=True,
        )

    if view.review_needed_cards:
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "review_needed")}</div>',
            unsafe_allow_html=True,
        )
        for card in view.review_needed_cards:
            st.markdown(
                f'<div class="ssa-card {card.tone}"><div class="ssa-card-title">{card.title}</div></div>',
                unsafe_allow_html=True,
            )

    if view.assumptions_limitations:
        assumptions_markup = "".join(f'<div class="ssa-list-item">{item}</div>' for item in view.assumptions_limitations)
        st.markdown(
            f'<div class="ssa-section-title">{translate(ui_language, "assumptions_limitations")}</div><div class="ssa-list-panel">{assumptions_markup}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="ssa-agent">
          <div class="ssa-section-title" style="color:#94a3b8; margin-top:0;">{translate(ui_language, "agent_explanation")}</div>
          <div class="ssa-agent-meta">{translate(ui_language, "provider_status")}: {view.agent.provider_label}</div>
          {f'<div class="ssa-agent-notice">{view.agent.notice}</div>' if view.agent.notice else ''}
          <div class="ssa-agent-summary">{view.agent.summary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    f'<div class="ssa-section-title">{view.report_title}</div>',
    unsafe_allow_html=True,
)
st.download_button(
    translate(ui_language, "download_bilingual_report"),
    data=evaluation["report"],
    file_name=report_filename,
    mime="text/markdown",
    use_container_width=True,
)
report_sections_markup = "".join(
    [
        "<div class=\"ssa-report-section\">"
        f"<div class=\"ssa-report-heading\">{section.heading}</div>"
        + "".join(f"<div class=\"ssa-report-item\">{item}</div>" for item in section.items)
        + "</div>"
        for section in report_preview.sections
    ]
)
st.markdown(
    f"""
    <div class="ssa-report">
      <div class="ssa-report-head">
        <div class="ssa-report-title">{report_preview.title}</div>
        <div class="ssa-report-note">{translate(ui_language, "report_export_note")}</div>
      </div>
      <div class="ssa-report-grid">
        {report_sections_markup}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
