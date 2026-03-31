from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.demo_data import main_demo_case


def test_kernel_returns_conditional_go_with_basis_ids_and_trace_refs() -> None:
    outcome = evaluate_screening_case(from_building_intake(main_demo_case()))

    assert outcome.decision.status == "conditional_go"
    assert outcome.decision.confidence == "medium"
    assert outcome.findings
    assert any(finding.basis_ids for finding in outcome.findings)
    assert any(
        trace.input_path == "roof.panel_thickness_mm"
        for finding in outcome.findings
        for trace in finding.traces
    )


def test_kernel_returns_go_when_verification_path_and_roof_geometry_are_closed() -> None:
    intake = main_demo_case().model_copy(
        update={
            "roof_panel_thickness_mm": 0.7,
            "roof_rib_height_mm": 76.0,
            "drawing_availability": "complete",
            "survey_available": True,
            "available_verification_path": "drawings_plus_survey",
        }
    )

    outcome = evaluate_screening_case(from_building_intake(intake))

    assert outcome.decision.status == "go"
    assert outcome.decision.confidence == "high"
    assert not outcome.findings
