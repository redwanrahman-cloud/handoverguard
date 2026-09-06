"""Shared AWS persistence helpers for HandoverGuard Lambdas."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

import boto3

TABLE = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


def now() -> str:
    return datetime.now(UTC).isoformat()


def record_trace(run_id: str, service: str, step: str, evidence: str) -> dict[str, str]:
    timestamp = now()
    item = {
        "PK": f"RUN#{run_id}",
        "SK": f"TRACE#{timestamp}#{uuid4().hex[:8]}",
        "entity_type": "TRACE",
        "service": service,
        "step": step,
        "evidence": evidence[:500],
        "occurred_at": timestamp,
    }
    TABLE.put_item(Item=item)
    return item
