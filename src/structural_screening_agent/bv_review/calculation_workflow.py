from __future__ import annotations

from structural_screening_agent.bv_review.calculation_engines import (
    build_foundation_calculation_run_from_fields,
    build_superstructure_calculation_run_from_fields,
)
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    ProjectReviewState,
)


FOUNDATION_RUN_ID = "foundation-run-001"
SUPERSTRUCTURE_POST_RUN_ID = "superstructure-run-post-P1-001"


def build_calculation_runs_from_locked_fields(
    state: ProjectReviewState,
) -> list[CalculationRun]:
    if not state.is_gate_locked("calculation"):
        return []

    locked_fields = state.locked_calculation_fields()
    return [
        build_foundation_calculation_run_from_fields(
            run_id=FOUNDATION_RUN_ID,
            fields=locked_fields,
        ),
        build_superstructure_calculation_run_from_fields(
            run_id=SUPERSTRUCTURE_POST_RUN_ID,
            fields=locked_fields,
            member_id="post-P1",
            member_type="post",
        ),
    ]
