from structural_screening_agent.app_state import evaluate_case
from structural_screening_agent.demo_data import main_demo_case


def test_evaluate_case_exposes_kernel_case_and_outcome() -> None:
    evaluation = evaluate_case(main_demo_case().model_dump(), language="zh")

    assert evaluation["kernel_case"].project.project_type == "rooftop_pv"
    assert evaluation["kernel_outcome"].decision.status == "conditional_go"
    assert evaluation["kernel_outcome"].findings
