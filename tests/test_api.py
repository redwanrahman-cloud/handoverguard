import hashlib
import json

from fastapi.testclient import TestClient

from handoverguard.api import app, get_service
from handoverguard.repository import Repository
from handoverguard.service import HandoverService

_test_service = HandoverService(Repository(":memory:"))


def override_service() -> HandoverService:
    return _test_service


app.dependency_overrides[get_service] = override_service
client = TestClient(app)


def test_health_and_locked_live_agent() -> None:
    assert client.get("/").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}
    response = client.post("/api/agent/run", json={"shift_id": "SHIFT-TEST-01"})
    assert response.status_code == 403


def test_demo_flow() -> None:
    reset = client.post("/api/demo/reset")
    assert reset.status_code == 200
    assert len(reset.json()) == 5

    process = client.post("/api/shifts/process", json={"shift_id": "SHIFT-NIGHT-2408"})
    assert process.status_code == 200
    assert len(process.json()) == 5

    approvals = client.get("/api/shifts/SHIFT-NIGHT-2408/approvals")
    assert approvals.status_code == 200
    assert len(approvals.json()) == 2
    approve = client.post(
        f"/api/approvals/{approvals.json()[0]['id']}/decision",
        json={"decision": "approve"},
    )
    assert approve.status_code == 200
    assert approve.json()["outcome"] == "approval_granted_task_created"
    reject = client.post(
        f"/api/approvals/{approvals.json()[1]['id']}/decision",
        json={"decision": "reject"},
    )
    assert reject.status_code == 200
    assert reject.json()["outcome"] == "approval_rejected_action_blocked"

    handover = client.get("/api/shifts/SHIFT-NIGHT-2408/handover")
    assert handover.status_code == 200
    assert handover.json()["unresolved_count"] == 4
    assert handover.json()["awaiting_approval_count"] == 0
    assert len(handover.json()["tasks"]) == 3
    assert handover.json()["raw_note_count"] == 5
    assert handover.json()["duplicate_count"] == 1

    audit = client.get("/api/audit/verify")
    assert audit.json()["valid"] is True

    events = client.get("/api/audit/events")
    assert events.status_code == 200
    assert len(events.json()) == audit.json()["event_count"]

    evidence = client.get("/api/shifts/SHIFT-NIGHT-2408/evidence")
    assert evidence.status_code == 200
    packet = evidence.json()
    assert packet["schema_version"] == "handoverguard-evidence-v1"
    assert packet["audit_chain_valid"] is True
    assert packet["external_actions_executed"] == 0
    digest = packet.pop("evidence_digest")
    canonical = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canonical.encode()).hexdigest() == digest
    assert "attachment" in evidence.headers["content-disposition"]


def test_unknown_approval_returns_404() -> None:
    response = client.post(
        "/api/approvals/APPROVAL-NOT-FOUND/decision",
        json={"decision": "approve"},
    )
    assert response.status_code == 404
