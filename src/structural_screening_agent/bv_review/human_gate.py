from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    EngineerApproval,
    ExtractedField,
)


def fields_ready_for_calculation(fields: list[ExtractedField]) -> bool:
    calculation_fields = [field for field in fields if field.include_in_calculation]
    if not calculation_fields:
        return False

    return all(
        field.is_confirmed and field.confirmed_value not in (None, "")
        for field in calculation_fields
    )


def build_engineer_approval(
    approval_id: str, target_id: str, reviewer: str, comment: str = ""
) -> EngineerApproval:
    return EngineerApproval(
        approval_id=approval_id,
        target_type="gate",
        target_id=target_id,
        status="approved",
        reviewer=reviewer,
        comment=comment,
        locked=True,
    )


def build_calculation_gate_run(
    run_id: str,
    engine_name: str,
    fields: list[ExtractedField],
) -> CalculationRun:
    calculation_fields = [field for field in fields if field.include_in_calculation]
    if not fields_ready_for_calculation(fields):
        return CalculationRun(
            run_id=run_id,
            engine_name=engine_name,
            engine_version="phase1-human-gate",
            input_field_ids=[field.field_id for field in calculation_fields],
            input_locked=False,
            status="blocked",
            structured_errors=[
                "Calculation gate requires at least one engineer-confirmed field marked for calculation."
            ],
        )

    return CalculationRun(
        run_id=run_id,
        engine_name=engine_name,
        engine_version="phase1-human-gate",
        input_field_ids=[field.field_id for field in calculation_fields],
        input_locked=True,
        status="ready",
    )
