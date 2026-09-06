"""HTTP API for synthetic judge runs and human approval decisions."""

from __future__ import annotations

import json
import os
from decimal import Decimal
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key
from common import TABLE, now, record_trace

S3 = boto3.client("s3")
SFN = boto3.client("stepfunctions")
BUCKET = os.environ["DATA_BUCKET"]


def json_default(value: object) -> int | float:
    """Encode DynamoDB numbers for the public judge API."""
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def response(status: int, body: object) -> dict[str, object]:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body, default=json_default),
    }


def handler(event: dict[str, object], _context: object) -> dict[str, object]:
    request = event.get("requestContext", {})
    http = request.get("http", {}) if isinstance(request, dict) else {}
    method = http.get("method", "") if isinstance(http, dict) else ""
    path = str(event.get("rawPath") or "")
    params = event.get("pathParameters") or {}

    if method == "POST" and path == "/runs":
        payload = json.loads(str(event.get("body") or "{}"))
        raw_text = str(payload.get("raw_text") or "").strip()
        if not raw_text or len(raw_text) > 10_000:
            return response(400, {"error": "raw_text must contain 1-10000 characters"})
        run_id = uuid4().hex
        created_at = now()
        TABLE.put_item(
            Item={
                "PK": f"RUN#{run_id}",
                "SK": "META",
                "entity_type": "RUN",
                "run_id": run_id,
                "status": "UPLOADED",
                "created_at": created_at,
                "property_id": str(payload.get("property_id") or "DEMO-RIYADH-01"),
            }
        )
        document = json.dumps({"run_id": run_id, "raw_text": raw_text, "created_at": created_at})
        S3.put_object(
            Bucket=BUCKET,
            Key=f"raw/{run_id}.json",
            Body=document.encode(),
            ContentType="application/json",
        )
        record_trace(
            run_id,
            "Amazon API Gateway",
            "Accepted synthetic handover",
            "Validated request and assigned a run ID",
        )
        record_trace(run_id, "Amazon S3", "Stored raw handover", f"s3://{BUCKET}/raw/{run_id}.json")
        return response(202, {"run_id": run_id, "status": "UPLOADED"})

    run_id = str(params.get("run_id") or "") if isinstance(params, dict) else ""
    if method == "GET" and path.endswith("/trace") and run_id:
        result = TABLE.query(
            KeyConditionExpression=Key("PK").eq(f"RUN#{run_id}") & Key("SK").begins_with("TRACE#")
        )
        return response(200, {"run_id": run_id, "steps": result.get("Items", [])})
    if method == "GET" and run_id:
        result = TABLE.query(KeyConditionExpression=Key("PK").eq(f"RUN#{run_id}"))
        return response(200, {"run_id": run_id, "items": result.get("Items", [])})

    approval_id = str(params.get("approval_id") or "") if isinstance(params, dict) else ""
    if method == "POST" and approval_id:
        approval = TABLE.get_item(Key={"PK": f"APPROVAL#{approval_id}", "SK": "META"}).get("Item")
        if not approval or "task_token" not in approval:
            return response(404, {"error": "pending approval not found"})
        payload = json.loads(str(event.get("body") or "{}"))
        decision = str(payload.get("decision") or "")
        if decision not in {"approve", "reject"}:
            return response(400, {"error": "decision must be approve or reject"})
        decision_status = {"approve": "APPROVED", "reject": "REJECTED"}[decision]
        SFN.send_task_success(
            taskToken=approval["task_token"],
            output=json.dumps({"decision": decision, "decided_at": now()}),
        )
        TABLE.update_item(
            Key={"PK": f"APPROVAL#{approval_id}", "SK": "META"},
            UpdateExpression="SET #s=:s, decided_at=:t",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": decision_status, ":t": now()},
        )
        TABLE.update_item(
            Key={"PK": f"RUN#{approval['run_id']}", "SK": f"APPROVAL#{approval_id}"},
            UpdateExpression="SET #s=:s, decided_at=:t",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": decision_status, ":t": now()},
        )
        record_trace(
            str(approval["run_id"]),
            "AWS Step Functions",
            "Human decision resumed workflow",
            f"Decision: {decision}",
        )
        return response(200, {"approval_id": approval_id, "decision": decision})

    return response(404, {"error": "route not found"})
