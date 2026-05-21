from structural_screening_agent.bv_review import (
    BVReviewIntake,
    PersistedWorkflowRunResult,
    PersistedWorkflowRunSummary,
    ProjectReviewState,
    run_persisted_local_agent_workflow_with_summary,
)
from structural_screening_agent.bv_review.human_gate import build_report_draft_gate_result
from structural_screening_agent.bv_review.persisted_workflow_session import (
    apply_persisted_authorized_agent_response,
    clear_persisted_workflow_session,
    get_active_persisted_project_id,
    get_active_persisted_workflow_state,
    get_active_persisted_workflow_summary,
    close_persisted_rfi_after_engineer_review,
    issue_persisted_blocked_calculation_draft_rfi,
    record_persisted_finding_closeout_decision,
    record_persisted_agent_review_decision,
    record_persisted_report_revision,
    record_persisted_rfi_client_response,
    run_persisted_rfi_incremental_calculation_recheck,
    store_persisted_workflow_state,
    store_persisted_workflow_result,
)
from structural_screening_agent.bv_review.agent_prompting import (
    AgentResponseApplicationAuthorization,
    build_agent_prompt_package,
    build_agent_response_application_plan,
    build_agent_response_engineer_handoff,
    build_agent_response_sandbox_result,
    build_sample_agent_response_json,
)
from structural_screening_agent.bv_review.project_state import (
    CalculationRun,
    DocumentVersion,
    EngineerApproval,
    ExtractedField,
    RFIItem,
)
from structural_screening_agent.bv_review.models import BVRiskItem
from structural_screening_agent.bv_review.report import build_bv_report_preview
from structural_screening_agent.bv_review.state_repository import (
    JsonProjectReviewStateRepository,
)
from structural_screening_agent.bv_review.workflow import evaluate_bv_review


def test_persisted_workflow_session_keeps_resumed_state_for_matching_project() -> None:
    session_state: dict[str, object] = {}
    result = PersistedWorkflowRunResult(
        state=ProjectReviewState(
            project_id="pv-001",
            intake=_sample_intake(),
            current_phase="engineer_data_lock",
        ),
        summary=PersistedWorkflowRunSummary(
            project_id="pv-001",
            start_phase="intake",
            final_phase="engineer_data_lock",
            applied_agent_event_ids=["agent-event-001"],
            applied_agent_roles=["document_intake"],
            artifact_counts={"agent_events": 1},
            saved=True,
        ),
    )

    store_persisted_workflow_result(session_state, result)

    active_state = get_active_persisted_workflow_state(session_state, "pv-001")
    active_summary = get_active_persisted_workflow_summary(session_state, "pv-001")
    assert get_active_persisted_project_id(session_state) == "pv-001"
    assert active_state is not None
    assert active_state.current_phase == "engineer_data_lock"
    assert active_summary is not None
    assert active_summary.final_phase == "engineer_data_lock"
    assert get_active_persisted_workflow_state(session_state, "pv-002") is None
    assert get_active_persisted_workflow_summary(session_state, "pv-002") is None


def test_store_persisted_workflow_state_replaces_active_state_without_losing_project_anchor() -> None:
    session_state: dict[str, object] = {}
    result = PersistedWorkflowRunResult(
        state=ProjectReviewState(project_id="pv-001", intake=_sample_intake()),
        summary=PersistedWorkflowRunSummary(
            project_id="pv-001",
            start_phase="intake",
            final_phase="intake",
            applied_agent_event_ids=["agent-event-001"],
            applied_agent_roles=["document_intake"],
            artifact_counts={"document_versions": 0},
            saved=True,
        ),
    )
    store_persisted_workflow_result(session_state, result)

    updated_state = ProjectReviewState(
        project_id="pv-001",
        intake=_sample_intake(),
        current_phase="report_draft",
        document_versions=[
            DocumentVersion(
                document_id="structural-drawing-s101",
                document_type="structural_drawing",
                revision="A",
                source_name="S-101 Rev A.pdf",
                status="available",
            )
        ],
    )
    store_persisted_workflow_state(session_state, updated_state)

    active_summary = get_active_persisted_workflow_summary(session_state, "pv-001")

    assert get_active_persisted_project_id(session_state) == "pv-001"
    assert get_active_persisted_workflow_state(session_state, "pv-001") == updated_state
    assert active_summary is not None
    assert active_summary.start_phase == "intake"
    assert active_summary.final_phase == "report_draft"
    assert active_summary.applied_agent_event_ids == ["agent-event-001"]
    assert active_summary.applied_agent_roles == ["document_intake"]
    assert active_summary.artifact_counts["document_versions"] == 1
    assert active_summary.saved is True


def test_clear_persisted_workflow_session_removes_resumed_state_and_summary() -> None:
    session_state: dict[str, object] = {}
    result = PersistedWorkflowRunResult(
        state=ProjectReviewState(project_id="pv-001", intake=_sample_intake()),
        summary=PersistedWorkflowRunSummary(
            project_id="pv-001",
            start_phase="intake",
            final_phase="intake",
            saved=True,
        ),
    )
    store_persisted_workflow_result(session_state, result)

    clear_persisted_workflow_session(session_state)

    assert get_active_persisted_workflow_state(session_state, "pv-001") is None
    assert get_active_persisted_workflow_summary(session_state, "pv-001") is None
    assert get_active_persisted_project_id(session_state) is None


def test_persisted_workflow_agent_review_decision_saves_state_and_session(
    tmp_path,
) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    repository.save(ProjectReviewState(project_id="pv-001", intake=_sample_intake()))
    result = run_persisted_local_agent_workflow_with_summary(repository, "pv-001")
    session_state: dict[str, object] = {}
    store_persisted_workflow_result(session_state, result)
    event_id = result.state.agent_events[0].event_id

    updated_state = record_persisted_agent_review_decision(
        session_state,
        repository,
        project_id="pv-001",
        event_id=event_id,
        decision="approved",
        reviewer="demo-review-engineer",
        comment="Approved after checking extracted evidence.",
    )

    persisted_state = repository.load("pv-001")
    active_state = get_active_persisted_workflow_state(session_state, "pv-001")
    assert updated_state == persisted_state
    assert active_state == updated_state
    approval = next(
        item
        for item in persisted_state.approvals
        if item.target_type == "agent_event" and item.target_id == event_id
    )
    assert approval.status == "approved"
    assert approval.locked is True
    assert approval.reviewer == "demo-review-engineer"
    assert approval.comment == "Approved after checking extracted evidence."


def test_persisted_authorized_agent_response_application_saves_state_and_session(
    tmp_path,
) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    state = ProjectReviewState(project_id="pv-application", intake=_sample_intake())
    repository.save(state)
    session_state: dict[str, object] = {}
    store_persisted_workflow_state(session_state, state)
    sandbox = build_agent_response_sandbox_result(
        build_agent_prompt_package("document_intake", state),
        build_sample_agent_response_json("document_intake", state),
        state=state,
    )
    plan = build_agent_response_application_plan(
        build_agent_response_engineer_handoff(sandbox)
    )
    authorization = AgentResponseApplicationAuthorization(
        plan_id=plan.plan_id,
        response_digest=plan.response_digest,
        reviewer="demo-review-engineer",
        decision="authorized",
        comment="Apply validated intake output.",
    )

    updated_state = apply_persisted_authorized_agent_response(
        session_state,
        repository,
        project_id="pv-application",
        sandbox=sandbox,
        plan=plan,
        authorization=authorization,
    )

    persisted_state = repository.load("pv-application")
    active_state = get_active_persisted_workflow_state(session_state, "pv-application")
    assert updated_state == persisted_state
    assert active_state == updated_state
    assert updated_state.current_phase == "document_check"
    assert updated_state.phase_statuses["document_check"] == "waiting_for_engineer"
    assert [document.document_id for document in updated_state.document_versions]
    assert updated_state.agent_events[0].agent_role == "document_intake"
    application_approval = persisted_state.approvals[-1]
    assert application_approval.target_type == "agent_application"
    assert application_approval.target_id == plan.plan_id
    assert application_approval.reviewer == "demo-review-engineer"
    assert application_approval.comment == "Apply validated intake output."
    assert application_approval.locked is True
    assert active_state is not None
    assert active_state.approvals[-1] == application_approval


def test_persisted_workflow_report_revision_saves_state_and_session(tmp_path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    intake = _report_ready_intake()
    result = evaluate_bv_review(intake)
    state = ProjectReviewState(
        project_id="pv-report-ready",
        intake=intake,
        current_phase="report_draft",
        approvals=[
            EngineerApproval(
                approval_id="approval-calculation",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            ),
            EngineerApproval(
                approval_id="approval-report",
                target_type="gate",
                target_id="report",
                status="approved",
                reviewer="demo-review-engineer",
                locked=True,
            ),
        ],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-human-gate",
                input_field_ids=["pile_length_m"],
                input_locked=True,
                status="ready",
            )
        ],
    )
    repository.save(state)
    session_state: dict[str, object] = {}
    store_persisted_workflow_state(session_state, state)
    preview = build_bv_report_preview(intake, result)
    gate = build_report_draft_gate_result(state, result)

    updated_state = record_persisted_report_revision(
        session_state,
        repository,
        project_id="pv-report-ready",
        revision_id="report-rev-001",
        report_preview=preview,
        gate_result=gate,
        reviewer="demo-review-engineer",
        note="Recorded from Streamlit report gate.",
        created_at="2026-05-21T11:00:00+08:00",
    )

    persisted_state = repository.load("pv-report-ready")
    active_state = get_active_persisted_workflow_state(session_state, "pv-report-ready")
    revision = updated_state.report_revisions[-1]
    assert updated_state == persisted_state
    assert active_state == updated_state
    assert revision.revision_id == "report-rev-001"
    assert revision.created_by == "demo-review-engineer"
    assert revision.note == "Recorded from Streamlit report gate."


def test_persisted_workflow_rfi_response_and_closeout_save_state_and_session(tmp_path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    state = ProjectReviewState(
        project_id="pv-rfi-closeout",
        intake=_report_ready_intake(),
        current_phase="report_draft",
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-run-001",
                question="Please confirm foundation reaction updates.",
                responsible_party="client / designer",
                trigger_basis="Foundation run requires clarification.",
                required_document_or_field="uplift_force_kn",
                status="open",
                reopen_review_items=["uplift_force_kn"],
                triggers_incremental_recheck=True,
            )
        ],
    )
    repository.save(state)
    session_state: dict[str, object] = {}
    store_persisted_workflow_state(session_state, state)

    responded_state = record_persisted_rfi_client_response(
        session_state,
        repository,
        project_id="pv-rfi-closeout",
        rfi_id="rfi-foundation-run-001",
        client_response="Designer submitted Rev B reaction table.",
    )

    assert repository.load("pv-rfi-closeout") == responded_state
    assert (
        get_active_persisted_workflow_state(session_state, "pv-rfi-closeout")
        == responded_state
    )
    assert responded_state.rfi_items[0].status == "responded"
    assert responded_state.phase_statuses["issue_rfi_closeout"] == "waiting_for_engineer"

    closed_state = close_persisted_rfi_after_engineer_review(
        session_state,
        repository,
        project_id="pv-rfi-closeout",
        rfi_id="rfi-foundation-run-001",
        closeout_note="Engineer completed incremental recheck.",
        completed_recheck_item_ids=["uplift_force_kn"],
    )

    closed_rfi = closed_state.rfi_items[0]
    assert repository.load("pv-rfi-closeout") == closed_state
    assert (
        get_active_persisted_workflow_state(session_state, "pv-rfi-closeout")
        == closed_state
    )
    assert closed_rfi.status == "closed"
    assert closed_rfi.completed_recheck_items == ["uplift_force_kn"]
    assert closed_state.phase_statuses["issue_rfi_closeout"] == "approved"


def test_persisted_workflow_finding_closeout_saves_state_and_session(tmp_path) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    state = ProjectReviewState(
        project_id="pv-finding-closeout",
        intake=_report_ready_intake(),
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
            )
        ],
    )
    repository.save(state)
    session_state: dict[str, object] = {}
    store_persisted_workflow_state(session_state, state)

    updated_state = record_persisted_finding_closeout_decision(
        session_state,
        repository,
        project_id="pv-finding-closeout",
        risk_id="foundation-bearing-capacity-open",
        decision="closed",
        reviewer="demo-review-engineer",
        closeout_note="Reviewed Rev B geotechnical evidence and closed the finding.",
        approved_at="2026-05-21T14:30:00+08:00",
    )

    persisted_state = repository.load("pv-finding-closeout")
    active_state = get_active_persisted_workflow_state(session_state, "pv-finding-closeout")
    assert updated_state == persisted_state
    assert active_state == updated_state
    assert updated_state.risks[0].status == "closed"
    assert updated_state.risks[0].closeout_note == (
        "Reviewed Rev B geotechnical evidence and closed the finding."
    )
    approval = updated_state.approvals[-1]
    assert approval.target_type == "finding"
    assert approval.target_id == "foundation-bearing-capacity-open"
    assert approval.reviewer == "demo-review-engineer"
    assert approval.approved_at == "2026-05-21T14:30:00+08:00"


def test_persisted_workflow_blocked_calculation_draft_rfi_issue_saves_state_and_session(
    tmp_path,
) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    state = ProjectReviewState(
        project_id="pv-blocked-rfi",
        intake=_report_ready_intake(),
        current_phase="engineer_data_lock",
        calculation_runs=[
            CalculationRun(
                run_id="foundation-failed-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["pile_length_m"],
                input_locked=False,
                status="failed",
                structured_errors=["foundation calculation failed."],
            )
        ],
    )
    repository.save(state)
    session_state: dict[str, object] = {}
    store_persisted_workflow_result(
        session_state,
        PersistedWorkflowRunResult(
            state=state,
            summary=PersistedWorkflowRunSummary(
                project_id="pv-blocked-rfi",
                start_phase="engineer_data_lock",
                final_phase="engineer_data_lock",
                artifact_counts={"calculation_runs": 1},
                saved=True,
            ),
        ),
    )

    updated_state = issue_persisted_blocked_calculation_draft_rfi(
        session_state,
        repository,
        project_id="pv-blocked-rfi",
        rfi_id="rfi-calculation_blocked_foundation_failed_001",
        reviewer="demo-review-engineer",
        comment="Issue blocked foundation calculation RFI.",
        approved_at="2026-05-21T12:30:00+08:00",
    )

    persisted_state = repository.load("pv-blocked-rfi")
    active_state = get_active_persisted_workflow_state(session_state, "pv-blocked-rfi")
    assert updated_state == persisted_state
    assert active_state == updated_state
    assert updated_state.current_phase == "issue_rfi_closeout"
    assert updated_state.phase_statuses["issue_rfi_closeout"] == "waiting_for_client"
    assert updated_state.rfi_items[0].rfi_id == "rfi-calculation_blocked_foundation_failed_001"
    approval = updated_state.approvals[-1]
    assert approval.target_type == "rfi"
    assert approval.target_id == "rfi-calculation_blocked_foundation_failed_001"
    assert approval.reviewer == "demo-review-engineer"
    assert approval.approved_at == "2026-05-21T12:30:00+08:00"
    active_summary = get_active_persisted_workflow_summary(session_state, "pv-blocked-rfi")
    assert active_summary is not None
    assert active_summary.artifact_counts["rfi_items"] == 1
    assert active_summary.artifact_counts["approvals"] == 1


def test_persisted_workflow_incremental_rfi_recheck_saves_runs_and_session(
    tmp_path,
) -> None:
    repository = JsonProjectReviewStateRepository(tmp_path)
    state = ProjectReviewState(
        project_id="pv-rfi-recheck",
        intake=_report_ready_intake(),
        current_phase="issue_rfi_closeout",
        extracted_fields=_locked_calculation_fields(),
        approvals=[
            EngineerApproval(
                approval_id="approval-calculation",
                target_type="gate",
                target_id="calculation",
                status="approved",
                locked=True,
            )
        ],
        calculation_runs=[
            CalculationRun(
                run_id="foundation-run-001",
                engine_name="foundation",
                engine_version="phase1-deterministic-screening",
                input_field_ids=["uplift_force_kn"],
                input_locked=True,
                status="completed",
            )
        ],
        rfi_items=[
            RFIItem(
                rfi_id="rfi-foundation-run-001",
                question="Please confirm foundation reaction updates.",
                responsible_party="client / designer",
                trigger_basis="Foundation run requires clarification.",
                required_document_or_field="uplift_force_kn",
                status="responded",
                client_response="Designer submitted Rev B reaction table.",
                reopen_review_items=["uplift_force_kn"],
                triggers_incremental_recheck=True,
            )
        ],
    )
    repository.save(state)
    session_state: dict[str, object] = {}
    store_persisted_workflow_result(
        session_state,
        PersistedWorkflowRunResult(
            state=state,
            summary=PersistedWorkflowRunSummary(
                project_id="pv-rfi-recheck",
                start_phase="issue_rfi_closeout",
                final_phase="issue_rfi_closeout",
                artifact_counts={"calculation_runs": 1, "rfi_items": 1},
                saved=True,
            ),
        ),
    )

    updated_state = run_persisted_rfi_incremental_calculation_recheck(
        session_state,
        repository,
        project_id="pv-rfi-recheck",
        rfi_id="rfi-foundation-run-001",
    )

    persisted_state = repository.load("pv-rfi-recheck")
    active_state = get_active_persisted_workflow_state(session_state, "pv-rfi-recheck")
    assert updated_state == persisted_state
    assert active_state == updated_state
    assert updated_state.rfi_items[0].completed_recheck_items == ["uplift_force_kn"]
    assert updated_state.calculation_runs[-1].run_id == (
        "incremental-recheck-rfi-foundation-run-001-foundation-001"
    )
    assert updated_state.calculation_runs[-1].status == "completed"
    active_summary = get_active_persisted_workflow_summary(session_state, "pv-rfi-recheck")
    assert active_summary is not None
    assert active_summary.artifact_counts["calculation_runs"] == 2
    assert active_summary.artifact_counts["rfi_items"] == 1


def _sample_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents={
            "structural_drawings": "available",
            "calculation_report": "partial",
            "geotechnical_report": "missing",
        },
    )


def _locked_field(field_id: str, value: str, unit: str) -> ExtractedField:
    return ExtractedField(
        field_id=field_id,
        name=field_id.replace("_", " ").title(),
        candidate_value=value,
        unit=unit,
        source_document_id="calculation-report-c001",
        page_or_section="Calculation input table",
        quote=f"{field_id} = {value}",
        confidence=0.92,
        is_confirmed=True,
        confirmed_value=value,
        confirmed_unit=unit,
        include_in_calculation=True,
    )


def _locked_calculation_fields() -> list[ExtractedField]:
    return [
        _locked_field("pile_diameter_mm", "300", "mm"),
        _locked_field("pile_length_m", "3.5", "m"),
        _locked_field("side_resistance_standard_kpa", "35", "kPa"),
        _locked_field("bearing_capacity_characteristic_kpa", "180", "kPa"),
        _locked_field("uplift_force_kn", "140", "kN"),
        _locked_field("compression_force_kn", "10", "kN"),
        _locked_field("horizontal_force_kn", "12", "kN"),
    ]


def _report_ready_intake() -> BVReviewIntake:
    return BVReviewIntake(
        project_name="Ground PV design review",
        country_or_region="China",
        project_type="utility_pv",
        design_stage="detailed_design",
        standards_systems=["gb", "iec"],
        review_objects=["mounting_structure", "foundation", "load_calculation"],
        documents={
            "structural_drawings": "available",
            "calculation_report": "available",
            "technical_specification": "available",
            "geotechnical_report": "available",
            "vendor_datasheets": "available",
            "contract_requirements": "available",
        },
    )
