from __future__ import annotations

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.models import BVRiskItem
from structural_screening_agent.bv_review.project_state import ProjectReviewState, RFIItem
from structural_screening_agent.bv_review.report import build_bv_open_rfi_items
from structural_screening_agent.bv_review.risk_register import build_calculation_run_risks


class BlockedCalculationReviewDraft(BaseModel):
    risks: list[BVRiskItem] = Field(default_factory=list)
    rfi_items: list[RFIItem] = Field(default_factory=list)


def build_blocked_calculation_review_draft(
    state: ProjectReviewState,
) -> BlockedCalculationReviewDraft:
    blocked_runs = [
        run for run in state.calculation_runs if run.status in {"blocked", "failed"}
    ]
    risks = build_calculation_run_risks(blocked_runs)
    return BlockedCalculationReviewDraft(
        risks=risks,
        rfi_items=build_bv_open_rfi_items(risks),
    )
