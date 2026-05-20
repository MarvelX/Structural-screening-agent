from structural_screening_agent.bv_review.models import BVChecklistItem, BVReviewIntake


DOCUMENT_RULES = {
    "structural_drawings": (
        "结构图纸",
        [
            "mounting_structure",
            "steel_structure",
            "concrete_structure",
            "connection",
            "existing_rooftop_added_load",
        ],
        "补充结构图纸或最新版设计图。",
    ),
    "calculation_report": (
        "结构计算书",
        [
            "mounting_structure",
            "steel_structure",
            "foundation",
            "connection",
            "load_calculation",
            "existing_rooftop_added_load",
        ],
        "补充结构计算书、荷载取值和设计校核过程。",
    ),
    "technical_specification": (
        "项目技术规格书",
        ["mounting_structure", "foundation", "connection", "load_calculation"],
        "补充项目技术规格书和设计输入条件。",
    ),
    "geotechnical_report": (
        "地勘报告",
        ["foundation"],
        "补充地勘报告、地基承载力特征值 fak、桩侧阻力标准值 qsk、土层参数和地下水条件。",
    ),
    "vendor_datasheets": (
        "厂家资料",
        ["mounting_structure", "connection"],
        "补充支架、夹具、锚栓或组件厂家资料。",
    ),
    "contract_requirements": (
        "合同技术要求",
        ["mounting_structure", "foundation", "connection", "load_calculation"],
        "补充合同技术条款和客户特殊要求。",
    ),
}


def build_document_checklist(intake: BVReviewIntake) -> list[BVChecklistItem]:
    items: list[BVChecklistItem] = []
    selected_objects = set(intake.review_objects)
    for document_key, (title, affected_objects, action) in DOCUMENT_RULES.items():
        relevant_objects = [item for item in affected_objects if item in selected_objects]
        if not relevant_objects:
            continue
        status = intake.documents.get(document_key, "missing")
        review_blocked = status == "missing"
        if status == "available":
            required_action = "资料已提供，进入技术审核。"
        elif status == "partial":
            required_action = f"资料部分提供；{action}"
        else:
            required_action = action
        items.append(
            BVChecklistItem(
                document_key=document_key,
                title=title,
                status=status,
                affected_review_objects=relevant_objects,
                review_blocked=review_blocked,
                required_action=required_action,
            )
        )
    return items
