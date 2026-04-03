from structural_screening_agent.photo_assist import build_photo_assist_interface


def test_photo_assist_interface_exposes_targets_and_backfill_boundaries() -> None:
    interface = build_photo_assist_interface("zh")

    assert "拍照" in interface.intro
    assert len(interface.targets) >= 3
    assert any("锁边" in item.title or "夹具" in item.title for item in interface.targets)
    assert any("檩条" in item.title for item in interface.targets)
    assert any("腐蚀" in item.title or "梁柱" in item.title for item in interface.targets)
    assert any("roof_panel_thickness_mm" in item.candidate_backfill_fields for item in interface.targets)
    assert any("purlin_type" in item.candidate_backfill_fields for item in interface.targets)
    assert any("corrosion_condition" in item.candidate_backfill_fields for item in interface.targets)
    assert any("不自动回填" in item for item in interface.boundary_notes)

