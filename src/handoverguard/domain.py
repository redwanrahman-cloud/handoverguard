"""Typed domain objects for hotel handover operations."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(UTC)


class Department(StrEnum):
    FRONT_DESK = "front_desk"
    HOUSEKEEPING = "housekeeping"
    MAINTENANCE = "maintenance"
    FINANCE = "finance"
    SECURITY = "security"


class Category(StrEnum):
    GUEST_REQUEST = "guest_request"
    MAINTENANCE = "maintenance"
    HOUSEKEEPING = "housekeeping"
    PAYMENT = "payment"
    SAFETY = "safety"
    GENERAL = "general"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class IssueStatus(StrEnum):
    NEW = "new"
    TRIAGED = "triaged"
    ACTIONED = "actioned"
    AWAITING_APPROVAL = "awaiting_approval"
    ESCALATED = "escalated"
    DECLINED = "declined"
    RESOLVED = "resolved"


class ActionKind(StrEnum):
    CREATE_INTERNAL_TASK = "create_internal_task"
    SEND_EXTERNAL_MESSAGE = "send_external_message"
    AUTHORIZE_COMPENSATION = "authorize_compensation"
    AUTHORIZE_PAYMENT = "authorize_payment"
    ESCALATE_SAFETY = "escalate_safety"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class IssueCreate(BaseModel):
    """Input accepted from a synthetic shift note or operational system."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source_ref: str = Field(min_length=3, max_length=80)
    property_id: str = Field(pattern=r"^DEMO-[A-Z0-9-]{2,30}$")
    shift_id: str = Field(pattern=r"^SHIFT-[A-Z0-9-]{2,30}$")
    department: Department
    category: Category
    summary: str = Field(min_length=5, max_length=180)
    details: str = Field(min_length=5, max_length=1500)
    priority: Priority = Priority.NORMAL
    room_label: str | None = Field(default=None, pattern=r"^ROOM-[A-Z0-9-]{1,20}$")
    requested_action: ActionKind = ActionKind.CREATE_INTERNAL_TASK
    financial_impact_sar: int = Field(default=0, ge=0, le=100_000)
    safety_sensitive: bool = False
    reported_at: datetime = Field(default_factory=utc_now)

    @field_validator("reported_at")
    @classmethod
    def require_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("reported_at must include a timezone")
        return value.astimezone(UTC)


class Issue(IssueCreate):
    id: str
    fingerprint: str
    status: IssueStatus
    duplicate_of: str | None = None
    due_at: datetime | None = None
    approval_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class FollowUpTask(BaseModel):
    id: str
    issue_id: str
    owner_department: Department
    title: str
    due_at: datetime
    status: str = "open"
    created_at: datetime


class ApprovalRequest(BaseModel):
    id: str
    issue_id: str
    action: ActionKind
    reason: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime
    decided_at: datetime | None = None
    decided_by: str | None = None


class AuditEvent(BaseModel):
    sequence: int
    event_type: str
    entity_type: str
    entity_id: str
    actor: str
    payload: dict[str, Any]
    occurred_at: datetime
    previous_hash: str
    event_hash: str


class TriageResult(BaseModel):
    issue: Issue
    outcome: str
    task: FollowUpTask | None = None
    approval: ApprovalRequest | None = None
    duplicate_of: str | None = None


class ApprovalDecisionResult(BaseModel):
    issue: Issue
    approval: ApprovalRequest
    outcome: str
    task: FollowUpTask | None = None


class HandoverReport(BaseModel):
    shift_id: str
    generated_at: datetime
    unresolved_count: int
    awaiting_approval_count: int
    critical_count: int
    issues: list[Issue]
    tasks: list[FollowUpTask]
