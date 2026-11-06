"""Endpoints de salud: liveness (proceso vivo) y readiness (dependencias disponibles)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel

from app.modules.health.service import ReadinessProbe

CheckStatus = Literal["ok", "unavailable"]

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: CheckStatus
    checks: dict[str, CheckStatus]


def get_readiness_probe(request: Request) -> ReadinessProbe:
    probe: ReadinessProbe = request.app.state.readiness_probe
    return probe


@router.get("/live")
async def live() -> LivenessResponse:
    return LivenessResponse(status="ok")


@router.get(
    "/ready",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
async def ready(
    response: Response,
    probe: Annotated[ReadinessProbe, Depends(get_readiness_probe)],
) -> ReadinessResponse:
    database: CheckStatus = "ok" if await probe.is_ready() else "unavailable"
    if database == "unavailable":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status=database, checks={"database": database})
