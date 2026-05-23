from typing import Optional, Protocol

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.models import (
    BVReportSection,
    BVReviewIntake,
    BVReviewResult,
)
from structural_screening_agent.bv_review.project_management import (
    ProjectManagementAction,
    build_project_management_action_rows,
    build_project_management_action_summary,
    build_project_management_action_summary_rows,
)
from structural_screening_agent.bv_review.foundation_evidence import (
    FoundationEvidenceItem,
    build_foundation_evidence_path,
)
from structural_screening_agent.bv_review.project_state import ProjectReviewState
from structural_screening_agent.bv_review.ui_state import (
    BV_DOCUMENT_LABELS,
    BV_REVIEW_OBJECT_LABELS,
)
from structural_screening_agent.localization import Language


class BVProjectManagementDashboardView(BaseModel):
    heading: str = Field(min_length=1)
    summary_rows: list[dict[str, object]] = Field(default_factory=list)
    action_rows: list[dict[str, object]] = Field(default_factory=list)
    empty_caption: str = Field(min_length=1)


class StreamlitSectionRenderer(Protocol):
    def markdown(self, text: str) -> None:
        ...

    def write(self, text: str) -> None:
        ...


def render_bv_section(
    streamlit_api: StreamlitSectionRenderer,
    title: str,
    items: list[str],
    limit: Optional[int] = None,
) -> None:
    streamlit_api.markdown(f"#### {title}")
    visible_items = items if limit is None else items[:limit]
    for item in visible_items:
        streamlit_api.write(f"- {item}")


def format_bv_label(
    label_map: dict[str, dict[str, str]], value: str, language: Language
) -> str:
    localized = label_map.get(value, {})
    return localized.get(language) or localized.get("en") or value


def format_bv_object_labels(values: list[str], language: Language) -> str:
    return ", ".join(
        format_bv_label(BV_REVIEW_OBJECT_LABELS, value, language) for value in values
    )


def build_bv_basis_items(bv_result: BVReviewResult, language: Language) -> list[str]:
    if language == "zh":
        return [
            f"{item.title}: {'; '.join(item.review_actions)}"
            for item in bv_result.basis_references
        ]
    return [
        f"{item.basis_id}: {item.source_type}; objects: "
        f"{format_bv_object_labels(item.review_objects, language)}"
        for item in bv_result.basis_references
    ]


def build_bv_path_items(bv_result: BVReviewResult, language: Language) -> list[str]:
    if language == "zh":
        return [
            f"{item.title}: {item.status} | {item.method}"
            for item in bv_result.review_paths
        ]
    return [
        f"{format_bv_label(BV_REVIEW_OBJECT_LABELS, item.review_object, language)}: "
        f"{item.status}; deliverables: {len(item.deliverables)}"
        for item in bv_result.review_paths
    ]


def build_bv_risk_items(bv_result: BVReviewResult, language: Language) -> list[str]:
    if language == "zh":
        return [
            f"{item.severity} | {item.title}: {item.recommendation}"
            for item in bv_result.risks
        ]
    return [
        f"{item.severity} | {item.category}: {item.risk_id}; "
        f"blocks report: {item.blocks_report_issue}"
        for item in bv_result.risks
    ]


def build_bv_plan_items(bv_result: BVReviewResult, language: Language) -> list[str]:
    if language == "zh":
        return [
            f"{item.phase}: {item.method} | {item.deliverable}"
            for item in bv_result.review_plan
        ]
    return [
        f"{item.phase}: {item.responsible_role}; item: {item.item_id}"
        for item in bv_result.review_plan
    ]


def build_bv_report_preview_sections(
    bv_intake: BVReviewIntake, bv_result: BVReviewResult, language: Language
) -> list[BVReportSection]:
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
            items=build_bv_basis_items(bv_result, language)[:4],
        ),
        BVReportSection(
            heading="Document Completeness",
            items=[
                f"{item.document_key}: {item.status}"
                for item in bv_result.checklist_items[:4]
            ],
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


def build_bv_project_management_dashboard_view(
    actions: list[ProjectManagementAction],
    language: Language,
) -> BVProjectManagementDashboardView:
    heading = (
        "Project Management Action Dashboard"
        if language == "en"
        else "项目管理行动看板"
    )
    empty_caption = (
        "No project management actions are currently open."
        if language == "en"
        else "当前没有待处理的项目管理行动。"
    )
    if not actions:
        return BVProjectManagementDashboardView(
            heading=heading,
            empty_caption=empty_caption,
        )
    summary = build_project_management_action_summary(actions)
    return BVProjectManagementDashboardView(
        heading=heading,
        summary_rows=build_project_management_action_summary_rows(summary, language),
        action_rows=build_project_management_action_rows(actions, language),
        empty_caption=empty_caption,
    )


def build_foundation_evidence_display_rows(
    state: ProjectReviewState,
    language: Language,
) -> list[dict[str, object]]:
    evidence_items = build_foundation_evidence_path(state)
    if language == "en":
        return [_foundation_evidence_row_en(item) for item in evidence_items]
    return [_foundation_evidence_row_zh(item) for item in evidence_items]


def _foundation_evidence_row_zh(
    item: FoundationEvidenceItem,
) -> dict[str, object]:
    return {
        "证据项": _foundation_evidence_title(item.evidence_id, "zh"),
        "状态": _foundation_evidence_status_label(item.status, "zh"),
        "必要资料": _document_list_label(item.required_document_keys, "zh"),
        "缺失资料": _document_list_label(item.missing_document_keys, "zh"),
        "部分资料": _document_list_label(item.partial_document_keys, "zh"),
        "已确认字段": ", ".join(item.confirmed_field_ids) or "无",
        "未确认字段": ", ".join(item.unconfirmed_field_ids) or "无",
        "缺失字段": ", ".join(item.missing_field_ids) or "无",
        "阻塞基础计算": "是" if item.blocks_calculation else "否",
        "建议动作": item.review_action,
    }


def _foundation_evidence_row_en(
    item: FoundationEvidenceItem,
) -> dict[str, object]:
    return {
        "Evidence Item": _foundation_evidence_title(item.evidence_id, "en"),
        "Status": _foundation_evidence_status_label(item.status, "en"),
        "Required Documents": _document_list_label(item.required_document_keys, "en"),
        "Missing Documents": _document_list_label(item.missing_document_keys, "en"),
        "Partial Documents": _document_list_label(item.partial_document_keys, "en"),
        "Confirmed Fields": ", ".join(item.confirmed_field_ids) or "None",
        "Unconfirmed Fields": ", ".join(item.unconfirmed_field_ids) or "None",
        "Missing Fields": ", ".join(item.missing_field_ids) or "None",
        "Blocks Foundation Calculation": "Yes" if item.blocks_calculation else "No",
        "Review Action": _foundation_evidence_action_label(item.evidence_id),
    }


def _foundation_evidence_title(evidence_id: str, language: Language) -> str:
    labels = {
        "geotechnical_parameters": {
            "zh": "地勘参数证据",
            "en": "Geotechnical Parameters",
        },
        "foundation_geometry": {
            "zh": "基础几何与布置证据",
            "en": "Foundation Geometry and Layout",
        },
        "foundation_reactions": {
            "zh": "基础最不利反力证据",
            "en": "Foundation Governing Reactions",
        },
    }
    return labels.get(evidence_id, {}).get(language, evidence_id)


def _foundation_evidence_status_label(status: str, language: Language) -> str:
    labels = {
        "satisfied": {"zh": "满足", "en": "Satisfied"},
        "partial": {"zh": "部分满足", "en": "Partial"},
        "missing": {"zh": "缺失", "en": "Missing"},
    }
    return labels.get(status, {}).get(language, status)


def _document_list_label(document_keys: list[str], language: Language) -> str:
    empty_label = "None" if language == "en" else "无"
    return ", ".join(
        BV_DOCUMENT_LABELS.get(key, {}).get(language, key) for key in document_keys
    ) or empty_label


def _foundation_evidence_action_label(evidence_id: str) -> str:
    actions = {
        "geotechnical_parameters": (
            "Provide or confirm the geotechnical report, characteristic bearing capacity, "
            "pile side resistance, soil parameters, and groundwater conditions."
        ),
        "foundation_geometry": (
            "Provide or confirm pile diameter, pile length, pile type, pile spacing, "
            "and the foundation layout source."
        ),
        "foundation_reactions": (
            "Provide or confirm governing uplift, compression, horizontal reaction, "
            "and load-combination source before foundation screening calculation."
        ),
    }
    return actions.get(evidence_id, evidence_id)
