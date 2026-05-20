from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    ProjectReviewState,
    RFIItem,
)
from structural_screening_agent.bv_review.service_scope import (
    build_service_scope_display_rows,
    build_service_scope_recommendations,
)
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def test_service_scope_recommendations_are_triggered_by_traceable_review_evidence() -> None:
    intake = _sample_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-service-scope",
        intake=intake,
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["pile_length_m", "uplift_force_kn"],
                input_locked=True,
                status="completed",
                result_summary={
                    "controlling_utilization_ratio": 1.12,
                    "screening_status": "review_required",
                    "screening_boundary": "screening-level check only",
                },
            )
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-run-001",
                question="Please provide updated foundation reaction table.",
                responsible_party="client / designer",
                trigger_basis="Foundation calculation run requires clarification.",
                required_document_or_field="uplift_force_kn",
                status="open",
                reopen_review_items=["uplift_force_kn"],
                triggers_incremental_recheck=True,
            )
        ],
    )

    recommendations = build_service_scope_recommendations(
        intake,
        result,
        project_state=state,
    )

    recommendation_ids = {item.recommendation_id for item in recommendations}
    assert "document_completeness_rfi_support" in recommendation_ids
    assert "rfi_closeout_management" in recommendation_ids
    assert "calculation_spot_check_follow_up" in recommendation_ids
    assert "constructability_optimization_review" in recommendation_ids
    assert all(item.trigger_evidence_ids for item in recommendations)
    assert all("不替代" in item.boundary_statement for item in recommendations)
    assert not any("官方签发" in item.client_value for item in recommendations)


def test_service_scope_display_rows_are_localized_for_streamlit_tables() -> None:
    recommendations = build_service_scope_recommendations(
        _sample_intake(),
        evaluate_bv_review(_sample_intake()),
    )

    zh_rows = build_service_scope_display_rows(recommendations, "zh")
    en_rows = build_service_scope_display_rows(recommendations, "en")

    assert zh_rows[0]["服务方向"] == "资料完整性与 RFI 关闭支持"
    assert zh_rows[0]["优先级"] == "高"
    assert en_rows[0]["Service Scope"] == "Document completeness and RFI closeout support"
    assert en_rows[0]["Priority"] == "High"
    assert "does not replace formal design" in en_rows[0]["Boundary"]


def test_service_scope_recommendations_do_not_create_unsupported_sales_items() -> None:
    intake = BVReviewIntake(
        project_name="Clean foundation-only review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb"],
        review_objects=["foundation"],
        documents={
            "calculation_report": "available",
            "technical_specification": "available",
            "geotechnical_report": "available",
            "contract_requirements": "available",
        },
    )
    result = evaluate_bv_review(intake)

    recommendations = build_service_scope_recommendations(intake, result)

    assert recommendations == []


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
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
