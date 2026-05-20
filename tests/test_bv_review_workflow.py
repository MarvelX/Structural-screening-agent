from structural_screening_agent.bv_review.basis import build_review_basis
from structural_screening_agent.bv_review.checklist import build_document_checklist
from structural_screening_agent.bv_review.models import (
    BVChecklistItem,
    BVReviewIntake,
    BVReviewPathItem,
)
from structural_screening_agent.bv_review.risk_register import build_risk_register
from structural_screening_agent.bv_review.review_plan import build_review_plan
from structural_screening_agent.bv_review.review_path import build_structural_review_path
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


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


def test_foundation_review_path_defines_bearing_capacity_evidence_path() -> None:
    intake = _sample_intake().model_copy(
        update={
            "review_objects": ["foundation"],
            "documents": {
                "calculation_report": "available",
                "technical_specification": "available",
                "geotechnical_report": "available",
                "contract_requirements": "available",
            },
        }
    )
    checklist = build_document_checklist(intake)

    foundation_path = build_structural_review_path(intake, checklist)[0]

    assert foundation_path.status == "ready"
    assert foundation_path.path_id == "foundation_review"
    assert "地基承载力特征值 fak" in foundation_path.required_inputs
    assert "桩径、桩长、桩型和桩间距" in foundation_path.required_inputs
    assert "最不利抗拔力、压力和水平力" in foundation_path.required_inputs
    assert "地勘参数" in foundation_path.method
    assert "基础计算输出" in foundation_path.method
    assert "基础证据路径与承载力审核意见" in foundation_path.deliverables


def test_review_plan_generates_itp_items_with_roles_methods_and_deliverables() -> None:
    checklist = build_document_checklist(_sample_intake())
    paths = build_structural_review_path(_sample_intake(), checklist)
    plan = build_review_plan(_sample_intake(), checklist, paths)

    phases = {item.phase for item in plan}
    assert {"intake", "document_review", "technical_check", "reporting"} <= phases
    assert any(item.responsible_role == "BV structural review engineer" for item in plan)
    assert any("设计审核意见" in item.deliverable or "初筛摘要" in item.deliverable for item in plan)


def test_review_plan_uses_fallback_deliverable_for_paths_without_deliverables() -> None:
    path = BVReviewPathItem(
        path_id="manual_empty_deliverables_review",
        review_object="mounting_structure",
        title="手工空交付物路径",
        method="复核手工构造的审核路径。",
        required_inputs=["项目技术规格书"],
        deliverables=[],
        status="ready",
    )

    plan = build_review_plan(_sample_intake(), [], [path])
    technical_item = next(item for item in plan if item.item_id == path.path_id)

    assert technical_item.phase == "technical_check"
    assert "手工空交付物路径" in technical_item.deliverable
    assert "审核记录" in technical_item.deliverable


def test_risk_register_flags_blocking_missing_documents_and_optimization_items() -> None:
    checklist = build_document_checklist(_sample_intake())
    paths = build_structural_review_path(_sample_intake(), checklist)
    risks = build_risk_register(_sample_intake(), checklist, paths)

    assert any(item.category == "nonconformity" and item.blocks_report_issue for item in risks)
    assert any(item.severity in {"high", "critical"} for item in risks)
    assert any(item.category == "optimization" for item in risks)
    assert any("结构计算书" in item.recommendation for item in risks)
    assert any(
        item.risk_id.startswith("partial_")
        and item.severity == "high"
        and item.blocks_report_issue is False
        for item in risks
    )
    calculation_risk = next(item for item in risks if item.risk_id == "missing_calculation_report")
    assert calculation_risk.linked_field_ids == ["calculation_report"]
    hold_risk = next(item for item in risks if item.risk_id == "review_path_has_holds")
    assert hold_risk.blocks_report_issue is True


def test_risk_register_treats_all_missing_documents_as_blocking_nonconformities() -> None:
    checklist = [
        BVChecklistItem(
            document_key="manually_missing_input",
            title="手工构造缺失资料",
            status="missing",
            affected_review_objects=["mounting_structure"],
            review_blocked=False,
            required_action="补充手工构造缺失资料。",
        )
    ]

    risks = build_risk_register(_sample_intake(), checklist, [])
    missing_risk = next(item for item in risks if item.risk_id == "missing_manually_missing_input")

    assert missing_risk.category == "nonconformity"
    assert missing_risk.severity == "critical"
    assert missing_risk.blocks_report_issue is True
    assert missing_risk.linked_field_ids == ["manually_missing_input"]


def test_bv_review_workflow_composes_basis_checklist_paths_risks_and_plan() -> None:
    result = evaluate_bv_review(_sample_intake())

    assert result.decision == "not_ready"
    assert result.basis_references
    assert result.checklist_items
    assert result.review_paths
    assert result.risks
    assert result.review_plan
    assert any(item.blocks_report_issue for item in result.risks)


def test_bv_review_workflow_marks_review_with_holds_when_only_partial_documents_remain() -> None:
    intake = _sample_intake().model_copy(
        update={
            "documents": {
                "structural_drawings": "partial",
                "calculation_report": "partial",
                "technical_specification": "available",
                "geotechnical_report": "partial",
                "vendor_datasheets": "partial",
                "contract_requirements": "available",
            }
        }
    )

    result = evaluate_bv_review(intake)

    assert result.decision == "review_with_holds"
    assert not any(item.blocks_report_issue for item in result.risks)


def test_bv_review_workflow_marks_ready_when_all_documents_are_available() -> None:
    intake = _sample_intake().model_copy(
        update={
            "documents": {
                "structural_drawings": "available",
                "calculation_report": "available",
                "technical_specification": "available",
                "geotechnical_report": "available",
                "vendor_datasheets": "available",
                "contract_requirements": "available",
            }
        }
    )

    result = evaluate_bv_review(intake)

    assert result.decision == "ready_for_review"
