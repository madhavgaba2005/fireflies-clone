"""Liveness and readiness probes (used by docker compose, hosting platforms and smoke tests)."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.dependencies import DatabaseDep, SettingsDep
from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def liveness(settings: SettingsDep) -> HealthResponse:
    """The process is up. Never touches dependencies, so it can't cause restart loops."""
    return HealthResponse(status="ok", service=settings.app_name)


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse}},
)
def readiness(database: DatabaseDep) -> JSONResponse:
    """The service can do useful work: the database answers."""
    database_ok = database.ping()
    body = ReadinessResponse(
        status="ready" if database_ok else "unavailable",
        checks={"database": "ok" if database_ok else "failed"},
    )
    return JSONResponse(status_code=200 if database_ok else 503, content=body.model_dump())
