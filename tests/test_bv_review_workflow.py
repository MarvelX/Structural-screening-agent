from structural_screening_agent.bv_review.basis import build_review_basis
from structural_screening_agent.bv_review.checklist import build_document_checklist
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.review_path import build_structural_review_path


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


def test_document_checklist_marks_missing_calculation_and_geotechnical_reports_as_review_holds() -> None:
    checklist = build_document_checklist(_sample_intake())

    missing_keys = {item.document_key for item in checklist if item.review_blocked}
    assert "calculation_report" in missing_keys
    assert "geotechnical_report" in missing_keys
    assert any("补充结构计算书" in item.required_action for item in checklist)
    assert any("foundation" in item.affected_review_objects for item in checklist)


def test_structural_review_path_creates_object_specific_review_methods_and_holds() -> None:
    checklist = build_document_checklist(_sample_intake())
    paths = build_structural_review_path(_sample_intake(), checklist)

    path_ids = {item.path_id for item in paths}
    assert "mounting_structure_review" in path_ids
    assert "foundation_review" in path_ids
    assert "existing_rooftop_added_load_review" in path_ids
    foundation_path = next(item for item in paths if item.path_id == "foundation_review")
    assert foundation_path.status == "hold"
    assert "地勘报告" in foundation_path.method
