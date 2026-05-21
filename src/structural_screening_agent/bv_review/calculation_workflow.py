from __future__ import annotations

from structural_screening_agent.bv_review.calculation_engines import (
    FOUNDATION_FIELD_IDS,
    SUPERSTRUCTURE_FIELD_IDS,
    build_foundation_calculation_run_from_fields,
    build_superstructure_calculation_run_from_fields,
)
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    ProjectReviewState,
    RFIItem,
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


def build_incremental_calculation_recheck_runs_for_rfi(
    state: ProjectReviewState,
    *,
    rfi_id: str,
    run_id_prefix: str = "incremental-recheck",
) -> list[CalculationRun]:
    if not state.is_gate_locked("calculation"):
        return []

    rfi = _find_unique_rfi(state, rfi_id)
    if not rfi.triggers_incremental_recheck:
        return []

    field_ids = _field_ids_for_rfi(rfi)
    engine_names = _affected_engine_names(field_ids, state.calculation_runs)
    locked_fields = state.locked_calculation_fields()
    slug = _slug(rfi.rfi_id)
    runs: list[CalculationRun] = []

    if "foundation" in engine_names:
        runs.append(
            build_foundation_calculation_run_from_fields(
                run_id=f"{run_id_prefix}-{slug}-foundation-001",
                fields=locked_fields,
            )
        )
    if "superstructure" in engine_names:
        member_id, member_type = _superstructure_member_identity(state.calculation_runs)
        runs.append(
            build_superstructure_calculation_run_from_fields(
                run_id=f"{run_id_prefix}-{slug}-superstructure-001",
                fields=locked_fields,
                member_id=member_id,
                member_type=member_type,
            )
        )

    return runs


def run_incremental_calculation_recheck_for_rfi(
    state: ProjectReviewState,
    *,
    rfi_id: str,
) -> ProjectReviewState:
    if not state.is_gate_locked("calculation"):
        raise ValueError("Calculation gate must be locked before incremental recheck.")

    rfi = _find_unique_rfi(state, rfi_id)
    if rfi.status != "responded":
        raise ValueError("Only responded RFI items can run deterministic recheck.")
    if not rfi.triggers_incremental_recheck:
        raise ValueError("RFI item does not trigger incremental recheck.")

    recheck_runs = build_incremental_calculation_recheck_runs_for_rfi(
        state,
        rfi_id=rfi_id,
    )
    if not recheck_runs:
        raise ValueError("No deterministic calculation recheck runs were generated.")

    all_completed = all(run.status == "completed" for run in recheck_runs)
    updated_rfi = rfi.model_copy(
        update={
            "completed_recheck_items": (
                list(rfi.reopen_review_items)
                if all_completed
                else list(rfi.completed_recheck_items)
            )
        }
    )
    recheck_run_ids = {run.run_id for run in recheck_runs}
    calculation_runs = [
        run for run in state.calculation_runs if run.run_id not in recheck_run_ids
    ]
    phase_statuses = dict(state.phase_statuses)
    phase_statuses["calculation_check"] = (
        "waiting_for_engineer" if all_completed else "blocked"
    )
    phase_statuses["issue_rfi_closeout"] = "waiting_for_engineer"
    return state.model_copy(
        update={
            "current_phase": "issue_rfi_closeout",
            "phase_statuses": phase_statuses,
            "calculation_runs": [*calculation_runs, *recheck_runs],
            "rfi_items": _replace_rfi(state.rfi_items, updated_rfi),
        }
    )


def _find_unique_rfi(state: ProjectReviewState, rfi_id: str) -> RFIItem:
    matches = [item for item in state.rfi_items if item.rfi_id == rfi_id]
    if not matches:
        raise ValueError(f"RFI item {rfi_id!r} does not exist.")
    if len(matches) > 1:
        raise ValueError(f"RFI item {rfi_id!r} is duplicated in project state.")
    return matches[0]


def _replace_rfi(rfi_items: list[RFIItem], updated_rfi: RFIItem) -> list[RFIItem]:
    return [
        updated_rfi if item.rfi_id == updated_rfi.rfi_id else item
        for item in rfi_items
    ]


def _field_ids_for_rfi(rfi: RFIItem) -> set[str]:
    field_ids: set[str] = set()
    for review_item_id in rfi.reopen_review_items:
        field_ids.update(_field_ids_from_review_item(review_item_id))
    for item in rfi.required_document_or_field.split(","):
        value = item.strip()
        if value:
            field_ids.update(_field_ids_from_review_item(value))
    return field_ids


def _field_ids_from_review_item(review_item_id: str) -> list[str]:
    for prefix in ("calculation-recheck-", "risk-reopen-"):
        if review_item_id.startswith(prefix):
            return [review_item_id.removeprefix(prefix)]
    if review_item_id.startswith("rfi-"):
        return []
    return [review_item_id]


def _affected_engine_names(
    field_ids: set[str],
    calculation_runs: list[CalculationRun],
) -> list[str]:
    engine_names: list[str] = []
    for run in calculation_runs:
        if run.engine_name in engine_names:
            continue
        if any(field_id in run.input_field_ids for field_id in field_ids):
            engine_names.append(run.engine_name)

    if "foundation" not in engine_names and field_ids.intersection(FOUNDATION_FIELD_IDS):
        engine_names.append("foundation")
    if "superstructure" not in engine_names and field_ids.intersection(SUPERSTRUCTURE_FIELD_IDS):
        engine_names.append("superstructure")

    return engine_names


def _superstructure_member_identity(
    calculation_runs: list[CalculationRun],
) -> tuple[str, str]:
    for run in calculation_runs:
        if run.engine_name != "superstructure":
            continue
        member_id = run.result_summary.get("member_id")
        member_type = run.result_summary.get("member_type")
        if isinstance(member_id, str) and member_type in {"post", "beam", "purlin", "brace"}:
            return member_id, str(member_type)
    return "post-P1", "post"


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-")
