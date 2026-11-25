"""Traducción de errores a respuestas HTTP sin detalles internos."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.prediction_service import InferenceError, ModelNotReadyError

logger = logging.getLogger(__name__)


def _error(status_code: int, detail: object) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def _validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Se omiten "input" y "ctx": evitan devolver datos del cliente y, si hay
    # NaN o Infinity, impedirían serializar la respuesta como JSON.
    errors = [
        {"type": e["type"], "loc": list(e["loc"]), "msg": e["msg"]}
        for e in exc.errors()
    ]
    return _error(status.HTTP_422_UNPROCESSABLE_CONTENT, errors)


async def _model_not_ready(request: Request, exc: ModelNotReadyError) -> JSONResponse:
    logger.warning("Predicción rechazada: modelo no disponible")
    return _error(
        status.HTTP_503_SERVICE_UNAVAILABLE, "Servicio de inferencia no disponible"
    )


async def _inference_error(request: Request, exc: InferenceError) -> JSONResponse:
    logger.error("Error de inferencia", exc_info=exc)
    return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error interno del servidor")


async def _unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # La traza completa la registra Uvicorn al propagarse la excepción.
    logger.error("Error inesperado en %s %s", request.method, request.url.path)
    return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error interno del servidor")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(ModelNotReadyError, _model_not_ready)
    app.add_exception_handler(InferenceError, _inference_error)
    app.add_exception_handler(Exception, _unexpected_error)
