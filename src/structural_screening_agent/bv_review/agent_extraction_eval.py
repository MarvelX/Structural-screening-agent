from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


ExpectedValue = Union[str, float, int, bool]


class ExpectedExtractedField(BaseModel):
    field_id: str = Field(min_length=1)
    expected_value: ExpectedValue
    unit: Optional[str] = None
    required: bool = True
    include_in_calculation: Optional[bool] = None


class AgentExtractionCase(BaseModel):
    case_id: str = Field(min_length=1)
    language: Literal["zh", "en", "mixed"]
    scenario: str = Field(min_length=1)
    source_text: str = Field(min_length=1)
    expected_fields: list[ExpectedExtractedField] = Field(default_factory=list)
    expected_missing_document_keys: list[str] = Field(default_factory=list)
    must_not_extract: list[str] = Field(default_factory=list)


def load_extraction_cases(path: Path) -> list[AgentExtractionCase]:
    raw_cases = json.loads(path.read_text(encoding="utf-8"))
    return [AgentExtractionCase.model_validate(raw_case) for raw_case in raw_cases]
