from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.scenario_classifier import classify_scenario


def test_classifies_rooftop_pv_demo_case() -> None:
    outcome = classify_scenario(main_demo_case())
    assert outcome.slug == "rooftop_pv"
    assert outcome.label_en == "Rooftop PV"
    assert outcome.label_zh == "屋顶光伏"


def test_marks_mixed_case_when_upgrade_and_pv_overlap() -> None:
    intake = main_demo_case().model_copy(
        update={"project_type": "mixed", "intended_modification": "pv plus equipment upgrade"}
    )
    outcome = classify_scenario(intake)
    assert outcome.slug == "mixed"
