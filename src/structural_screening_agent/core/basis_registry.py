from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class BasisReference(BaseModel):
    basis_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    title_en: str = Field(min_length=1)
    title_zh: str = Field(min_length=1)
    citation_en: str = Field(min_length=1)
    citation_zh: str = Field(min_length=1)
    applicable_standards: List[str] = Field(min_length=1)
    trigger_conditions: List[str] = Field(min_length=1)
    review_requirements: List[str] = Field(min_length=1)
    evidence_requirements: List[str] = Field(min_length=1)


class BasisRegistry(BaseModel):
    references: Dict[str, BasisReference]

    def get(self, basis_id: str) -> Optional[BasisReference]:
        return self.references.get(basis_id)


def _registry_path() -> Path:
    return Path(__file__).resolve().parents[3] / "rules" / "basis_registry.yaml"


def load_basis_registry() -> BasisRegistry:
    payload: List[dict] = yaml.safe_load(_registry_path().read_text())
    return BasisRegistry(
        references={item["basis_id"]: BasisReference(**item) for item in payload}
    )
