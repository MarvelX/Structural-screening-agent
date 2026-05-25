from pathlib import Path

from structural_screening_agent.bv_review.agent_extraction_eval import (
    load_extraction_cases,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_load_extraction_cases_reads_curated_golden_cases() -> None:
    cases = load_extraction_cases(FIXTURE_DIR / "bv_agent_extraction_cases.json")

    assert len(cases) == 10
    assert cases[0].case_id == "pv-cn-ground-fixed-foundation-001"
    assert cases[0].language == "zh"
    assert cases[0].scenario == "ground_fixed_foundation"
    assert cases[0].expected_fields[0].field_id == "tilt_angle_deg"
    assert cases[0].expected_fields[0].expected_value == 25
    assert "steel_grade" in cases[0].must_not_extract
