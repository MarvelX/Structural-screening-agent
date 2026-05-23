from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.models import BVRiskItem
from structural_screening_agent.bv_review.project_state import (
    ExtractedField,
    ProjectReviewState,
)


FoundationEvidenceStatus = Literal["satisfied", "partial", "missing"]


class FoundationEvidenceItem(BaseModel):
    evidence_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: FoundationEvidenceStatus
    required_document_keys: list[str] = Field(default_factory=list)
    required_field_ids: list[str] = Field(default_factory=list)
    available_document_keys: list[str] = Field(default_factory=list)
    partial_document_keys: list[str] = Field(default_factory=list)
    missing_document_keys: list[str] = Field(default_factory=list)
    confirmed_field_ids: list[str] = Field(default_factory=list)
    unconfirmed_field_ids: list[str] = Field(default_factory=list)
    missing_field_ids: list[str] = Field(default_factory=list)
    blocks_calculation: bool = False
    review_action: str = Field(min_length=1)


_FOUNDATION_EVIDENCE_DEFINITIONS: tuple[
    tuple[str, str, tuple[str, ...], tuple[str, ...], str],
    ...,
] = (
    (
        "geotechnical_parameters",
        "地勘参数证据",
        ("geotechnical_report",),
        ("bearing_capacity_characteristic_kpa", "side_resistance_standard_kpa"),
        "补充或确认地勘报告、地基承载力特征值 fak、桩侧阻力标准值 qsk、土层参数和地下水条件。",
    ),
    (
        "foundation_geometry",
        "基础几何与布置证据",
        ("calculation_report",),
        ("pile_diameter_mm", "pile_length_m"),
        "补充或确认桩径、桩长、桩型、桩间距和基础布置来源。",
    ),
    (
        "foundation_reactions",
        "基础最不利反力证据",
        ("calculation_report",),
        ("uplift_force_kn", "compression_force_kn", "horizontal_force_kn"),
        "补充或确认最不利抗拔力、压力、水平力及其荷载组合来源；证据完整后进入基础筛查级计算。",
    ),
)


def build_foundation_evidence_path(
    state: ProjectReviewState,
) -> list[FoundationEvidenceItem]:
    if "foundation" not in state.intake.review_objects:
        return []

    fields_by_id = {field.field_id: field for field in state.extracted_fields}
    return [
        _build_evidence_item(
            state,
            fields_by_id,
            evidence_id=evidence_id,
            title=title,
            required_document_keys=list(required_document_keys),
            required_field_ids=list(required_field_ids),
            review_action=review_action,
        )
        for (
            evidence_id,
            title,
            required_document_keys,
            required_field_ids,
            review_action,
        ) in _FOUNDATION_EVIDENCE_DEFINITIONS
    ]


def build_foundation_evidence_risks(
    state: ProjectReviewState,
) -> list[BVRiskItem]:
    risks: list[BVRiskItem] = []
    for item in build_foundation_evidence_path(state):
        if not item.blocks_calculation:
            continue
        linked_field_ids = _unique_preserving_order(
            [
                *item.missing_document_keys,
                *item.partial_document_keys,
                *item.missing_field_ids,
                *item.unconfirmed_field_ids,
            ]
        )
        risks.append(
            BVRiskItem(
                risk_id=f"foundation_evidence_blocked_{item.evidence_id}",
                title=f"{item.title}不足，阻塞基础筛查级计算",
                severity="critical" if item.status == "missing" else "high",
                trigger_basis=_foundation_evidence_trigger_basis(item),
                linked_field_ids=linked_field_ids,
                impact_scope="基础证据路径、基础筛查级计算和相关 RFI/NCR 判断",
                recommendation=item.review_action,
                blocks_report_issue=True,
                category="nonconformity" if item.status == "missing" else "risk",
            )
        )
    return risks


def _build_evidence_item(
    state: ProjectReviewState,
    fields_by_id: dict[str, ExtractedField],
    *,
    evidence_id: str,
    title: str,
    required_document_keys: list[str],
    required_field_ids: list[str],
    review_action: str,
) -> FoundationEvidenceItem:
    available_document_keys = [
        key for key in required_document_keys if state.intake.documents.get(key) == "available"
    ]
    partial_document_keys = [
        key for key in required_document_keys if state.intake.documents.get(key) == "partial"
    ]
    missing_document_keys = [
        key
        for key in required_document_keys
        if state.intake.documents.get(key, "missing") == "missing"
    ]
    confirmed_field_ids: list[str] = []
    unconfirmed_field_ids: list[str] = []
    missing_field_ids: list[str] = []

    for field_id in required_field_ids:
        field = fields_by_id.get(field_id)
        if field is None:
            missing_field_ids.append(field_id)
        elif field.is_confirmed and field.include_in_calculation:
            confirmed_field_ids.append(field_id)
        else:
            unconfirmed_field_ids.append(field_id)

    status = _resolve_evidence_status(
        missing_document_keys=missing_document_keys,
        partial_document_keys=partial_document_keys,
        missing_field_ids=missing_field_ids,
        unconfirmed_field_ids=unconfirmed_field_ids,
    )
    return FoundationEvidenceItem(
        evidence_id=evidence_id,
        title=title,
        status=status,
        required_document_keys=required_document_keys,
        required_field_ids=required_field_ids,
        available_document_keys=available_document_keys,
        partial_document_keys=partial_document_keys,
        missing_document_keys=missing_document_keys,
        confirmed_field_ids=confirmed_field_ids,
        unconfirmed_field_ids=unconfirmed_field_ids,
        missing_field_ids=missing_field_ids,
        blocks_calculation=status != "satisfied",
        review_action=review_action,
    )


def _resolve_evidence_status(
    *,
    missing_document_keys: list[str],
    partial_document_keys: list[str],
    missing_field_ids: list[str],
    unconfirmed_field_ids: list[str],
) -> FoundationEvidenceStatus:
    if missing_document_keys or missing_field_ids:
        return "missing"
    if partial_document_keys or unconfirmed_field_ids:
        return "partial"
    return "satisfied"


def _foundation_evidence_trigger_basis(item: FoundationEvidenceItem) -> str:
    return (
        f"基础证据路径 {item.evidence_id}: 状态={item.status}; "
        f"缺失资料={_joined_or_na(item.missing_document_keys)}; "
        f"部分资料={_joined_or_na(item.partial_document_keys)}; "
        f"缺失字段={_joined_or_na(item.missing_field_ids)}; "
        f"未确认字段={_joined_or_na(item.unconfirmed_field_ids)}."
    )


def _joined_or_na(values: list[str]) -> str:
    return ", ".join(values) if values else "N/A"


def _unique_preserving_order(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values
