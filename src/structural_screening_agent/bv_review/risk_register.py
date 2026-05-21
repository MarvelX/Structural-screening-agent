from __future__ import annotations

import re

from structural_screening_agent.bv_review.models import (
    BVChecklistItem,
    BVRiskItem,
    BVReviewIntake,
    BVReviewPathItem,
)
from structural_screening_agent.bv_review.project_state import CalculationRun


def build_risk_register(
    intake: BVReviewIntake,
    checklist: list[BVChecklistItem],
    review_paths: list[BVReviewPathItem],
    *,
    calculation_runs: list[CalculationRun] | None = None,
) -> list[BVRiskItem]:
    risks: list[BVRiskItem] = []
    for item in checklist:
        if item.status == "missing":
            risks.append(
                BVRiskItem(
                    risk_id=f"missing_{item.document_key}",
                    title=f"{item.title}缺失",
                    severity="critical",
                    trigger_basis=item.title,
                    linked_field_ids=[item.document_key],
                    impact_scope="、".join(item.affected_review_objects),
                    recommendation=item.required_action,
                    blocks_report_issue=True,
                    category="nonconformity",
                )
            )
        elif item.status == "partial":
            risks.append(
                BVRiskItem(
                    risk_id=f"partial_{item.document_key}",
                    title=f"{item.title}不完整",
                    severity="high",
                    trigger_basis=item.title,
                    linked_field_ids=[item.document_key],
                    impact_scope="、".join(item.affected_review_objects),
                    recommendation=item.required_action,
                    blocks_report_issue=False,
                    category="risk",
                )
            )
    if "mounting_structure" in intake.review_objects:
        risks.append(
            BVRiskItem(
                risk_id="mounting_layout_optimization",
                title="支架布置与施工可行性优化",
                severity="medium",
                trigger_basis="项目技术规格书与支架厂家资料",
                impact_scope="支架布置、防腐、施工通道和维护空间",
                recommendation="复核支架排布、檩条或基础接口、防腐等级和施工维护通道，形成优化建议。",
                blocks_report_issue=False,
                category="optimization",
            )
        )
    if any(path.status == "hold" for path in review_paths):
        risks.append(
            BVRiskItem(
                risk_id="review_path_has_holds",
                title="部分技术审核路径被资料缺口阻塞",
                severity="high",
                trigger_basis="资料完整性检查",
                impact_scope="设计审核计划与报告签发",
                recommendation="先关闭阻塞资料项，再签发无保留的设计审查报告。",
                blocks_report_issue=True,
                category="risk",
            )
        )
    risks.extend(_calculation_risks(calculation_runs or []))
    return risks


def _calculation_risks(calculation_runs: list[CalculationRun]) -> list[BVRiskItem]:
    risks: list[BVRiskItem] = []
    for run in calculation_runs:
        if run.status in {"blocked", "failed"}:
            risks.append(_blocked_calculation_risk(run))
            continue
        if run.status != "completed":
            continue
        ratio = run.result_summary.get("controlling_utilization_ratio")
        screening_status = run.result_summary.get("screening_status")
        if screening_status != "review_required" and not _ratio_exceeds_one(ratio):
            continue
        risks.append(
            BVRiskItem(
                risk_id=f"calculation_review_required_{_slug(run.run_id)}",
                title=f"{_engine_title(run.engine_name)}筛查结果需工程师复核",
                severity="high",
                trigger_basis=(
                    f"确定性筛查计算 {run.run_id}: 控制利用率={ratio}; "
                    f"筛查状态={_screening_status_label(screening_status)}; "
                    f"引擎版本={run.engine_version}; "
                    f"边界={run.result_summary.get('screening_boundary')}。"
                ),
                linked_field_ids=list(run.input_field_ids),
                impact_scope=_engine_impact_scope(run.engine_name),
                recommendation=(
                    "将该结果作为筛查级风险草稿，由工程师复核原计算书、输入参数、"
                    "荷载组合和适用标准后，再决定是否形成 RFI、NCR 或优化建议。"
                ),
                blocks_report_issue=True,
                category="risk",
            )
        )
    return risks


def _blocked_calculation_risk(run: CalculationRun) -> BVRiskItem:
    error_summary = "; ".join(run.structured_errors) if run.structured_errors else "无结构化错误说明"
    return BVRiskItem(
        risk_id=f"calculation_blocked_{_slug(run.run_id)}",
        title=f"{_engine_title(run.engine_name)}确定性计算输入阻塞",
        severity="critical",
        trigger_basis=(
            f"确定性筛查计算 {run.run_id}: 状态={run.status}; "
            f"结构化错误={error_summary}; "
            f"引擎版本={run.engine_version}。"
        ),
        linked_field_ids=list(run.input_field_ids),
        impact_scope=_engine_impact_scope(run.engine_name),
        recommendation=(
            "先关闭确定性计算输入缺口，复核工程师确认字段、资料版本和单位，"
            "再重新运行筛查级计算并进入报告草稿。"
        ),
        blocks_report_issue=True,
        category="nonconformity",
    )


def _ratio_exceeds_one(value: object) -> bool:
    try:
        return float(value) > 1.0
    except (TypeError, ValueError):
        return False


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _engine_title(engine_name: str) -> str:
    if engine_name == "foundation":
        return "基础"
    if engine_name == "superstructure":
        return "上部支架构件"
    return engine_name


def _engine_impact_scope(engine_name: str) -> str:
    if engine_name == "foundation":
        return "基础抗拔、地基承载力和相关 RFI/NCR 判断"
    if engine_name == "superstructure":
        return "上部支架构件强度、稳定和相关 RFI/NCR 判断"
    return "设计审核风险登记册"


def _screening_status_label(value: object) -> str:
    if value == "review_required":
        return "需复核"
    if value == "pass":
        return "通过"
    return str(value)
