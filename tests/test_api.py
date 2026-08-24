from fastapi.testclient import TestClient

from handoverguard.api import app, get_service
from handoverguard.repository import Repository
from handoverguard.service import HandoverService


def override_service() -> HandoverService:
    return HandoverService(Repository(":memory:"))


app.dependency_overrides[get_service] = override_service
client = TestClient(app)


def test_health_and_locked_live_agent() -> None:
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

    handover = client.get("/api/shifts/SHIFT-NIGHT-2408/handover")
    assert handover.status_code == 200
    assert handover.json()["unresolved_count"] == 4

    audit = client.get("/api/audit/verify")
    assert audit.json()["valid"] is True
