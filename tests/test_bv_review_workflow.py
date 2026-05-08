from structural_screening_agent.bv_review.basis import build_review_basis
from structural_screening_agent.bv_review.models import BVReviewIntake


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Hebei rooftop PV design review",
        country_or_region="China",
        project_type="rooftop_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "existing_rooftop_added_load"],
        client_requirements=["Client requires independent structural design review."],
        documents={
            "structural_drawings": "partial",
            "calculation_report": "missing",
            "technical_specification": "available",
            "geotechnical_report": "missing",
            "vendor_datasheets": "partial",
            "contract_requirements": "available",
        },
    )


def test_review_basis_builder_maps_standards_and_review_objects_to_references() -> None:
    basis = build_review_basis(_sample_intake())

    basis_ids = {item.basis_id for item in basis}
    assert "gb_50797_pv_power_station_design" in basis_ids
    assert "gb_50017_steel_structure_design" in basis_ids
    assert "iec_62548_pv_array_design" in basis_ids
    assert "project_contract_requirements" in basis_ids
    assert any("支架" in item.title for item in basis)
    assert all(item.evidence_requirements for item in basis)


def test_review_basis_builder_does_not_include_unselected_review_objects() -> None:
    intake = BVReviewIntake(
        project_name="Foundation-only PV design review",
        country_or_region="China",
        project_type="rooftop_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["foundation"],
    )

    basis = build_review_basis(intake)
    basis_ids = {item.basis_id for item in basis}
    selected_objects = set(intake.review_objects)

    assert "gb_50797_pv_power_station_design" in basis_ids
    assert "project_contract_requirements" in basis_ids
    assert "gb_50017_steel_structure_design" not in basis_ids
    assert "iec_62548_pv_array_design" not in basis_ids
    assert all(set(item.review_objects) <= selected_objects for item in basis)


def test_review_basis_builder_intersects_gb_50017_review_objects() -> None:
    intake = BVReviewIntake(
        project_name="Connection-only PV design review",
        country_or_region="China",
        project_type="rooftop_pv",
        design_stage="construction_drawing",
        standards_systems=["gb"],
        review_objects=["connection"],
    )

    basis = build_review_basis(intake)
    gb_50017 = next(
        item for item in basis if item.basis_id == "gb_50017_steel_structure_design"
    )

    assert gb_50017.review_objects == ["connection"]
