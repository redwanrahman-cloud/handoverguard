"""Policy-bound AgentCore Gateway tools for hotel operations."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from common import TABLE, now, record_trace
from policy_rules import approval_reasons

S3 = boto3.client("s3")
SFN = boto3.client("stepfunctions")
BUCKET = os.environ["DATA_BUCKET"]
WORKFLOW_ARN = os.environ["APPROVAL_WORKFLOW_ARN"]


def _tool_name(context: object) -> str:
    client_context = getattr(context, "client_context", None)
    custom = getattr(client_context, "custom", {}) or {}
    full_name = str(custom.get("bedrockAgentCoreToolName", ""))
    return full_name.split("___")[-1]


def _store_issue(run_id: str, event: dict[str, Any]) -> None:
    TABLE.put_item(
        Item={
            "PK": f"RUN#{run_id}",
            "SK": f"ISSUE#{event['issue_id']}",
            "entity_type": "ISSUE",
            "issue_id": event["issue_id"],
            "department": event["department"],
            "title": event["title"],
            "category": event["category"],
            "priority": event["priority"],
            "action": event["action"],
            "financial_impact_sar": int(event["financial_impact_sar"]),
            "safety_sensitive": bool(event["safety_sensitive"]),
            "created_at": now(),
        }
    )


def _create_task(run_id: str, event: dict[str, Any]) -> dict[str, object]:
    task_id = hashlib.sha256(f"{run_id}|{event['issue_id']}".encode()).hexdigest()[:16]
    item = {
        "PK": f"RUN#{run_id}",
        "SK": f"TASK#{task_id}",
        "entity_type": "TASK",
        "task_id": task_id,
        "issue_id": event["issue_id"],
        "department": event["department"],
        "title": event["title"],
        "status": "OPEN",
        "created_at": now(),
    }
    try:
        TABLE.put_item(
            Item=item, ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)"
        )
        record_trace(
            run_id,
            "AWS Lambda + Amazon DynamoDB",
            "Created idempotent internal task",
            str(event["title"]),
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
            raise
        record_trace(run_id, "Amazon DynamoDB", "Reused idempotent internal task", task_id)
    return {"route": "INTERNAL_TASK", "task_id": task_id, "status": "OPEN"}


def _request_approval(run_id: str, event: dict[str, Any], reasons: list[str]) -> dict[str, object]:
    reason = "; ".join(reasons)
    execution = SFN.start_execution(
        stateMachineArn=WORKFLOW_ARN,
        name=f"approval-{uuid4().hex[:20]}",
        input=json.dumps({"run_id": run_id, "issue_id": event["issue_id"], "reason": reason}),
    )
    record_trace(run_id, "AWS Step Functions", "Started human approval workflow", reason)
    return {
        "route": "HUMAN_APPROVAL",
        "status": "PENDING_HUMAN",
        "reasons": reasons,
        "execution_arn": execution["executionArn"],
    }


def handler(event: dict[str, Any], context: object) -> dict[str, object]:
    """Handle the narrow tool surface exposed through AgentCore Gateway."""
    tool_name = _tool_name(context)
    run_id = str(event["run_id"])
    if tool_name == "record_trace":
        item = record_trace(
            run_id, str(event["service"]), str(event["step"]), str(event["evidence"])
        )
        return {"recorded": True, "occurred_at": item["occurred_at"]}
    if tool_name == "route_issue":
        _store_issue(run_id, event)
        reasons = approval_reasons(event)
        return _request_approval(run_id, event, reasons) if reasons else _create_task(run_id, event)
    if tool_name == "write_evidence":
        evidence = {
            "schema_version": "handoverguard-aws-v1",
            "run_id": run_id,
            "summary": event["summary"],
            "generated_at": now(),
        }
        canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"))
        evidence["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
        key = f"evidence/{run_id}.json"
        S3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=json.dumps(evidence).encode(),
            ContentType="application/json",
        )
        record_trace(run_id, "Amazon S3", "Stored digest-bearing evidence", f"s3://{BUCKET}/{key}")
        return {"bucket": BUCKET, "key": key, "sha256": evidence["sha256"]}
    raise ValueError(f"Unknown AgentCore tool: {tool_name}")
