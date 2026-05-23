from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.project_state import (
    DocumentVersion,
    ExtractedField,
    ProjectReviewState,
)


EvidenceSourceType = Literal["field", "document", "missing"]
EvidenceStatus = Literal[
    "confirmed",
    "unconfirmed",
    "excluded",
    "available",
    "partial",
    "missing",
    "not_applicable",
]


class EvidenceMatrixItem(BaseModel):
    finding_id: str = Field(min_length=1)
    finding_title: str = Field(min_length=1)
    linked_id: str = Field(min_length=1)
    source_type: EvidenceSourceType
    source_document_id: str = ""
    source_location: str = ""
    evidence_excerpt: str = Field(min_length=1)
    evidence_status: EvidenceStatus
    confidence: Optional[float] = None


def build_evidence_matrix(state: ProjectReviewState) -> list[EvidenceMatrixItem]:
    fields_by_id = {field.field_id: field for field in state.extracted_fields}
    documents_by_key = _index_documents_by_key(state.document_versions)
    rows: list[EvidenceMatrixItem] = []
    for risk in state.risks:
        for linked_id in risk.linked_field_ids:
            field = fields_by_id.get(linked_id)
            if field is not None:
                rows.append(_field_evidence_item(risk.risk_id, risk.title, linked_id, field))
                continue
            document = documents_by_key.get(linked_id)
            if document is not None:
                rows.append(
                    _document_version_evidence_item(
                        risk.risk_id,
                        risk.title,
                        linked_id,
                        document,
                    )
                )
                continue
            if linked_id in state.intake.documents:
                rows.append(
                    _intake_document_evidence_item(
                        risk.risk_id,
                        risk.title,
                        linked_id,
                        state.intake.documents[linked_id],
                    )
                )
                continue
            rows.append(_missing_evidence_item(risk.risk_id, risk.title, linked_id))
    return rows


def _index_documents_by_key(
    document_versions: list[DocumentVersion],
) -> dict[str, DocumentVersion]:
    documents: dict[str, DocumentVersion] = {}
    for document in document_versions:
        documents.setdefault(document.document_type, document)
        documents.setdefault(document.document_id, document)
    return documents


def _field_evidence_item(
    finding_id: str,
    finding_title: str,
    linked_id: str,
    field: ExtractedField,
) -> EvidenceMatrixItem:
    return EvidenceMatrixItem(
        finding_id=finding_id,
        finding_title=finding_title,
        linked_id=linked_id,
        source_type="field",
        source_document_id=field.source_document_id,
        source_location=field.page_or_section,
        evidence_excerpt=field.quote,
        evidence_status=_field_evidence_status(field),
        confidence=field.confidence,
    )


def _document_version_evidence_item(
    finding_id: str,
    finding_title: str,
    linked_id: str,
    document: DocumentVersion,
) -> EvidenceMatrixItem:
    return EvidenceMatrixItem(
        finding_id=finding_id,
        finding_title=finding_title,
        linked_id=linked_id,
        source_type="document",
        source_document_id=document.document_id,
        source_location=f"Revision {document.revision}",
        evidence_excerpt=document.source_name,
        evidence_status=document.status,
    )


def _intake_document_evidence_item(
    finding_id: str,
    finding_title: str,
    linked_id: str,
    document_status: EvidenceStatus,
) -> EvidenceMatrixItem:
    return EvidenceMatrixItem(
        finding_id=finding_id,
        finding_title=finding_title,
        linked_id=linked_id,
        source_type="document",
        source_document_id=linked_id,
        source_location="Intake document status",
        evidence_excerpt=document_status,
        evidence_status=document_status,
    )


def _missing_evidence_item(
    finding_id: str,
    finding_title: str,
    linked_id: str,
) -> EvidenceMatrixItem:
    return EvidenceMatrixItem(
        finding_id=finding_id,
        finding_title=finding_title,
        linked_id=linked_id,
        source_type="missing",
        evidence_excerpt=(
            "No extracted field, document version, or intake document status is available."
        ),
        evidence_status="missing",
    )


def _field_evidence_status(field: ExtractedField) -> EvidenceStatus:
    if field.is_confirmed and field.include_in_calculation:
        return "confirmed"
    if field.is_confirmed:
        return "excluded"
    return "unconfirmed"
