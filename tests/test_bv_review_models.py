import pytest
from pydantic import ValidationError

from structural_screening_agent.bv_review.models import (
    BVDocumentStatus,
    BVReviewIntake,
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
