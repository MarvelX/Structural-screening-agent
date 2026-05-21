from pathlib import Path

import pytest

from structural_screening_agent.bv_review import BVReviewIntake, ProjectReviewState
from structural_screening_agent.bv_review.models import BVRiskItem
from structural_screening_agent.bv_review.project_state import (
    AgentWorkflowEvent,
    CalculationRun,
    DocumentVersion,
    EngineerApproval,
    ExtractedField,
    RFIItem,
    ReportRevision,
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
        agent_events=[
            AgentWorkflowEvent(
                event_id="agent-event-001",
                agent_role="document_intake",
                target_phase="document_check",
                status="applied",
                output_schema_version="phase2-agent-contracts-v1",
                requires_engineer_review=True,
                summary_counts={"document_versions": 1, "extracted_fields": 1},
            )
        ],
        report_revisions=[
            ReportRevision(
                revision_id="report-rev-001",
                source_phase="report_draft",
                report_title="BV 光伏结构设计审查报告",
                section_count=9,
                rfi_count=1,
                created_by="Engineer A",
            )
        ],
        risks=[
            BVRiskItem(
                risk_id="foundation-bearing-capacity-open",
                title="Foundation bearing capacity evidence remains open",
                severity="critical",
                trigger_basis="Missing geotechnical confirmation.",
                impact_scope="Foundation review",
                recommendation="Close after engineer review of geotechnical evidence.",
                blocks_report_issue=True,
                category="nonconformity",
            ),
            BVRiskItem(
                risk_id="layout-optimization-closed",
                title="Layout optimization comment closed",
                severity="medium",
                trigger_basis="Engineer accepted residual comment.",
                impact_scope="PV layout review",
                recommendation="Keep residual comment in workpaper.",
                blocks_report_issue=True,
                category="optimization",
                status="closed",
                closeout_note="Closed after engineer review.",
            ),
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
    assert loaded.agent_events[0].agent_role == "document_intake"
    assert loaded.agent_events[0].summary_counts["document_versions"] == 1
    assert loaded.report_revisions[0].revision_id == "report-rev-001"
    assert repository.list_project_ids() == ["pv-ground-001"]


def test_json_state_repository_lists_project_summaries(tmp_path: Path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    first_state = _sample_state().model_copy(
        update={
            "current_phase": "document_check",
            "phase_statuses": {
                **_sample_state().phase_statuses,
                "document_check": "waiting_for_engineer",
            },
        }
    )
    second_state = _sample_state().model_copy(
        update={
            "project_id": "pv-ground-002",
            "current_phase": "report_draft",
            "agent_events": [],
            "rfi_items": [],
            "risks": [],
            "report_revisions": [],
        }
    )
    repository.save(first_state)
    repository.save(second_state)

    summaries = repository.list_project_summaries()

    assert [item.project_id for item in summaries] == ["pv-ground-001", "pv-ground-002"]
    assert summaries[0].project_name == "Ground PV design review"
    assert summaries[0].current_phase == "document_check"
    assert summaries[0].agent_event_count == 1
    assert summaries[0].pending_agent_review_count == 1
    assert summaries[0].active_rfi_count == 1
    assert summaries[0].open_finding_count == 1
    assert summaries[0].report_revision_count == 1
    assert summaries[0].timeline_event_count == 5
    assert summaries[0].locked_gate_count == 1
    assert summaries[0].management_action_count == 3
    assert summaries[0].blocking_action_count == 3
    assert summaries[0].workflow_status == "blocked"
    assert summaries[0].next_action_ids == [
        "rfi-client-response-rfi-001",
        "finding-closeout-foundation-bearing-capacity-open",
        "agent-review-agent-event-001",
    ]
    assert summaries[0].next_action_categories == [
        "rfi_client_response",
        "finding_closeout",
        "agent_engineer_review",
    ]
    assert summaries[1].current_phase == "report_draft"
    assert summaries[1].agent_event_count == 0
    assert summaries[1].pending_agent_review_count == 0
    assert summaries[1].active_rfi_count == 0
    assert summaries[1].open_finding_count == 0
    assert summaries[1].report_revision_count == 0
    assert summaries[1].timeline_event_count == 1
    assert summaries[1].locked_gate_count == 1
    assert summaries[1].management_action_count == 0
    assert summaries[1].blocking_action_count == 0
    assert summaries[1].workflow_status == "ready"
    assert summaries[1].next_action_ids == []
    assert summaries[1].next_action_categories == []


def test_json_state_repository_inventory_reports_invalid_project_files(
    tmp_path: Path,
) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    repository.save(_sample_state())
    (tmp_path / "broken-project.json").write_text("{not-json", encoding="utf-8")

    inventory = repository.list_project_inventory()

    assert [item.project_id for item in inventory.summaries] == ["pv-ground-001"]
    assert inventory.invalid_project_ids == ["broken-project"]
    assert inventory.invalid_project_count == 1


def test_json_state_repository_round_trips_incremental_recheck_rfi_state(tmp_path: Path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    state = _sample_state().model_copy(
        update={
            "document_versions": [
                DocumentVersion(
                    document_id="foundation-drawing-f201-rev-b",
                    document_type="structural_drawings",
                    revision="B",
                    source_name="F-201 Foundation Schedule Rev B.pdf",
                    status="available",
                    supersedes="foundation-drawing-f201-rev-a",
                )
            ],
            "rfi_items": [
                RFIItem(
                    rfi_id="rfi-pile_length_m",
                    question="Please confirm updated input for Pile Length M.",
                    responsible_party="client",
                    trigger_basis="Field pile_length_m changed from '3.5' to '4.0'.",
                    required_document_or_field="pile_length_m",
                    status="reopened",
                    reopen_review_items=["calculation-recheck-pile_length_m"],
                    triggers_incremental_recheck=True,
                )
            ],
        }
    )

    repository.save(state)
    loaded = repository.load("pv-ground-001")

    assert loaded.document_versions[0].supersedes == "foundation-drawing-f201-rev-a"
    assert loaded.rfi_items[0].status == "reopened"
    assert loaded.rfi_items[0].triggers_incremental_recheck is True
    assert loaded.rfi_items[0].reopen_review_items == ["calculation-recheck-pile_length_m"]


def test_json_state_repository_loads_closed_rfi_recheck_plan_from_saved_state(tmp_path: Path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    state = _sample_state().model_copy(
        update={
            "calculation_runs": [
                CalculationRun(
                    run_id="foundation-run-001",
                    engine_name="foundation",
                    engine_version="phase1-human-gate",
                    input_field_ids=["pile_length_m"],
                    input_locked=True,
                    status="completed",
                )
            ],
            "rfi_items": [
                RFIItem(
                    rfi_id="rfi-pile_length_m",
                    question="Please confirm updated input for Pile Length M.",
                    responsible_party="client",
                    trigger_basis="Field pile_length_m changed from '3.5' to '4.0'.",
                    required_document_or_field="pile_length_m",
                    status="closed",
                    client_response="Confirmed Rev B pile length is 4.0 m.",
                    reopen_review_items=["calculation-recheck-pile_length_m"],
                    completed_recheck_items=["calculation-recheck-pile_length_m"],
                    triggers_incremental_recheck=True,
                )
            ],
        }
    )

    repository.save(state)
    plan = repository.load_closed_rfi_recheck_plan("pv-ground-001")

    assert [item.rfi_id for item in plan.rfi_items] == ["rfi-pile_length_m"]
    assert plan.affected_items[0].item_id == "calculation-recheck-pile_length_m"
    assert plan.affected_items[0].field_ids == ["pile_length_m"]
    assert plan.affected_items[0].calculation_run_ids == ["foundation-run-001"]


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
