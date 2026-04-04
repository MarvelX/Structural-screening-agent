from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.app_state import evaluate_case
from structural_screening_agent.presentation import build_workbench_view


def test_workbench_view_prioritizes_decision_and_main_option() -> None:
    evaluation = evaluate_case(
        main_demo_case().model_dump()
    )

    view = build_workbench_view(evaluation)

    assert view.hero_decision == "有条件推进"
    assert view.hero_tone == "amber"
    assert len(view.assessment_metric_cards) >= 3
    assert any("当前结论" in card.title for card in view.assessment_metric_cards)
    assert any("控制因素" in card.title for card in view.assessment_metric_cards)
    assert any("控制比值" in card.title for card in view.assessment_metric_cards)
    assert view.conclusion_overview_card is not None
    assert "结论摘要" in view.conclusion_overview_card.title
    assert "当前结论" in view.conclusion_overview_card.detail
    assert "控制因素" in view.conclusion_overview_card.detail
    assert len(view.management_summary) >= 3
    assert any("当前结论" in item for item in view.management_summary)
    assert any("优先路径" in item for item in view.management_summary)
    assert any("规范复核" in item for item in view.management_summary)
    assert view.options[0].emphasis == "primary"
    assert any("适用情形" in detail for detail in view.options[0].details)
    assert any("当前优先原因" in detail for detail in view.options[0].details)
    assert any("初筛成本区间" in detail for detail in view.options[0].details)
    assert len(view.preliminary_conclusion_cards) >= 1
    assert len(view.traceability_cards) >= 1
    assert len(view.missing_data_cards) >= 1
    assert view.verification_readiness_title.startswith("结构复核准备度")
    assert len(view.engineering_check_cards) == 2
    assert len(view.member_reserve_uncertainty_cards) >= 4
    assert any("新增荷载需求" in card.title for card in view.member_reserve_uncertainty_cards)
    assert any("高不确定性" in card.title for card in view.member_reserve_uncertainty_cards)
    assert len(view.attachment_pathway_cards) == 4
    assert any("夹持式屋面连接" in card.title for card in view.attachment_pathway_cards)
    assert any("需专项复核" in card.title for card in view.attachment_pathway_cards)
    assert len(view.resource_recommendation_cards) >= 3
    assert any("结构复核工程师" in card.title for card in view.resource_recommendation_cards)
    assert any("屋面系统" in card.title for card in view.resource_recommendation_cards)
    assert len(view.review_trigger_cards) >= 1
    assert any("连接复核触发项" in card.title for card in view.review_trigger_cards)
    assert len(view.traceability_cards) >= 1
    assert all("gb_portal_frame_purlin_screening" not in card.detail for card in view.traceability_cards)
    assert all("依据 ID" not in card.detail for card in view.traceability_cards)
    assert any("檩条强度比" in card.detail for card in view.traceability_cards)
    assert all("portal_frame.controlling_path" not in card.detail for card in view.traceability_cards)
    assert any("檩条挠度控制" in card.detail or "主门架梁控制" in card.detail for card in view.traceability_cards)
    assert len(view.review_progression_summary) >= 2
    assert any("连接复核路径" in item for item in view.review_progression_summary)
    assert len(view.check_action_links) >= 2
    assert any("承载储备筛查" in card.title for card in view.check_action_links)
    assert any("必须先做" in card.detail and "优先路径" in card.detail for card in view.check_action_links)
    assert any("承载储备筛查" in card.title for card in view.engineering_check_cards)
    assert any("连接可行性筛查" in card.title for card in view.engineering_check_cards)
    assert any("图纸" in item for item in view.drawing_facts)
    assert any("既有构件表" in item for item in view.drawing_facts)
    assert any("节点连接做法" in item for item in view.drawing_facts)
    assert any("屋面系统厂家资料" in item for item in view.drawing_facts)
    assert any("仅用于前期结构筛查" in item for item in view.assumptions_limitations)
    assert any("现场调查" in item or "节点连接做法资料" in item for item in view.assumptions_limitations)
    assert any("建筑跨度" in item for item in view.screening_snapshot)
    assert any("檐口高度" in item for item in view.screening_snapshot)
    assert any("钢材标号" in item for item in view.screening_snapshot)
    assert any("可用复核路径" in item for item in view.screening_snapshot)
    assert view.standards_context_label == "规范体系: 国标 GB"
    assert any("GB 门式刚架檩条筛查依据" in card.title for card in view.review_needed_cards)
    assert {group.title for group in view.action_groups} >= {"可后续做"}
    assert any("因此当前优先路径" in item for item in view.decision_chain)
    assert any("GB 门式刚架檩条筛查依据" in item for item in view.decision_chain)
    assert view.agent.provider_label == "模拟降级模式"
    assert len(view.assessment_scope_cards) >= 2
    assert any("复核范围" in card.title for card in view.assessment_scope_cards)
    assert len(view.evidence_status_cards) >= 1
    assert any("构件图纸" in card.title or "构件表" in card.title for card in view.evidence_status_cards)
    assert all("member_evidence." not in card.detail for card in view.evidence_status_cards)
    assert len(view.evidence_overview_cards) >= 1
    assert any("证据摘要" in card.title for card in view.evidence_overview_cards)
    assert len(view.calc_summary_cards) >= 3
    assert any("新增屋面恒载" in card.title for card in view.calc_summary_cards)
    assert any("檩条强度比" in card.title for card in view.calc_summary_cards)
    assert any("檩条挠度比" in card.title for card in view.calc_summary_cards)
    assert any("kPa" in card.detail for card in view.calc_summary_cards)
    assert any("结果单位" in card.detail for card in view.calc_summary_cards)
    assert any("主门架筛查比值" in card.title for card in view.calc_summary_cards)
    assert any("主门架梁筛查比值" in card.title for card in view.calc_summary_cards)
    assert any("主门架柱筛查比值" in card.title for card in view.calc_summary_cards)
    assert any("主门架梁挠度敏感性" in card.title for card in view.calc_summary_cards)
    assert any("主门架柱稳定敏感性" in card.title for card in view.calc_summary_cards)
    assert any("主门架柱附加弯矩代理值" in card.title for card in view.calc_summary_cards)
    assert len(view.load_combination_sensitivity_cards) >= 1
    assert any("荷载组合" in card.title for card in view.load_combination_sensitivity_cards)
    assert any("风" in card.detail or "雪" in card.detail for card in view.load_combination_sensitivity_cards)
    assert len(view.basis_reference_cards) >= 1
    assert any("GB 门式刚架檩条筛查依据" in card.title or "Portal Frame" in card.title for card in view.basis_reference_cards)
    assert any("工程含义" in card.detail for card in view.basis_reference_cards)
    assert any("适用规范体系" in card.detail for card in view.basis_reference_cards)
    assert any("触发条件" in card.detail for card in view.basis_reference_cards)
    assert any("证据需求" in card.detail for card in view.basis_reference_cards)
    assert any("后续复核要求" in card.detail for card in view.basis_reference_cards)
    assert all("依据 ID" not in card.detail for card in view.basis_reference_cards)
    assert all("gb_portal_frame_purlin_screening" not in card.detail for card in view.basis_reference_cards)
    assert len(view.preliminary_conclusion_cards) >= 1
    assert any("初步结论" in card.title for card in view.preliminary_conclusion_cards)
    assert len(view.next_step_cards) >= 1
    assert any("檩条强度比" in card.detail for card in view.traceability_cards)


def test_workbench_view_surfaces_conservative_assumption_items_when_inputs_are_missing() -> None:
    evaluation = evaluate_case(
        main_demo_case().model_copy(update={"steel_grade": None}).model_dump()
    )

    view = build_workbench_view(evaluation)

    assert any("Q235" in item for item in view.assumptions_limitations)
    assert any("保守" in item for item in view.assumptions_limitations)


def test_workbench_view_surfaces_added_load_sensitivity_message() -> None:
    evaluation = evaluate_case(
        main_demo_case().model_copy(
            update={
                "estimated_added_load_kpa": 0.10,
                "roof_panel_thickness_mm": 0.7,
                "roof_rib_height_mm": 76.0,
                "drawing_availability": "complete",
                "survey_available": True,
                "available_verification_path": "drawings_plus_survey",
                "existing_member_schedule_status": "available",
                "connection_detail_status": "available",
                "roof_vendor_data_status": "available",
                "corrosion_condition": "low",
            }
        ).model_dump()
    )

    view = build_workbench_view(evaluation)

    assert any("临界新增荷载估算" in card.title for card in view.load_combination_sensitivity_cards)
    assert any("再增加约" in card.detail for card in view.load_combination_sensitivity_cards)


def test_workbench_view_shows_primary_frame_control_factor_when_rafter_governs() -> None:
    evaluation = evaluate_case(
        main_demo_case().model_copy(update={"rafter_section": "250x125x6x8 welded rafter"}).model_dump()
    )

    view = build_workbench_view(evaluation)

    assert any("主门架梁筛查比值" in card.title for card in view.calc_summary_cards)
    assert any("主门架柱筛查比值" in card.title for card in view.calc_summary_cards)
    assert any("主门架梁" in card.detail for card in view.preliminary_conclusion_cards)


def test_workbench_view_formats_risks_actions_and_questions_for_cards() -> None:
    evaluation = evaluate_case(
        {
            "project_type": "retrofit",
            "building_type": "industrial production building",
            "structural_system": "steel-concrete composite",
            "roof_type": "insulated panel roof",
            "intended_modification": "partial line retrofit and use change",
            "estimated_added_load_kpa": 0.28,
            "shutdown_constraint": "strict",
            "drawing_availability": "missing",
            "survey_available": False,
        }
    )

    view = build_workbench_view(evaluation)

    assert len(view.risk_cards) >= 1
    assert len(view.action_cards) >= 1
    assert len(view.question_cards) >= 1
    assert view.report_title == "复核摘要"


def test_workbench_view_surfaces_fallback_notice() -> None:
    evaluation = evaluate_case(
        {
            "project_type": "rooftop_pv",
            "building_type": "existing warehouse",
            "structural_system": "steel portal frame",
            "roof_type": "metal roof",
            "intended_modification": "distributed rooftop pv",
            "estimated_added_load_kpa": 0.18,
            "shutdown_constraint": "limited",
            "drawing_availability": "partial",
            "survey_available": False,
        }
    )
    evaluation["explanation"].requested_provider = "openai"
    evaluation["explanation"].fallback_reason = "provider unavailable"

    view = build_workbench_view(evaluation)

    assert view.agent.notice is not None
    assert "已切换降级" in view.agent.notice


def test_workbench_view_uses_compact_provider_status_label() -> None:
    evaluation = evaluate_case(
        {
            "project_type": "rooftop_pv",
            "building_type": "existing warehouse",
            "structural_system": "steel portal frame",
            "roof_type": "metal roof",
            "intended_modification": "distributed rooftop pv",
            "estimated_added_load_kpa": 0.18,
            "drawing_availability": "partial",
            "shutdown_constraint": "limited",
            "survey_available": False,
        }
    )

    view = build_workbench_view(evaluation)

    assert view.agent.provider_label in {"模拟降级模式", "在线模型模式", "Mock fallback", "Live model"}
