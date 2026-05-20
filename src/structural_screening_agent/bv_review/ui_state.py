from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.field_diff import FieldDiff, IncrementalRecheckPlan
from structural_screening_agent.bv_review.project_state import ExtractedField, ProjectReviewState
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

BV_REVIEW_PHASE_LABELS = {
    "intake": {"zh": "项目录入", "en": "Intake"},
    "document_check": {"zh": "资料检查", "en": "Document Check"},
    "basis_build": {"zh": "审核依据", "en": "Review Basis"},
    "review_plan": {"zh": "审核计划", "en": "Review Plan"},
    "engineer_data_lock": {"zh": "工程师数据锁定", "en": "Engineer Data Lock"},
    "calculation_check": {"zh": "计算校核", "en": "Calculation Check"},
    "risk_register": {"zh": "风险登记", "en": "Risk Register"},
    "report_draft": {"zh": "报告草稿", "en": "Report Draft"},
    "engineer_approval": {"zh": "工程师批准", "en": "Engineer Approval"},
    "issue_rfi_closeout": {"zh": "签发 / RFI 关闭", "en": "Issue / RFI Closeout"},
}

BV_REVIEW_PHASE_STATUS_LABELS = {
    "pending": {"zh": "待处理", "en": "Pending"},
    "running": {"zh": "运行中", "en": "Running"},
    "blocked": {"zh": "阻塞", "en": "Blocked"},
    "waiting_for_client": {"zh": "等待客户", "en": "Waiting for Client"},
    "waiting_for_engineer": {"zh": "等待工程师", "en": "Waiting for Engineer"},
    "approved": {"zh": "已批准", "en": "Approved"},
    "rejected": {"zh": "已驳回", "en": "Rejected"},
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
                "include_in_calculation": False,
            },
            {
                "field_id": "pile_diameter_mm",
                "field_name": "桩径",
                "candidate_value": "300",
                "unit": "mm",
                "source_document_id": "foundation-drawing-f201",
                "page_or_section": "F-201 基础表",
                "quote": "PHC 桩径 D=300mm。",
                "confidence": 0.9,
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
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "side_resistance_standard_kpa",
                "field_name": "侧阻力标准值",
                "candidate_value": "35",
                "unit": "kPa",
                "source_document_id": "geotechnical-report-g001",
                "page_or_section": "地勘报告第 4.3 节",
                "quote": "桩侧阻力标准值 qsk=35kPa。",
                "confidence": 0.72,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "uplift_force_kn",
                "field_name": "最不利抗拔力",
                "candidate_value": "140",
                "unit": "kN",
                "source_document_id": "calculation-report-c001",
                "page_or_section": "基础反力汇总表",
                "quote": "最不利抗拔反力 Nk=140kN。",
                "confidence": 0.84,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "compression_force_kn",
                "field_name": "最不利压力",
                "candidate_value": "10",
                "unit": "kN",
                "source_document_id": "calculation-report-c001",
                "page_or_section": "基础反力汇总表",
                "quote": "最不利压力 Nk=10kN。",
                "confidence": 0.84,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "section_area_mm2",
                "field_name": "立柱截面面积",
                "candidate_value": "2400",
                "unit": "mm2",
                "source_document_id": "calculation-report-c001",
                "page_or_section": "上部结构构件参数表",
                "quote": "立柱截面面积 A=2400mm2。",
                "confidence": 0.86,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "section_modulus_mm3",
                "field_name": "立柱截面模量",
                "candidate_value": "180000",
                "unit": "mm3",
                "source_document_id": "calculation-report-c001",
                "page_or_section": "上部结构构件参数表",
                "quote": "立柱截面模量 W=180000mm3。",
                "confidence": 0.86,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "radius_of_gyration_mm",
                "field_name": "立柱回转半径",
                "candidate_value": "32",
                "unit": "mm",
                "source_document_id": "calculation-report-c001",
                "page_or_section": "上部结构构件参数表",
                "quote": "立柱回转半径 i=32mm。",
                "confidence": 0.86,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "effective_length_m",
                "field_name": "立柱计算长度",
                "candidate_value": "3.2",
                "unit": "m",
                "source_document_id": "calculation-report-c001",
                "page_or_section": "上部结构计算长度表",
                "quote": "立柱计算长度 l0=3.2m。",
                "confidence": 0.86,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "steel_yield_strength_mpa",
                "field_name": "钢材屈服强度",
                "candidate_value": "235",
                "unit": "MPa",
                "source_document_id": "technical-specification-t001",
                "page_or_section": "材料章节",
                "quote": "钢材屈服强度 fy=235MPa。",
                "confidence": 0.88,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "axial_force_kn",
                "field_name": "立柱最不利轴力",
                "candidate_value": "60",
                "unit": "kN",
                "source_document_id": "calculation-report-c001",
                "page_or_section": "上部结构内力包络",
                "quote": "立柱最不利轴力 N=60kN。",
                "confidence": 0.86,
                "is_confirmed": True,
                "include_in_calculation": True,
            },
            {
                "field_id": "bending_moment_knm",
                "field_name": "立柱最不利弯矩",
                "candidate_value": "18",
                "unit": "kN*m",
                "source_document_id": "calculation-report-c001",
                "page_or_section": "上部结构内力包络",
                "quote": "立柱最不利弯矩 M=18kN*m。",
                "confidence": 0.86,
                "is_confirmed": True,
                "include_in_calculation": True,
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
            "include_in_calculation": False,
        },
        {
            "field_id": "pile_diameter_mm",
            "field_name": "Pile diameter",
            "candidate_value": "300",
            "unit": "mm",
            "source_document_id": "foundation-drawing-f201",
            "page_or_section": "F-201 foundation schedule",
            "quote": "PHC pile diameter D=300mm.",
            "confidence": 0.9,
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
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "side_resistance_standard_kpa",
            "field_name": "Standard side resistance",
            "candidate_value": "35",
            "unit": "kPa",
            "source_document_id": "geotechnical-report-g001",
            "page_or_section": "Geotechnical report section 4.3",
            "quote": "Standard pile side resistance qsk=35kPa.",
            "confidence": 0.72,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "uplift_force_kn",
            "field_name": "Worst uplift force",
            "candidate_value": "140",
            "unit": "kN",
            "source_document_id": "calculation-report-c001",
            "page_or_section": "Foundation reaction summary",
            "quote": "Worst uplift reaction Nk=140kN.",
            "confidence": 0.84,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "compression_force_kn",
            "field_name": "Worst compression force",
            "candidate_value": "10",
            "unit": "kN",
            "source_document_id": "calculation-report-c001",
            "page_or_section": "Foundation reaction summary",
            "quote": "Worst compression reaction Nk=10kN.",
            "confidence": 0.84,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "section_area_mm2",
            "field_name": "Post section area",
            "candidate_value": "2400",
            "unit": "mm2",
            "source_document_id": "calculation-report-c001",
            "page_or_section": "Superstructure member property table",
            "quote": "Post section area A=2400mm2.",
            "confidence": 0.86,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "section_modulus_mm3",
            "field_name": "Post section modulus",
            "candidate_value": "180000",
            "unit": "mm3",
            "source_document_id": "calculation-report-c001",
            "page_or_section": "Superstructure member property table",
            "quote": "Post section modulus W=180000mm3.",
            "confidence": 0.86,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "radius_of_gyration_mm",
            "field_name": "Post radius of gyration",
            "candidate_value": "32",
            "unit": "mm",
            "source_document_id": "calculation-report-c001",
            "page_or_section": "Superstructure member property table",
            "quote": "Post radius of gyration i=32mm.",
            "confidence": 0.86,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "effective_length_m",
            "field_name": "Post effective length",
            "candidate_value": "3.2",
            "unit": "m",
            "source_document_id": "calculation-report-c001",
            "page_or_section": "Superstructure effective length table",
            "quote": "Post effective length l0=3.2m.",
            "confidence": 0.86,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "steel_yield_strength_mpa",
            "field_name": "Steel yield strength",
            "candidate_value": "235",
            "unit": "MPa",
            "source_document_id": "technical-specification-t001",
            "page_or_section": "Material section",
            "quote": "Steel yield strength fy=235MPa.",
            "confidence": 0.88,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "axial_force_kn",
            "field_name": "Post worst axial force",
            "candidate_value": "60",
            "unit": "kN",
            "source_document_id": "calculation-report-c001",
            "page_or_section": "Superstructure force envelope",
            "quote": "Post worst axial force N=60kN.",
            "confidence": 0.86,
            "is_confirmed": True,
            "include_in_calculation": True,
        },
        {
            "field_id": "bending_moment_knm",
            "field_name": "Post worst bending moment",
            "candidate_value": "18",
            "unit": "kN*m",
            "source_document_id": "calculation-report-c001",
            "page_or_section": "Superstructure force envelope",
            "quote": "Post worst bending moment M=18kN*m.",
            "confidence": 0.86,
            "is_confirmed": True,
            "include_in_calculation": True,
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


def build_agent_workflow_phase_rows(
    state: ProjectReviewState, language: Language
) -> list[dict[str, object]]:
    labels = (
        {"phase": "阶段", "status": "状态", "current": "当前", "yes": "是", "no": ""}
        if language == "zh"
        else {"phase": "Phase", "status": "Status", "current": "Current", "yes": "Yes", "no": ""}
    )
    return [
        {
            labels["phase"]: BV_REVIEW_PHASE_LABELS[phase][language],
            labels["status"]: BV_REVIEW_PHASE_STATUS_LABELS[status][language],
            labels["current"]: labels["yes"] if phase == state.current_phase else labels["no"],
        }
        for phase, status in state.phase_statuses.items()
    ]


def build_agent_workflow_artifact_rows(
    state: ProjectReviewState, language: Language
) -> list[dict[str, object]]:
    labels = (
        {"artifact": "产物", "count": "数量"}
        if language == "zh"
        else {"artifact": "Artifact", "count": "Count"}
    )
    artifact_labels = (
        [
            ("资料版本", len(state.document_versions)),
            ("抽取字段", len(state.extracted_fields)),
            ("审核依据", len(state.basis_references)),
            ("审核计划", len(state.review_plan)),
            ("审核路径", len(state.review_paths)),
            ("计算运行", len(state.calculation_runs)),
            ("风险 / NCR", len(state.risks)),
            ("RFI", len(state.rfi_items)),
            ("报告章节", len(state.report_sections)),
        ]
        if language == "zh"
        else [
            ("Document Versions", len(state.document_versions)),
            ("Extracted Fields", len(state.extracted_fields)),
            ("Review Basis", len(state.basis_references)),
            ("Review Plan", len(state.review_plan)),
            ("Review Paths", len(state.review_paths)),
            ("Calculation Runs", len(state.calculation_runs)),
            ("Risks / NCR", len(state.risks)),
            ("RFI", len(state.rfi_items)),
            ("Report Sections", len(state.report_sections)),
        ]
    )
    return [
        {labels["artifact"]: artifact, labels["count"]: count}
        for artifact, count in artifact_labels
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


def build_calculation_result_summary_rows(
    result_summary: dict[str, object], language: Language
) -> list[dict[str, object]]:
    item_label = "项目" if language == "zh" else "Item"
    result_label = "结果" if language == "zh" else "Result"
    return [
        {
            item_label: _localized_calculation_result_key(key, language),
            result_label: _localized_calculation_result_value(value, language),
        }
        for key, value in result_summary.items()
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


def _localized_calculation_result_key(key: str, language: Language) -> str:
    if language != "zh":
        return key
    labels = {
        "screening_boundary": "筛查边界",
        "overturning_check_note": "抗倾覆提示",
        "uplift_capacity_kn": "抗拔承载力",
        "bearing_capacity_kn": "地基承载力",
        "uplift_utilization_ratio": "抗拔利用率",
        "bearing_utilization_ratio": "地基承载力利用率",
        "controlling_utilization_ratio": "控制利用率",
        "screening_status": "筛查状态",
        "member_id": "构件 ID",
        "member_type": "构件类型",
        "axial_stress_mpa": "轴向应力",
        "bending_stress_mpa": "弯曲应力",
        "strength_utilization_ratio": "强度利用率",
        "slenderness_ratio": "长细比",
        "slenderness_utilization_ratio": "长细比利用率",
        "stability_utilization_ratio": "稳定利用率",
    }
    return labels.get(key, key)


def _localized_calculation_result_value(value: object, language: Language) -> object:
    if language != "zh":
        return value
    labels = {
        "screening-level review support only": "仅用于筛查级审核支持",
        "not covered; engineer review required": "未覆盖；需工程师复核",
        "pass": "通过",
        "review_required": "需复核",
        "post": "立柱",
        "beam": "横梁",
        "purlin": "檩条",
        "brace": "斜撑",
    }
    return labels.get(value, value)
