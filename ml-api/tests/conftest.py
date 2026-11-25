import os
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

API_KEY = "clave-solo-para-pruebas-0123456789abcdef"
AUTH = {"X-API-Key": API_KEY}


@pytest.fixture(scope="session", autouse=True)
def isolated_environment() -> Iterator[None]:
    """Evita que variables del equipo alteren las pruebas."""
    patch = pytest.MonkeyPatch()
    for key in list(os.environ):
        if key.lower() in Settings.model_fields:
            patch.delenv(key)
    yield
    patch.undo()


@pytest.fixture(scope="session")
def make_settings(isolated_environment) -> Callable[..., Settings]:
    def _make(**overrides: object) -> Settings:
        return Settings(_env_file=None, **{"api_key": API_KEY, **overrides})

    return _make


@pytest.fixture(scope="session")
def client(make_settings: Callable[..., Settings]) -> Iterator[TestClient]:
    with TestClient(create_app(make_settings()), headers=AUTH) as test_client:
        yield test_client


@pytest.fixture
def client_without_model(
    make_settings: Callable[..., Settings], tmp_path: Path
) -> Iterator[TestClient]:
    settings = make_settings(model_path=tmp_path / "no-existe.joblib")
    with TestClient(create_app(settings), headers=AUTH) as test_client:
        yield test_client


@pytest.fixture
def payload() -> dict[str, float]:
    return {
        "sepal_length_cm": 5.1,
        "sepal_width_cm": 3.5,
        "petal_length_cm": 1.4,
        "petal_width_cm": 0.2,
    }
