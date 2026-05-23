from structural_screening_agent.bv_review.ui import (
    build_bv_basis_items,
    build_foundation_evidence_display_rows,
    build_bv_project_management_dashboard_view,
    build_bv_report_preview_sections,
)
from structural_screening_agent.bv_review.project_management import (
    build_project_management_actions,
)
from structural_screening_agent.bv_review.project_state import (
    ExtractedField,
    ProjectReviewState,
    RFIItem,
)
from structural_screening_agent.bv_review.ui_state import default_bv_review_intake
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def test_bv_ui_helpers_import_without_streamlit_runtime() -> None:
    intake = default_bv_review_intake()
    result = evaluate_bv_review(intake)

    zh_items = build_bv_basis_items(result, "zh")
    en_items = build_bv_basis_items(result, "en")

    assert zh_items
    assert en_items
    assert "Review Basis" not in str(zh_items)
    assert "objects:" in en_items[0]


def test_bv_report_preview_sections_support_chinese_and_english() -> None:
    intake = default_bv_review_intake()
    result = evaluate_bv_review(intake)

    zh_sections = build_bv_report_preview_sections(intake, result, "zh")
    en_sections = build_bv_report_preview_sections(intake, result, "en")

    assert zh_sections[0].heading == "项目与审核范围"
    assert en_sections[0].heading == "Project and Review Scope"
    assert "Project name:" in en_sections[0].items[0]
    assert "Project name:" not in str(zh_sections)


def test_bv_project_management_dashboard_view_localizes_summary_and_rows() -> None:
    intake = default_bv_review_intake()
    actions = build_project_management_actions(
        ProjectReviewState(
            project_id="pv-ui-management-dashboard",
            intake=intake,
            rfi_items=[
                RFIItem(
                    rfi_id="rfi-load-001",
                    question="Please confirm updated load table.",
                    responsible_party="client / designer",
                    trigger_basis="Client replied with Rev B load table.",
                    required_document_or_field="uplift_force_kn",
                    status="responded",
                    client_response="Rev B load table submitted.",
                    reopen_review_items=["uplift_force_kn"],
                    triggers_incremental_recheck=True,
                )
            ],
        )
    )

    zh_view = build_bv_project_management_dashboard_view(actions, "zh")
    en_view = build_bv_project_management_dashboard_view(actions, "en")
    empty_view = build_bv_project_management_dashboard_view([], "en")

    assert zh_view.heading == "项目管理行动看板"
    assert zh_view.summary_rows[0] == {"指标": "项目待办", "数值": 1}
    assert zh_view.action_rows[0]["行动类型"] == "RFI 工程师关闭"
    assert en_view.heading == "Project Management Action Dashboard"
    assert en_view.summary_rows[0] == {"Metric": "Project Actions", "Value": 1}
    assert en_view.action_rows[0]["Action Type"] == "RFI Engineer Closeout"
    assert empty_view.summary_rows == []
    assert empty_view.action_rows == []
    assert empty_view.empty_caption == "No project management actions are currently open."


def test_foundation_evidence_display_rows_localize_status_and_documents() -> None:
    intake = default_bv_review_intake()
    state = ProjectReviewState(
        project_id="pv-ui-foundation-evidence",
        intake=intake,
        extracted_fields=[
            ExtractedField(
                field_id="bearing_capacity_characteristic_kpa",
                name="Bearing capacity characteristic",
                candidate_value="180",
                unit="kPa",
                source_document_id="geotechnical-report-g001",
                page_or_section="Geotechnical parameter table",
                quote="fak = 180 kPa",
                confidence=0.88,
                is_confirmed=False,
                include_in_calculation=False,
            )
        ],
    )

    zh_rows = build_foundation_evidence_display_rows(state, "zh")
    en_rows = build_foundation_evidence_display_rows(state, "en")

    assert zh_rows[0]["证据项"] == "地勘参数证据"
    assert zh_rows[0]["状态"] == "缺失"
    assert zh_rows[0]["缺失资料"] == "地勘报告"
    assert zh_rows[0]["阻塞基础计算"] == "是"
    assert en_rows[0]["Evidence Item"] == "Geotechnical Parameters"
    assert en_rows[0]["Status"] == "Missing"
    assert en_rows[0]["Missing Documents"] == "Geotechnical Report"
    assert en_rows[0]["Blocks Foundation Calculation"] == "Yes"
    assert "地勘报告" not in str(en_rows)
