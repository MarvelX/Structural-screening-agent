from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.field_diff import FieldDiff, IncrementalRecheckPlan
from structural_screening_agent.bv_review.project_state import ExtractedField
from structural_screening_agent.localization import Language


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
        standards_systems=list(standards_systems),
        review_objects=list(review_objects),
        client_requirements=_split_client_requirements(client_requirements_text),
        documents={key: documents.get(key, default.documents[key]) for key in BV_DOCUMENT_LABELS},
    )


def build_ground_fixed_human_gate_rows(language: Language) -> list[dict[str, object]]:
    if language == "zh":
        return [
            {
                "field_id": "tilt_angle_deg",
                "field_name": "支架倾角",
                "candidate_value": "25",
                "unit": "deg",
                "source_document_id": "structural-drawing-s101",
                "page_or_section": "S-101 支架布置图，第 3 条说明",
                "quote": "支架安装倾角 25 deg。",
                "confidence": 0.95,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "pile_length_m",
                "field_name": "桩长",
                "candidate_value": "3.5",
                "unit": "m",
                "source_document_id": "foundation-drawing-f201",
                "page_or_section": "F-201 基础表",
                "quote": "PHC 桩长 L=3.5m。",
                "confidence": 0.9,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "bearing_capacity_characteristic_kpa",
                "field_name": "地基承载力特征值",
                "candidate_value": "180",
                "unit": "kPa",
                "source_document_id": "geotechnical-report-g001",
                "page_or_section": "地勘报告第 4.2 节",
                "quote": "建议地基承载力特征值 fak=180kPa。",
                "confidence": 0.72,
                "is_confirmed": False,
                "include_in_calculation": False,
            },
        ]

    return [
        {
            "field_id": "tilt_angle_deg",
            "field_name": "Rack tilt angle",
            "candidate_value": "25",
            "unit": "deg",
            "source_document_id": "structural-drawing-s101",
            "page_or_section": "S-101 mounting layout, note 3",
            "quote": "Rack installation tilt angle: 25 deg.",
            "confidence": 0.95,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "pile_length_m",
            "field_name": "Pile length",
            "candidate_value": "3.5",
            "unit": "m",
            "source_document_id": "foundation-drawing-f201",
            "page_or_section": "F-201 foundation schedule",
            "quote": "PHC pile length L=3.5m.",
            "confidence": 0.9,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "bearing_capacity_characteristic_kpa",
            "field_name": "Characteristic bearing capacity",
            "candidate_value": "180",
            "unit": "kPa",
            "source_document_id": "geotechnical-report-g001",
            "page_or_section": "Geotechnical report section 4.2",
            "quote": "Recommended characteristic bearing capacity fak=180kPa.",
            "confidence": 0.72,
            "is_confirmed": False,
            "include_in_calculation": False,
        },
    ]


def build_extracted_fields_from_human_gate_rows(rows: list[dict[str, object]]) -> list[ExtractedField]:
    return [
        ExtractedField(
            field_id=str(row["field_id"]),
            name=str(row["field_name"]),
            candidate_value=str(row["candidate_value"]),
            unit=str(row["unit"]) if row.get("unit") else None,
            source_document_id=str(row["source_document_id"]),
            page_or_section=str(row["page_or_section"]),
            quote=str(row["quote"]),
            confidence=float(row["confidence"]),
            is_confirmed=bool(row["is_confirmed"]),
            confirmed_value=str(row["candidate_value"]) if row.get("is_confirmed") else None,
            confirmed_unit=str(row["unit"]) if row.get("is_confirmed") and row.get("unit") else None,
            include_in_calculation=bool(row["include_in_calculation"]),
        )
        for row in rows
    ]


def build_incremental_recheck_summary_rows(
    plan: IncrementalRecheckPlan, language: Language
) -> list[dict[str, object]]:
    if language == "zh":
        item_type_labels = {
            "field_confirmation": "字段确认",
            "calculation_recheck": "计算复核",
            "risk_reopen": "风险重开",
            "rfi": "RFI",
        }
        field_labels = {
            "item_id": "复核项 ID",
            "item_type_label": "类型",
            "reason": "原因",
            "field_ids": "字段 ID",
            "calculation_run_ids": "计算运行 ID",
            "risk_ids": "风险 ID",
        }
    else:
        item_type_labels = {
            "field_confirmation": "Field Confirmation",
            "calculation_recheck": "Calculation Recheck",
            "risk_reopen": "Risk Reopen",
            "rfi": "RFI",
        }
        field_labels = {
            "item_id": "Item ID",
            "item_type_label": "Type",
            "reason": "Reason",
            "field_ids": "Field IDs",
            "calculation_run_ids": "Calculation Run IDs",
            "risk_ids": "Risk IDs",
        }

    return [
        {
            field_labels["item_id"]: item.item_id,
            field_labels["item_type_label"]: item_type_labels[item.item_type],
            field_labels["reason"]: _localized_recheck_reason(item, language),
            field_labels["field_ids"]: ", ".join(item.field_ids),
            field_labels["calculation_run_ids"]: ", ".join(item.calculation_run_ids),
            field_labels["risk_ids"]: ", ".join(item.risk_ids),
        }
        for item in plan.affected_items
    ]


def build_field_diff_summary_rows(
    diffs: list[FieldDiff], language: Language
) -> list[dict[str, object]]:
    if language == "zh":
        labels = {
            "field_id": "字段 ID",
            "diff_type": "差分类型",
            "old_value": "原值",
            "new_value": "新值",
            "affects_calculation": "影响已锁定计算",
            "reopen_risk": "重开风险",
        }
        diff_type_labels = {
            "added": "新增",
            "modified": "修改",
            "removed": "删除",
            "source_changed": "来源变化",
        }
    else:
        labels = {
            "field_id": "Field ID",
            "diff_type": "Diff Type",
            "old_value": "Old Value",
            "new_value": "New Value",
            "affects_calculation": "Affects Locked Calculation",
            "reopen_risk": "Reopen Risk",
        }
        diff_type_labels = {
            "added": "Added",
            "modified": "Modified",
            "removed": "Removed",
            "source_changed": "Source Changed",
        }

    return [
        {
            labels["field_id"]: diff.field_id,
            labels["diff_type"]: diff_type_labels[diff.diff_type],
            labels["old_value"]: diff.old_value,
            labels["new_value"]: diff.new_value,
            labels["affects_calculation"]: _localized_bool(
                diff.affects_confirmed_calculation, language
            ),
            labels["reopen_risk"]: _localized_bool(diff.should_reopen_risk_items, language),
        }
        for diff in diffs
    ]


def localize_report_gate_reason(reason: str, language: Language) -> str:
    incremental_prefix = "Open RFI items trigger incremental recheck: "
    if language == "zh" and reason.startswith(incremental_prefix):
        return "未关闭的 RFI 触发增量复核：" + reason.removeprefix(incremental_prefix)
    return reason


def _localized_recheck_reason(item, language: Language) -> str:
    field_ids = ", ".join(item.field_ids)
    if language == "zh":
        if item.item_type == "calculation_recheck":
            return f"{field_ids} 已变化，需要重新复核已锁定计算输入。"
        if item.item_type == "risk_reopen":
            return f"{field_ids} 已变化，需要重开关联风险项。"
        if item.item_type == "field_confirmation":
            return f"{field_ids} 需要工程师重新确认。"
        return item.reason
    return item.reason


def _localized_bool(value: bool, language: Language) -> str:
    if language == "zh":
        return "是" if value else "否"
    return "Yes" if value else "No"
