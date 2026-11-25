"""Creación de la aplicación FastAPI."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_error_handlers
from app.api.routes import health, prediction
from app.api.security import API_KEY_HEADER, BodySizeLimitMiddleware
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    service = PredictionService(settings.model_path, settings.model_sha256)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Iniciando %s %s", settings.app_name, settings.api_version)
        service.load()
        yield
        service.unload()
        logger.info("Servicio detenido")

    docs_enabled = settings.environment != "production"
    app = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    app.state.prediction_service = service
    app.state.api_key = settings.api_key

    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)

    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", API_KEY_HEADER],
        )

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(prediction.router)
    return app
