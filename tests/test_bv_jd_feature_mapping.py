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


def test_bv_jd_feature_mapping_and_roadmap_include_foundation_evidence_rfi_closure() -> None:
    root = project_root()
    mapping = (root / "docs" / "bv-jd-feature-mapping.md").read_text()
    roadmap = (root / "docs" / "bv-pv-design-review-workbench-roadmap.md").read_text()

    for phrase in [
        "Foundation Review Evidence Path",
        "基础证据路径",
        "草稿 RFI",
        "foundation_evidence_blocked_geotechnical_parameters",
    ]:
        assert phrase in mapping
        assert phrase in roadmap


def test_bv_roadmap_reflects_current_traceability_and_clean_workspace_baseline() -> None:
    roadmap = (
        project_root() / "docs" / "bv-pv-design-review-workbench-roadmap.md"
    ).read_text()

    for completed_phrase in [
        "JD feature mapping documentation",
        "portfolio narrative page",
        "BV UI helper smoke tests",
        "BV section renderer extraction",
        "BV label formatter extraction",
        "BV evidence table text extraction",
        "BV gate panel text extraction",
        "BV report gate status renderer extraction",
        "finding lifecycle summary",
        "responsible-party status",
        "responsible-party SLA / overdue tracking",
        "report-facing responsible-party SLA status",
        "blocked-calculation RFI issue timestamps",
        "incremental-recheck RFI timestamps",
        "agent-review event timestamps",
        "project inventory SLA summary",
        "service scope recommendations",
        "report revision history with traceable revision status",
        "report reissue gate",
        "clarification history view",
        "project review dashboard",
        "default Pytest duplicate-copy exclusion",
        "workspace cleanliness policy",
        "UI / report evidence matrix alignment",
    ]:
        assert completed_phrase in roadmap

    for stale_next_step in [
        "Add `docs/bv-jd-feature-mapping.md`",
        "Add a portfolio narrative page under `docs/showcase/`",
        "Add a small regression test or smoke test that imports the BV UI helper",
    ]:
        assert stale_next_step not in roadmap
