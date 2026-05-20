from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from structural_screening_agent.bv_review.models import (
    BVDocumentStatus,
    BVReviewIntake,
    BVReviewResult,
)
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    ProjectReviewState,
)


ServiceScopeArea = Literal[
    "document_control",
    "rfi_closeout",
    "calculation_review",
    "optimization_review",
]
ServiceScopePriority = Literal["high", "medium", "low"]
ServiceScopeLanguage = Literal["zh", "en"]


class ServiceScopeRecommendation(BaseModel):
    recommendation_id: str = Field(min_length=1)
    service_area: ServiceScopeArea
    title: str = Field(min_length=1)
    priority: ServiceScopePriority
    trigger_evidence_ids: list[str] = Field(min_length=1)
    trigger_basis: str = Field(min_length=1)
    client_value: str = Field(min_length=1)
    boundary_statement: str = Field(min_length=1)


def build_service_scope_recommendations(
    intake: BVReviewIntake,
    result: BVReviewResult,
    *,
    project_state: ProjectReviewState | None = None,
) -> list[ServiceScopeRecommendation]:
    recommendations: list[ServiceScopeRecommendation] = []
    document_evidence = _document_evidence(result)
    if document_evidence:
        recommendations.append(
            ServiceScopeRecommendation(
                recommendation_id="document_completeness_rfi_support",
                service_area="document_control",
                title="资料完整性与 RFI 关闭支持",
                priority="high",
                trigger_evidence_ids=document_evidence,
                trigger_basis="资料完整性检查识别缺失或不完整资料。",
                client_value=(
                    "帮助客户、设计院和承包商明确补资清单、责任边界和关闭顺序，"
                    "减少设计审查反复。"
                ),
                boundary_statement=_BOUNDARY_STATEMENT,
            )
        )

    active_rfi_ids = _active_rfi_ids(project_state)
    if active_rfi_ids:
        recommendations.append(
            ServiceScopeRecommendation(
                recommendation_id="rfi_closeout_management",
                service_area="rfi_closeout",
                title="RFI 台账、客户回复与增量复核管理",
                priority="high",
                trigger_evidence_ids=active_rfi_ids,
                trigger_basis="当前存在未关闭 RFI 或客户回复后待工程师复核项。",
                client_value=(
                    "以可追踪台账管理澄清问题、客户回复、关闭证据和增量复核，"
                    "支持后续报告再签发决策。"
                ),
                boundary_statement=_BOUNDARY_STATEMENT,
            )
        )

    calculation_evidence = _calculation_evidence(result, project_state)
    if calculation_evidence:
        recommendations.append(
            ServiceScopeRecommendation(
                recommendation_id="calculation_spot_check_follow_up",
                service_area="calculation_review",
                title="结构计算筛查结果专项复核",
                priority="high",
                trigger_evidence_ids=calculation_evidence,
                trigger_basis="确定性筛查计算或风险登记册提示需工程师复核。",
                client_value=(
                    "聚焦基础承载力、支架构件强度/稳定和最不利内力路径，"
                    "帮助客户决定是否需要补充正式计算书或设计修改。"
                ),
                boundary_statement=_BOUNDARY_STATEMENT,
            )
        )

    optimization_evidence = [
        risk.risk_id for risk in result.risks if risk.category == "optimization"
    ]
    if optimization_evidence:
        recommendations.append(
            ServiceScopeRecommendation(
                recommendation_id="constructability_optimization_review",
                service_area="optimization_review",
                title="支架布置、基础接口与施工可行性优化审查",
                priority="medium",
                trigger_evidence_ids=optimization_evidence,
                trigger_basis="风险登记册存在优化类发现。",
                client_value=(
                    "在不替代设计单位方案的前提下，提出支架布置、基础接口、"
                    "防腐和施工维护路径的第三方优化审查方向。"
                ),
                boundary_statement=_BOUNDARY_STATEMENT,
            )
        )

    return recommendations


def build_service_scope_display_rows(
    recommendations: list[ServiceScopeRecommendation],
    language: ServiceScopeLanguage,
) -> list[dict[str, str]]:
    if language == "zh":
        return [
            {
                "建议 ID": item.recommendation_id,
                "服务方向": _localized_title(item, "zh"),
                "优先级": _localized_priority(item.priority, "zh"),
                "触发证据": ", ".join(item.trigger_evidence_ids),
                "客户价值": _localized_client_value(item, "zh"),
                "边界声明": _localized_boundary("zh"),
            }
            for item in recommendations
        ]
    return [
        {
            "Recommendation ID": item.recommendation_id,
            "Service Scope": _localized_title(item, "en"),
            "Priority": _localized_priority(item.priority, "en"),
            "Trigger Evidence": ", ".join(item.trigger_evidence_ids),
            "Client Value": _localized_client_value(item, "en"),
            "Boundary": _localized_boundary("en"),
        }
        for item in recommendations
    ]


_BOUNDARY_STATEMENT = (
    "该建议仅用于第三方设计审核和 review-support 服务范围沟通，"
    "不替代正式设计、法定审批、盖章计算或 BV 官方签发流程。"
)

_EN_BOUNDARY_STATEMENT = (
    "This recommendation supports third-party design review and review-support "
    "scope discussions; it does not replace formal design, statutory approval, "
    "stamped calculations, or the official BV issue process."
)

_DISPLAY_TEXT = {
    "document_completeness_rfi_support": {
        "zh_title": "资料完整性与 RFI 关闭支持",
        "en_title": "Document completeness and RFI closeout support",
        "zh_value": (
            "帮助客户、设计院和承包商明确补资清单、责任边界和关闭顺序，"
            "减少设计审查反复。"
        ),
        "en_value": (
            "Clarifies missing document lists, responsibility boundaries, and "
            "closeout sequence for the client, designer, and contractor."
        ),
    },
    "rfi_closeout_management": {
        "zh_title": "RFI 台账、客户回复与增量复核管理",
        "en_title": "RFI register, client response, and incremental recheck management",
        "zh_value": (
            "以可追踪台账管理澄清问题、客户回复、关闭证据和增量复核，"
            "支持后续报告再签发决策。"
        ),
        "en_value": (
            "Tracks clarification items, client responses, closeout evidence, and "
            "incremental rechecks for later report re-issue decisions."
        ),
    },
    "calculation_spot_check_follow_up": {
        "zh_title": "结构计算筛查结果专项复核",
        "en_title": "Structural calculation screening follow-up review",
        "zh_value": (
            "聚焦基础承载力、支架构件强度/稳定和最不利内力路径，"
            "帮助客户决定是否需要补充正式计算书或设计修改。"
        ),
        "en_value": (
            "Focuses on foundation capacity, mounting member strength/stability, "
            "and governing force paths to support decisions on calculation updates."
        ),
    },
    "constructability_optimization_review": {
        "zh_title": "支架布置、基础接口与施工可行性优化审查",
        "en_title": "Mounting layout, foundation interface, and constructability review",
        "zh_value": (
            "在不替代设计单位方案的前提下，提出支架布置、基础接口、"
            "防腐和施工维护路径的第三方优化审查方向。"
        ),
        "en_value": (
            "Provides third-party review directions for layout, foundation "
            "interfaces, corrosion protection, and construction/maintenance access."
        ),
    },
}


def _document_evidence(result: BVReviewResult) -> list[str]:
    evidence_statuses: set[BVDocumentStatus] = {"missing", "partial"}
    return [
        item.document_key
        for item in result.checklist_items
        if item.status in evidence_statuses
    ]


def _active_rfi_ids(project_state: ProjectReviewState | None) -> list[str]:
    if project_state is None:
        return []
    return [
        item.rfi_id
        for item in project_state.rfi_items
        if item.status in {"open", "responded", "reopened"}
    ]


def _calculation_evidence(
    result: BVReviewResult,
    project_state: ProjectReviewState | None,
) -> list[str]:
    evidence_ids = [
        risk.risk_id
        for risk in result.risks
        if risk.risk_id.startswith("calculation_review_required_")
    ]
    if project_state is None:
        return evidence_ids
    return [
        *evidence_ids,
        *[
            run.run_id
            for run in project_state.calculation_runs
            if _calculation_run_requires_follow_up(run)
        ],
    ]


def _calculation_run_requires_follow_up(run: CalculationRun) -> bool:
    if run.status != "completed":
        return False
    if run.result_summary.get("screening_status") == "review_required":
        return True
    try:
        return float(run.result_summary.get("controlling_utilization_ratio", 0)) > 1.0
    except (TypeError, ValueError):
        return False


def _localized_title(
    recommendation: ServiceScopeRecommendation,
    language: ServiceScopeLanguage,
) -> str:
    key = "zh_title" if language == "zh" else "en_title"
    return _DISPLAY_TEXT[recommendation.recommendation_id][key]


def _localized_client_value(
    recommendation: ServiceScopeRecommendation,
    language: ServiceScopeLanguage,
) -> str:
    key = "zh_value" if language == "zh" else "en_value"
    return _DISPLAY_TEXT[recommendation.recommendation_id][key]


def _localized_priority(
    priority: ServiceScopePriority,
    language: ServiceScopeLanguage,
) -> str:
    if language == "zh":
        return {"high": "高", "medium": "中", "low": "低"}[priority]
    return {"high": "High", "medium": "Medium", "low": "Low"}[priority]


def _localized_boundary(language: ServiceScopeLanguage) -> str:
    if language == "zh":
        return _BOUNDARY_STATEMENT
    return _EN_BOUNDARY_STATEMENT
