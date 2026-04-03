import pytest

from pydantic import ValidationError

from structural_screening_agent.core import basis_registry as basis_registry_module
from structural_screening_agent.core.basis_registry import load_basis_registry


def test_basis_registry_loads_named_references_by_id() -> None:
    registry = load_basis_registry()

    reference = registry.get("gb_50017_general")

    assert reference is not None
    assert reference.basis_id == "gb_50017_general"
    assert "GB 50017" in reference.title_en
    assert reference.source_type == "standard"
    assert "gb" in reference.applicable_standards
    assert any("steel member" in item.lower() for item in reference.review_requirements)
    assert any("drawings" in item.lower() for item in reference.evidence_requirements)
    assert reference.trigger_conditions


def test_basis_registry_rejects_unknown_reference_ids() -> None:
    registry = load_basis_registry()

    assert registry.get("missing_basis") is None


def test_basis_registry_requires_structured_metadata_for_each_reference() -> None:
    registry = load_basis_registry()

    assert registry.references
    for reference in registry.references.values():
        assert reference.applicable_standards
        assert reference.trigger_conditions
        assert reference.review_requirements
        assert reference.evidence_requirements


def test_basis_registry_contains_portal_frame_screening_references() -> None:
    registry = load_basis_registry()

    assert registry.get("gb_portal_frame_purlin_screening") is not None
    assert registry.get("aisc_portal_frame_purlin_screening") is not None
    assert registry.get("eurocode_portal_frame_purlin_screening") is not None


def test_portal_frame_basis_reference_carries_method_and_boundary_text() -> None:
    registry = load_basis_registry()
    reference = registry.get("gb_portal_frame_purlin_screening")

    assert reference is not None
    assert "purlin" in reference.title_en.lower()
    assert any("screening" in item.lower() for item in reference.trigger_conditions)
    assert any("formal review" in item.lower() for item in reference.review_requirements)


def test_basis_registry_rejects_missing_required_metadata(tmp_path, monkeypatch) -> None:
    registry_path = tmp_path / "basis_registry.yaml"
    registry_path.write_text(
        "\n".join(
            [
                "- basis_id: broken_basis",
                "  source_type: standard",
                "  title_en: Broken Basis",
                "  title_zh: 损坏依据",
                "  citation_en: Broken citation",
                "  citation_zh: 损坏引文",
            ]
        )
    )

    monkeypatch.setattr(basis_registry_module, "_registry_path", lambda: registry_path)

    with pytest.raises(ValidationError):
        load_basis_registry()
