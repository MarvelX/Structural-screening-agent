import pytest
from pydantic import ValidationError

from structural_screening_agent.bv_review.models import (
    BVDocumentStatus,
    BVReviewIntake,
    BVRiskItem,
)


def test_bv_review_intake_captures_project_standards_objects_and_documents() -> None:
    intake = BVReviewIntake(
        project_name="Hebei rooftop PV design review",
        country_or_region="China",
        project_type="rooftop_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "existing_rooftop_added_load"],
        client_requirements=["BV-style independent design review report"],
        documents={
            "structural_drawings": "partial",
            "calculation_report": "missing",
            "technical_specification": "available",
            "geotechnical_report": "missing",
            "vendor_datasheets": "partial",
            "contract_requirements": "available",
        },
    )

    assert intake.project_name == "Hebei rooftop PV design review"
    assert "gb" in intake.standards_systems
    assert "existing_rooftop_added_load" in intake.review_objects
    assert intake.documents["calculation_report"] == "missing"


def test_bv_review_intake_rejects_empty_standards_and_objects() -> None:
    with pytest.raises(ValidationError):
        BVReviewIntake(
            project_name="Invalid review",
            country_or_region="China",
            project_type="rooftop_pv",
            design_stage="tender",
            standards_systems=[],
            review_objects=[],
            documents={},
        )


def test_bv_document_status_type_accepts_expected_status_values() -> None:
    status: BVDocumentStatus = "partial"

    assert status == "partial"


def test_bv_risk_item_carries_structured_linked_field_ids() -> None:
    risk = BVRiskItem(
        risk_id="missing_geotechnical_report",
        title="Missing geotechnical report",
        severity="critical",
        trigger_basis="Document checklist",
        linked_field_ids=["geotechnical_report"],
        impact_scope="Foundation review",
        recommendation="Provide geotechnical report.",
        blocks_report_issue=True,
        category="nonconformity",
    )

    assert risk.linked_field_ids == ["geotechnical_report"]


def test_bv_risk_item_defaults_to_no_linked_fields_for_legacy_risks() -> None:
    risk = BVRiskItem(
        risk_id="legacy_review_risk",
        title="Legacy review risk",
        severity="medium",
        trigger_basis="Legacy deterministic rule",
        impact_scope="Review planning",
        recommendation="Track the risk in the register.",
        category="risk",
    )

    assert risk.linked_field_ids == []


def test_bv_risk_item_tracks_finding_lifecycle_status_and_closeout_note() -> None:
    risk = BVRiskItem(
        risk_id="foundation_bearing_capacity_closed",
        title="Foundation bearing capacity clarification closed",
        severity="high",
        trigger_basis="Engineer reviewed geotechnical Rev B response.",
        impact_scope="Foundation review",
        recommendation="Keep closeout evidence in the report workpaper.",
        blocks_report_issue=True,
        category="nonconformity",
        status="closed",
        closeout_note="Engineer accepted Rev B bearing capacity evidence.",
    )

    assert risk.status == "closed"
    assert risk.closeout_note == "Engineer accepted Rev B bearing capacity evidence."
