from typing import List, Literal

from pydantic import BaseModel, Field

from structural_screening_agent.core.basis_registry import load_basis_registry
from structural_screening_agent.core.domain import ScreeningCase


class TraceRef(BaseModel):
    input_path: str = Field(min_length=1)
    observed_value: str


class KernelFinding(BaseModel):
    finding_id: str = Field(min_length=1)
    severity: Literal["info", "caution", "blocking"]
    summary_en: str = Field(min_length=1)
    summary_zh: str = Field(min_length=1)
    basis_ids: List[str] = Field(default_factory=list)
    traces: List[TraceRef] = Field(default_factory=list)


class KernelDecision(BaseModel):
    status: Literal["go", "conditional_go", "no_go"]
    confidence: Literal["high", "medium", "low"]


class KernelOutcome(BaseModel):
    decision: KernelDecision
    findings: List[KernelFinding] = Field(default_factory=list)


def _trace(path: str, value: object) -> TraceRef:
    return TraceRef(input_path=path, observed_value=str(value))


def evaluate_screening_case(case: ScreeningCase) -> KernelOutcome:
    registry = load_basis_registry()
    findings: List[KernelFinding] = []

    if case.verification.available_path == "no_viable_path_yet":
        findings.append(
            KernelFinding(
                finding_id="verification_path_blocked",
                severity="blocking",
                summary_en="No defendable verification path is available at the current project stage.",
                summary_zh="当前项目阶段尚无可辩护的复核路径。",
                basis_ids=["gb_50017_general"] if registry.get("gb_50017_general") else [],
                traces=[
                    _trace("verification.available_path", case.verification.available_path),
                    _trace("evidence.drawing_availability", case.evidence.drawing_availability),
                    _trace("evidence.survey_available", case.evidence.survey_available),
                ],
            )
        )

    if case.roof.panel_type == "profiled_sheet" and (
        case.roof.panel_thickness_mm is None or case.roof.rib_height_mm is None
    ):
        findings.append(
            KernelFinding(
                finding_id="roof_attachment_uncertainty",
                severity="caution",
                summary_en="Roof attachment pathway remains uncertain because panel geometry is incomplete.",
                summary_zh="由于屋面板几何信息不完整，当前连接路径仍不确定。",
                basis_ids=["gb_50017_general"] if registry.get("gb_50017_general") else [],
                traces=[
                    _trace("roof.panel_type", case.roof.panel_type),
                    _trace("roof.panel_thickness_mm", case.roof.panel_thickness_mm),
                    _trace("roof.rib_height_mm", case.roof.rib_height_mm),
                ],
            )
        )

    if any(finding.severity == "blocking" for finding in findings):
        return KernelOutcome(
            decision=KernelDecision(status="no_go", confidence="low"),
            findings=findings,
        )

    if findings:
        return KernelOutcome(
            decision=KernelDecision(status="conditional_go", confidence="medium"),
            findings=findings,
        )

    return KernelOutcome(
        decision=KernelDecision(status="go", confidence="high"),
        findings=[],
    )
