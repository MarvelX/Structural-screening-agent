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
    "default_package": {"zh": "经验默认包", "en": "Default Package"},
    "default_package_hint": {"zh": "仅用于补齐未填写字段，不覆盖你已明确输入的条件。", "en": "Only fills blank fields and does not overwrite values you already provided."},
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
    "eave_height": {"zh": "檐口高度 (m)", "en": "Eave Height (m)"},
    "steel_grade": {"zh": "钢材标号", "en": "Steel Grade"},
    "steel_grade_preset": {"zh": "钢材标号常规选项", "en": "Steel Grade Preset"},
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
    "purlin_spacing": {"zh": "檩条间距 (m)", "en": "Purlin Spacing (m)"},
    "rafter_section": {"zh": "门架梁截面", "en": "Rafter Section"},
    "rafter_section_preset": {"zh": "门架梁截面常规选项", "en": "Rafter Section Preset"},
    "column_section": {"zh": "门架柱截面", "en": "Column Section"},
    "column_section_preset": {"zh": "门架柱截面常规选项", "en": "Column Section Preset"},
    "main_case_screening_inputs": {"zh": "主案例筛查项", "en": "Main-Case Screening Inputs"},
    "basis": {"zh": "依据", "en": "Basis"},
    "basis_ids": {"zh": "依据 ID", "en": "Basis IDs"},
    "engineering_meaning": {"zh": "工程含义", "en": "Engineering Meaning"},
    "input_traces": {"zh": "输入追踪", "en": "Input Traces"},
    "traceability_basis": {"zh": "可追溯性与依据", "en": "Traceability and Basis"},
    "assessment_scope": {"zh": "评估范围", "en": "Assessment Scope"},
    "project_input_tab": {"zh": "项目输入", "en": "Project Input"},
    "assessment_tab": {"zh": "评估结论", "en": "Assessment"},
    "basis_traceability_tab": {"zh": "依据与追溯", "en": "Basis & Traceability"},
    "report_export_tab": {"zh": "报告导出", "en": "Report Export"},
    "pv_3d_studio_tab": {"zh": "3D 展示", "en": "3D Studio"},
    "pv_3d_studio_heading": {"zh": "光伏支架 3D 结构实验室", "en": "PV Mounting 3D Structure Studio"},
    "pv_3d_studio_boundary": {
        "zh": "用于展示固定支架构件、传力链、基础和场区接口；不替代厂家模型、结构计算书或签章成果。",
        "en": "Demonstrates fixed rack components, load path, foundation, and site interfaces; it does not replace vendor models, structural calculations, or signed deliverables.",
    },
    "calculation_extension_tab": {"zh": "计算扩展", "en": "Calculation Extension"},
    "public_demo_banner": {
        "zh": "公开演示版本：仅用于 screening-level 审核支持展示，不替代正式设计、法定审批或签章计算。",
        "en": "Public demo build: for screening-level review support only; it does not replace formal design, statutory approval, or stamped calculations.",
    },
    "public_demo_caption": {
        "zh": "当前版本用于作品集展示与演示浏览，重点展示 BV 审核工作流、依据追溯和报告导出。",
        "en": "This build is intended for portfolio review and walkthroughs, focusing on BV review workflow, traceability, and report export.",
    },
    "bv_review_tab": {"zh": "BV 审核总览", "en": "BV Review"},
    "portal_frame_tab": {"zh": "门刚场景模块", "en": "Portal-Frame Scenario Module"},
    "bv_review_intake_heading": {"zh": "项目设计审核输入", "en": "Project Review Intake"},
    "bv_review_checklist_heading": {"zh": "设计资料完整性", "en": "Design Document Checklist"},
    "bv_review_basis_heading": {"zh": "审核依据", "en": "Review Basis"},
    "bv_review_path_heading": {"zh": "结构审核路径", "en": "Structural Review Path"},
    "bv_review_risk_heading": {"zh": "风险与不符合项清单", "en": "Risk & Nonconformity Register"},
    "bv_review_plan_heading": {"zh": "ITP 与审核计划", "en": "ITP & Review Plan"},
    "multi_agent_workflow_heading": {"zh": "多 Agent 工作流底座", "en": "Multi-Agent Workflow Foundation"},
    "human_gate_heading": {"zh": "工程师数据确认门禁", "en": "Engineer Data Confirmation Gate"},
    "human_gate_caption": {
        "zh": "示例参数来自地面固定支架审核场景。只有经工程师确认并标记进入计算的字段，才允许进入后续 A+B 计算接口。",
        "en": "Example fields come from the ground-fixed PV mounting review scenario. Only engineer-confirmed fields marked for calculation can enter later A+B calculation interfaces.",
    },
    "data_lock_button": {"zh": "确认并检查计算门禁", "en": "Confirm and Check Calculation Gate"},
    "calculation_gate_ready": {
        "zh": "计算门禁已准备：当前仅表示接口输入已锁定，不代表完成结构验算。",
        "en": "Calculation gate ready: this only means interface inputs are locked; it does not mean structural checks are complete.",
    },
    "calculation_gate_blocked": {
        "zh": "计算门禁阻塞：请先确认至少一个可追溯字段并标记进入计算。",
        "en": "Calculation gate blocked: confirm at least one traceable field and mark it for calculation first.",
    },
    "bv_review_warning_standards": {"zh": "请至少选择一个标准体系。", "en": "Select at least one standards system."},
    "bv_review_warning_objects": {"zh": "请至少选择一个审核对象。", "en": "Select at least one review object."},
    "photo_assist_entry": {"zh": "拍照辅助识别入口", "en": "Photo Assist Entry"},
    "photo_assist_targets": {"zh": "辅助识别目标", "en": "Photo Assist Targets"},
    "photo_assist_backfill_boundary": {"zh": "当前回填边界", "en": "Current Backfill Boundary"},
    "photo_assist_upload_hint": {
        "zh": "支持上传节点、檩条、屋面板和梁柱现状照片，后续用于辅助识别，不替代正式复核。",
        "en": "Upload connection, purlin, roof panel, and member-condition photos for future assisted recognition; this does not replace formal review.",
    },
    "photo_assist_received": {"zh": "已接收图片数量", "en": "Uploaded Photo Count"},
    "candidate_backfill_fields": {"zh": "候选回填字段", "en": "Candidate Backfill Fields"},
    "load_combination_sensitivity": {"zh": "荷载组合敏感性", "en": "Load Combination Sensitivity"},
    "input_summary": {"zh": "输入摘要", "en": "Input Summary"},
    "evidence_status": {"zh": "证据状态", "en": "Evidence Status"},
    "simplified_calculation_results": {"zh": "简化计算结果", "en": "Simplified Calculation Results"},
    "basis_references": {"zh": "规范依据", "en": "Basis References"},
    "applicable_standards": {"zh": "适用规范体系", "en": "Applicable Standards"},
    "trigger_conditions": {"zh": "触发条件", "en": "Trigger Conditions"},
    "evidence_requirements": {"zh": "证据需求", "en": "Evidence Requirements"},
    "follow_up_review": {"zh": "后续复核要求", "en": "Follow-up Review"},
    "preliminary_structural_conclusion": {"zh": "初步结构结论", "en": "Preliminary Structural Conclusion"},
    "next_step_review_actions": {"zh": "后续复核建议", "en": "Next-Step Review Actions"},
    "portal_frame_screening_title": {"zh": "门式刚架屋面光伏增载初筛", "en": "Portal-Frame Rooftop PV Screening"},
    "portal_frame_screening_subtitle": {
        "zh": "用于既有单层门式刚架厂房/仓库的结构初筛复核，输出简化计算结果、控制因素与下一步正式复核建议。",
        "en": "Structural screening review for existing single-story portal-frame buildings with rooftop PV added load.",
    },
    "portal_frame_screening_panel": {"zh": "门刚光伏初筛", "en": "Portal Frame PV Screening"},
    "priority_rationale": {"zh": "当前优先原因", "en": "Priority Rationale"},
    "fit_when": {"zh": "适用情形", "en": "Fit When"},
    "main_constraint": {"zh": "主要约束", "en": "Main Constraint"},
    "operational_impact": {"zh": "运营影响", "en": "Operational Impact"},
    "cost_level": {"zh": "成本等级", "en": "Cost Level"},
    "screening_cost_range": {"zh": "初筛成本区间", "en": "Screening Cost Range"},
    "screening_cost_note": {"zh": "成本区间说明", "en": "Cost Range Note"},
    "schedule_impact": {"zh": "工期影响", "en": "Schedule Impact"},
    "recommendation_note": {"zh": "推荐说明", "en": "Recommendation Note"},
    "top_risks": {"zh": "关键风险", "en": "Top Risks"},
    "recommended_action": {"zh": "建议动作", "en": "Recommended Actions"},
    "review_needed": {"zh": "后续规范复核提示", "en": "Review Needed"},
    "missing_data": {"zh": "待补关键资料", "en": "Missing Critical Data"},
    "follow_up_questions": {"zh": "建议补充追问", "en": "Follow-up Questions"},
    "options": {"zh": "方案选项", "en": "Options"},
    "agent_explanation": {"zh": "复核说明", "en": "Review Note"},
    "decision_memo": {"zh": "复核摘要", "en": "Review Summary"},
    "update_assessment": {"zh": "更新评估", "en": "Update Assessment"},
    "control_factors": {"zh": "控制因素", "en": "Controlling Factors"},
    "key_calculation_results": {"zh": "关键计算结果", "en": "Key Calculation Results"},
    "critical_calculation_results": {"zh": "关键计算结果", "en": "Critical Calculation Results"},
    "detailed_calculation_results": {"zh": "详细计算明细", "en": "Detailed Calculation Details"},
    "detailed_evidence_status": {"zh": "详细证据状态", "en": "Detailed Evidence Status"},
    "export_overview": {"zh": "导出说明", "en": "Export Overview"},
    "extension_overview": {"zh": "扩展接口说明", "en": "Extension Overview"},
    "scenario": {"zh": "场景", "en": "Scenario"},
    "confidence": {"zh": "置信度", "en": "Confidence"},
    "language": {"zh": "界面语言", "en": "Interface Language"},
    "fallback_active": {"zh": "已切换降级", "en": "Fallback Active"},
    "primary_path": {"zh": "优先路径", "en": "Primary Path"},
    "backup_path": {"zh": "备选路径", "en": "Backup Path"},
    "download_bilingual_report": {"zh": "下载双语版报告", "en": "Download Bilingual Report"},
    "download_word_report": {"zh": "下载文档版报告", "en": "Download Word Report"},
    "download_pdf_report": {"zh": "下载 PDF 版报告", "en": "Download PDF Report"},
    "download_text_report": {"zh": "下载文本报告", "en": "Download Markdown Report"},
    "custom_input": {"zh": "自定义输入", "en": "Custom Input"},
    "none": {"zh": "无", "en": "None"},
    "featured_demo": {"zh": "示例项目", "en": "Reference Case"},
    "demo_flow": {"zh": "查看顺序", "en": "Review Flow"},
    "report_export_note": {"zh": "文本版导出", "en": "Markdown Export"},
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
    "result_unit": {"zh": "结果单位", "en": "Result Unit"},
    "mock_fallback": {"zh": "模拟降级模式", "en": "Mock fallback"},
    "live_model": {"zh": "在线模型模式", "en": "Live model"},
    "app_title": {"zh": "门式刚架屋面光伏增载结构初筛", "en": "Portal-Frame Rooftop PV Structural Screening"},
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
    "default_package_key": {
        "none": {"zh": "不使用默认包", "en": "No Default Package"},
        "portal_frame_conservative": {"zh": "门刚保守默认包", "en": "Portal-Frame Conservative Package"},
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

INPUT_PATH_TRANSLATIONS: Dict[str, Dict[Language, str]] = {
    "member_evidence.drawing_availability": {"zh": "构件图纸完整性", "en": "Member Drawing Availability"},
    "member_evidence.member_schedule_status": {"zh": "既有构件表状态", "en": "Member Schedule Status"},
    "member_evidence.survey_available": {"zh": "现场调查状态", "en": "Site Survey Status"},
    "connection_evidence.connection_detail_status": {"zh": "连接做法资料状态", "en": "Connection Detail Status"},
    "connection_evidence.roof_vendor_data_status": {"zh": "屋面厂家资料状态", "en": "Roof Vendor Data Status"},
    "connection_evidence.available_verification_path": {"zh": "复核路径", "en": "Verification Path"},
    "roof_system.panel_thickness_mm": {"zh": "屋面板厚", "en": "Roof Panel Thickness"},
    "roof_system.rib_height_mm": {"zh": "屋面板波高", "en": "Roof Rib Height"},
    "pv_load.added_dead_load_kpa": {"zh": "新增屋面恒载", "en": "Added Roof Dead Load"},
    "secondary_members.purlin_spacing_m": {"zh": "檩条间距", "en": "Purlin Spacing"},
    "geometry.eave_height_m": {"zh": "檐口高度", "en": "Eave Height"},
    "portal_frame.controlling_path": {"zh": "当前控制路径", "en": "Current Controlling Path"},
    "portal_frame.purlin_strength_ratio": {"zh": "檩条强度比", "en": "Purlin Strength Ratio"},
    "portal_frame.purlin_deflection_ratio": {"zh": "檩条挠度比", "en": "Purlin Deflection Ratio"},
    "portal_frame.primary_frame_rafter_screening_ratio": {"zh": "主门架梁筛查比值", "en": "Primary Frame Rafter Screening Ratio"},
    "portal_frame.primary_frame_column_screening_ratio": {"zh": "主门架柱筛查比值", "en": "Primary Frame Column Screening Ratio"},
    "portal_frame.primary_frame_screening_ratio": {"zh": "主门架筛查比值", "en": "Primary Frame Screening Ratio"},
}

BASIS_TERM_TRANSLATIONS: Dict[str, Dict[Language, str]] = {
    "incomplete steel member evidence": {"zh": "钢构件证据不完整", "en": "incomplete steel member evidence"},
    "connection review required": {"zh": "需要开展连接复核", "en": "connection review required"},
    "steel member review under AISC context": {"zh": "AISC 体系下钢构件复核", "en": "steel member review under AISC context"},
    "connection review under AISC context": {"zh": "AISC 体系下连接复核", "en": "connection review under AISC context"},
    "steel member review under Eurocode context": {"zh": "Eurocode 体系下钢构件复核", "en": "steel member review under Eurocode context"},
    "connection review under Eurocode context": {"zh": "Eurocode 体系下连接复核", "en": "connection review under Eurocode context"},
    "screening-stage portal-frame purlin check": {"zh": "筛查阶段门式刚架檩条验算", "en": "screening-stage portal-frame purlin check"},
    "roof photovoltaic load increase requires screening": {"zh": "屋面光伏增载需要先做筛查", "en": "roof photovoltaic load increase requires screening"},
    "screening-stage portal-frame purlin check under AISC context": {"zh": "AISC 体系下筛查阶段门式刚架檩条验算", "en": "screening-stage portal-frame purlin check under AISC context"},
    "screening-stage portal-frame purlin check under Eurocode context": {"zh": "Eurocode 体系下筛查阶段门式刚架檩条验算", "en": "screening-stage portal-frame purlin check under Eurocode context"},
    "Continue steel member and connection review": {"zh": "继续开展钢构件与连接复核", "en": "Continue steel member and connection review"},
    "Verify local roof attachment detailing": {"zh": "核对局部屋面连接构造", "en": "Verify local roof attachment detailing"},
    "Continue member stability review under AISC 360": {"zh": "按 AISC 360 继续开展构件稳定复核", "en": "Continue member stability review under AISC 360"},
    "Continue steel design and connection review": {"zh": "继续开展钢构件设计与连接复核", "en": "Continue steel design and connection review"},
    "Continue steel member review under Eurocode 3": {"zh": "按 Eurocode 3 继续开展钢构件复核", "en": "Continue steel member review under Eurocode 3"},
    "Continue local execution and connection review": {"zh": "继续开展局部构造与连接复核", "en": "Continue local execution and connection review"},
    "Escalate to formal review if purlin utilization, deflection, or support reactions exceed screening thresholds": {"zh": "当檩条利用率、挠度或支座反力超过筛查阈值时，应升级为正式复核", "en": "Escalate to formal review if purlin utilization, deflection, or support reactions exceed screening thresholds"},
    "Perform deeper review for portal-frame roof load path and local connection effects": {"zh": "进一步复核门架屋面荷载路径及局部连接效应", "en": "Perform deeper review for portal-frame roof load path and local connection effects"},
    "Escalate to formal review if purlin demand, drift, or connection effects exceed screening thresholds": {"zh": "当檩条需求、变形或连接效应超过筛查阈值时，应升级为正式复核", "en": "Escalate to formal review if purlin demand, drift, or connection effects exceed screening thresholds"},
    "Perform deeper review for portal-frame load combinations and member stability": {"zh": "进一步复核门架荷载组合与构件稳定", "en": "Perform deeper review for portal-frame load combinations and member stability"},
    "Escalate to formal review if purlin resistance, serviceability, or support reactions exceed screening thresholds": {"zh": "当檩条承载力、正常使用或支座反力超过筛查阈值时，应升级为正式复核", "en": "Escalate to formal review if purlin resistance, serviceability, or support reactions exceed screening thresholds"},
    "portal frame geometry": {"zh": "门式刚架几何参数", "en": "portal frame geometry"},
    "purlin spacing and section data": {"zh": "檩条间距与截面资料", "en": "purlin spacing and section data"},
    "roof photovoltaic load summary": {"zh": "屋面光伏荷载摘要", "en": "roof photovoltaic load summary"},
    "structural drawings": {"zh": "结构图纸", "en": "structural drawings"},
    "member schedule": {"zh": "构件表", "en": "member schedule"},
    "connection details": {"zh": "连接节点资料", "en": "connection details"},
}

BASIS_TEXT_TRANSLATIONS: Dict[str, Dict[Language, str]] = {
    "incomplete steel member evidence": {"zh": "钢构件证据不完整", "en": "incomplete steel member evidence"},
    "connection review required": {"zh": "需要开展连接复核", "en": "connection review required"},
    "Continue steel member and connection review": {"zh": "继续开展钢构件与连接复核", "en": "Continue steel member and connection review"},
    "Verify local roof attachment detailing": {"zh": "核对局部屋面连接做法", "en": "Verify local roof attachment detailing"},
    "structural drawings": {"zh": "结构图纸", "en": "structural drawings"},
    "member schedule": {"zh": "构件表", "en": "member schedule"},
    "connection details": {"zh": "连接节点资料", "en": "connection details"},
    "steel member review under AISC context": {"zh": "AISC 体系下需开展钢构件复核", "en": "steel member review under AISC context"},
    "connection review under AISC context": {"zh": "AISC 体系下需开展连接复核", "en": "connection review under AISC context"},
    "Continue member stability review under AISC 360": {"zh": "继续按 AISC 360 开展构件稳定复核", "en": "Continue member stability review under AISC 360"},
    "Continue steel design and connection review": {"zh": "继续开展钢结构设计与连接复核", "en": "Continue steel design and connection review"},
    "steel member review under Eurocode context": {"zh": "Eurocode 体系下需开展钢构件复核", "en": "steel member review under Eurocode context"},
    "connection review under Eurocode context": {"zh": "Eurocode 体系下需开展连接复核", "en": "connection review under Eurocode context"},
    "Continue steel member review under Eurocode 3": {"zh": "继续按 Eurocode 3 开展钢构件复核", "en": "Continue steel member review under Eurocode 3"},
    "Continue local execution and connection review": {"zh": "继续开展局部构造与连接复核", "en": "Continue local execution and connection review"},
    "screening-stage portal-frame purlin check": {"zh": "筛查阶段门式刚架檩条检查", "en": "screening-stage portal-frame purlin check"},
    "roof photovoltaic load increase requires screening": {"zh": "屋面光伏增载需要进行筛查", "en": "roof photovoltaic load increase requires screening"},
    "Escalate to formal review if purlin utilization, deflection, or support reactions exceed screening thresholds": {
        "zh": "若檩条利用率、挠度或支反力超出筛查阈值，应升级至正式复核",
        "en": "Escalate to formal review if purlin utilization, deflection, or support reactions exceed screening thresholds",
    },
    "Perform deeper review for portal-frame roof load path and local connection effects": {
        "zh": "进一步复核门式刚架屋面传力路径及局部连接效应",
        "en": "Perform deeper review for portal-frame roof load path and local connection effects",
    },
    "portal frame geometry": {"zh": "门式刚架几何参数", "en": "portal frame geometry"},
    "purlin spacing and section data": {"zh": "檩条间距与截面资料", "en": "purlin spacing and section data"},
    "roof photovoltaic load summary": {"zh": "屋面光伏荷载汇总", "en": "roof photovoltaic load summary"},
    "screening-stage portal-frame purlin check under AISC context": {"zh": "AISC 体系下筛查阶段门式刚架檩条检查", "en": "screening-stage portal-frame purlin check under AISC context"},
    "Escalate to formal review if purlin demand, drift, or connection effects exceed screening thresholds": {
        "zh": "若檩条需求、变形或连接效应超出筛查阈值，应升级至正式复核",
        "en": "Escalate to formal review if purlin demand, drift, or connection effects exceed screening thresholds",
    },
    "Perform deeper review for portal-frame load combinations and member stability": {
        "zh": "进一步复核门式刚架荷载组合与构件稳定",
        "en": "Perform deeper review for portal-frame load combinations and member stability",
    },
    "screening-stage portal-frame purlin check under Eurocode context": {"zh": "Eurocode 体系下筛查阶段门式刚架檩条检查", "en": "screening-stage portal-frame purlin check under Eurocode context"},
    "Escalate to formal review if purlin resistance, serviceability, or support reactions exceed screening thresholds": {
        "zh": "若檩条抗力、正常使用或支反力超出筛查阈值，应升级至正式复核",
        "en": "Escalate to formal review if purlin resistance, serviceability, or support reactions exceed screening thresholds",
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


def localize_input_path(language: Language, path: str) -> str:
    return INPUT_PATH_TRANSLATIONS.get(path, {"zh": path, "en": path})[language]


def localize_trace_value(language: Language, input_path: str, value: str) -> str:
    if input_path == "portal_frame.controlling_path":
        mapping = {
            "purlin_strength": {"zh": "檩条强度控制", "en": "Purlin Strength Governing"},
            "purlin_deflection": {"zh": "檩条挠度控制", "en": "Purlin Deflection Governing"},
            "primary_frame_rafter": {"zh": "主门架梁控制", "en": "Primary Frame Rafter Governing"},
            "primary_frame_column": {"zh": "主门架柱控制", "en": "Primary Frame Column Governing"},
        }
        return mapping.get(value, {"zh": value, "en": value})[language]
    return value


def localize_basis_term(language: Language, value: str) -> str:
    return BASIS_TERM_TRANSLATIONS.get(value, {"zh": value, "en": value})[language]


def localize_basis_text(language: Language, text: str) -> str:
    return BASIS_TEXT_TRANSLATIONS.get(text, {"zh": text, "en": text})[language]


def localize_calc_unit(language: Language, unit: str) -> str:
    unit_map = {
        "kPa": {"zh": "kPa", "en": "kPa"},
        "kN/m": {"zh": "kN/m", "en": "kN/m"},
        "kN*m": {"zh": "kN·m", "en": "kN·m"},
        "dimensionless": {"zh": "无量纲", "en": "dimensionless"},
        "score": {"zh": "分", "en": "score"},
    }
    return unit_map.get(unit, {"zh": unit, "en": unit})[language]


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
