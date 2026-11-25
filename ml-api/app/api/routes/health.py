from fastapi import APIRouter, Response, status

from app.api.dependencies import PredictionServiceDep
from app.schemas.common import HealthResponse, LivenessResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    summary="Servicio preparado para predecir (readiness)",
    responses={503: {"model": HealthResponse, "description": "Modelo no disponible"}},
)
async def health(service: PredictionServiceDep, response: Response) -> HealthResponse:
    if not service.is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unavailable", model_loaded=False)
    return HealthResponse(status="ok", model_loaded=True)


@router.get("/live", summary="Proceso activo (liveness)")
async def live() -> LivenessResponse:
    return LivenessResponse()
