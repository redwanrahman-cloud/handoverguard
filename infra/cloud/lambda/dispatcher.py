"""Consume EventBridge/SQS handover events and invoke AgentCore Runtime."""

from __future__ import annotations

import json
import os
from urllib.parse import unquote_plus

import boto3
from common import TABLE, record_trace

S3 = boto3.client("s3")
AGENTCORE = boto3.client("bedrock-agentcore")
RUNTIME_ARN = os.environ.get("AGENT_RUNTIME_ARN", "")


def handler(event: dict[str, object], _context: object) -> None:
    for record in event.get("Records", []):
        envelope = json.loads(record["body"])
        detail = envelope["detail"]
        bucket = detail["bucket"]["name"]
        key = unquote_plus(detail["object"]["key"])
        document = json.loads(S3.get_object(Bucket=bucket, Key=key)["Body"].read())
        run_id = document["run_id"]
        TABLE.update_item(
            Key={"PK": f"RUN#{run_id}", "SK": "META"},
            UpdateExpression="SET #s=:s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "AGENT_RUNNING"},
        )
        record_trace(run_id, "Amazon EventBridge + Amazon SQS", "Delivered handover to agent", key)
        if not RUNTIME_ARN:
            raise RuntimeError("AgentCore Runtime has not been deployed yet")
        payload = json.dumps(document).encode()
        response = AGENTCORE.invoke_agent_runtime(
            agentRuntimeArn=RUNTIME_ARN,
            runtimeSessionId=f"handover-{run_id[:24]}",
            contentType="application/json",
            accept="application/json",
            payload=payload,
        )
        result = json.loads(response["response"].read())
        TABLE.update_item(
            Key={"PK": f"RUN#{run_id}", "SK": "META"},
            UpdateExpression=(
                "SET #s=:s, model_id=:m, agent_latency_ms=:a, guardrail_latency_ms=:g, summary=:r"
            ),
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": str(result.get("status", "COMPLETED")),
                ":m": str(result.get("model", "Amazon Nova")),
                ":a": int(result.get("agent_latency_ms", 0)),
                ":g": int(result.get("guardrail_latency_ms", 0)),
                ":r": str(result.get("summary", ""))[:2000],
            },
        )
        record_trace(
            run_id,
            "Amazon Bedrock AgentCore Runtime",
            "Completed Strands supervisor invocation",
            f"model={result.get('model')} latency_ms={result.get('agent_latency_ms')}",
        )
