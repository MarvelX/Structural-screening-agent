from structural_screening_agent.bv_review.models import (
    BVChecklistItem,
    BVRiskItem,
    BVReviewIntake,
    BVReviewPathItem,
)


def build_risk_register(
    intake: BVReviewIntake,
    checklist: list[BVChecklistItem],
    review_paths: list[BVReviewPathItem],
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
    return risks
