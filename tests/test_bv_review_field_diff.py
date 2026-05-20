from structural_screening_agent.bv_review.field_diff import (
    build_incremental_recheck_plan,
    diff_extracted_fields,
)
from structural_screening_agent.bv_review.models import BVRiskItem
from structural_screening_agent.bv_review.project_state import CalculationRun, ExtractedField


def _field(
    field_id: str,
    value: str,
    *,
    unit: str | None = None,
    source: str = "doc-v1",
    page: str = "Section 1",
    quote: str = "Original value",
    confirmed: bool = False,
    include_in_calculation: bool = False,
) -> ExtractedField:
    return ExtractedField(
        field_id=field_id,
        name=field_id.replace("_", " ").title(),
        candidate_value=value,
        unit=unit,
        source_document_id=source,
        page_or_section=page,
        quote=quote,
        confidence=0.9,
        is_confirmed=confirmed,
        confirmed_value=value if confirmed else None,
        confirmed_unit=unit if confirmed else None,
        include_in_calculation=include_in_calculation,
    )


def test_field_diff_detects_added_modified_removed_and_source_changed_fields() -> None:
    old_fields = [
        _field("tilt_angle_deg", "25", unit="deg"),
        _field("pile_length_m", "3.5", unit="m"),
        _field("snow_load_kpa", "0.35", unit="kPa"),
        _field("bearing_capacity_kpa", "180", unit="kPa", source="geo-v1", quote="fak=180kPa"),
    ]
    new_fields = [
        _field("tilt_angle_deg", "25", unit="deg"),
        _field("pile_length_m", "4.0", unit="m"),
        _field("wind_pressure_kpa", "0.45", unit="kPa"),
        _field("bearing_capacity_kpa", "180", unit="kPa", source="geo-v2", quote="fak=180kPa updated source"),
    ]

    diffs = diff_extracted_fields(old_fields, new_fields)
    diff_by_id = {diff.field_id: diff for diff in diffs}

    assert "tilt_angle_deg" not in diff_by_id
    assert diff_by_id["pile_length_m"].diff_type == "modified"
    assert diff_by_id["wind_pressure_kpa"].diff_type == "added"
    assert diff_by_id["snow_load_kpa"].diff_type == "removed"
    assert diff_by_id["bearing_capacity_kpa"].diff_type == "source_changed"


def test_field_diff_rejects_duplicate_field_ids() -> None:
    duplicate_fields = [
        _field("pile_length_m", "3.5", unit="m"),
        _field("pile_length_m", "4.0", unit="m"),
    ]

    try:
        diff_extracted_fields(duplicate_fields, [])
    except ValueError as exc:
        assert "Duplicate field_id" in str(exc)
        assert "pile_length_m" in str(exc)
    else:
        raise AssertionError("duplicate field_id values should be rejected")


def test_field_diff_marks_changed_confirmed_calculation_field_as_affecting_locked_inputs() -> None:
    diffs = diff_extracted_fields(
        [_field("pile_length_m", "3.5", unit="m", confirmed=True, include_in_calculation=True)],
        [_field("pile_length_m", "4.0", unit="m", confirmed=True, include_in_calculation=True)],
        calculation_runs=[
            CalculationRun(
                run_id="run-001",
                engine_name="foundation",
                engine_version="phase1-human-gate",
                input_field_ids=["pile_length_m"],
                input_locked=True,
                status="ready",
            )
        ],
    )

    assert diffs[0].affects_confirmed_calculation is True
    assert diffs[0].affected_calculation_run_ids == ["run-001"]


def test_field_diff_ignores_non_calculation_note_changes_for_recheck() -> None:
    diffs = diff_extracted_fields(
        [_field("drawing_note", "Issued for review")],
        [_field("drawing_note", "Issued for construction")],
    )

    assert diffs[0].diff_type == "modified"
    assert diffs[0].affects_confirmed_calculation is False
    assert diffs[0].should_reopen_risk_items is False


def test_incremental_recheck_plan_creates_calculation_recheck_for_locked_run_input_change() -> None:
    diffs = diff_extracted_fields(
        [_field("pile_length_m", "3.5", unit="m", confirmed=True, include_in_calculation=True)],
        [_field("pile_length_m", "4.0", unit="m", confirmed=True, include_in_calculation=True)],
        calculation_runs=[
            CalculationRun(
                run_id="run-001",
                engine_name="foundation",
                engine_version="phase1-human-gate",
                input_field_ids=["pile_length_m"],
                input_locked=True,
                status="ready",
            )
        ],
    )

    plan = build_incremental_recheck_plan(diffs)

    assert any(item.item_type == "calculation_recheck" for item in plan.affected_items)
    assert plan.rfi_items[0].triggers_incremental_recheck is True


def test_incremental_recheck_plan_reopens_matching_risk_items_for_required_document_change() -> None:
    diffs = diff_extracted_fields(
        [_field("geotechnical_report", "missing")],
        [_field("geotechnical_report", "available", source="geo-v2")],
        risks=[
            BVRiskItem(
                risk_id="missing_geotechnical_report",
                title="Missing geotechnical report",
                severity="critical",
                trigger_basis="Missing geotechnical report",
                linked_field_ids=["geotechnical_report"],
                impact_scope="Foundation review",
                recommendation="Provide geotechnical report.",
                blocks_report_issue=True,
                category="nonconformity",
            )
        ],
    )

    plan = build_incremental_recheck_plan(diffs)

    assert diffs[0].should_reopen_risk_items is True
    assert diffs[0].affected_risk_ids == ["missing_geotechnical_report"]
    assert any(item.item_type == "risk_reopen" for item in plan.affected_items)


def test_field_diff_does_not_reopen_risk_items_from_string_similarity_without_linked_fields() -> None:
    diffs = diff_extracted_fields(
        [_field("geotechnical_report", "missing")],
        [_field("geotechnical_report", "available", source="geo-v2")],
        risks=[
            BVRiskItem(
                risk_id="missing_geotechnical_report",
                title="Missing geotechnical report",
                severity="critical",
                trigger_basis="Missing geotechnical report",
                impact_scope="Foundation review",
                recommendation="Provide geotechnical report.",
                blocks_report_issue=True,
                category="nonconformity",
            )
        ],
    )

    assert diffs[0].should_reopen_risk_items is False
    assert diffs[0].affected_risk_ids == []


def test_incremental_recheck_plan_creates_rfi_item_without_agent_generated_language() -> None:
    diffs = diff_extracted_fields(
        [_field("pile_length_m", "3.5", unit="m", confirmed=True, include_in_calculation=True)],
        [_field("pile_length_m", "4.0", unit="m", confirmed=True, include_in_calculation=True)],
    )

    plan = build_incremental_recheck_plan(diffs, rfi_prefix="rfi-demo")

    assert plan.rfi_items[0].rfi_id == "rfi-demo-pile_length_m"
    assert plan.rfi_items[0].responsible_party == "client"
    assert "Please confirm updated input" in plan.rfi_items[0].question
    assert "AI" not in plan.rfi_items[0].question
