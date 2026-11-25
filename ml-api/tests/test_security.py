import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app
from tests.conftest import API_KEY, AUTH


@pytest.fixture
def anonymous(client):
    """Cliente sin API Key sobre la misma aplicación."""
    return TestClient(client.app)


def test_predict_without_key(anonymous, payload):
    response = anonymous.post("/predict", json=payload)
    assert response.status_code == 401
    assert response.json() == {"detail": "API Key ausente o inválida"}
    assert response.headers["www-authenticate"] == "ApiKey"


@pytest.mark.parametrize("key", ["", "incorrecta", API_KEY[:-1], API_KEY + "x", "ñ"])
def test_predict_with_wrong_key(anonymous, payload, key):
    headers = {"X-API-Key": key.encode("latin-1")}
    response = anonymous.post("/predict", json=payload, headers=headers)
    assert response.status_code == 401


def test_key_is_not_accepted_in_query_string(anonymous, payload):
    response = anonymous.post("/predict", json=payload, params=AUTH)
    assert response.status_code == 401


def test_authentication_precedes_body_validation(anonymous):
    assert anonymous.post("/predict", json={"x": 1}).status_code == 401


@pytest.mark.parametrize("path", ["/health", "/health/live"])
def test_health_is_public(anonymous, path):
    assert anonymous.get(path).status_code == 200


def test_key_is_never_logged(anonymous, payload, caplog):
    with caplog.at_level(logging.DEBUG):
        anonymous.post("/predict", json=payload, headers=AUTH)
        anonymous.post("/predict", json=payload, headers={"X-API-Key": "intento-x"})
    assert "API Key ausente o inválida" in caplog.text
    assert API_KEY not in caplog.text
    assert "intento-x" not in caplog.text


def test_settings_require_a_key(isolated_environment):
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_short_key_is_rejected_without_revealing_it():
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, api_key="corta-secreta")
    assert "corta-secreta" not in str(error.value)


def test_settings_do_not_reveal_the_key(make_settings):
    assert API_KEY not in repr(make_settings())


def test_body_over_the_limit(client):
    response = client.post("/predict", content=b"x" * 10_241)
    assert response.status_code == 413
    assert response.json() == {"detail": "Solicitud demasiado grande"}


def test_chunked_body_over_the_limit(client):
    chunks = (b"x" * 1024 for _ in range(20))
    assert client.post("/predict", content=chunks).status_code == 413


def test_body_at_the_limit_reaches_validation(client, payload):
    body = b'{"x": "%s"}' % (b"a" * (10_240 - 9))
    assert len(body) <= 10_240
    headers = {"Content-Type": "application/json"}
    assert client.post("/predict", content=body, headers=headers).status_code == 422


def test_cors_preflight_allows_api_key_header(make_settings):
    origin = "https://permitido.example"
    app = create_app(make_settings(cors_allowed_origins=[origin]))
    response = TestClient(app).options(
        "/predict",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert response.status_code == 200


def test_openapi_documents_the_scheme(client):
    spec = client.get("/openapi.json").json()
    assert spec["components"]["securitySchemes"]["APIKeyHeader"]["name"] == "X-API-Key"
    assert spec["paths"]["/predict"]["post"]["security"] == [{"APIKeyHeader": []}]
    assert "security" not in spec["paths"]["/health"]["get"]
