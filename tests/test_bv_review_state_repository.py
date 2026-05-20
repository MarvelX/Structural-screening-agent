from pathlib import Path

import pytest

from structural_screening_agent.bv_review import BVReviewIntake, ProjectReviewState
from structural_screening_agent.bv_review.project_state import (
    DocumentVersion,
    EngineerApproval,
    ExtractedField,
    RFIItem,
)
from structural_screening_agent.bv_review.state_repository import JsonProjectReviewStateRepository


def _sample_state() -> ProjectReviewState:
    intake = BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents={"structural_drawings": "available"},
    )
    return ProjectReviewState(
        project_id="pv-ground-001",
        intake=intake,
        document_versions=[
            DocumentVersion(
                document_id="structural-drawing-a101",
                document_type="structural_drawings",
                revision="A",
                source_name="S-101 Mounting Layout.pdf",
                status="available",
            )
        ],
        extracted_fields=[
            ExtractedField(
                field_id="tilt",
                name="Tilt angle",
                candidate_value="25",
                unit="deg",
                source_document_id="structural-drawing-a101",
                page_or_section="Sheet S-101, mounting layout note 3",
                quote="Tilt angle: 25 deg",
                confidence=0.95,
                is_confirmed=True,
                confirmed_value="25",
                confirmed_unit="deg",
                include_in_calculation=True,
            )
        ],
        approvals=[
            EngineerApproval(
                approval_id="approval-001",
                target_type="gate",
                target_id="calculation",
                status="approved",
                reviewer="Engineer A",
                locked=True,
            )
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-001",
                question="Please provide the geotechnical report.",
                responsible_party="client",
                trigger_basis="Foundation review requires geotechnical inputs.",
                required_document_or_field="geotechnical_report",
                status="open",
            )
        ],
    )


def test_json_state_repository_round_trips_project_review_state(tmp_path: Path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    state = _sample_state()

    repository.save(state)
    loaded = repository.load("pv-ground-001")

    assert loaded.project_id == state.project_id
    assert loaded.intake.project_name == "Ground PV design review"
    assert loaded.document_versions[0].document_id == "structural-drawing-a101"
    assert loaded.extracted_fields[0].source_document_id == "structural-drawing-a101"
    assert loaded.approvals[0].locked is True
    assert loaded.rfi_items[0].status == "open"
    assert repository.list_project_ids() == ["pv-ground-001"]


def test_json_state_repository_raises_for_missing_project(tmp_path: Path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)

    with pytest.raises(FileNotFoundError):
        repository.load("missing-project")


def test_json_state_repository_rejects_project_ids_that_escape_root(tmp_path: Path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    state = _sample_state().model_copy(update={"project_id": "../escape"})

    with pytest.raises(ValueError):
        repository.save(state)

    with pytest.raises(ValueError):
        repository.load("../escape")

    with pytest.raises(ValueError):
        repository.load("nested/project")

    assert not (tmp_path.parent / "escape.json").exists()
