"""Contratos compartidos entre endpoints."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "unavailable"]
    model_loaded: bool = Field(description="Indica si el servicio puede predecir")


class LivenessResponse(BaseModel):
    status: Literal["alive"] = "alive"


class ErrorResponse(BaseModel):
    detail: str
