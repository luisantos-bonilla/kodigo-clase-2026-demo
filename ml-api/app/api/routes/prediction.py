from fastapi import APIRouter, Depends

from app.api.dependencies import PredictionServiceDep
from app.api.security import require_api_key
from app.schemas.common import ErrorResponse
from app.schemas.prediction import PredictionRequest, PredictionResponse

router = APIRouter(tags=["prediction"])


# `def` y no `async def`: la inferencia usa CPU y se ejecuta en el threadpool,
# sin bloquear el event loop.
@router.post(
    "/predict",
    summary="Clasificar una flor de Iris",
    dependencies=[Depends(require_api_key)],
    responses={
        401: {"model": ErrorResponse, "description": "API Key ausente o inválida"},
        413: {"model": ErrorResponse, "description": "Solicitud demasiado grande"},
        500: {"model": ErrorResponse, "description": "Error interno"},
        503: {"model": ErrorResponse, "description": "Modelo no disponible"},
    },
)
def predict(
    payload: PredictionRequest, service: PredictionServiceDep
) -> PredictionResponse:
    return service.predict(payload)
