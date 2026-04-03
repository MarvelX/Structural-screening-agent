from typing import List

from pydantic import BaseModel, Field

from structural_screening_agent.localization import Language


class PhotoAssistTarget(BaseModel):
    title: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    candidate_backfill_fields: List[str] = Field(default_factory=list)


class PhotoAssistInterface(BaseModel):
    intro: str = Field(min_length=1)
    targets: List[PhotoAssistTarget] = Field(default_factory=list)
    boundary_notes: List[str] = Field(default_factory=list)


def build_photo_assist_interface(language: Language = "zh") -> PhotoAssistInterface:
    if language == "zh":
        return PhotoAssistInterface(
            intro=(
                "可上传现场拍照资料作为后续辅助识别入口，用于判断屋面连接、檩条支承、梁柱现状等敏感点。"
                "当前版本只定义入口和回填边界，不直接自动改写项目输入。"
            ),
            targets=[
                PhotoAssistTarget(
                    title="锁边 / 夹具 / 节点照片",
                    detail="用于辅助判断锁边形式、夹具路径和连接做法是否具备可辩护性。",
                    candidate_backfill_fields=[
                        "roof_panel_type",
                        "roof_panel_thickness_mm",
                        "roof_rib_height_mm",
                        "roof_attachment_preference",
                        "connection_detail_status",
                        "roof_vendor_data_status",
                    ],
                ),
                PhotoAssistTarget(
                    title="檩条与支承照片",
                    detail="用于辅助识别檩条形式、支承关系和局部传力路径，支持后续檩条筛查补证。",
                    candidate_backfill_fields=[
                        "purlin_type",
                        "purlin_spacing_m",
                        "existing_member_schedule_status",
                    ],
                ),
                PhotoAssistTarget(
                    title="门架梁柱与腐蚀照片",
                    detail="用于辅助识别梁柱截面现状、腐蚀等级和现场调查范围，支持主门架初筛补证。",
                    candidate_backfill_fields=[
                        "rafter_section",
                        "column_section",
                        "corrosion_condition",
                        "survey_available",
                    ],
                ),
            ],
            boundary_notes=[
                "当前版本仅保留入口，不自动回填项目输入。",
                "后续识别结果只应作为候选字段，仍需人工确认后才能进入正式计算链。",
                "拍照辅助识别不能替代原结构图纸、现场复核和顾问正式判断。",
            ],
        )

    return PhotoAssistInterface(
        intro=(
            "Upload field photos as a future-assisted recognition entry for roof attachment, purlin support, and portal-frame condition."
            " This version defines the intake boundary only and does not auto-write back into project inputs."
        ),
        targets=[
            PhotoAssistTarget(
                title="Seam / Clamp / Connection Photos",
                detail="Supports future inference of seam type, clamp path, and connection defensibility.",
                candidate_backfill_fields=[
                    "roof_panel_type",
                    "roof_panel_thickness_mm",
                    "roof_rib_height_mm",
                    "roof_attachment_preference",
                    "connection_detail_status",
                    "roof_vendor_data_status",
                ],
            ),
            PhotoAssistTarget(
                title="Purlin and Support Photos",
                detail="Supports future inference of purlin type, support relationship, and local load path.",
                candidate_backfill_fields=[
                    "purlin_type",
                    "purlin_spacing_m",
                    "existing_member_schedule_status",
                ],
            ),
            PhotoAssistTarget(
                title="Rafter / Column / Corrosion Photos",
                detail="Supports future inference of member condition, corrosion severity, and survey coverage.",
                candidate_backfill_fields=[
                    "rafter_section",
                    "column_section",
                    "corrosion_condition",
                    "survey_available",
                ],
            ),
        ],
        boundary_notes=[
            "This version keeps the entry only and does not auto-write back into project inputs.",
            "Any future recognition output should stay as candidate fields until manually confirmed.",
            "Photo-assisted recognition does not replace original drawings, site verification, or formal engineering review.",
        ],
    )
