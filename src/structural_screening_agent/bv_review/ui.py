from structural_screening_agent.bv_review.models import (
    BVReportSection,
    BVReviewIntake,
    BVReviewResult,
)
from structural_screening_agent.bv_review.ui_state import BV_REVIEW_OBJECT_LABELS
from structural_screening_agent.localization import Language


def format_bv_label(
    label_map: dict[str, dict[str, str]], value: str, language: Language
) -> str:
    return label_map.get(value, {}).get(language, value)


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
