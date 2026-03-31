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
    return ScenarioOutcome(
        slug=match["slug"],
        label_en=match["label_en"],
        label_zh=match["label_zh"],
    )
