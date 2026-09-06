"""Persist a Step Functions callback token and notify the judge-facing UI."""

from __future__ import annotations

import os
from uuid import uuid4

import boto3
from common import TABLE, now, record_trace

SNS = boto3.client("sns")
TOPIC_ARN = os.environ["APPROVAL_TOPIC_ARN"]


def handler(event: dict[str, str], _context: object) -> dict[str, str]:
    approval_id = uuid4().hex
    created_at = now()
    TABLE.put_item(
        Item={
            "PK": f"APPROVAL#{approval_id}",
            "SK": "META",
            "entity_type": "APPROVAL",
            "approval_id": approval_id,
            "run_id": event["run_id"],
            "issue_id": event["issue_id"],
            "reason": event["reason"],
            "status": "PENDING",
            "task_token": event["task_token"],
            "created_at": created_at,
        }
    )
    TABLE.put_item(
        Item={
            "PK": f"RUN#{event['run_id']}",
            "SK": f"APPROVAL#{approval_id}",
            "entity_type": "APPROVAL",
            "approval_id": approval_id,
            "issue_id": event["issue_id"],
            "reason": event["reason"],
            "status": "PENDING",
            "created_at": created_at,
        }
    )
    record_trace(
        event["run_id"], "AWS Step Functions", "Paused for human authority", event["reason"]
    )
    SNS.publish(
        TopicArn=TOPIC_ARN,
        Subject="HandoverGuard approval required",
        Message=f"Synthetic approval {approval_id} requires a decision.",
    )
    return {"approval_id": approval_id, "status": "PENDING"}
