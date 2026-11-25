"""Carga del modelo e inferencia. No depende de FastAPI."""

import hashlib
import io
import logging
import warnings
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import InconsistentVersionWarning

from app.schemas.prediction import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)

# El artefacto se entrenó con matrices NumPy y no guarda nombres de columnas:
# el ORDEN de esta tupla es el contrato con el modelo (sklearn.datasets.load_iris).
# Los rangos son el mínimo y máximo de la partición de entrenamiento.
FEATURE_TRAINING_RANGES: tuple[tuple[str, float, float], ...] = (
    ("sepal_length_cm", 4.3, 7.9),
    ("sepal_width_cm", 2.0, 4.4),
    ("petal_length_cm", 1.1, 6.9),
    ("petal_width_cm", 0.1, 2.5),
)
CLASS_NAMES: dict[int, str] = {0: "setosa", 1: "versicolor", 2: "virginica"}


class ModelLoadError(Exception):
    """El artefacto no existe, está corrupto o es incompatible."""


class ModelNotReadyError(Exception):
    """Se pidió una predicción sin un modelo cargado."""


class InferenceError(Exception):
    """El modelo falló al predecir."""


def load_model(path: Path, expected_sha256: str) -> RandomForestClassifier:
    """Carga el modelo tras verificar su integridad y luego su compatibilidad."""
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ModelLoadError("No se pudo leer el archivo del modelo") from exc

    # Pickle puede ejecutar código: se verifican y deserializan los mismos bytes.
    if hashlib.sha256(content).hexdigest() != expected_sha256:
        raise ModelLoadError("La huella SHA-256 del modelo no coincide")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", InconsistentVersionWarning)
            model = joblib.load(io.BytesIO(content))
    except Exception as exc:
        raise ModelLoadError("Modelo corrupto o incompatible") from exc

    if not isinstance(model, RandomForestClassifier):
        raise ModelLoadError("El artefacto no es un RandomForestClassifier")
    if getattr(model, "n_features_in_", None) != len(FEATURE_TRAINING_RANGES):
        raise ModelLoadError("Número de características inesperado")
    if list(getattr(model, "classes_", [])) != list(CLASS_NAMES):
        raise ModelLoadError("Clases inesperadas en el modelo")
    return model


class PredictionService:
    def __init__(self, model_path: Path, model_sha256: str) -> None:
        self._model_path = model_path
        self._model_sha256 = model_sha256
        self._model: RandomForestClassifier | None = None

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        """Intenta cargar el modelo; si falla, el servicio queda no preparado."""
        try:
            self._model = load_model(self._model_path, self._model_sha256)
        except ModelLoadError:
            logger.exception("Fallo al cargar el modelo; servicio no preparado")
        else:
            logger.info("Modelo cargado correctamente")

    def unload(self) -> None:
        self._model = None

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        model = self._model
        if model is None:
            raise ModelNotReadyError

        values = [getattr(request, name) for name, _, _ in FEATURE_TRAINING_RANGES]
        try:
            probabilities = model.predict_proba(np.array([values], dtype=float))[0]
            # Mismo criterio que RandomForestClassifier.predict (argmax).
            class_id = int(model.classes_[int(np.argmax(probabilities))])
            return PredictionResponse(
                class_id=class_id,
                class_name=CLASS_NAMES[class_id],
                probabilities={
                    CLASS_NAMES[int(label)]: float(probability)
                    for label, probability in zip(model.classes_, probabilities)
                },
                out_of_range_features=[
                    name
                    for (name, low, high), value in zip(FEATURE_TRAINING_RANGES, values)
                    if not low <= value <= high
                ],
            )
        except Exception as exc:
            raise InferenceError from exc
