"""Contratos de entrada y salida de la predicción."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# Límite técnico amplio: descarta valores imposibles (p. ej. milímetros enviados
# como centímetros). No es el rango de entrenamiento, que se trata aparte.
MAX_LENGTH_CM = 30.0

Centimeters = Annotated[float, Field(gt=0, le=MAX_LENGTH_CM, allow_inf_nan=False)]


class PredictionRequest(BaseModel):
    """Medidas de una flor en centímetros."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        json_schema_extra={
            "examples": [
                {
                    "sepal_length_cm": 5.1,
                    "sepal_width_cm": 3.5,
                    "petal_length_cm": 1.4,
                    "petal_width_cm": 0.2,
                }
            ]
        },
    )

    sepal_length_cm: Centimeters = Field(description="Longitud del sépalo (cm)")
    sepal_width_cm: Centimeters = Field(description="Ancho del sépalo (cm)")
    petal_length_cm: Centimeters = Field(description="Longitud del pétalo (cm)")
    petal_width_cm: Centimeters = Field(description="Ancho del pétalo (cm)")


class PredictionResponse(BaseModel):
    class_id: int = Field(description="Índice de la clase predicha (0, 1 o 2)")
    class_name: str = Field(description="Especie predicha")
    probabilities: dict[str, float] = Field(
        description="Probabilidad estimada por especie; suman 1"
    )
    out_of_range_features: list[str] = Field(
        description=(
            "Características fuera del rango visto en el entrenamiento. Si no está "
            "vacía, la predicción es una extrapolación y es menos fiable."
        )
    )
