from structural_screening_agent.bv_review.basis import build_review_basis
from structural_screening_agent.bv_review.checklist import build_document_checklist
from structural_screening_agent.bv_review.models import BVReviewDecision, BVReviewIntake, BVReviewResult
from structural_screening_agent.bv_review.project_state import ProjectReviewState
from structural_screening_agent.bv_review.report import build_bv_report_preview
from structural_screening_agent.bv_review.review_path import build_structural_review_path
from structural_screening_agent.bv_review.review_plan import build_review_plan
from structural_screening_agent.bv_review.risk_register import build_risk_register


def _resolve_decision(result: BVReviewResult) -> BVReviewDecision:
    if any(item.blocks_report_issue for item in result.risks):
        return "not_ready"
    if any(item.status in {"partial", "missing"} for item in result.checklist_items):
        return "review_with_holds"
    return "ready_for_review"


def evaluate_bv_review(intake: BVReviewIntake) -> BVReviewResult:
    basis = build_review_basis(intake)
    checklist = build_document_checklist(intake)
    review_paths = build_structural_review_path(intake, checklist)
    risks = build_risk_register(intake, checklist, review_paths)
    review_plan = build_review_plan(intake, checklist, review_paths)
    result = BVReviewResult(
        decision="review_with_holds",
        basis_references=basis,
        checklist_items=checklist,
        review_paths=review_paths,
        risks=risks,
        review_plan=review_plan,
    )
    result = result.model_copy(update={"decision": _resolve_decision(result)})
    return result.model_copy(update={"report_preview": build_bv_report_preview(intake, result)})


def build_bv_review_result_from_project_state(
    state: ProjectReviewState,
) -> BVReviewResult:
    result = BVReviewResult(
        decision="review_with_holds",
        basis_references=list(state.basis_references),
        checklist_items=build_document_checklist(state.intake),
        review_paths=list(state.review_paths),
        risks=list(state.risks),
        review_plan=list(state.review_plan),
    )
    result = result.model_copy(update={"decision": _resolve_decision(result)})
    return result.model_copy(
        update={
            "report_preview": build_bv_report_preview(
                state.intake,
                result,
                project_state=state,
            )
        }
    )
