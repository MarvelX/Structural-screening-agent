from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_bv_jd_feature_mapping_doc_exists_with_required_columns() -> None:
    doc_path = project_root() / "docs" / "bv-jd-feature-mapping.md"

    assert doc_path.exists()
    content = doc_path.read_text()

    assert "# BV JD Feature Mapping" in content
    for heading in ["JD 条款", "产品模块", "当前覆盖度", "下一步补强项"]:
        assert heading in content


def test_bv_jd_feature_mapping_covers_major_responsibilities() -> None:
    content = (project_root() / "docs" / "bv-jd-feature-mapping.md").read_text()

    required_phrases = [
        "土建、钢结构、支架及基础",
        "公司质量体系",
        "GB / IEC / AS/NZS / Eurocode",
        "合同要求、法规、技术标准和项目规范",
        "设计审核计划、检查与测试计划",
        "设计审查报告",
        "客户、设计院及承包商",
        "潜在风险、错误、遗漏及不经济之处",
        "结构荷载计算、连接节点设计、地基承载力计算",
        "独立技术判断",
        "BV 服务与解决方案",
        "设计项目管理",
    ]

    for phrase in required_phrases:
        assert phrase in content


def test_bv_jd_feature_mapping_states_current_boundaries() -> None:
    content = (project_root() / "docs" / "bv-jd-feature-mapping.md").read_text()

    for phrase in [
        "screening-level / review-support",
        "不替代正式设计",
        "不替代 BV 官方签发",
        "不做完整 CAD 自动审图",
        "不做完整有限元分析",
    ]:
        assert phrase in content
