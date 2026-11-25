"""Seguridad básica: API Key y límite de tamaño de las solicitudes."""

import logging
import secrets
from typing import Annotated

from fastapi import HTTPException, Request, Security, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)

API_KEY_HEADER = "X-API-Key"
_api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


def require_api_key(
    request: Request, api_key: Annotated[str | None, Security(_api_key_header)]
) -> None:
    """Rechaza la solicitud si la clave falta o no coincide."""
    expected = request.app.state.api_key.get_secret_value()
    # compare_digest evita filtrar información por el tiempo de respuesta.
    if not secrets.compare_digest((api_key or "").encode(), expected.encode()):
        logger.warning("Acceso rechazado: API Key ausente o inválida")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key ausente o inválida",
            headers={"WWW-Authenticate": "ApiKey"},
        )


class BodySizeLimitMiddleware:
    """Responde 413 sin acumular en memoria cuerpos mayores que el límite.

    Cuenta los bytes recibidos: no se fía de Content-Length, que puede faltar.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self._app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        body = b""
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body += message.get("body", b"")
            more_body = message.get("more_body", False)
            if len(body) > self._max_bytes:
                logger.warning("Solicitud rechazada: cuerpo demasiado grande")
                response = JSONResponse(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    content={"detail": "Solicitud demasiado grande"},
                )
                await response(scope, receive, send)
                return

        delivered = False

        async def replay() -> Message:
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self._app(scope, replay, send)
