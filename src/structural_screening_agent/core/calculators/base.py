import re
from typing import Any, Literal, Optional, Protocol

from pydantic import BaseModel, Field, model_validator

from structural_screening_agent.core.domain import PortalFrameScreeningCase


class CalculationRow(BaseModel):
    row_id: str = Field(min_length=1)
    numeric_value: Optional[float] = None
    value_text: str = Field(min_length=1)
    unit: Optional[str] = None
    label_en: str = Field(min_length=1)
    label_zh: str = Field(min_length=1)
    formula_en: Optional[str] = None
    formula_zh: Optional[str] = None
    note: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _upgrade_legacy_shape(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values
        if "row_id" in values:
            return values

        label = str(values.get("label") or "calculation_row")
        value = str(values.get("value") or "")
        note = values.get("note")
        return {
            "row_id": label,
            "numeric_value": None,
            "value_text": value or label,
            "unit": None,
            "label_en": label,
            "label_zh": label,
            "formula_en": None,
            "formula_zh": None,
            "note": note,
        }


class PortalFrameScreeningResult(BaseModel):
    conclusion_status: Literal[
        "insufficient_evidence",
        "calculator_result",
        "formal_review_required",
        "screening_pass",
    ]
    screening_level: Literal["level_a", "level_b", "level_c"]
    code_path: Optional[Literal["gb", "aisc", "eurocode"]] = None
    calculation_summary: str = Field(min_length=1)
    calculation_rows: list[CalculationRow] = Field(default_factory=list)
    controlling_component: Optional[Literal["purlin", "primary_frame"]] = None
    controlling_path: Optional[
        Literal[
            "purlin_strength",
            "purlin_deflection",
            "primary_frame_rafter",
            "primary_frame_column",
        ]
    ] = None
    code_reference_ids: list[str] = Field(default_factory=list)


class PortalFrameCalculator(Protocol):
    standard: Literal["gb", "aisc", "eurocode"]

    def calculate(self, case: PortalFrameScreeningCase) -> PortalFrameScreeningResult:
        ...


def parse_section_dimensions(section: Optional[str]) -> Optional[tuple[float, float, float, float]]:
    if not section:
        return None
    values = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", section)]
    if len(values) < 4:
        return None
    return values[0], values[1], values[2], values[3]


def steel_grade_yield_strength(standard: str, steel_grade: Optional[str]) -> float:
    if not steel_grade:
        return {"gb": 235.0, "aisc": 248.0, "eurocode": 275.0}.get(standard, 235.0)
    label = steel_grade.strip().upper()
    explicit_map = {
        "Q235": 235.0,
        "Q355": 355.0,
        "A36": 248.0,
        "A572 GR50": 345.0,
        "A572GR50": 345.0,
        "S275": 275.0,
        "S355": 355.0,
    }
    if label in explicit_map:
        return explicit_map[label]
    match = re.search(r"(Q|S)\s*(\d{3})", label)
    if match:
        return float(match.group(2))
    match = re.search(r"GR\s*50|GRADE\s*50", label)
    if match:
        return 345.0
    return {"gb": 235.0, "aisc": 248.0, "eurocode": 275.0}.get(standard, 235.0)


def steel_grade_factor(standard: str, steel_grade: Optional[str]) -> float:
    return round(steel_grade_yield_strength(standard, steel_grade) / 345.0, 3)


def estimate_primary_frame_reference_moment(
    section: Optional[str],
    *,
    standard: str,
    steel_grade: Optional[str],
) -> Optional[float]:
    dims = parse_section_dimensions(section)
    if dims is None:
        return None
    depth_mm, flange_width_mm, _web_thickness_mm, flange_thickness_mm = dims
    base_proxy = (depth_mm * flange_width_mm * flange_thickness_mm) / 3000.0
    return round(base_proxy * steel_grade_factor(standard, steel_grade), 2)


def estimate_rafter_deflection_sensitivity(
    *,
    line_load: float,
    span_m: float,
    rafter_reference_moment: Optional[float],
) -> Optional[float]:
    if not span_m or not rafter_reference_moment:
        return None
    return round((line_load * (span_m**3) / rafter_reference_moment) / 100.0, 2)


def estimate_column_stability_sensitivity(
    *,
    column_added_moment: float,
    eave_height_m: float,
    column_section: Optional[str],
    column_reference_moment: Optional[float],
) -> Optional[float]:
    dims = parse_section_dimensions(column_section)
    if dims is None or not eave_height_m or not column_reference_moment:
        return None
    column_depth_m = dims[0] / 1000.0
    if column_depth_m <= 0:
        return None
    return round(((column_added_moment / column_reference_moment) * (eave_height_m / column_depth_m)) / 10.0, 2)


def resolve_controlling_path(
    *,
    strength_ratio: float,
    deflection_ratio: float,
    rafter_ratio: Optional[float],
    column_ratio: Optional[float],
) -> tuple[
    Literal["purlin", "primary_frame"],
    Literal["purlin_strength", "purlin_deflection", "primary_frame_rafter", "primary_frame_column"],
    float,
]:
    path_candidates = {
        "purlin_strength": strength_ratio,
        "purlin_deflection": deflection_ratio,
    }
    if rafter_ratio is not None:
        path_candidates["primary_frame_rafter"] = rafter_ratio
    if column_ratio is not None:
        path_candidates["primary_frame_column"] = column_ratio

    controlling_path = max(path_candidates, key=path_candidates.get)
    controlling_component: Literal["purlin", "primary_frame"] = (
        "purlin" if controlling_path.startswith("purlin_") else "primary_frame"
    )
    return controlling_component, controlling_path, path_candidates[controlling_path]
