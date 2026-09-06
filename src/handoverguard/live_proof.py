"""Judge-readable proof of a real Strands + Amazon Bedrock agent cycle."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from .demo_data import DEMO_SHIFT_ID, demo_issues
from .domain import ApprovalStatus
from .repository import Repository
from .service import HandoverService
from .strands_agent import run_shift_agent


class LiveProof(BaseModel):
    """Evidence captured after a Bedrock-backed Strands run."""

    scenario: str
    data_classification: str
    framework: str
    model_provider: str
    model_id: str
    model_summary: str
    issues_ingested: int
    duplicates_linked: int
    safe_internal_tasks_created: int
    human_approvals_pending: int
    external_actions_executed: int
    audit_events: int
    audit_chain_valid: bool
    safety_invariants_passed: bool


def run_live_proof(
    agent_runner: Callable[[HandoverService, str], str] = run_shift_agent,
) -> LiveProof:
    """Seed synthetic notes, invoke Strands/Bedrock, and verify policy state."""
    service = HandoverService(Repository(":memory:"))
    ingested = [service.ingest(issue, actor="live-proof-seeder") for issue in demo_issues()]
    summary = agent_runner(service, DEMO_SHIFT_ID)

    report = service.handover(DEMO_SHIFT_ID)
    approvals = service.repository.list_approvals(DEMO_SHIFT_ID)
    events = service.repository.list_audit_events()
    duplicates = sum(issue.duplicate_of is not None for issue in ingested)
    pending_approvals = sum(approval.status is ApprovalStatus.PENDING for approval in approvals)
    external_actions = sum(
        event.payload.get("external_action_executed") is True for event in events
    )
    safe_tasks = len(report.tasks)
    audit_valid = service.repository.verify_audit_chain()
    invariants_passed = all(
        [
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

    return LiveProof(
        scenario=DEMO_SHIFT_ID,
        data_classification="synthetic-only",
        framework="Strands Agents",
        model_provider="Amazon Bedrock",
        model_id=os.getenv("HANDOVERGUARD_BEDROCK_MODEL", "us.amazon.nova-lite-v1:0"),
        model_summary=summary,
        issues_ingested=len(ingested),
        duplicates_linked=duplicates,
        safe_internal_tasks_created=safe_tasks,
        human_approvals_pending=pending_approvals,
        external_actions_executed=external_actions,
        audit_events=len(events),
        audit_chain_valid=audit_valid,
        safety_invariants_passed=invariants_passed,
    )


def _human_summary(proof: LiveProof) -> str:
    status = "PASS" if proof.safety_invariants_passed else "FAIL"
    lines: list[tuple[str, Any]] = [
        ("Framework", proof.framework),
        ("Model", proof.model_id),
        ("Synthetic notes", proof.issues_ingested),
        ("Duplicate notes linked", proof.duplicates_linked),
        ("Safe internal tasks created", proof.safe_internal_tasks_created),
        ("Sensitive actions held for approval", proof.human_approvals_pending),
        ("External actions executed", proof.external_actions_executed),
        ("Audit chain valid", proof.audit_chain_valid),
    ]
    body = "\n".join(f"  {label}: {value}" for label, value in lines)
    return (
        f"HandoverGuard live Strands + Bedrock proof: {status}\n{body}\n"
        f"  Model summary: {proof.model_summary}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run HandoverGuard's live Strands + Amazon Bedrock proof."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    proof = run_live_proof()
    if args.json:
        print(json.dumps(proof.model_dump(mode="json"), indent=2, sort_keys=True))
    else:
        print(_human_summary(proof))
    if not proof.safety_invariants_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
