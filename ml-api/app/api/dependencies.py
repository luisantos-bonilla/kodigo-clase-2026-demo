"""Dependencias compartidas por las rutas."""

from typing import Annotated

from fastapi import Depends, Request

from app.services.prediction_service import PredictionService


def get_prediction_service(request: Request) -> PredictionService:
    return request.app.state.prediction_service


PredictionServiceDep = Annotated[PredictionService, Depends(get_prediction_service)]
