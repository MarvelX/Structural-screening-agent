from typing import Dict, Literal

from structural_screening_agent.models import (
    AttachmentPathway,
    BilingualItem,
    DecisionStatus,
    EngineeringCheck,
    ReserveUncertainty,
    ResourceRecommendation,
    ReviewTrigger,
    ScreeningOption,
)

Language = Literal["zh", "en"]

TRANSLATIONS: Dict[str, Dict[Language, str]] = {
    "project_intake": {"zh": "项目输入", "en": "Project Intake"},
    "demo_scenario": {"zh": "案例库", "en": "Case Library"},
    "project_type": {"zh": "项目类型", "en": "Project Type"},
    "design_standard_context": {"zh": "规范体系", "en": "Design Standard Context"},
    "input_group_project_basics": {"zh": "基本项目条件", "en": "Project Basics"},
    "input_group_structural_evidence": {"zh": "结构证据链", "en": "Structural Evidence"},
    "input_group_roof_connection": {"zh": "屋面连接证据链", "en": "Roof Attachment Evidence"},
    "input_group_execution_constraints": {"zh": "施工约束", "en": "Execution Constraints"},
    "input_group_verification_route": {"zh": "复核路径", "en": "Verification Route"},
    "project_summary": {"zh": "项目概况", "en": "Project Summary"},
    "executive_summary": {"zh": "执行摘要", "en": "Executive Summary"},
    "decision_snapshot": {"zh": "决策快照", "en": "Decision Snapshot"},
    "immediate_actions": {"zh": "即刻动作", "en": "Immediate Actions"},
    "review_paths_resources": {"zh": "复核路径与资源", "en": "Review Paths and Resources"},
    "management_summary": {"zh": "管理层摘要", "en": "Management Summary"},
    "drawing_facts_summary": {"zh": "图纸关键信息摘录", "en": "Drawing Facts Summary"},
    "verification_readiness": {"zh": "结构复核准备度", "en": "Verification Readiness"},
    "engineering_checks": {"zh": "工程筛查检查", "en": "Engineering Screening Checks"},
    "member_reserve_uncertainty_matrix": {"zh": "构件承载储备不确定性矩阵", "en": "Member Reserve Uncertainty Matrix"},
    "attachment_pathway_matrix": {"zh": "屋面连接路径矩阵", "en": "Roof Attachment Pathway Matrix"},
    "review_trigger_matrix": {"zh": "专项复核触发项", "en": "Review Trigger Matrix"},
    "review_progression": {"zh": "复核推进链", "en": "Review Progression"},
    "resource_recommendations": {"zh": "建议配置资源", "en": "Recommended Resources"},
    "check_action_linkage": {"zh": "检查联动摘要", "en": "Check-to-Action Linkage"},
    "assumptions_limitations": {"zh": "假设与边界", "en": "Assumptions and Limits"},
    "case_brief": {"zh": "案例概况", "en": "Case Brief"},
    "decision_chain": {"zh": "决策链摘要", "en": "Decision Chain"},
    "decision_summary": {"zh": "决策摘要", "en": "Decision Summary"},
    "decision": {"zh": "决策结论", "en": "Decision"},
    "building_type": {"zh": "建筑类型", "en": "Building Type"},
    "structural_system": {"zh": "结构体系", "en": "Structural System"},
    "roof_type": {"zh": "屋面类型", "en": "Roof Type"},
    "modification": {"zh": "拟改造内容", "en": "Modification"},
    "added_load": {"zh": "新增荷载 (kPa)", "en": "Added Load (kPa)"},
    "shutdown_constraint": {"zh": "停工约束", "en": "Shutdown Constraint"},
    "drawing_availability": {"zh": "图纸完整性", "en": "Drawing Availability"},
    "survey_available": {"zh": "已有现场调查", "en": "Survey Available"},
    "roof_panel_thickness": {"zh": "压型钢板板厚 (mm)", "en": "Roof Panel Thickness (mm)"},
    "roof_rib_height": {"zh": "压型钢板波高 (mm)", "en": "Roof Rib Height (mm)"},
    "building_span": {"zh": "建筑跨度 (m)", "en": "Building Span (m)"},
    "column_spacing": {"zh": "柱距 (m)", "en": "Column Spacing (m)"},
    "purlin_type": {"zh": "檩条形式", "en": "Purlin Type"},
    "roof_panel_type": {"zh": "屋面板类型", "en": "Roof Panel Type"},
    "attachment_preference": {"zh": "连接偏好", "en": "Attachment Preference"},
    "existing_member_schedule_status": {"zh": "既有构件表", "en": "Existing Member Schedule"},
    "connection_detail_status": {"zh": "节点连接做法", "en": "Connection Detail Record"},
    "roof_vendor_data_status": {"zh": "屋面系统厂家资料", "en": "Roof Vendor Data"},
    "corrosion_condition": {"zh": "腐蚀状况", "en": "Corrosion Condition"},
    "waterproofing_sensitivity": {"zh": "防水敏感性", "en": "Waterproofing Sensitivity"},
    "restricted_installation_zones": {"zh": "限制安装区域", "en": "Restricted Installation Zones"},
    "verification_path": {"zh": "可用复核路径", "en": "Available Verification Path"},
    "main_case_screening_inputs": {"zh": "主案例筛查项", "en": "Main-Case Screening Inputs"},
    "basis": {"zh": "依据", "en": "Basis"},
    "priority_rationale": {"zh": "当前优先原因", "en": "Priority Rationale"},
    "fit_when": {"zh": "适用情形", "en": "Fit When"},
    "main_constraint": {"zh": "主要约束", "en": "Main Constraint"},
    "operational_impact": {"zh": "运营影响", "en": "Operational Impact"},
    "cost_level": {"zh": "成本等级", "en": "Cost Level"},
    "schedule_impact": {"zh": "工期影响", "en": "Schedule Impact"},
    "recommendation_note": {"zh": "推荐说明", "en": "Recommendation Note"},
    "top_risks": {"zh": "关键风险", "en": "Top Risks"},
    "recommended_action": {"zh": "建议动作", "en": "Recommended Actions"},
    "review_needed": {"zh": "后续规范复核提示", "en": "Review Needed"},
    "missing_data": {"zh": "待补关键资料", "en": "Missing Critical Data"},
    "follow_up_questions": {"zh": "建议补充追问", "en": "Follow-up Questions"},
    "options": {"zh": "方案选项", "en": "Options"},
    "agent_explanation": {"zh": "智能体说明", "en": "Agent Explanation"},
    "decision_memo": {"zh": "决策摘要", "en": "Decision Memo"},
    "scenario": {"zh": "场景", "en": "Scenario"},
    "confidence": {"zh": "置信度", "en": "Confidence"},
    "language": {"zh": "界面语言", "en": "Interface Language"},
    "fallback_active": {"zh": "已切换降级", "en": "Fallback Active"},
    "primary_path": {"zh": "优先路径", "en": "Primary Path"},
    "backup_path": {"zh": "备选路径", "en": "Backup Path"},
    "download_bilingual_report": {"zh": "下载双语报告", "en": "Download Bilingual Report"},
    "none": {"zh": "无", "en": "None"},
    "featured_demo": {"zh": "推荐案例", "en": "Recommended Case"},
    "demo_flow": {"zh": "使用流程", "en": "How to Use"},
    "report_export_note": {"zh": "Markdown 双语导出", "en": "Bilingual Markdown export"},
    "product_scope": {"zh": "当前适用边界", "en": "Current Scope"},
    "standards_context_note": {"zh": "规范上下文说明", "en": "Standards Context"},
    "scope_note": {
        "zh": "当前输出仅用于前期结构筛查与路径判断，不替代正式结构设计、规范计算或签字结论。",
        "en": "Current output is for early-stage structural screening and path selection only. It does not replace formal design, code calculations, or signed engineering conclusions.",
    },
    "standards_note": {
        "zh": "规范体系仅用于标记后续应进入哪套规范复核路径，当前版本不执行 GB / AISC / Eurocode 的正式条文计算。",
        "en": "The standards context only marks which code path should govern the next-stage review. This version does not perform full GB / AISC / Eurocode calculations.",
    },
    "provider_status": {"zh": "模型状态", "en": "Provider Status"},
    "mock_fallback": {"zh": "模拟降级模式", "en": "Mock fallback"},
    "live_model": {"zh": "在线模型模式", "en": "Live model"},
    "app_title": {"zh": "结构可行性评估智能体", "en": "Structural Feasibility Screening Agent"},
    "must_do": {"zh": "必须先做", "en": "Must Do"},
    "parallel": {"zh": "建议并行做", "en": "Parallel Track"},
    "later": {"zh": "可后续做", "en": "Later Step"},
    "ready": {"zh": "已具备", "en": "Ready"},
    "partial": {"zh": "部分具备", "en": "Partial Ready"},
    "not_ready": {"zh": "尚不具备", "en": "Not Ready"},
    "screen_pass": {"zh": "可初步放行", "en": "Screen Pass"},
    "review": {"zh": "需专项复核", "en": "Review Needed"},
    "undetermined": {"zh": "当前不可判定", "en": "Undetermined"},
    "uncertainty_low": {"zh": "低不确定性", "en": "Low Uncertainty"},
    "uncertainty_medium": {"zh": "中等不确定性", "en": "Medium Uncertainty"},
    "uncertainty_high": {"zh": "高不确定性", "en": "High Uncertainty"},
}

OPTION_TRANSLATIONS: Dict[str, Dict[str, Dict[Language, str]]] = {
    "project_type": {
        "rooftop_pv": {"zh": "屋面光伏", "en": "Rooftop PV"},
        "load_upgrade": {"zh": "荷载升级", "en": "Load Upgrade"},
        "retrofit": {"zh": "结构改造", "en": "Retrofit"},
        "mixed": {"zh": "混合场景", "en": "Mixed Scenario"},
    },
    "design_standard_context": {
        "gb": {"zh": "国标 GB", "en": "GB"},
        "aisc": {"zh": "美标 AISC", "en": "AISC"},
        "eurocode": {"zh": "欧标 Eurocode", "en": "Eurocode"},
    },
    "shutdown_constraint": {
        "none": {"zh": "不停工约束", "en": "No Shutdown Constraint"},
        "limited": {"zh": "有限停工", "en": "Limited Shutdown"},
        "strict": {"zh": "严格不停工", "en": "Strict No Shutdown"},
    },
    "drawing_availability": {
        "complete": {"zh": "完整", "en": "Complete"},
        "partial": {"zh": "部分缺失", "en": "Partial"},
        "missing": {"zh": "缺失", "en": "Missing"},
    },
    "roof_panel_type": {
        "profiled_sheet": {"zh": "压型钢板", "en": "Profiled Steel Sheet"},
        "sandwich_panel": {"zh": "夹芯板", "en": "Sandwich Panel"},
        "standing_seam": {"zh": "直立锁边板", "en": "Standing Seam Roof"},
        "unknown": {"zh": "暂不明确", "en": "Unknown"},
    },
    "roof_attachment_preference": {
        "clamp_based": {"zh": "夹持式", "en": "Clamp-based"},
        "penetrating": {"zh": "穿透式", "en": "Penetrating"},
        "undecided": {"zh": "尚未决定", "en": "Undecided"},
    },
    "corrosion_condition": {
        "low": {"zh": "低", "en": "Low"},
        "moderate": {"zh": "中等", "en": "Moderate"},
        "high": {"zh": "高", "en": "High"},
        "unknown": {"zh": "未知", "en": "Unknown"},
    },
    "waterproofing_sensitivity": {
        "low": {"zh": "低", "en": "Low"},
        "medium": {"zh": "中", "en": "Medium"},
        "high": {"zh": "高", "en": "High"},
    },
    "available_verification_path": {
        "drawings_only": {"zh": "仅图纸路径", "en": "Drawings Only"},
        "survey_only": {"zh": "仅调查路径", "en": "Survey Only"},
        "drawings_plus_survey": {"zh": "图纸 + 调查", "en": "Drawings plus Survey"},
        "no_viable_path_yet": {"zh": "暂无可行路径", "en": "No Viable Path Yet"},
    },
    "document_status": {
        "available": {"zh": "已掌握", "en": "Available"},
        "partial": {"zh": "部分掌握", "en": "Partial"},
        "missing": {"zh": "缺失", "en": "Missing"},
    },
    "purlin_type": {
        "cold_formed_z": {"zh": "冷弯 Z 型檩条", "en": "Cold-Formed Z Purlin"},
        "cold_formed_c": {"zh": "冷弯 C 型檩条", "en": "Cold-Formed C Purlin"},
        "hot_rolled": {"zh": "热轧型钢檩条", "en": "Hot-Rolled Purlin"},
        "unknown": {"zh": "暂不明确", "en": "Unknown"},
    },
}

PRESET_TEXT_TRANSLATIONS: Dict[str, Dict[str, Dict[Language, str]]] = {
    "building_type": {
        "existing warehouse": {"zh": "既有仓库", "en": "existing warehouse"},
        "existing logistics warehouse": {"zh": "既有物流仓库", "en": "existing logistics warehouse"},
        "industrial production building": {"zh": "工业生产建筑", "en": "industrial production building"},
    },
    "structural_system": {
        "steel portal frame": {"zh": "门式刚架钢结构", "en": "steel portal frame"},
        "steel frame": {"zh": "钢框架", "en": "steel frame"},
        "steel-concrete composite": {"zh": "钢-混凝土组合结构", "en": "steel-concrete composite"},
    },
    "roof_type": {
        "metal roof": {"zh": "金属屋面", "en": "metal roof"},
        "insulated panel roof": {"zh": "保温夹芯板屋面", "en": "insulated panel roof"},
    },
    "modification": {
        "distributed rooftop pv": {"zh": "分布式屋面光伏", "en": "distributed rooftop pv"},
        "add conveyor and mezzanine support load": {
            "zh": "新增输送线与夹层支撑荷载",
            "en": "add conveyor and mezzanine support load",
        },
        "partial line retrofit and use change": {
            "zh": "产线局部改造与用途调整",
            "en": "partial line retrofit and use change",
        },
    },
}


def translate(language: Language, key: str) -> str:
    return TRANSLATIONS[key][language]


def translate_option(language: Language, group: str, value: str) -> str:
    return OPTION_TRANSLATIONS[group][value][language]


def language_label(language: Language, value: Language) -> str:
    labels = {
        "zh": {"zh": "中文", "en": "英文"},
        "en": {"zh": "Chinese", "en": "English"},
    }
    return labels[language][value]


def localize_preset_text(language: Language, field: str, value: str) -> str:
    field_mapping = PRESET_TEXT_TRANSLATIONS.get(field, {})
    localized = field_mapping.get(value)
    if localized:
        return localized[language]
    return value


def canonicalize_preset_text(field: str, value: str) -> str:
    field_mapping = PRESET_TEXT_TRANSLATIONS.get(field, {})
    for canonical_value, localized in field_mapping.items():
        if value in localized.values():
            return canonical_value
    return value


def format_bilingual_item(item: BilingualItem, language: Language) -> str:
    return item.title_zh if language == "zh" else item.title_en


def format_bilingual_detail(item: BilingualItem, language: Language) -> str:
    detail = item.detail_zh if language == "zh" else item.detail_en
    if not detail:
        return ""
    return f"{translate(language, 'basis')}: {detail}"


def format_option_detail(option: ScreeningOption, field: str, language: Language) -> str:
    value = getattr(option, f"{field}_{language}")
    return f"{translate(language, field)}: {value}"


def format_decision_localized(status: DecisionStatus, language: Literal["zh", "en", "bilingual"]) -> str:
    mapping = {
        DecisionStatus.GO: {"zh": "可推进", "en": "Go", "bilingual": "Go | 可推进"},
        DecisionStatus.CONDITIONAL_GO: {
            "zh": "有条件推进",
            "en": "Conditional Go",
            "bilingual": "Conditional Go | 有条件推进",
        },
        DecisionStatus.NO_GO: {"zh": "暂不建议推进", "en": "No-Go", "bilingual": "No-Go | 暂不建议推进"},
    }
    return mapping[status][language]


def format_confidence(value: str, language: Language) -> str:
    mapping = {
        "high": {"zh": "高", "en": "High"},
        "medium": {"zh": "中", "en": "Medium"},
        "low": {"zh": "低", "en": "Low"},
    }
    return mapping[value][language]


def format_verification_readiness(level: Literal["ready", "partial", "not_ready"], language: Language) -> str:
    return translate(language, level)


def format_engineering_check(check: EngineeringCheck, language: Language) -> str:
    title = check.title_zh if language == "zh" else check.title_en
    return f"{title}: {translate(language, check.status)}"


def format_reserve_uncertainty(item: ReserveUncertainty, language: Language) -> str:
    title = item.title_zh if language == "zh" else item.title_en
    severity_key = f"uncertainty_{item.severity}"
    return f"{title}: {translate(language, severity_key)}"


def format_attachment_pathway(item: AttachmentPathway, language: Language) -> str:
    title = item.title_zh if language == "zh" else item.title_en
    return f"{title}: {translate(language, item.status)}"


def format_resource_recommendation(item: ResourceRecommendation, language: Language) -> str:
    return item.title_zh if language == "zh" else item.title_en


def format_review_trigger(trigger: ReviewTrigger, language: Language) -> str:
    return trigger.title_zh if language == "zh" else trigger.title_en
