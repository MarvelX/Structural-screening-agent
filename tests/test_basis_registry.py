from structural_screening_agent.core.basis_registry import load_basis_registry


def test_basis_registry_loads_named_references_by_id() -> None:
    registry = load_basis_registry()

    reference = registry.get("gb_50017_general")

    assert reference is not None
    assert reference.basis_id == "gb_50017_general"
    assert "GB 50017" in reference.title_en
    assert reference.source_type == "standard"


def test_basis_registry_rejects_unknown_reference_ids() -> None:
    registry = load_basis_registry()

    assert registry.get("missing_basis") is None
