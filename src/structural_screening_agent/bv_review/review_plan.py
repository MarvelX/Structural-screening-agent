from structural_screening_agent.bv_review.models import (
    BVChecklistItem,
    BVReviewIntake,
    BVReviewPathItem,
    BVReviewPlanItem,
)


def build_review_plan(
    intake: BVReviewIntake,
    checklist: list[BVChecklistItem],
    review_paths: list[BVReviewPathItem],
) -> list[BVReviewPlanItem]:
    plan: list[BVReviewPlanItem] = [
        BVReviewPlanItem(
            item_id="intake_scope_confirmation",
            phase="intake",
            input_documents=["合同技术要求", "项目技术规格书"],
            method="确认审核范围、标准体系、设计阶段、客户特殊要求和报告交付边界。",
            responsible_role="BV project review lead",
            blocking_condition="审核范围或适用标准未确认",
            deliverable="设计审核范围确认记录",
        )
    ]
    for item in checklist:
        plan.append(
            BVReviewPlanItem(
                item_id=f"document_check_{item.document_key}",
                phase="document_review",
                input_documents=[item.title],
                method=f"核对{item.title}是否满足当前审核对象的输入需求。",
                responsible_role="BV document controller",
                blocking_condition=item.required_action if item.review_blocked else None,
                deliverable=f"{item.title}完整性检查记录",
            )
        )
    for path in review_paths:
        plan.append(
            BVReviewPlanItem(
                item_id=path.path_id,
                phase="technical_check",
                review_object=path.review_object,
                input_documents=path.required_inputs,
                method=path.method,
                responsible_role="BV structural review engineer",
                blocking_condition="必要输入资料未闭合" if path.status == "hold" else None,
                deliverable=path.deliverables[0] if path.deliverables else f"{path.title}审核记录",
            )
        )
    plan.append(
        BVReviewPlanItem(
            item_id="report_issue_review",
            phase="reporting",
            input_documents=["资料完整性检查记录", "技术审核意见", "风险与不符合项清单"],
            method="汇总审核范围、依据、主要发现、不符合项、风险、优化建议和后续行动。",
            responsible_role="BV project review lead",
            blocking_condition="存在阻塞报告签发的不符合项",
            deliverable="BV 风格设计审查报告",
        )
    )
    return plan
