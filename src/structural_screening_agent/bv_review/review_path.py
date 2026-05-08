from structural_screening_agent.bv_review.models import (
    BVChecklistItem,
    BVReviewIntake,
    BVReviewObject,
    BVReviewPathItem,
)


PATH_DEFINITIONS = {
    "mounting_structure": (
        "mounting_structure_review",
        "支架结构审核",
        "核对支架布置、构件强度、变形、防腐和厂家资料。",
        ["结构图纸", "结构计算书", "厂家资料"],
        ["支架结构审核意见"],
    ),
    "steel_structure": (
        "steel_structure_review",
        "钢结构审核",
        "核对钢构件强度、稳定、节点构造和防腐等级。",
        ["结构图纸", "结构计算书"],
        ["钢结构审核意见"],
    ),
    "concrete_structure": (
        "concrete_structure_review",
        "混凝土结构审核",
        "核对混凝土构件、预埋件、裂缝控制和耐久性要求。",
        ["结构图纸", "结构计算书"],
        ["混凝土结构审核意见"],
    ),
    "foundation": (
        "foundation_review",
        "地基与基础审核",
        "核对地勘报告、基础形式、承载力、抗拔和沉降控制。",
        ["地勘报告", "基础计算书"],
        ["基础审核意见"],
    ),
    "connection": (
        "connection_review",
        "连接节点审核",
        "核对夹具、锚栓、焊缝、螺栓和防水构造。",
        ["节点详图", "厂家资料", "结构计算书"],
        ["连接节点审核意见"],
    ),
    "load_calculation": (
        "load_calculation_review",
        "荷载计算审核",
        "核对恒载、风荷载、雪荷载、检修荷载和组合路径。",
        ["荷载计算书", "项目技术规格书"],
        ["荷载审核意见"],
    ),
    "existing_rooftop_added_load": (
        "existing_rooftop_added_load_review",
        "既有屋面增载审核",
        "复用现有门式刚架屋面光伏增载 screening kernel，并核对图纸、计算书和现场调查边界。",
        ["原结构图纸", "既有计算书", "现场调查"],
        ["既有结构增载初筛摘要"],
    ),
}


def _object_is_blocked(
    review_object: BVReviewObject, checklist: list[BVChecklistItem]
) -> bool:
    return any(
        item.review_blocked and review_object in item.affected_review_objects
        for item in checklist
    )


def build_structural_review_path(
    intake: BVReviewIntake, checklist: list[BVChecklistItem]
) -> list[BVReviewPathItem]:
    paths: list[BVReviewPathItem] = []
    for review_object in intake.review_objects:
        path_id, title, method, required_inputs, deliverables = PATH_DEFINITIONS[
            review_object
        ]
        blocked = _object_is_blocked(review_object, checklist)
        paths.append(
            BVReviewPathItem(
                path_id=path_id,
                review_object=review_object,
                title=title,
                method=method,
                required_inputs=required_inputs,
                deliverables=deliverables,
                status="hold" if blocked else "ready",
            )
        )
    return paths
