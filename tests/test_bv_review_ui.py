from structural_screening_agent.bv_review.ui import (
    build_bv_basis_items,
    build_bv_evidence_table_text,
    build_bv_gate_panel_text,
    build_foundation_evidence_display_rows,
    build_bv_project_management_dashboard_view,
    build_bv_report_reissue_gate_view,
    build_bv_report_revision_history_view,
    build_bv_report_preview_sections,
    format_bv_label,
    render_bv_report_gate_status,
    render_bv_section,
)
from structural_screening_agent.bv_review.human_gate import ReportDraftGateResult
from structural_screening_agent.bv_review.project_management import (
    build_project_management_actions,
)
from structural_screening_agent.bv_review.project_state import (
    ExtractedField,
    ProjectReviewState,
    RFIItem,
    ReportRevision,
    EngineerApproval,
)
from structural_screening_agent.bv_review.ui_state import default_bv_review_intake
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


class _FakeStreamlit:
    def __init__(self) -> None:
        self.markdown_calls: list[str] = []
        self.write_calls: list[str] = []
        self.success_calls: list[str] = []
        self.warning_calls: list[str] = []
        self.caption_calls: list[str] = []

    def markdown(self, text: str) -> None:
        self.markdown_calls.append(text)

    def write(self, text: str) -> None:
        self.write_calls.append(text)

    def success(self, text: str) -> None:
        self.success_calls.append(text)

    def warning(self, text: str) -> None:
        self.warning_calls.append(text)

    def caption(self, text: str) -> None:
        self.caption_calls.append(text)


def test_bv_ui_helpers_import_without_streamlit_runtime() -> None:
    intake = default_bv_review_intake()
    result = evaluate_bv_review(intake)

    zh_items = build_bv_basis_items(result, "zh")
    en_items = build_bv_basis_items(result, "en")

    assert zh_items
    assert en_items
    assert "Review Basis" not in str(zh_items)
    assert "objects:" in en_items[0]


def test_format_bv_label_prefers_language_then_english_then_raw_value() -> None:
    labels = {
        "foundation": {"zh": "基础验算", "en": "Foundation"},
        "superstructure": {"en": "Superstructure"},
    }

    assert format_bv_label(labels, "foundation", "zh") == "基础验算"
    assert format_bv_label(labels, "superstructure", "zh") == "Superstructure"
    assert format_bv_label(labels, "unknown", "zh") == "unknown"


def test_bv_evidence_table_text_localizes_headings_and_empty_captions() -> None:
    zh_text = build_bv_evidence_table_text("zh")
    en_text = build_bv_evidence_table_text("en")

    assert zh_text.foundation_heading == "基础证据路径"
    assert zh_text.report_gate_empty_caption == "当前没有结构化报告门禁证据。"
    assert zh_text.closed_rfi_heading == "已关闭澄清问题增量复核证据"
    assert "No " not in str(zh_text)
    assert "RFI" not in zh_text.closed_rfi_heading
    assert en_text.foundation_heading == "Foundation Evidence Path"
    assert en_text.evidence_matrix_empty_caption == (
        "No finding source evidence is available yet."
    )
    assert en_text.closed_rfi_heading == "Closed RFI Recheck Evidence"


def test_bv_gate_panel_text_localizes_quality_gate_heading() -> None:
    zh_text = build_bv_gate_panel_text("zh")
    en_text = build_bv_gate_panel_text("en")

    assert zh_text.quality_gate_heading == "质量门禁状态"
    assert en_text.quality_gate_heading == "Quality Gate Status"
    assert "Quality Gate Status" not in str(zh_text)


def test_render_bv_report_gate_status_renders_ready_and_blocked_states() -> None:
    ready_st = _FakeStreamlit()
    render_bv_report_gate_status(
        ready_st,
        ReportDraftGateResult(
            status="ready",
            notes=["Calculation run is ready but not yet completed."],
        ),
        "en",
        ready_message="Report draft gate ready.",
        blocked_message="Report draft gate blocked.",
    )

    assert ready_st.success_calls == ["Report draft gate ready."]
    assert ready_st.warning_calls == []
    assert ready_st.write_calls == []
    assert ready_st.caption_calls == ["Calculation run is ready but not yet completed."]

    blocked_st = _FakeStreamlit()
    render_bv_report_gate_status(
        blocked_st,
        ReportDraftGateResult(
            status="blocked",
            reasons=[
                "Missing required document inputs block report draft input: geotechnical_report",
                "Reason 2",
                "Reason 3",
                "Reason 4",
                "Reason 5",
                "Reason 6",
            ],
            notes=["Engineer closeout remains pending."],
        ),
        "zh",
        ready_message="报告草稿输入门禁已满足。",
        blocked_message="报告草稿输入门禁阻塞。",
    )

    assert blocked_st.success_calls == []
    assert blocked_st.warning_calls == ["报告草稿输入门禁阻塞。"]
    assert len(blocked_st.write_calls) == 5
    assert blocked_st.write_calls[0].startswith("- 缺失必要资料：")
    assert "Missing required document inputs" not in blocked_st.write_calls[0]
    assert blocked_st.caption_calls == ["Engineer closeout remains pending."]


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


def test_bv_report_revision_history_view_localizes_rows_and_empty_state() -> None:
    state = ProjectReviewState(
        project_id="pv-ui-report-revisions",
        intake=default_bv_review_intake(),
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=8,
                rfi_count=1,
                created_by="Engineer A",
                created_at="2026-05-20T09:00:00+08:00",
                revision_status="issued_for_review",
                issue_purpose="Internal review package",
            )
        ],
    )

    zh_view = build_bv_report_revision_history_view(state, "zh")
    en_view = build_bv_report_revision_history_view(state, "en")
    empty_view = build_bv_report_revision_history_view(
        ProjectReviewState(
            project_id="pv-ui-empty-report-revisions",
            intake=default_bv_review_intake(),
        ),
        "en",
    )

    assert zh_view.heading == "报告修订历史"
    assert zh_view.summary_rows[0] == {"指标": "报告修订数", "数值": 1}
    assert zh_view.revision_rows[0]["状态"] == "发给复核"
    assert en_view.heading == "Report Revision History"
    assert en_view.revision_rows[0]["Status"] == "Issued for Review"
    assert empty_view.empty_caption == "No report revision snapshots have been recorded."


def test_bv_report_reissue_gate_view_localizes_summary_rows() -> None:
    state = ProjectReviewState(
        project_id="pv-ui-report-reissue",
        intake=default_bv_review_intake(),
        approvals=[
            EngineerApproval(
                approval_id="report-gate-approval",
                target_type="report",
                target_id="report",
                status="approved",
                reviewer="Engineer A",
                locked=True,
            )
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-001",
                question="Please provide Rev B geotechnical response.",
                responsible_party="client / designer",
                trigger_basis="Foundation evidence gap.",
                required_document_or_field="geotechnical_report",
                status="closed",
                client_response="Rev B provided.\nCloseout: Engineer accepted.",
                reopen_review_items=["bearing_capacity_characteristic_kpa"],
                completed_recheck_items=["bearing_capacity_characteristic_kpa"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    zh_view = build_bv_report_reissue_gate_view(state, "zh")
    en_view = build_bv_report_reissue_gate_view(state, "en")

    assert zh_view.heading == "报告再签发门禁"
    assert zh_view.summary_rows[0] == {"指标": "再签发状态", "数值": "可记录新版报告"}
    assert "Reissue" not in str(zh_view)
    assert en_view.heading == "Report Reissue Gate"
    assert en_view.summary_rows[0] == {
        "Metric": "Reissue Status",
        "Value": "Ready to Record Reissue",
    }

    blocked_view = build_bv_report_reissue_gate_view(
        ProjectReviewState(
            project_id="pv-ui-report-reissue-blocked",
            intake=default_bv_review_intake(),
            rfi_items=[
                RFIItem(
                    rfi_id="rfi-foundation-002",
                    question="Please provide Rev B geotechnical response.",
                    responsible_party="client / designer",
                    trigger_basis="Foundation evidence gap.",
                    required_document_or_field="geotechnical_report",
                    status="open",
                    reopen_review_items=["bearing_capacity_characteristic_kpa"],
                    triggers_incremental_recheck=True,
                )
            ],
        ),
        "zh",
    )

    assert blocked_view.blocking_reasons[0] == (
        "待客户 / 设计院回复的澄清问题：rfi-foundation-002"
    )
    assert "Open or reopened" not in str(blocked_view)


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


def test_render_bv_section_uses_streamlit_like_api_and_limit() -> None:
    fake_st = _FakeStreamlit()

    render_bv_section(
        fake_st,
        "Review Basis",
        ["GB 50797", "IEC 62548", "Eurocode"],
        limit=2,
    )

    assert fake_st.markdown_calls == ["#### Review Basis"]
    assert fake_st.write_calls == ["- GB 50797", "- IEC 62548"]
