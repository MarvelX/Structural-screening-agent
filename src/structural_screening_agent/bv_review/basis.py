from structural_screening_agent.bv_review.models import BVBasisReference, BVReviewIntake


GB_50017_REVIEW_OBJECTS = {
    "mounting_structure",
    "steel_structure",
    "connection",
    "existing_rooftop_added_load",
}
IEC_62548_REVIEW_OBJECTS = {"mounting_structure", "connection", "load_calculation"}


def _selected_review_objects(
    intake: BVReviewIntake, applicable_objects: set[str]
) -> list[str]:
    return [item for item in intake.review_objects if item in applicable_objects]


def build_review_basis(intake: BVReviewIntake) -> list[BVBasisReference]:
    references: list[BVBasisReference] = []

    if "gb" in intake.standards_systems:
        references.append(
            BVBasisReference(
                basis_id="gb_50797_pv_power_station_design",
                title="GB 50797 光伏发电站设计规范审核依据",
                source_type="code",
                standards_systems=["gb"],
                review_objects=list(intake.review_objects),
                trigger_conditions=["项目采用 GB 体系或位于中国项目语境"],
                evidence_requirements=["项目技术规格书", "设计说明", "总平面与结构专业图纸"],
                review_actions=["核对光伏电站总体设计、结构接口和设计边界"],
            )
        )
    gb_50017_review_objects = _selected_review_objects(intake, GB_50017_REVIEW_OBJECTS)
    if "gb" in intake.standards_systems and gb_50017_review_objects:
        references.append(
            BVBasisReference(
                basis_id="gb_50017_steel_structure_design",
                title="GB 50017 钢结构与支架设计标准审核依据",
                source_type="code",
                standards_systems=["gb"],
                review_objects=gb_50017_review_objects,
                trigger_conditions=["审核对象包含钢结构、支架、连接或既有钢结构增载"],
                evidence_requirements=["结构计算书", "构件截面表", "节点详图", "钢材牌号"],
                review_actions=["核对强度、稳定、变形、连接和构造审查路径"],
            )
        )
    iec_62548_review_objects = _selected_review_objects(intake, IEC_62548_REVIEW_OBJECTS)
    if "iec" in intake.standards_systems and iec_62548_review_objects:
        references.append(
            BVBasisReference(
                basis_id="iec_62548_pv_array_design",
                title="IEC 62548 光伏阵列设计结构接口审核依据",
                source_type="iec_standard",
                standards_systems=["iec"],
                review_objects=iec_62548_review_objects,
                trigger_conditions=["项目选择 IEC 体系或需核对组件阵列安装接口"],
                evidence_requirements=["组件布置图", "支架厂家资料", "安装说明", "接地与桥架接口说明"],
                review_actions=["核对阵列安装、支架接口、维护通道和结构接口边界"],
            )
        )
    if "as_nzs" in intake.standards_systems:
        references.append(
            BVBasisReference(
                basis_id="as_nzs_structural_review_context",
                title="AS/NZS 结构设计审核路径",
                source_type="code",
                standards_systems=["as_nzs"],
                review_objects=list(intake.review_objects),
                trigger_conditions=["项目选择 AS/NZS 体系"],
                evidence_requirements=["项目适用标准清单", "风荷载参数", "结构计算书"],
                review_actions=["按项目指定 AS/NZS 条款组织结构审核路径"],
            )
        )
    if "eurocode" in intake.standards_systems:
        references.append(
            BVBasisReference(
                basis_id="eurocode_structural_review_context",
                title="Eurocode 结构设计审核路径",
                source_type="code",
                standards_systems=["eurocode"],
                review_objects=list(intake.review_objects),
                trigger_conditions=["项目选择 Eurocode 体系"],
                evidence_requirements=["National Annex", "荷载参数", "结构计算书"],
                review_actions=["按 Eurocode 与项目 National Annex 组织结构审核路径"],
            )
        )
    references.append(
        BVBasisReference(
            basis_id="project_contract_requirements",
            title="项目技术规格书与合同要求",
            source_type="contract",
            standards_systems=list(intake.standards_systems),
            review_objects=list(intake.review_objects),
            trigger_conditions=["所有第三方设计审核项目均应核对合同和客户技术要求"],
            evidence_requirements=["合同技术条款", "业主要求", "设计输入条件"],
            review_actions=["确认审核范围、交付物、设计边界和报告签发条件"],
        )
    )
    return references
