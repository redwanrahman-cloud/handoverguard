from handoverguard.demo_data import DEMO_SHIFT_ID, demo_issues
from handoverguard.domain import IssueStatus
from handoverguard.repository import Repository
from handoverguard.service import HandoverService


def service() -> HandoverService:
    return HandoverService(Repository(":memory:"))


def test_shift_processing_deduplicates_and_enforces_approvals() -> None:
    app = service()
    ingested = [app.ingest(issue) for issue in demo_issues()]

    assert ingested[1].duplicate_of == ingested[0].id

    results = app.process_shift(DEMO_SHIFT_ID)
    outcomes = [result.outcome for result in results]
    assert outcomes.count("safe_task_created") == 2
    assert outcomes.count("duplicate_linked") == 1
    assert outcomes.count("awaiting_human_approval") == 2

    report = app.handover(DEMO_SHIFT_ID)
    assert report.unresolved_count == 4
    assert report.awaiting_approval_count == 2
    assert report.critical_count == 1
    assert len(report.tasks) == 2
    assert app.repository.verify_audit_chain()


def test_processing_is_idempotent() -> None:
    app = service()
    first_issue = app.ingest(demo_issues()[0])
    duplicate_ingest = app.ingest(demo_issues()[0])
    assert duplicate_ingest.id == first_issue.id

    first = app.triage(first_issue.id)
    second = app.triage(first_issue.id)
    assert first.task is not None
    assert second.task is not None
    assert first.task.id == second.task.id
    assert second.outcome == "task_already_exists"


def test_safety_never_creates_an_automatic_task() -> None:
    app = service()
    safety = app.ingest(demo_issues()[-1])
    result = app.triage(safety.id)
    assert result.task is None
    assert result.approval is not None
    assert result.issue.status is IssueStatus.ESCALATED


def test_audit_tampering_is_detected() -> None:
    app = service()
    app.ingest(demo_issues()[0])
    assert app.repository.verify_audit_chain()
    with app.repository.connection() as connection:
        connection.execute("UPDATE audit_events SET actor = 'tampered' WHERE sequence = 1")
    assert not app.repository.verify_audit_chain()
