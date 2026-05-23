from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.models import BVRiskItem
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    ExtractedField,
    FieldValue,
    RFIItem,
)


FieldDiffType = Literal["added", "modified", "removed", "source_changed"]


class FieldDiff(BaseModel):
    field_id: str = Field(min_length=1)
    field_name: str = Field(min_length=1)
    diff_type: FieldDiffType
    old_value: Optional[FieldValue] = None
    new_value: Optional[FieldValue] = None
    old_unit: Optional[str] = None
    new_unit: Optional[str] = None
    old_source_document_id: Optional[str] = None
    new_source_document_id: Optional[str] = None
    affects_confirmed_calculation: bool = False
    should_reopen_risk_items: bool = False
    affected_calculation_run_ids: list[str] = Field(default_factory=list)
    affected_risk_ids: list[str] = Field(default_factory=list)


class AffectedReviewItem(BaseModel):
    item_id: str = Field(min_length=1)
    item_type: Literal["field_confirmation", "calculation_recheck", "risk_reopen", "rfi"]
    reason: str = Field(min_length=1)
    field_ids: list[str] = Field(default_factory=list)
    calculation_run_ids: list[str] = Field(default_factory=list)
    risk_ids: list[str] = Field(default_factory=list)


class IncrementalRecheckPlan(BaseModel):
    diffs: list[FieldDiff] = Field(default_factory=list)
    affected_items: list[AffectedReviewItem] = Field(default_factory=list)
    rfi_items: list[RFIItem] = Field(default_factory=list)


def _source_tuple(field: ExtractedField) -> tuple[str, str, str]:
    return (field.source_document_id, field.page_or_section, field.quote)


def _value_or_unit_changed(old_field: ExtractedField, new_field: ExtractedField) -> bool:
    return (
        old_field.candidate_value != new_field.candidate_value
        or old_field.unit != new_field.unit
    )


def _find_affected_run_ids(field_id: str, calculation_runs: list[CalculationRun]) -> list[str]:
    return [
        run.run_id
        for run in calculation_runs
        if run.input_locked and field_id in run.input_field_ids
    ]


def _matching_risk_ids(field_id: str, risks: list[BVRiskItem]) -> list[str]:
    return [risk.risk_id for risk in risks if field_id in risk.linked_field_ids]


def _index_fields_by_id(fields: list[ExtractedField], label: str) -> dict[str, ExtractedField]:
    indexed: dict[str, ExtractedField] = {}
    duplicate_ids: list[str] = []
    for field in fields:
        if field.field_id in indexed:
            duplicate_ids.append(field.field_id)
        indexed[field.field_id] = field
    if duplicate_ids:
        raise ValueError(f"Duplicate field_id values in {label}: {', '.join(sorted(set(duplicate_ids)))}.")
    return indexed


def _build_diff(
    *,
    field_id: str,
    field_name: str,
    diff_type: FieldDiffType,
    old_field: Optional[ExtractedField] = None,
    new_field: Optional[ExtractedField] = None,
    calculation_runs: list[CalculationRun],
    risks: list[BVRiskItem],
) -> FieldDiff:
    affected_run_ids = _find_affected_run_ids(field_id, calculation_runs)
    affected_risk_ids = _matching_risk_ids(field_id, risks)
    old_affects_calculation = bool(
        old_field and old_field.is_confirmed and old_field.include_in_calculation
    )
    new_affects_calculation = bool(new_field and new_field.include_in_calculation)

    return FieldDiff(
        field_id=field_id,
        field_name=field_name,
        diff_type=diff_type,
        old_value=old_field.candidate_value if old_field else None,
        new_value=new_field.candidate_value if new_field else None,
        old_unit=old_field.unit if old_field else None,
        new_unit=new_field.unit if new_field else None,
        old_source_document_id=old_field.source_document_id if old_field else None,
        new_source_document_id=new_field.source_document_id if new_field else None,
        affects_confirmed_calculation=bool(
            old_affects_calculation or new_affects_calculation or affected_run_ids
        ),
        should_reopen_risk_items=bool(affected_risk_ids),
        affected_calculation_run_ids=affected_run_ids,
        affected_risk_ids=affected_risk_ids,
    )


def diff_extracted_fields(
    old_fields: list[ExtractedField],
    new_fields: list[ExtractedField],
    *,
    calculation_runs: Optional[list[CalculationRun]] = None,
    risks: Optional[list[BVRiskItem]] = None,
) -> list[FieldDiff]:
    runs = calculation_runs or []
    risk_items = risks or []
    old_by_id = _index_fields_by_id(old_fields, "old_fields")
    new_by_id = _index_fields_by_id(new_fields, "new_fields")
    diffs: list[FieldDiff] = []

    for field_id in sorted(set(old_by_id) | set(new_by_id)):
        old_field = old_by_id.get(field_id)
        new_field = new_by_id.get(field_id)
        if old_field is None and new_field is not None:
            diffs.append(
                _build_diff(
                    field_id=field_id,
                    field_name=new_field.name,
                    diff_type="added",
                    new_field=new_field,
                    calculation_runs=runs,
                    risks=risk_items,
                )
            )
        elif old_field is not None and new_field is None:
            diffs.append(
                _build_diff(
                    field_id=field_id,
                    field_name=old_field.name,
                    diff_type="removed",
                    old_field=old_field,
                    calculation_runs=runs,
                    risks=risk_items,
                )
            )
        elif old_field is not None and new_field is not None:
            if _value_or_unit_changed(old_field, new_field):
                diffs.append(
                    _build_diff(
                        field_id=field_id,
                        field_name=new_field.name,
                        diff_type="modified",
                        old_field=old_field,
                        new_field=new_field,
                        calculation_runs=runs,
                        risks=risk_items,
                    )
                )
            elif _source_tuple(old_field) != _source_tuple(new_field):
                diffs.append(
                    _build_diff(
                        field_id=field_id,
                        field_name=new_field.name,
                        diff_type="source_changed",
                        old_field=old_field,
                        new_field=new_field,
                        calculation_runs=runs,
                        risks=risk_items,
                    )
                )

    return diffs


def build_incremental_recheck_plan(
    diffs: list[FieldDiff],
    *,
    rfi_prefix: str = "rfi",
    opened_at: Optional[str] = None,
) -> IncrementalRecheckPlan:
    affected_items: list[AffectedReviewItem] = []
    rfi_items: list[RFIItem] = []
    rfi_opened_at = _rfi_opened_date(opened_at)

    for diff in diffs:
        if diff.affects_confirmed_calculation:
            item_id = f"calculation-recheck-{diff.field_id}"
            affected_items.append(
                AffectedReviewItem(
                    item_id=item_id,
                    item_type="calculation_recheck",
                    reason=f"{diff.field_name} changed and affects locked calculation inputs.",
                    field_ids=[diff.field_id],
                    calculation_run_ids=list(diff.affected_calculation_run_ids),
                )
            )
        if diff.should_reopen_risk_items:
            affected_items.append(
                AffectedReviewItem(
                    item_id=f"risk-reopen-{diff.field_id}",
                    item_type="risk_reopen",
                    reason=f"{diff.field_name} changed and may reopen linked risk items.",
                    field_ids=[diff.field_id],
                    risk_ids=list(diff.affected_risk_ids),
                )
            )
        if diff.affects_confirmed_calculation or diff.should_reopen_risk_items:
            rfi_items.append(
                RFIItem(
                    rfi_id=f"{rfi_prefix}-{diff.field_id}",
                    question=f"Please confirm updated input for {diff.field_name}.",
                    responsible_party="client",
                    trigger_basis=(
                        f"Field {diff.field_id} changed from {diff.old_value!r} to {diff.new_value!r}."
                    ),
                    required_document_or_field=diff.field_id,
                    status="open",
                    opened_at=rfi_opened_at,
                    reopen_review_items=[item.item_id for item in affected_items if diff.field_id in item.field_ids],
                    triggers_incremental_recheck=diff.affects_confirmed_calculation,
                )
            )

    return IncrementalRecheckPlan(
        diffs=diffs,
        affected_items=affected_items,
        rfi_items=rfi_items,
    )


def _rfi_opened_date(opened_at: Optional[str]) -> str:
    if opened_at:
        return opened_at[:10]
    return date.today().isoformat()


def build_incremental_recheck_plan_from_closed_rfis(
    rfi_items: list[RFIItem],
    *,
    calculation_runs: Optional[list[CalculationRun]] = None,
) -> IncrementalRecheckPlan:
    runs = select_latest_calculation_evidence_runs(calculation_runs or [])
    closed_rfis = [
        item
        for item in rfi_items
        if rfi_incremental_recheck_is_complete(item)
    ]
    affected_items: list[AffectedReviewItem] = []
    seen_item_ids: set[str] = set()

    for rfi in closed_rfis:
        for review_item_id in rfi.reopen_review_items:
            if review_item_id in seen_item_ids:
                continue
            seen_item_ids.add(review_item_id)
            field_ids = _field_ids_from_review_item(review_item_id)
            affected_items.append(
                AffectedReviewItem(
                    item_id=review_item_id,
                    item_type=_item_type_from_review_item(review_item_id),
                    reason=f"Closed RFI {rfi.rfi_id} requires completed incremental recheck.",
                    field_ids=field_ids,
                    calculation_run_ids=_run_ids_for_fields(field_ids, runs),
                )
            )

    return IncrementalRecheckPlan(
        diffs=[],
        affected_items=affected_items,
        rfi_items=closed_rfis,
    )


def rfi_incremental_recheck_is_complete(rfi: RFIItem) -> bool:
    required_items = set(rfi.reopen_review_items)
    completed_items = set(rfi.completed_recheck_items)
    return (
        rfi.triggers_incremental_recheck
        and rfi.status == "closed"
        and bool(required_items)
        and completed_items == required_items
    )


def select_latest_calculation_evidence_runs(
    calculation_runs: list[CalculationRun],
) -> list[CalculationRun]:
    covered_incremental_fields_by_engine: dict[str, set[str]] = {}
    selected_reversed: list[CalculationRun] = []

    for run in reversed(calculation_runs):
        covered_fields = covered_incremental_fields_by_engine.get(run.engine_name, set())
        run_fields = set(run.input_field_ids)
        if run_fields and covered_fields.intersection(run_fields):
            continue

        selected_reversed.append(run)
        if _is_incremental_recheck_run(run):
            covered_incremental_fields_by_engine.setdefault(
                run.engine_name,
                set(),
            ).update(run_fields)

    return list(reversed(selected_reversed))


def _is_incremental_recheck_run(run: CalculationRun) -> bool:
    return run.run_id.startswith("incremental-recheck-")


def _item_type_from_review_item(
    review_item_id: str,
) -> Literal["field_confirmation", "calculation_recheck", "risk_reopen", "rfi"]:
    if review_item_id.startswith("calculation-recheck-"):
        return "calculation_recheck"
    if review_item_id.startswith("risk-reopen-"):
        return "risk_reopen"
    if review_item_id.startswith("rfi-"):
        return "rfi"
    return "field_confirmation"


def _field_ids_from_review_item(review_item_id: str) -> list[str]:
    for prefix in ("calculation-recheck-", "risk-reopen-"):
        if review_item_id.startswith(prefix):
            return [review_item_id.removeprefix(prefix)]
    if review_item_id.startswith("rfi-"):
        return []
    return [review_item_id]


def _run_ids_for_fields(
    field_ids: list[str],
    calculation_runs: list[CalculationRun],
) -> list[str]:
    if not field_ids:
        return []
    matched_run_ids: list[str] = []
    for run in calculation_runs:
        if not run.input_locked:
            continue
        if any(field_id in run.input_field_ids for field_id in field_ids):
            matched_run_ids.append(run.run_id)
    return matched_run_ids
