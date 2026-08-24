"""Strands agent wiring with policy-bound tools."""

from __future__ import annotations

import json
import os
from typing import Any

from strands import Agent, tool
from strands.models import BedrockModel

from .domain import IssueCreate
from .service import HandoverService

SYSTEM_PROMPT = """You are HandoverGuard, a hotel operations agent.
Use tools to process the specified synthetic shift. Perform routine internal work autonomously.
Never claim an external message, payment, compensation, safety resolution, or guest contact
occurred.
Those actions require a human approval request enforced by the tools. Never mark issues resolved.
Finish with a factual shift summary derived only from tool results.
"""


def build_tools(service: HandoverService) -> list[Any]:
    @tool
    def ingest_synthetic_issue(issue_json: str) -> dict[str, Any]:
        """Ingest one synthetic operational issue encoded as JSON.

        Args:
            issue_json: A JSON object matching the documented synthetic issue schema.
        """
        incoming = IssueCreate.model_validate_json(issue_json)
        issue = service.ingest(incoming)
        return issue.model_dump(mode="json")

    @tool
    def list_shift_issues(shift_id: str) -> list[dict[str, Any]]:
        """List all issues currently recorded for a synthetic shift.

        Args:
            shift_id: Synthetic shift identifier beginning with SHIFT-.
        """
        return [issue.model_dump(mode="json") for issue in service.repository.list_issues(shift_id)]

    @tool
    def triage_issue(issue_id: str) -> dict[str, Any]:
        """Apply policy and perform the permitted next action for one issue.

        Args:
            issue_id: Existing issue identifier.
        """
        return service.triage(issue_id).model_dump(mode="json")

    @tool
    def generate_shift_handover(shift_id: str) -> dict[str, Any]:
        """Generate the current factual handover for a synthetic shift.

        Args:
            shift_id: Synthetic shift identifier beginning with SHIFT-.
        """
        return service.handover(shift_id).model_dump(mode="json")

    @tool
    def verify_audit_chain() -> dict[str, bool]:
        """Verify that the append-only operational audit chain has not been altered."""
        return {"valid": service.repository.verify_audit_chain()}

    return [
        ingest_synthetic_issue,
        list_shift_issues,
        triage_issue,
        generate_shift_handover,
        verify_audit_chain,
    ]


def build_agent(service: HandoverService) -> Agent:
    model = BedrockModel(
        model_id=os.getenv("HANDOVERGUARD_BEDROCK_MODEL", "us.amazon.nova-lite-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        temperature=0,
    )
    return Agent(
        name="HandoverGuard",
        description="Autonomous hotel shift-handover and exception-management agent.",
        model=model,
        tools=build_tools(service),
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )


def run_shift_agent(service: HandoverService, shift_id: str) -> str:
    """Run one live Bedrock-backed Strands cycle."""
    agent = build_agent(service)
    result = agent(
        f"Process every unprocessed issue for {shift_id}. Then verify the audit chain and "
        "generate the handover. Return a concise operational summary."
    )
    return str(result)


def serialize_demo_issues(issues: list[IssueCreate]) -> list[str]:
    return [json.dumps(issue.model_dump(mode="json")) for issue in issues]
