from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.core.persistence import ScreeningRepository
from structural_screening_agent.demo_data import main_demo_case


def test_repository_persists_case_and_kernel_outcome(tmp_path) -> None:
    repository = ScreeningRepository(tmp_path / "screening.db")
    case = from_building_intake(main_demo_case())
    outcome = evaluate_screening_case(case)

    run_id = repository.save_run(case, outcome)
    stored = repository.load_run(run_id)

    assert stored.run_id == run_id
    assert stored.case.project.project_type == "rooftop_pv"
    assert stored.outcome.decision.status == "conditional_go"
