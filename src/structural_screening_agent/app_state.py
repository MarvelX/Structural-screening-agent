from typing import Dict, List

from structural_screening_agent.core.domain import from_building_intake
from structural_screening_agent.core.kernel import evaluate_screening_case
from structural_screening_agent.decision_agent import build_bilingual_explanation, build_follow_up_questions
from structural_screening_agent.demo_data import all_demo_cases, main_demo_case
from structural_screening_agent.localization import Language
from structural_screening_agent.models import BuildingIntake
from structural_screening_agent.report_generator import build_markdown_report
from structural_screening_agent.rule_engine import evaluate_screening


def default_form_values() -> Dict[str, object]:
    intake = main_demo_case()
    return intake.model_dump()


def demo_case_options() -> Dict[str, BuildingIntake]:
    return all_demo_cases()


def demo_case_catalog(language: Language = "zh") -> Dict[str, Dict[str, object]]:
    if language == "zh":
        return {
            "main_warehouse_pv": {
                "label": "推荐案例：既有钢结构仓库 + 屋面光伏",
                "note": "适用于既有仓库屋面光伏项目前期结构筛查，重点展示证据链、专项复核触发项与当前优先路径。",
                "featured": True,
                "narrative_steps": [
                    "先录入项目条件和证据状态，确认图纸、构件表、连接做法与屋面资料掌握程度。",
                    "再看管理层摘要，快速判断当前结论、主要约束、下一步和优先路径。",
                    "然后查看专项复核触发项与复核推进链，理解为什么先进入构件或连接复核。",
                    "最后比较当前优先方案并导出决策摘要，作为内部讨论或顾问交接材料。",
                ],
            },
            "warehouse_upgrade": {
                "label": "次案例：仓库荷载升级",
                "note": "用于补充说明平台或设备升级场景下的结构筛查逻辑。",
                "featured": False,
                "narrative_steps": [],
            },
            "industrial_retrofit": {
                "label": "补充案例：工业建筑改造",
                "note": "用于展示 No-Go / 高不确定性场景下的 gatekeeping 能力。",
                "featured": False,
                "narrative_steps": [],
            },
        }

    return {
        "main_warehouse_pv": {
            "label": "Recommended Case: Existing Steel Warehouse + Rooftop PV",
            "note": "Best suited for early-stage rooftop PV screening on existing warehouses, with emphasis on evidence strength, review triggers, and the preferred path.",
            "featured": True,
            "narrative_steps": [
                "Start by entering the project conditions and evidence status, including drawings, member schedules, connection details, and roof-system data.",
                "Review the management summary to understand the current decision, primary constraint, next step, and preferred path.",
                "Inspect the review triggers and review progression to see why the project should move into member or connection review next.",
                "Compare the preferred path and export the decision summary for internal review or consultant handoff.",
            ],
        },
        "warehouse_upgrade": {
            "label": "Supporting Case: Warehouse Upgrade",
            "note": "Supports load upgrade and platform/equipment screening logic.",
            "featured": False,
            "narrative_steps": [],
        },
        "industrial_retrofit": {
            "label": "Supporting Case: Industrial Retrofit",
            "note": "Shows No-Go / high uncertainty gatekeeping behavior.",
            "featured": False,
            "narrative_steps": [],
        },
    }


def ordered_demo_keys() -> List[str]:
    return ["main_warehouse_pv", "warehouse_upgrade", "industrial_retrofit"]


def build_intake(form_data: Dict[str, object]) -> BuildingIntake:
    return BuildingIntake(**form_data)


def evaluate_case(form_data: Dict[str, object], language: Language = "zh") -> Dict[str, object]:
    intake = build_intake(form_data)
    kernel_case = from_building_intake(intake)
    kernel_outcome = evaluate_screening_case(kernel_case)
    result = evaluate_screening(intake)
    questions: List[str] = build_follow_up_questions(intake, result, language=language)
    explanation = build_bilingual_explanation(intake, result, language=language)
    report = build_markdown_report(intake, result, explanation)
    return {
        "intake": intake,
        "kernel_case": kernel_case,
        "kernel_outcome": kernel_outcome,
        "result": result,
        "questions": questions,
        "explanation": explanation,
        "report": report,
    }
