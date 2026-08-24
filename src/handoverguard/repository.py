"""SQLite persistence with a tamper-evident append-only audit chain."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .domain import ApprovalRequest, AuditEvent, FollowUpTask, Issue, IssueStatus

GENESIS_HASH = "0" * 64


class Repository:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._shared_connection = self._connect() if self.path == ":memory:" else None
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._shared_connection or self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            if self._shared_connection is None:
                connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS issues (
                    id TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    source_ref TEXT NOT NULL UNIQUE,
                    property_id TEXT NOT NULL,
                    shift_id TEXT NOT NULL,
                    department TEXT NOT NULL,
                    category TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    details TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    room_label TEXT,
                    requested_action TEXT NOT NULL,
                    financial_impact_sar INTEGER NOT NULL,
                    safety_sensitive INTEGER NOT NULL,
                    reported_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duplicate_of TEXT,
                    due_at TEXT,
                    approval_reason TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (duplicate_of) REFERENCES issues(id)
                );
                CREATE INDEX IF NOT EXISTS idx_issues_fingerprint ON issues(fingerprint);
                CREATE INDEX IF NOT EXISTS idx_issues_shift_status ON issues(shift_id, status);

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    issue_id TEXT NOT NULL UNIQUE,
                    owner_department TEXT NOT NULL,
                    title TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (issue_id) REFERENCES issues(id)
                );

                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    issue_id TEXT NOT NULL UNIQUE,
                    action TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (issue_id) REFERENCES issues(id)
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                );
                """
            )

    @staticmethod
    def _issue_from_row(row: sqlite3.Row) -> Issue:
        return Issue.model_validate(dict(row))

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> FollowUpTask:
        return FollowUpTask.model_validate(dict(row))

    @staticmethod
    def _approval_from_row(row: sqlite3.Row) -> ApprovalRequest:
        return ApprovalRequest.model_validate(dict(row))

    def insert_issue(self, issue: Issue) -> None:
        values = issue.model_dump(mode="json")
        values["safety_sensitive"] = int(issue.safety_sensitive)
        columns = ", ".join(values)
        placeholders = ", ".join(f":{key}" for key in values)
        with self.connection() as connection:
            connection.execute(f"INSERT INTO issues ({columns}) VALUES ({placeholders})", values)

    def update_issue(self, issue: Issue) -> None:
        values = issue.model_dump(mode="json")
        values["safety_sensitive"] = int(issue.safety_sensitive)
        assignments = ", ".join(f"{key} = :{key}" for key in values if key != "id")
        with self.connection() as connection:
            connection.execute(f"UPDATE issues SET {assignments} WHERE id = :id", values)

    def get_issue(self, issue_id: str) -> Issue | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
        return self._issue_from_row(row) if row else None

    def get_issue_by_source_ref(self, source_ref: str) -> Issue | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM issues WHERE source_ref = ?", (source_ref,)
            ).fetchone()
        return self._issue_from_row(row) if row else None

    def find_open_by_fingerprint(self, fingerprint: str) -> Issue | None:
        with self.connection() as connection:
            row = connection.execute(
                """SELECT * FROM issues
                WHERE fingerprint = ? AND duplicate_of IS NULL AND status != ?
                ORDER BY created_at LIMIT 1""",
                (fingerprint, IssueStatus.RESOLVED.value),
            ).fetchone()
        return self._issue_from_row(row) if row else None

    def list_issues(self, shift_id: str | None = None) -> list[Issue]:
        query = "SELECT * FROM issues"
        params: tuple[str, ...] = ()
        if shift_id:
            query += " WHERE shift_id = ?"
            params = (shift_id,)
        query += " ORDER BY reported_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._issue_from_row(row) for row in rows]

    def insert_task(self, task: FollowUpTask) -> None:
        values = task.model_dump(mode="json")
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO tasks
                (id, issue_id, owner_department, title, due_at, status, created_at)
                VALUES
                (:id, :issue_id, :owner_department, :title, :due_at, :status, :created_at)""",
                values,
            )

    def get_task_for_issue(self, issue_id: str) -> FollowUpTask | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM tasks WHERE issue_id = ?", (issue_id,)
            ).fetchone()
        return self._task_from_row(row) if row else None

    def list_tasks(self, issue_ids: list[str] | None = None) -> list[FollowUpTask]:
        query = "SELECT * FROM tasks"
        params: tuple[str, ...] = ()
        if issue_ids:
            placeholders = ",".join("?" for _ in issue_ids)
            query += f" WHERE issue_id IN ({placeholders})"
            params = tuple(issue_ids)
        query += " ORDER BY due_at, id"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._task_from_row(row) for row in rows]

    def insert_approval(self, approval: ApprovalRequest) -> None:
        values = approval.model_dump(mode="json")
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO approvals
                (id, issue_id, action, reason, status, created_at)
                VALUES (:id, :issue_id, :action, :reason, :status, :created_at)""",
                values,
            )

    def get_approval_for_issue(self, issue_id: str) -> ApprovalRequest | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM approvals WHERE issue_id = ?", (issue_id,)
            ).fetchone()
        return self._approval_from_row(row) if row else None

    def append_audit(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor: str,
        payload: dict[str, Any],
        occurred_at: datetime | None = None,
    ) -> AuditEvent:
        timestamp = (occurred_at or datetime.now(UTC)).astimezone(UTC)
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        with self.connection() as connection:
            row = connection.execute(
                "SELECT sequence, event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            previous_hash = row["event_hash"] if row else GENESIS_HASH
            sequence = (int(row["sequence"]) if row else 0) + 1
            canonical = "|".join(
                [
                    str(sequence),
                    event_type,
                    entity_type,
                    entity_id,
                    actor,
                    payload_json,
                    timestamp.isoformat(),
                    previous_hash,
                ]
            )
            event_hash = hashlib.sha256(canonical.encode()).hexdigest()
            connection.execute(
                """INSERT INTO audit_events
                (sequence, event_type, entity_type, entity_id, actor, payload_json,
                 occurred_at, previous_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sequence,
                    event_type,
                    entity_type,
                    entity_id,
                    actor,
                    payload_json,
                    timestamp.isoformat(),
                    previous_hash,
                    event_hash,
                ),
            )
        return AuditEvent(
            sequence=sequence,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            payload=json.loads(payload_json),
            occurred_at=timestamp,
            previous_hash=previous_hash,
            event_hash=event_hash,
        )

    def list_audit_events(self) -> list[AuditEvent]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM audit_events ORDER BY sequence").fetchall()
        return [
            AuditEvent(
                sequence=row["sequence"],
                event_type=row["event_type"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                actor=row["actor"],
                payload=json.loads(row["payload_json"]),
                occurred_at=row["occurred_at"],
                previous_hash=row["previous_hash"],
                event_hash=row["event_hash"],
            )
            for row in rows
        ]

    def verify_audit_chain(self) -> bool:
        previous_hash = GENESIS_HASH
        for event in self.list_audit_events():
            payload_json = json.dumps(
                event.payload, sort_keys=True, separators=(",", ":"), default=str
            )
            canonical = "|".join(
                [
                    str(event.sequence),
                    event.event_type,
                    event.entity_type,
                    event.entity_id,
                    event.actor,
                    payload_json,
                    event.occurred_at.astimezone(UTC).isoformat(),
                    previous_hash,
                ]
            )
            expected = hashlib.sha256(canonical.encode()).hexdigest()
            if event.previous_hash != previous_hash or event.event_hash != expected:
                return False
            previous_hash = event.event_hash
        return True

    def clear_demo_data(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                DELETE FROM audit_events;
                DELETE FROM approvals;
                DELETE FROM tasks;
                DELETE FROM issues;
                """
            )
