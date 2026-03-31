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
    assert len(view.management_summary) >= 4
    assert any("当前结论" in item for item in view.management_summary)
    assert any("主要约束" in item for item in view.management_summary)
    assert any("下一步" in item for item in view.management_summary)
    assert any("优先路径" in item for item in view.management_summary)
    assert view.options[0].emphasis == "primary"
    assert any("适用情形" in detail for detail in view.options[0].details)
    assert any("当前优先原因" in detail for detail in view.options[0].details)
    assert any(card.detail for card in view.risk_cards)
    assert len(view.missing_data_cards) >= 1
    assert view.verification_readiness_title.startswith("结构复核准备度")
    assert len(view.engineering_check_cards) == 2
    assert len(view.member_reserve_uncertainty_cards) >= 4
    assert any("新增荷载需求" in card.title for card in view.member_reserve_uncertainty_cards)
    assert any("高不确定性" in card.title for card in view.member_reserve_uncertainty_cards)
    assert len(view.attachment_pathway_cards) == 4
    assert any("夹持式屋面连接" in card.title for card in view.attachment_pathway_cards)
    assert any("当前不可判定" in card.title for card in view.attachment_pathway_cards)
    assert len(view.resource_recommendation_cards) >= 3
    assert any("结构复核工程师" in card.title for card in view.resource_recommendation_cards)
    assert any("屋面系统" in card.title for card in view.resource_recommendation_cards)
    assert len(view.review_trigger_cards) >= 2
    assert any("构件复核触发项" in card.title for card in view.review_trigger_cards)
    assert any("连接复核触发项" in card.title for card in view.review_trigger_cards)
    assert len(view.review_progression_summary) >= 2
    assert any("构件复核路径" in item for item in view.review_progression_summary)
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
    assert any("构件表" in item for item in view.assumptions_limitations)
    assert any("建筑跨度" in item for item in view.screening_snapshot)
    assert any("可用复核路径" in item for item in view.screening_snapshot)
    assert view.standards_context_label == "规范体系: 国标 GB"
    assert any("GB 50017" in card.title for card in view.review_needed_cards)
    assert {group.title for group in view.action_groups} >= {"必须先做", "建议并行做", "可后续做"}
    assert any("因此当前优先路径" in item for item in view.decision_chain)
    assert any("GB 50017" in item for item in view.decision_chain)
    assert view.agent.provider_label == "模拟降级模式"


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
    assert view.report_title == "决策摘要"


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
