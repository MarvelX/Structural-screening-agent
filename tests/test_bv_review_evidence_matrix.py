from structural_screening_agent.bv_review import (
    DocumentVersion,
    EvidenceMatrixItem,
    ExtractedField,
    ProjectReviewState,
    build_evidence_matrix,
)
from structural_screening_agent.bv_review.models import BVRiskItem, BVReviewIntake


def test_evidence_matrix_links_findings_to_fields_documents_and_missing_evidence() -> None:
    state = ProjectReviewState(
        project_id="pv-evidence-matrix",
        intake=BVReviewIntake(
            project_name="Ground PV evidence matrix",
            country_or_region="China",
            project_type="utility_pv",
            design_stage="detailed_design",
            standards_systems=["gb"],
            review_objects=["foundation"],
            documents={
                "geotechnical_report": "available",
                "calculation_report": "missing",
            },
        ),
        document_versions=[
            DocumentVersion(
                document_id="geo-r1",
                document_type="geotechnical_report",
                revision="R1",
                source_name="Geotechnical report package",
                status="available",
            )
        ],
        extracted_fields=[
            ExtractedField(
                field_id="bearing_capacity_characteristic_kpa",
                name="Bearing capacity characteristic value",
                candidate_value="180",
                unit="kPa",
                source_document_id="geo-r1",
                page_or_section="Section 4.2",
                quote="fak = 180 kPa",
                confidence=0.91,
                is_confirmed=True,
                confirmed_value="180",
                confirmed_unit="kPa",
                include_in_calculation=True,
            )
        ],
        risks=[
            BVRiskItem(
                risk_id="foundation_evidence_blocked_geotechnical_parameters",
                title="地勘参数证据不足",
                severity="critical",
                trigger_basis="缺少地勘参数证据。",
                linked_field_ids=[
                    "bearing_capacity_characteristic_kpa",
                    "geotechnical_report",
                    "side_resistance_standard_kpa",
                ],
                impact_scope="基础筛查级计算",
                recommendation="补充地勘参数。",
                blocks_report_issue=True,
                category="nonconformity",
            )
        ],
    )

    matrix = build_evidence_matrix(state)

    assert all(isinstance(item, EvidenceMatrixItem) for item in matrix)
    assert [
        (item.linked_id, item.source_type, item.source_document_id, item.evidence_status)
        for item in matrix
    ] == [
        (
            "bearing_capacity_characteristic_kpa",
            "field",
            "geo-r1",
            "confirmed",
        ),
        ("geotechnical_report", "document", "geo-r1", "available"),
        ("side_resistance_standard_kpa", "missing", "", "missing"),
    ]
    assert matrix[0].source_location == "Section 4.2"
    assert matrix[0].evidence_excerpt == "fak = 180 kPa"
    assert matrix[0].confidence == 0.91
    assert matrix[1].source_location == "Revision R1"
    assert matrix[1].evidence_excerpt == "Geotechnical report package"
    assert matrix[2].evidence_excerpt == (
        "No extracted field, document version, or intake document status is available."
    )


def test_evidence_matrix_uses_intake_document_status_when_version_is_absent() -> None:
    state = ProjectReviewState(
        project_id="pv-evidence-matrix-intake",
        intake=BVReviewIntake(
            project_name="Ground PV evidence matrix",
            country_or_region="China",
            project_type="utility_pv",
            design_stage="detailed_design",
            standards_systems=["gb"],
            review_objects=["foundation"],
            documents={"geotechnical_report": "partial"},
        ),
        risks=[
            BVRiskItem(
                risk_id="risk-geotech",
                title="地勘报告部分提供",
                severity="high",
                trigger_basis="地勘报告缺少侧阻力参数。",
                linked_field_ids=["geotechnical_report"],
                impact_scope="基础筛查级计算",
                recommendation="补充完整地勘报告。",
                blocks_report_issue=True,
                category="risk",
            )
        ],
    )

    matrix = build_evidence_matrix(state)

    assert len(matrix) == 1
    assert matrix[0].source_type == "document"
    assert matrix[0].source_document_id == "geotechnical_report"
    assert matrix[0].source_location == "Intake document status"
    assert matrix[0].evidence_excerpt == "partial"
    assert matrix[0].evidence_status == "partial"
