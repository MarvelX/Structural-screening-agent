import zipfile
from io import BytesIO

from structural_screening_agent.app_state import evaluate_case
from structural_screening_agent.bv_review.models import BVReviewIntake
from structural_screening_agent.bv_review.report import build_bv_report_preview
from structural_screening_agent.bv_review.workflow import evaluate_bv_review
from structural_screening_agent.demo_data import main_demo_case
from structural_screening_agent.report_export import build_docx_report_bytes, build_pdf_report_bytes
from structural_screening_agent.report_generator import build_report_preview


def test_report_export_generates_docx_and_pdf_bytes() -> None:
    evaluation = evaluate_case(main_demo_case().model_dump(), language="zh")
    preview = build_report_preview(
        evaluation["intake"],
        evaluation["result"],
        evaluation["explanation"],
        language="zh",
        kernel_outcome=evaluation["kernel_outcome"],
    )

    docx_bytes = build_docx_report_bytes(preview)
    pdf_bytes = build_pdf_report_bytes(preview)

    assert docx_bytes[:2] == b"PK"
    assert pdf_bytes[:4] == b"%PDF"
    assert len(docx_bytes) > 5000
    assert len(pdf_bytes) > 2000

    with zipfile.ZipFile(BytesIO(docx_bytes)) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
        footer_parts = [
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.startswith("word/footer")
        ]
        footer_xml = "\n".join(footer_parts)

    assert "门式刚架屋面光伏增载初筛复核摘要" in document_xml
    assert "简化计算结果" in document_xml
    assert "当前控制因素" in document_xml
    assert "初步结构结论" in document_xml
    assert "规范体系: 国标 GB" in document_xml
    assert "建筑类型: 既有仓库" in document_xml
    assert "建筑跨度" in document_xml
    assert "柱距" in document_xml
    assert "门式刚架屋面光伏增载初筛复核摘要" in footer_xml


def _sample_bv_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Hebei rooftop PV design review",
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


def test_report_export_generates_docx_and_pdf_bytes_for_bv_preview() -> None:
    intake = _sample_bv_intake()
    result = evaluate_bv_review(intake)
    preview = build_bv_report_preview(intake, result)

    docx_bytes = build_docx_report_bytes(preview)
    pdf_bytes = build_pdf_report_bytes(preview)

    assert docx_bytes[:2] == b"PK"
    assert pdf_bytes[:4] == b"%PDF"
    assert len(docx_bytes) > 3000
    assert len(pdf_bytes) > 1500

    with zipfile.ZipFile(BytesIO(docx_bytes)) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
        footer_parts = [
            archive.read(name).decode("utf-8", errors="ignore")
            for name in archive.namelist()
            if name.startswith("word/footer")
        ]
        footer_xml = "\n".join(footer_parts)

    assert "BV 光伏结构设计审查报告" in document_xml
    assert "项目与审核范围" in document_xml
    assert "审核依据" in document_xml
    assert "审核边界声明" in document_xml
    assert "BV 光伏结构设计审查报告" in footer_xml
