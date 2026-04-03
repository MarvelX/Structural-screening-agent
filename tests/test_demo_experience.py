from structural_screening_agent.app_state import demo_case_catalog, ordered_demo_keys


def test_main_demo_is_featured_and_sorted_first() -> None:
    catalog = demo_case_catalog("zh")
    ordered_keys = ordered_demo_keys()

    assert ordered_keys == ["main_warehouse_pv"]
    assert ordered_keys[0] == "main_warehouse_pv"
    assert catalog["main_warehouse_pv"]["featured"] is True
    assert "门式刚架" in catalog["main_warehouse_pv"]["label"]
    assert "结构初筛复核" in catalog["main_warehouse_pv"]["note"]


def test_main_demo_has_fixed_four_step_usage_flow() -> None:
    catalog = demo_case_catalog("zh")
    steps = catalog["main_warehouse_pv"]["narrative_steps"]

    assert len(steps) == 4
    assert "门式刚架几何" in steps[0]
    assert "图纸、计算书、现场核查" in steps[1]
    assert "简化计算结果" in steps[2]
    assert "结构初筛摘要" in steps[3]
