from typing import Dict, List, Optional

from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.core.persistence import ScreeningRepository
from structural_screening_agent.decision_agent import build_bilingual_explanation, build_follow_up_questions
from structural_screening_agent.demo_data import all_default_packages, all_demo_cases, main_demo_case
from structural_screening_agent.localization import Language
from structural_screening_agent.models import BuildingIntake
from structural_screening_agent.report_generator import build_markdown_report
from structural_screening_agent.rule_engine import evaluate_screening


def default_form_values() -> Dict[str, object]:
    intake = main_demo_case()
    return intake.model_dump()


def demo_case_options() -> Dict[str, BuildingIntake]:
    return all_demo_cases()


def default_package_options() -> Dict[str, BuildingIntake]:
    return all_default_packages()


def demo_case_catalog(language: Language = "zh") -> Dict[str, Dict[str, object]]:
    if language == "zh":
        return {
            "main_warehouse_pv": {
                "label": "门式刚架厂房/仓库 + 屋面光伏增载初筛",
                "note": "面向既有单层门式刚架建筑的结构初筛复核，重点输出简化计算结果、控制因素和下一步正式复核建议。",
                "featured": True,
                "narrative_steps": [
                    "先录入门式刚架几何、构件截面、檩条参数和光伏附加荷载。",
                    "再确认图纸、计算书、现场核查和屋面/连接资料掌握程度。",
                    "然后查看简化计算结果、控制因素和当前初步结构结论。",
                    "最后导出结构初筛摘要，作为顾问深化复核或内部决策输入。",
                ],
            },
        }

    return {
        "main_warehouse_pv": {
            "label": "Portal-Frame Building + Rooftop PV Added-Load Screening",
            "note": "Focused on structural screening review for existing single-story portal-frame buildings, with simplified calculations, controlling factors, and next-step review actions.",
            "featured": True,
            "narrative_steps": [
                "Enter portal-frame geometry, member sections, purlin parameters, and rooftop PV added load.",
                "Confirm drawings, original calculations, field survey status, and roof/connection evidence.",
                "Review simplified screening calculations, controlling factors, and the preliminary structural conclusion.",
                "Export the structural screening memo for consultant handoff or internal decision review.",
            ],
        },
    }


def ordered_demo_keys() -> List[str]:
    return ["main_warehouse_pv"]


def _merge_default_package(form_data: Dict[str, object]) -> Dict[str, object]:
    package_key = form_data.get("default_package_key")
    if not package_key:
        return dict(form_data)

    package = default_package_options().get(str(package_key))
    if package is None:
        return dict(form_data)

    merged = package.model_dump()
    for key, value in form_data.items():
        if key == "default_package_key":
            continue
        if value not in (None, ""):
            merged[key] = value
    return merged


def build_intake(form_data: Dict[str, object]) -> BuildingIntake:
    merged = _merge_default_package(form_data)
    return BuildingIntake(**merged)


def evaluate_case(
    form_data: Dict[str, object],
    language: Language = "zh",
    repository: Optional[ScreeningRepository] = None,
) -> Dict[str, object]:
    intake = build_intake(form_data)
    kernel_case = from_building_intake(intake)
    kernel_outcome = evaluate_screening_case(kernel_case)
    result = evaluate_screening(intake)
    questions: List[str] = build_follow_up_questions(
        intake,
        result,
        language=language,
        kernel_outcome=kernel_outcome,
    )
    explanation = build_bilingual_explanation(
        intake,
        result,
        language=language,
        kernel_outcome=kernel_outcome,
    )
    report = build_markdown_report(intake, result, explanation, kernel_outcome=kernel_outcome)
    payload = {
        "intake": intake,
        "kernel_case": kernel_case,
        "kernel_outcome": kernel_outcome,
        "result": result,
        "questions": questions,
        "explanation": explanation,
        "report": report,
    }
    if repository is not None:
        run_id, result_id = repository.save_run_and_evaluation(
            case=kernel_case,
            outcome=kernel_outcome,
            report_markdown=report,
            explanation_payload=explanation.model_dump(mode="json"),
            language=language,
        )
        payload["persistence"] = {
            "run_id": run_id,
            "result_id": result_id,
        }
    return payload
