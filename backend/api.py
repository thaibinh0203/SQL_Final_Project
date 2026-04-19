"""FastAPI deployment entrypoint for the recruitment backend."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend import crud
from backend.config import get_settings
from backend.crud import BackendError, NotFoundError, ValidationError


app = FastAPI(
    title="Recruitment Management System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


class LoginRequest(BaseModel):
    """Credential payload for API login."""

    email: str
    password: str


@app.exception_handler(BackendError)
async def handle_backend_error(_: Any, exc: BackendError) -> JSONResponse:
    """Return safe backend errors as JSON responses."""

    if isinstance(exc, NotFoundError):
        status_code = 404
    elif isinstance(exc, ValidationError):
        status_code = 400
    else:
        status_code = 500
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


@app.get("/")
def root() -> dict[str, str]:
    """Simple root response for Render."""

    return {
        "service": "recruitment-management-system-api",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    """Health endpoint with resolved runtime config."""

    settings = get_settings()
    return {
        "status": "ok",
        "database_host": settings.db_host,
        "database_name": settings.db_name,
    }


@app.get("/smoke-test")
def smoke_test() -> dict[str, Any]:
    """Minimal read-path verification for deployed environments."""

    jobs = crud.list_open_job_positions()
    return {
        "status": "ok",
        "open_jobs": len(jobs),
    }


@app.post("/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    """Authenticate one employer or candidate account."""

    user = crud.authenticate_user(payload.email, payload.password)
    return {
        "account_id": user.account_id,
        "email": user.email,
        "role": user.role,
        "employer_id": user.employer_id,
        "candidate_id": user.candidate_id,
        "display_name": user.display_name,
    }


@app.get("/jobs/open")
def open_jobs(search: str | None = None) -> dict[str, Any]:
    """Return globally visible open job positions."""

    rows = crud.list_open_job_positions(search_term=search)
    return {"count": len(rows), "items": rows}


@app.get("/employers/{employer_id}/dashboard-metrics")
def employer_dashboard_metrics(employer_id: int) -> dict[str, Any]:
    """Return dashboard metrics for one employer."""

    return crud.get_employer_dashboard_metrics(employer_id)


@app.get("/employers/{employer_id}/applications")
def employer_applications(employer_id: int) -> dict[str, Any]:
    """Return employer-owned applications."""

    rows = crud.list_employer_applications(employer_id)
    return {"count": len(rows), "items": rows}


@app.get("/employers/{employer_id}/interviews")
def employer_interviews(employer_id: int) -> dict[str, Any]:
    """Return employer-owned interview results."""

    rows = crud.list_employer_interview_results(employer_id)
    return {"count": len(rows), "items": rows}


@app.get("/candidates/{candidate_id}/applications")
def candidate_applications(candidate_id: int) -> dict[str, Any]:
    """Return one candidate's applications."""

    rows = crud.list_candidate_applications(candidate_id)
    return {"count": len(rows), "items": rows}


@app.get("/candidates/{candidate_id}/interviews")
def candidate_interviews(candidate_id: int) -> dict[str, Any]:
    """Return one candidate's interviews."""

    rows = crud.list_candidate_interviews(candidate_id)
    return {"count": len(rows), "items": rows}
