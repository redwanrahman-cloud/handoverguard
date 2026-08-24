from datetime import UTC, datetime

from handoverguard.domain import ActionKind, Category, Department, IssueCreate
from handoverguard.policy import evaluate_issue


def issue(**overrides: object) -> IssueCreate:
    values: dict[str, object] = {
        "source_ref": "DEMO-TEST-001",
        "property_id": "DEMO-RIYADH-01",
        "shift_id": "SHIFT-TEST-01",
        "department": Department.MAINTENANCE,
        "category": Category.MAINTENANCE,
        "summary": "Inspect a synthetic air conditioner",
        "details": "Synthetic test detail for an internal maintenance task.",
        "reported_at": datetime(2026, 8, 24, tzinfo=UTC),
    }
    values.update(overrides)
    return IssueCreate.model_validate(values)


def test_internal_task_does_not_require_approval() -> None:
    decision = evaluate_issue(issue())
    assert not decision.requires_approval
    assert decision.approval_reason is None


def test_compensation_is_always_held_for_human() -> None:
    decision = evaluate_issue(
        issue(
            requested_action=ActionKind.AUTHORIZE_COMPENSATION,
            financial_impact_sar=250,
        )
    )
    assert decision.requires_approval
    assert "compensation" in (decision.approval_reason or "").lower()


def test_safety_is_immediate_and_escalated() -> None:
    decision = evaluate_issue(issue(category=Category.SAFETY, safety_sensitive=True))
    assert decision.requires_approval
    assert decision.force_escalation
    assert decision.due_after.total_seconds() == 0
