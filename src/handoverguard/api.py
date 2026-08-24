"""FastAPI boundary for the HandoverGuard demo."""

from __future__ import annotations

import os
from functools import lru_cache

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .demo_data import DEMO_SHIFT_ID, demo_issues
from .domain import HandoverReport, Issue, TriageResult
from .repository import Repository
from .service import HandoverService
from .strands_agent import run_shift_agent


class AgentRunResponse(BaseModel):
    shift_id: str
    summary: str


class ShiftRequest(BaseModel):
    shift_id: str = Field(pattern=r"^SHIFT-[A-Z0-9-]{2,30}$")


@lru_cache
def get_service() -> HandoverService:
    path = os.getenv("HANDOVERGUARD_DB_PATH", "data/handoverguard.db")
    return HandoverService(Repository(path))


app = FastAPI(
    title="HandoverGuard",
    version="0.1.0",
    description="Policy-bound hotel shift-handover agent demo using synthetic data.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/demo/reset", response_model=list[Issue])
def reset_demo() -> list[Issue]:
    service = get_service()
    service.repository.clear_demo_data()
    return [service.ingest(issue, actor="demo-seeder") for issue in demo_issues()]


@app.post("/api/shifts/process", response_model=list[TriageResult])
def process_shift(request: ShiftRequest) -> list[TriageResult]:
    return get_service().process_shift(request.shift_id)


@app.get("/api/shifts/{shift_id}/handover", response_model=HandoverReport)
def get_handover(shift_id: str) -> HandoverReport:
    return get_service().handover(shift_id)


@app.get("/api/audit/verify")
def verify_audit() -> dict[str, bool | int]:
    repository = get_service().repository
    return {
        "valid": repository.verify_audit_chain(),
        "event_count": len(repository.list_audit_events()),
    }


@app.post("/api/agent/run", response_model=AgentRunResponse)
def run_agent(request: ShiftRequest) -> AgentRunResponse:
    if os.getenv("HANDOVERGUARD_ENABLE_LIVE_AGENT") != "true":
        raise HTTPException(
            status_code=403,
            detail="Live Bedrock agent is disabled. Use deterministic processing for local review.",
        )
    summary = run_shift_agent(get_service(), request.shift_id)
    return AgentRunResponse(shift_id=request.shift_id, summary=summary)


@app.get("/api/demo")
def demo_metadata() -> dict[str, str]:
    return {"shift_id": DEMO_SHIFT_ID, "data_classification": "synthetic-only"}


def main() -> None:
    uvicorn.run("handoverguard.api:app", host="127.0.0.1", port=8000, reload=False)
