"""Repeatable, cloud-free competition proof for HandoverGuard."""

from __future__ import annotations

import argparse
import json
from typing import Any

from pydantic import BaseModel

from .demo_data import DEMO_SHIFT_ID, demo_issues
from .domain import ApprovalStatus
from .repository import Repository
from .service import HandoverService


class DemoProof(BaseModel):
    """Judge-readable evidence produced by the deterministic scenario."""

    scenario: str
    data_classification: str
    issues_ingested: int
    canonical_issues: int
    duplicates_linked: int
    safe_internal_tasks_created: int
    human_approvals_pending: int
    critical_issues: int
    external_actions_executed: int
    audit_events: int
    audit_chain_valid: bool
    safety_invariants_passed: bool


def run_demo_proof() -> DemoProof:
    """Execute the complete synthetic scenario against a fresh in-memory database."""
    service = HandoverService(Repository(":memory:"))
    ingested = [service.ingest(issue, actor="competition-demo") for issue in demo_issues()]
    results = service.process_shift(DEMO_SHIFT_ID, actor="competition-demo")
    report = service.handover(DEMO_SHIFT_ID)
    approvals = service.repository.list_approvals(DEMO_SHIFT_ID)
    audit_events = service.repository.list_audit_events()

    duplicates = sum(issue.duplicate_of is not None for issue in ingested)
    external_actions = sum(
        event.payload.get("external_action_executed") is True for event in audit_events
    )
    pending_approvals = sum(
        approval.status is ApprovalStatus.PENDING for approval in approvals
    )
    safe_tasks = sum(result.outcome == "safe_task_created" for result in results)
    audit_valid = service.repository.verify_audit_chain()
    expected_outcomes = sorted(
        [
            "awaiting_human_approval",
            "awaiting_human_approval",
            "duplicate_linked",
            "safe_task_created",
            "safe_task_created",
        ]
    )
    invariants_passed = all(
        [
            sorted(result.outcome for result in results) == expected_outcomes,
            len(ingested) == 5,
            duplicates == 1,
            safe_tasks == 2,
            pending_approvals == 2,
            report.awaiting_approval_count == 2,
            report.critical_count == 1,
            external_actions == 0,
            audit_valid,
        ]
    )

    return DemoProof(
        scenario=DEMO_SHIFT_ID,
        data_classification="synthetic-only",
        issues_ingested=len(ingested),
        canonical_issues=report.unresolved_count,
        duplicates_linked=duplicates,
        safe_internal_tasks_created=safe_tasks,
        human_approvals_pending=pending_approvals,
        critical_issues=report.critical_count,
        external_actions_executed=external_actions,
        audit_events=len(audit_events),
        audit_chain_valid=audit_valid,
        safety_invariants_passed=invariants_passed,
    )


def _human_summary(proof: DemoProof) -> str:
    status = "PASS" if proof.safety_invariants_passed else "FAIL"
    lines: list[tuple[str, Any]] = [
        ("Scenario", proof.scenario),
        ("Synthetic notes", proof.issues_ingested),
        ("Duplicate notes linked", proof.duplicates_linked),
        ("Safe internal tasks created", proof.safe_internal_tasks_created),
        ("Sensitive actions held for approval", proof.human_approvals_pending),
        ("External actions executed", proof.external_actions_executed),
        ("Audit events", proof.audit_events),
        ("Audit chain valid", proof.audit_chain_valid),
    ]
    body = "\n".join(f"  {label}: {value}" for label, value in lines)
    return f"HandoverGuard deterministic judge proof: {status}\n{body}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run HandoverGuard's deterministic, cloud-free competition proof."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    proof = run_demo_proof()
    if args.json:
        print(json.dumps(proof.model_dump(mode="json"), indent=2, sort_keys=True))
    else:
        print(_human_summary(proof))
    if not proof.safety_invariants_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
