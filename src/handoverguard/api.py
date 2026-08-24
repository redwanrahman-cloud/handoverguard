"""FastAPI boundary for the HandoverGuard demo."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .demo_data import DEMO_SHIFT_ID, demo_issues
from .domain import AuditEvent, HandoverReport, Issue, TriageResult
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


ServiceDep = Annotated[HandoverService, Depends(get_service)]


app = FastAPI(
    title="HandoverGuard",
    version="0.1.0",
    description="Policy-bound hotel shift-handover agent demo using synthetic data.",
)
static_directory = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_directory), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(static_directory / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/demo/reset", response_model=list[Issue])
def reset_demo(service: ServiceDep) -> list[Issue]:
    service.repository.clear_demo_data()
    return [service.ingest(issue, actor="demo-seeder") for issue in demo_issues()]


@app.post("/api/shifts/process", response_model=list[TriageResult])
def process_shift(request: ShiftRequest, service: ServiceDep) -> list[TriageResult]:
    return service.process_shift(request.shift_id)


@app.get("/api/shifts/{shift_id}/handover", response_model=HandoverReport)
def get_handover(shift_id: str, service: ServiceDep) -> HandoverReport:
    return service.handover(shift_id)


@app.get("/api/audit/verify")
def verify_audit(service: ServiceDep) -> dict[str, bool | int]:
    repository = service.repository
    return {
        "valid": repository.verify_audit_chain(),
        "event_count": len(repository.list_audit_events()),
    }


@app.get("/api/audit/events", response_model=list[AuditEvent])
def audit_events(service: ServiceDep) -> list[AuditEvent]:
    return service.repository.list_audit_events()


@app.post("/api/agent/run", response_model=AgentRunResponse)
def run_agent(request: ShiftRequest, service: ServiceDep) -> AgentRunResponse:
    if os.getenv("HANDOVERGUARD_ENABLE_LIVE_AGENT") != "true":
        raise HTTPException(
            status_code=403,
            detail="Live Bedrock agent is disabled. Use deterministic processing for local review.",
        )
    summary = run_shift_agent(service, request.shift_id)
    return AgentRunResponse(shift_id=request.shift_id, summary=summary)


@app.get("/api/demo")
def demo_metadata() -> dict[str, str]:
    return {"shift_id": DEMO_SHIFT_ID, "data_classification": "synthetic-only"}


def main() -> None:
    uvicorn.run("handoverguard.api:app", host="127.0.0.1", port=8000, reload=False)
