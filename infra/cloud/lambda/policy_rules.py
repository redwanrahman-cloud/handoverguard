"""Deterministic policy rules applied after Nova extracts structured issues."""

from __future__ import annotations

from collections.abc import Mapping


def approval_reasons(issue: Mapping[str, object]) -> list[str]:
    """Return machine-enforced reasons that require human authority."""
    reasons: list[str] = []
    category = str(issue.get("category", "")).lower()
    action = str(issue.get("action", "")).lower()
    priority = str(issue.get("priority", "")).lower()
    financial_impact = int(issue.get("financial_impact_sar", 0) or 0)
    if bool(issue.get("safety_sensitive")) or category == "safety":
        reasons.append("safety-sensitive issue")
    if "compensation" in action or "refund" in action:
        reasons.append("guest compensation or refund")
    if "payment" in action or "charge" in action:
        reasons.append("payment-affecting action")
    if any(
        term in action for term in ("send message", "email guest", "contact guest", "call guest")
    ):
        reasons.append("external guest communication")
    if financial_impact >= 100:
        reasons.append(f"financial impact is SAR {financial_impact}")
    if priority == "critical" and not reasons:
        reasons.append("critical-priority issue")
    return reasons
