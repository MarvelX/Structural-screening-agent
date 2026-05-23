from structural_screening_agent.bv_review import (
    ProjectReviewState,
    build_foundation_evidence_path,
)
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.project_state import ExtractedField


def _foundation_intake(documents: dict[str, str]) -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground fixed PV foundation review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb"],
        review_objects=["foundation"],
        documents=documents,
    )


def _field(
    field_id: str,
    value: str,
    *,
    confirmed: bool = True,
    include_in_calculation: bool = True,
) -> ExtractedField:
    return ExtractedField(
        field_id=field_id,
        name=field_id.replace("_", " ").title(),
        candidate_value=value,
        unit="kN" if field_id.endswith("_kn") else None,
        source_document_id="calculation-report-c001",
        page_or_section="Foundation input table",
        quote=f"{field_id} = {value}",
        confidence=0.9,
        is_confirmed=confirmed,
        confirmed_value=value if confirmed else None,
        include_in_calculation=include_in_calculation,
    )


def test_foundation_evidence_path_blocks_when_geotechnical_parameters_are_missing() -> None:
    state = ProjectReviewState(
        project_id="pv-foundation-evidence-gap",
        intake=_foundation_intake(
            {
                "calculation_report": "partial",
                "technical_specification": "available",
                "geotechnical_report": "missing",
            }
        ),
        extracted_fields=[
            _field("pile_diameter_mm", "300"),
            _field("pile_length_m", "3.5"),
            _field(
                "bearing_capacity_characteristic_kpa",
                "180",
                confirmed=False,
                include_in_calculation=False,
            ),
            _field("uplift_force_kn", "140"),
            _field("compression_force_kn", "20"),
            _field("horizontal_force_kn", "12"),
        ],
    )

    path = build_foundation_evidence_path(state)
    geotech = next(item for item in path if item.evidence_id == "geotechnical_parameters")
    reactions = next(item for item in path if item.evidence_id == "foundation_reactions")

    assert geotech.status == "missing"
    assert geotech.blocks_calculation is True
    assert geotech.missing_document_keys == ["geotechnical_report"]
    assert geotech.missing_field_ids == ["side_resistance_standard_kpa"]
    assert geotech.unconfirmed_field_ids == ["bearing_capacity_characteristic_kpa"]
    assert "地勘报告" in geotech.review_action
    assert reactions.status == "partial"
    assert reactions.partial_document_keys == ["calculation_report"]


def test_foundation_evidence_path_is_satisfied_when_documents_and_confirmed_fields_are_ready() -> None:
    required_fields = [
        "pile_diameter_mm",
        "pile_length_m",
        "side_resistance_standard_kpa",
        "bearing_capacity_characteristic_kpa",
        "uplift_force_kn",
        "compression_force_kn",
        "horizontal_force_kn",
    ]
    state = ProjectReviewState(
        project_id="pv-foundation-evidence-ready",
        intake=_foundation_intake(
            {
                "calculation_report": "available",
                "technical_specification": "available",
                "geotechnical_report": "available",
            }
        ),
        extracted_fields=[_field(field_id, "10") for field_id in required_fields],
    )

    path = build_foundation_evidence_path(state)

    assert [item.status for item in path] == ["satisfied", "satisfied", "satisfied"]
    assert all(item.blocks_calculation is False for item in path)
    assert path[0].confirmed_field_ids == [
        "bearing_capacity_characteristic_kpa",
        "side_resistance_standard_kpa",
    ]
    assert "基础筛查级计算" in path[-1].review_action
