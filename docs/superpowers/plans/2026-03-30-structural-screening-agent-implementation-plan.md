# Structural Screening Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bilingual Streamlit MVP that screens retrofit feasibility for新能源/物流场景 with a rule-backed decision, LLM follow-up questions, and exportable summary output.

**Architecture:** The app uses a deterministic screening core for scenario classification, risk evaluation, decision status, and option generation. A thin OpenAI-backed agent layer only asks follow-up questions and explains results; it never decides feasibility on its own. Streamlit renders a four-zone decision workbench and report export on top of the Python package.

**Tech Stack:** Python 3.12, Streamlit, Pydantic, PyYAML, OpenAI Python SDK, pytest

---

## File Map

- `README.md`: project overview, setup, run instructions, MVP scope
- `pyproject.toml`: package metadata, dependencies, pytest config
- `app.py`: Streamlit entry point
- `src/structural_screening_agent/models.py`: intake, rules, decision, report models
- `src/structural_screening_agent/bilingual.py`: same-line bilingual formatting helpers
- `src/structural_screening_agent/scenario_classifier.py`: map intake into supported scenarios
- `src/structural_screening_agent/rule_engine.py`: load YAML rules and compute decision outputs
- `src/structural_screening_agent/decision_agent.py`: build follow-up questions and explanations with OpenAI client abstraction
- `src/structural_screening_agent/report_generator.py`: Markdown summary export
- `src/structural_screening_agent/demo_data.py`: prepared demo scenarios
- `src/structural_screening_agent/app_state.py`: orchestration helpers used by `app.py`
- `rules/scenarios.yaml`: scenario labels and keywords
- `rules/risks.yaml`: risk and decision rules
- `rules/options.yaml`: option templates
- `tests/test_project_layout.py`: project bootstrap smoke coverage
- `tests/test_models.py`: model validation coverage
- `tests/test_scenario_classifier.py`: classifier behavior
- `tests/test_rule_engine.py`: decision/risk/option evaluation
- `tests/test_report_generator.py`: report output coverage

### Task 1: Bootstrap Project Skeleton

**Files:**
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `app.py`
- Create: `src/structural_screening_agent/__init__.py`
- Create: `tests/test_project_layout.py`

- [ ] **Step 1: Write the failing environment smoke test**

```python
# tests/test_project_layout.py
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_project_layout_exists() -> None:
    root = project_root()
    assert (root / "app.py").exists()
    assert (root / "pyproject.toml").exists()
    assert (root / "src" / "structural_screening_agent").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_layout.py -q`
Expected: FAIL because `app.py` and `pyproject.toml` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```toml
# pyproject.toml
[project]
name = "structural-screening-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "openai>=1.76.0",
  "pydantic>=2.11.0",
  "pyyaml>=6.0.2",
  "streamlit>=1.44.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.3.5"]

[tool.pytest.ini_options]
pythonpath = ["src", "."]
testpaths = ["tests"]
```

```python
# app.py
import streamlit as st

st.set_page_config(page_title="Structural Screening Agent", layout="wide")
st.title("Structural Feasibility Screening Agent | 结构可行性评估 Agent")
st.caption("MVP shell in place. Core logic lands in subsequent tasks.")
```

```python
# src/structural_screening_agent/__init__.py
__all__ = ["__version__"]

__version__ = "0.1.0"
```

```markdown
# README.md
# Structural Screening Agent

Bilingual Streamlit MVP for structural feasibility screening in renewable energy and logistics retrofit scenarios.

## Run

```bash
python -m pip install -e ".[dev]"
streamlit run app.py
pytest
```
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_layout.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md pyproject.toml app.py src/structural_screening_agent/__init__.py tests/test_project_layout.py
git commit -m "chore: bootstrap structural screening agent skeleton"
```

### Task 2: Add Validated Domain Models And Demo Inputs

**Files:**
- Create: `src/structural_screening_agent/models.py`
- Create: `src/structural_screening_agent/demo_data.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing model tests**

```python
from structural_screening_agent.models import BuildingIntake, DecisionStatus


def test_building_intake_requires_project_type() -> None:
    try:
        BuildingIntake(
            building_type="warehouse",
            structural_system="steel",
            roof_type="metal deck",
            intended_modification="rooftop_pv",
            estimated_added_load_kpa=0.18,
            shutdown_constraint="limited",
            drawing_availability="partial",
        )
    except ValueError as exc:
        assert "project_type" in str(exc)
    else:
        raise AssertionError("Expected validation failure")


def test_demo_case_uses_conditional_go_target() -> None:
    from structural_screening_agent.demo_data import main_demo_case

    intake = main_demo_case()
    assert intake.project_type == "rooftop_pv"
    assert DecisionStatus.CONDITIONAL_GO.value == "conditional_go"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -q`
Expected: FAIL with import errors because `models.py` and `demo_data.py` do not exist.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/models.py
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DecisionStatus(str, Enum):
    GO = "go"
    CONDITIONAL_GO = "conditional_go"
    NO_GO = "no_go"


class BuildingIntake(BaseModel):
    project_type: Literal["rooftop_pv", "load_upgrade", "retrofit", "mixed"]
    building_type: str = Field(min_length=1)
    structural_system: str = Field(min_length=1)
    roof_type: str = Field(min_length=1)
    intended_modification: str = Field(min_length=1)
    estimated_added_load_kpa: float | None = None
    shutdown_constraint: Literal["none", "limited", "strict"]
    drawing_availability: Literal["complete", "partial", "missing"]
    survey_available: bool = False
```

```python
# src/structural_screening_agent/demo_data.py
from structural_screening_agent.models import BuildingIntake


def main_demo_case() -> BuildingIntake:
    return BuildingIntake(
        project_type="rooftop_pv",
        building_type="existing warehouse",
        structural_system="steel portal frame",
        roof_type="metal roof",
        intended_modification="distributed rooftop pv",
        estimated_added_load_kpa=0.18,
        shutdown_constraint="limited",
        drawing_availability="partial",
        survey_available=False,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/models.py src/structural_screening_agent/demo_data.py tests/test_models.py
git commit -m "feat: add intake models and demo cases"
```

### Task 3: Implement Scenario Classification

**Files:**
- Create: `src/structural_screening_agent/scenario_classifier.py`
- Create: `rules/scenarios.yaml`
- Test: `tests/test_scenario_classifier.py`

- [ ] **Step 1: Write the failing classifier tests**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scenario_classifier.py -q`
Expected: FAIL because classifier module and scenario rules are missing.

- [ ] **Step 3: Write minimal implementation**

```yaml
# rules/scenarios.yaml
- slug: rooftop_pv
  label_en: Rooftop PV
  label_zh: 屋顶光伏
  project_types: ["rooftop_pv"]
- slug: load_upgrade
  label_en: Load Upgrade
  label_zh: 荷载升级
  project_types: ["load_upgrade"]
- slug: retrofit
  label_en: Retrofit
  label_zh: 改造
  project_types: ["retrofit"]
- slug: mixed
  label_en: Mixed Scenario
  label_zh: 混合场景
  project_types: ["mixed"]
```

```python
# src/structural_screening_agent/scenario_classifier.py
from pathlib import Path

import yaml
from pydantic import BaseModel

from structural_screening_agent.models import BuildingIntake


class ScenarioOutcome(BaseModel):
    slug: str
    label_en: str
    label_zh: str


def classify_scenario(intake: BuildingIntake) -> ScenarioOutcome:
    rules_path = Path(__file__).resolve().parents[2] / "rules" / "scenarios.yaml"
    rules = yaml.safe_load(rules_path.read_text())
    match = next(rule for rule in rules if intake.project_type in rule["project_types"])
    return ScenarioOutcome(**match)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scenario_classifier.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/scenario_classifier.py rules/scenarios.yaml tests/test_scenario_classifier.py
git commit -m "feat: add scenario classification"
```

### Task 4: Implement Rule Engine For Decision, Risks, Missing Data, And Options

**Files:**
- Create: `src/structural_screening_agent/rule_engine.py`
- Create: `src/structural_screening_agent/bilingual.py`
- Create: `rules/risks.yaml`
- Create: `rules/options.yaml`
- Test: `tests/test_rule_engine.py`

- [ ] **Step 1: Write the failing rule engine tests**

```python
from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.rule_engine import evaluate_screening


def test_partial_drawings_and_no_survey_yield_conditional_go() -> None:
    result = evaluate_screening(main_demo_case())
    assert result.status.value == "conditional_go"
    assert result.confidence == "medium"
    assert any("reserve capacity" in risk.title_en.lower() for risk in result.risks)
    assert any("survey" in item.title_en.lower() for item in result.missing_data)
    assert len(result.options) >= 2


def test_missing_drawings_and_strict_shutdown_can_trigger_no_go() -> None:
    intake = main_demo_case().model_copy(
        update={"drawing_availability": "missing", "shutdown_constraint": "strict"}
    )
    result = evaluate_screening(intake)
    assert result.status.value == "no_go"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_rule_engine.py -q`
Expected: FAIL with missing module errors.

- [ ] **Step 3: Write minimal implementation**

```yaml
# rules/risks.yaml
- id: pv_capacity_gap
  applies_to: ["rooftop_pv", "mixed"]
  triggers:
    drawing_availability: ["partial", "missing"]
  risk_level: high
  decision_impact: conditional_go
  title_en: Insufficient reserve capacity in roof members
  title_zh: 屋面构件承载储备不足
  recommended_action_en: Perform targeted structural verification
  recommended_action_zh: 开展针对性结构复核
- id: no_path_to_verify
  applies_to: ["rooftop_pv", "mixed", "retrofit"]
  triggers:
    drawing_availability: ["missing"]
    shutdown_constraint: ["strict"]
  risk_level: critical
  decision_impact: no_go
  title_en: No viable verification path under current constraints
  title_zh: 当前约束下缺少可执行的复核路径
  recommended_action_en: Pause and secure drawings or intrusive survey scope
  recommended_action_zh: 暂停推进并补齐图纸或破损性调查范围
```

```yaml
# rules/options.yaml
- id: restricted_installation
  applies_to: ["rooftop_pv", "mixed"]
  title_en: Restrict installation zones
  title_zh: 限定安装分区
- id: local_strengthening
  applies_to: ["rooftop_pv", "load_upgrade", "mixed"]
  title_en: Local strengthening before installation
  title_zh: 安装前局部加固
```

```python
# src/structural_screening_agent/bilingual.py
def same_line(en: str, zh: str) -> str:
    return f"{en} | {zh}"
```

```python
# src/structural_screening_agent/rule_engine.py
from pathlib import Path

import yaml
from pydantic import BaseModel

from structural_screening_agent.models import BuildingIntake, DecisionStatus
from structural_screening_agent.scenario_classifier import classify_scenario


class BilingualItem(BaseModel):
    title_en: str
    title_zh: str


class ScreeningResult(BaseModel):
    status: DecisionStatus
    confidence: str
    risks: list[BilingualItem]
    missing_data: list[BilingualItem]
    options: list[BilingualItem]


def evaluate_screening(intake: BuildingIntake) -> ScreeningResult:
    scenario = classify_scenario(intake)
    base_path = Path(__file__).resolve().parents[2] / "rules"
    risks = yaml.safe_load((base_path / "risks.yaml").read_text())
    options = yaml.safe_load((base_path / "options.yaml").read_text())

    matched_risks = []
    status = DecisionStatus.GO
    for rule in risks:
        if scenario.slug not in rule["applies_to"]:
            continue
        if intake.drawing_availability not in rule["triggers"].get("drawing_availability", [intake.drawing_availability]):
            continue
        if intake.shutdown_constraint not in rule["triggers"].get("shutdown_constraint", [intake.shutdown_constraint]):
            continue
        matched_risks.append(BilingualItem(title_en=rule["title_en"], title_zh=rule["title_zh"]))
        if rule["decision_impact"] == "no_go":
            status = DecisionStatus.NO_GO
        elif status != DecisionStatus.NO_GO:
            status = DecisionStatus.CONDITIONAL_GO

    missing_data = []
    if intake.drawing_availability != "complete":
        missing_data.append(BilingualItem(title_en="Original structural drawings", title_zh="原结构图纸"))
    if not intake.survey_available:
        missing_data.append(BilingualItem(title_en="Targeted site survey", title_zh="针对性现场调查"))

    applicable_options = [
        BilingualItem(title_en=option["title_en"], title_zh=option["title_zh"])
        for option in options
        if scenario.slug in option["applies_to"]
    ]

    confidence = "low" if status == DecisionStatus.NO_GO else "medium" if matched_risks else "high"
    return ScreeningResult(
        status=status,
        confidence=confidence,
        risks=matched_risks,
        missing_data=missing_data,
        options=applicable_options,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_rule_engine.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/structural_screening_agent/bilingual.py src/structural_screening_agent/rule_engine.py rules/risks.yaml rules/options.yaml tests/test_rule_engine.py
git commit -m "feat: add rule-backed screening engine"
```

### Task 5: Add Report Generator, Agent Layer, And Streamlit Workbench

**Files:**
- Create: `src/structural_screening_agent/decision_agent.py`
- Create: `src/structural_screening_agent/report_generator.py`
- Create: `src/structural_screening_agent/app_state.py`
- Modify: `app.py`
- Test: `tests/test_report_generator.py`

- [ ] **Step 1: Write the failing report test**

```python
from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.report_generator import build_markdown_report
from structural_screening_agent.rule_engine import evaluate_screening


def test_report_contains_bilingual_headings_and_decision() -> None:
    intake = main_demo_case()
    result = evaluate_screening(intake)
    report = build_markdown_report(intake, result)
    assert "Decision | 决策结论" in report
    assert "Conditional Go | 有条件推进" in report
    assert "Top Risks | 关键风险" in report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_report_generator.py -q`
Expected: FAIL because report generator does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/structural_screening_agent/report_generator.py
from structural_screening_agent.bilingual import same_line
from structural_screening_agent.models import BuildingIntake, DecisionStatus
from structural_screening_agent.rule_engine import ScreeningResult


def format_decision(status: DecisionStatus) -> str:
    mapping = {
        DecisionStatus.GO: same_line("Go", "可推进"),
        DecisionStatus.CONDITIONAL_GO: same_line("Conditional Go", "有条件推进"),
        DecisionStatus.NO_GO: same_line("No-Go", "暂不建议推进"),
    }
    return mapping[status]


def build_markdown_report(intake: BuildingIntake, result: ScreeningResult) -> str:
    risk_lines = "\n".join(f"- {same_line(item.title_en, item.title_zh)}" for item in result.risks)
    return "\n".join(
        [
            "# Structural Feasibility Screening Agent | 结构可行性评估 Agent",
            "",
            f"## {same_line('Decision', '决策结论')}",
            format_decision(result.status),
            "",
            f"## {same_line('Top Risks', '关键风险')}",
            risk_lines or "- None | 无",
        ]
    )
```

```python
# src/structural_screening_agent/decision_agent.py
from structural_screening_agent.models import BuildingIntake
from structural_screening_agent.rule_engine import ScreeningResult


def build_follow_up_questions(intake: BuildingIntake, result: ScreeningResult) -> list[str]:
    questions = []
    if intake.drawing_availability != "complete":
        questions.append("Do you have any original structural drawings or prior calculation notes?")
    if not intake.survey_available:
        questions.append("Can a targeted roof survey and member measurement be arranged?")
    return questions
```

```python
# src/structural_screening_agent/app_state.py
from structural_screening_agent.decision_agent import build_follow_up_questions
from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.report_generator import build_markdown_report
from structural_screening_agent.rule_engine import evaluate_screening


def run_main_demo() -> dict[str, object]:
    intake = main_demo_case()
    result = evaluate_screening(intake)
    return {
        "intake": intake,
        "result": result,
        "questions": build_follow_up_questions(intake, result),
        "report": build_markdown_report(intake, result),
    }
```

```python
# app.py
import streamlit as st

from structural_screening_agent.app_state import run_main_demo
from structural_screening_agent.bilingual import same_line
from structural_screening_agent.report_generator import format_decision

st.set_page_config(page_title="Structural Screening Agent", layout="wide")
st.title("Structural Feasibility Screening Agent | 结构可行性评估 Agent")

demo = run_main_demo()
left, right = st.columns([1.1, 0.9])

with left:
    st.subheader(same_line("Project Intake", "项目输入"))
    st.json(demo["intake"].model_dump())
    st.subheader(same_line("Agent Questions", "Agent 追问"))
    for question in demo["questions"]:
        st.write(f"- {question}")

with right:
    st.subheader(same_line("Decision Panel", "决策面板"))
    st.metric(same_line("Decision", "决策结论"), format_decision(demo["result"].status))
    st.metric(same_line("Confidence", "置信度"), demo["result"].confidence)
    st.subheader(same_line("Options & Report", "方案与报告"))
    st.markdown(demo["report"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_report_generator.py -q`
Expected: PASS

- [ ] **Step 5: Run the fast integration check**

Run: `pytest -q`
Expected: PASS for all unit tests.

Run: `streamlit run app.py --server.headless true`
Expected: Streamlit starts without import or config errors.

- [ ] **Step 6: Commit**

```bash
git add src/structural_screening_agent/decision_agent.py src/structural_screening_agent/report_generator.py src/structural_screening_agent/app_state.py app.py tests/test_report_generator.py
git commit -m "feat: add bilingual decision workbench"
```

## Self-Review

- Spec coverage: intake, scenario classifier, rule engine, follow-up questions, bilingual outputs, option comparison, exportable summary, and main demo scenario are all mapped to Tasks 1-5.
- Placeholder scan: no `TBD`, `TODO`, or unresolved file references remain.
- Type consistency: `BuildingIntake`, `DecisionStatus`, `ScenarioOutcome`, and `ScreeningResult` are introduced before downstream usage.
