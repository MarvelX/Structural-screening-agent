from structural_screening_agent.bv_review.models import BVReviewIntake


BV_STANDARD_LABELS = {
    "gb": {"zh": "GB 国标", "en": "GB"},
    "iec": {"zh": "IEC 光伏标准", "en": "IEC"},
    "as_nzs": {"zh": "AS/NZS", "en": "AS/NZS"},
    "eurocode": {"zh": "Eurocode", "en": "Eurocode"},
}

BV_REVIEW_OBJECT_LABELS = {
    "mounting_structure": {"zh": "支架结构", "en": "Mounting Structure"},
    "steel_structure": {"zh": "钢结构", "en": "Steel Structure"},
    "concrete_structure": {"zh": "混凝土结构", "en": "Concrete Structure"},
    "foundation": {"zh": "地基与基础", "en": "Foundation"},
    "connection": {"zh": "连接节点", "en": "Connection"},
    "load_calculation": {"zh": "荷载计算", "en": "Load Calculation"},
    "existing_rooftop_added_load": {"zh": "既有屋面增载", "en": "Existing Rooftop Added Load"},
}

BV_DOCUMENT_LABELS = {
    "structural_drawings": {"zh": "结构图纸", "en": "Structural Drawings"},
    "calculation_report": {"zh": "结构计算书", "en": "Calculation Report"},
    "technical_specification": {"zh": "项目技术规格书", "en": "Technical Specification"},
    "geotechnical_report": {"zh": "地勘报告", "en": "Geotechnical Report"},
    "vendor_datasheets": {"zh": "厂家资料", "en": "Vendor Datasheets"},
    "contract_requirements": {"zh": "合同技术要求", "en": "Contract Requirements"},
}

BV_PROJECT_TYPE_LABELS = {
    "utility_pv": {"zh": "集中式光伏", "en": "Utility PV"},
    "rooftop_pv": {"zh": "屋面光伏", "en": "Rooftop PV"},
    "distributed_pv": {"zh": "分布式光伏", "en": "Distributed PV"},
    "mixed": {"zh": "混合项目", "en": "Mixed"},
}

BV_DESIGN_STAGE_LABELS = {
    "concept": {"zh": "概念阶段", "en": "Concept"},
    "tender": {"zh": "招标阶段", "en": "Tender"},
    "detailed_design": {"zh": "详细设计", "en": "Detailed Design"},
    "construction_drawing": {"zh": "施工图阶段", "en": "Construction Drawing"},
    "as_built": {"zh": "竣工资料", "en": "As-built"},
}

BV_DOCUMENT_STATUS_LABELS = {
    "available": {"zh": "已提供", "en": "Available"},
    "partial": {"zh": "部分提供", "en": "Partial"},
    "missing": {"zh": "缺失", "en": "Missing"},
    "not_applicable": {"zh": "不适用", "en": "Not Applicable"},
}


def _split_client_requirements(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def default_bv_review_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="BV rooftop PV design review demo",
        country_or_region="China",
        project_type="rooftop_pv",
        design_stage="construction_drawing",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "existing_rooftop_added_load"],
        client_requirements=["Client requires independent structural design review."],
        documents={
            "structural_drawings": "partial",
            "calculation_report": "missing",
            "technical_specification": "available",
            "geotechnical_report": "missing",
            "vendor_datasheets": "partial",
            "contract_requirements": "available",
        },
    )


def build_bv_review_intake(
    *,
    project_name: str,
    country_or_region: str,
    project_type: str,
    design_stage: str,
    standards_systems: list[str],
    review_objects: list[str],
    client_requirements_text: str,
    documents: dict[str, str],
) -> BVReviewIntake:
    default = default_bv_review_intake()
    return BVReviewIntake(
        project_name=project_name.strip() or default.project_name,
        country_or_region=country_or_region.strip() or default.country_or_region,
        project_type=project_type,
        design_stage=design_stage,
        standards_systems=standards_systems or list(default.standards_systems),
        review_objects=review_objects or list(default.review_objects),
        client_requirements=_split_client_requirements(client_requirements_text),
        documents={key: documents.get(key, default.documents[key]) for key in BV_DOCUMENT_LABELS},
    )
