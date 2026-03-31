from structural_screening_agent.demo_data import all_demo_cases, main_demo_case


def test_main_demo_case_matches_warehouse_pv_priority() -> None:
    intake = main_demo_case()
    assert intake.project_type == "rooftop_pv"
    assert "warehouse" in intake.building_type.lower()
    assert "steel" in intake.structural_system.lower()


def test_demo_library_contains_three_cases() -> None:
    demo_cases = all_demo_cases()
    assert len(demo_cases) == 3
    assert "main_warehouse_pv" in demo_cases
    assert "warehouse_upgrade" in demo_cases
    assert "industrial_retrofit" in demo_cases
