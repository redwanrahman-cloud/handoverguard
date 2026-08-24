"""Application service enforcing workflow invariants."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from uuid import uuid4

from .domain import (
    ApprovalRequest,
    FollowUpTask,
    HandoverReport,
    Issue,
    IssueCreate,
    IssueStatus,
    Priority,
    TriageResult,
)
from .policy import evaluate_issue
from .repository import Repository


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def fingerprint(issue: IssueCreate) -> str:
    material = "|".join(
        [
            issue.property_id,
            issue.department.value,
            issue.category.value,
            issue.room_label or "none",
            _normalize(issue.summary),
        ]
    )
    return hashlib.sha256(material.encode()).hexdigest()


class HandoverService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def ingest(self, incoming: IssueCreate, *, actor: str = "handoverguard-agent") -> Issue:
        existing_source = self.repository.get_issue_by_source_ref(incoming.source_ref)
        if existing_source:
            return existing_source

        now = datetime.now(UTC)
        issue_fingerprint = fingerprint(incoming)
        duplicate = self.repository.find_open_by_fingerprint(issue_fingerprint)
        issue = Issue(
            **incoming.model_dump(),
            id=_id("ISSUE"),
            fingerprint=issue_fingerprint,
            status=IssueStatus.TRIAGED if duplicate else IssueStatus.NEW,
            duplicate_of=duplicate.id if duplicate else None,
            created_at=now,
            updated_at=now,
        )
        self.repository.insert_issue(issue)
        self.repository.append_audit(
            event_type="issue_ingested",
            entity_type="issue",
            entity_id=issue.id,
            actor=actor,
            payload={"source_ref": issue.source_ref, "duplicate_of": issue.duplicate_of},
        )
        if duplicate:
            self.repository.append_audit(
                event_type="duplicate_linked",
                entity_type="issue",
                entity_id=issue.id,
                actor=actor,
                payload={"canonical_issue_id": duplicate.id},
            )
        return issue

    def triage(self, issue_id: str, *, actor: str = "handoverguard-agent") -> TriageResult:
        issue = self._require_issue(issue_id)
        if issue.duplicate_of:
            return TriageResult(
                issue=issue,
                outcome="duplicate_linked",
                duplicate_of=issue.duplicate_of,
            )

        existing_task = self.repository.get_task_for_issue(issue.id)
        existing_approval = self.repository.get_approval_for_issue(issue.id)
        if existing_task:
            return TriageResult(issue=issue, outcome="task_already_exists", task=existing_task)
        if existing_approval:
            return TriageResult(
                issue=issue,
                outcome="approval_already_pending",
                approval=existing_approval,
            )

        decision = evaluate_issue(issue)
        due_at = issue.reported_at + decision.due_after
        issue.due_at = due_at
        issue.approval_reason = decision.approval_reason
        issue.updated_at = datetime.now(UTC)

        if decision.requires_approval:
            issue.status = (
                IssueStatus.ESCALATED
                if decision.force_escalation
                else IssueStatus.AWAITING_APPROVAL
            )
            approval = ApprovalRequest(
                id=_id("APPROVAL"),
                issue_id=issue.id,
                action=issue.requested_action,
                reason=decision.approval_reason or "Human approval required.",
                created_at=datetime.now(UTC),
            )
            self.repository.update_issue(issue)
            self.repository.insert_approval(approval)
            self.repository.append_audit(
                event_type="human_approval_requested",
                entity_type="issue",
                entity_id=issue.id,
                actor=actor,
                payload={"approval_id": approval.id, "reason": approval.reason},
            )
            return TriageResult(issue=issue, outcome="awaiting_human_approval", approval=approval)

        issue.status = IssueStatus.ACTIONED
        task = FollowUpTask(
            id=_id("TASK"),
            issue_id=issue.id,
            owner_department=issue.department,
            title=issue.summary,
            due_at=due_at,
            created_at=datetime.now(UTC),
        )
        self.repository.update_issue(issue)
        self.repository.insert_task(task)
        self.repository.append_audit(
            event_type="internal_task_created",
            entity_type="issue",
            entity_id=issue.id,
            actor=actor,
            payload={"task_id": task.id, "owner_department": task.owner_department.value},
        )
        return TriageResult(issue=issue, outcome="safe_task_created", task=task)

    def process_shift(
        self, shift_id: str, *, actor: str = "handoverguard-agent"
    ) -> list[TriageResult]:
        return [
            self.triage(issue.id, actor=actor) for issue in self.repository.list_issues(shift_id)
        ]

    def handover(self, shift_id: str) -> HandoverReport:
        issues = [
            issue
            for issue in self.repository.list_issues(shift_id)
            if issue.status is not IssueStatus.RESOLVED and issue.duplicate_of is None
        ]
        tasks = self.repository.list_tasks([issue.id for issue in issues]) if issues else []
        return HandoverReport(
            shift_id=shift_id,
            generated_at=datetime.now(UTC),
            unresolved_count=len(issues),
            awaiting_approval_count=sum(
                issue.status in {IssueStatus.AWAITING_APPROVAL, IssueStatus.ESCALATED}
                for issue in issues
            ),
            critical_count=sum(issue.priority is Priority.CRITICAL for issue in issues),
            issues=issues,
            tasks=tasks,
        )

    def _require_issue(self, issue_id: str) -> Issue:
        issue = self.repository.get_issue(issue_id)
        if not issue:
            raise KeyError(f"Unknown issue: {issue_id}")
        return issue
