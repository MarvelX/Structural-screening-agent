from structural_screening_agent.app_state import demo_case_catalog, ordered_demo_keys


def test_main_demo_is_featured_and_sorted_first() -> None:
    catalog = demo_case_catalog("zh")
    ordered_keys = ordered_demo_keys()

    assert ordered_keys[0] == "main_warehouse_pv"
    assert catalog["main_warehouse_pv"]["featured"] is True
    assert "推荐案例" in catalog["main_warehouse_pv"]["label"]
    assert "面试" not in catalog["main_warehouse_pv"]["note"]


def test_main_demo_has_fixed_four_step_usage_flow() -> None:
    catalog = demo_case_catalog("zh")
    steps = catalog["main_warehouse_pv"]["narrative_steps"]

    assert len(steps) == 4
    assert "先录入项目条件和证据状态" in steps[0]
    assert "再看管理层摘要" in steps[1]
    assert "专项复核触发项" in steps[2]
    assert "优先方案" in steps[3]
