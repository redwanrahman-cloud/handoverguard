"""Non-bypassable operational policy for HandoverGuard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from .domain import ActionKind, Category, IssueCreate, Priority

SLA_MINUTES: dict[Category, int] = {
    Category.SAFETY: 0,
    Category.GUEST_REQUEST: 20,
    Category.HOUSEKEEPING: 30,
    Category.MAINTENANCE: 60,
    Category.PAYMENT: 240,
    Category.GENERAL: 120,
}


@dataclass(frozen=True)
class PolicyDecision:
    due_after: timedelta
    requires_approval: bool
    approval_reason: str | None
    force_escalation: bool


def evaluate_issue(issue: IssueCreate) -> PolicyDecision:
    """Evaluate an issue without relying on a model's judgment."""
    reasons: list[str] = []

    if issue.safety_sensitive or issue.category is Category.SAFETY:
        reasons.append("Safety-sensitive action requires an on-duty human decision.")
    if issue.requested_action is ActionKind.AUTHORIZE_COMPENSATION:
        reasons.append("Guest compensation requires manager approval.")
    if issue.requested_action is ActionKind.AUTHORIZE_PAYMENT:
        reasons.append("Payments require finance approval.")
    if issue.requested_action is ActionKind.SEND_EXTERNAL_MESSAGE:
        reasons.append("External communication requires human approval.")
    if issue.financial_impact_sar >= 100:
        reasons.append("Financial impact is SAR 100 or greater.")

    force_escalation = (
        issue.safety_sensitive
        or issue.category is Category.SAFETY
        or issue.priority is Priority.CRITICAL
    )
    minutes = 0 if force_escalation else SLA_MINUTES[issue.category]
    return PolicyDecision(
        due_after=timedelta(minutes=minutes),
        requires_approval=bool(reasons),
        approval_reason=" ".join(reasons) or None,
        force_escalation=force_escalation,
    )
