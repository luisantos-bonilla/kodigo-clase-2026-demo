from fastapi.testclient import TestClient

from app.main import create_app


def test_health_ready(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_loaded": True}


def test_health_not_ready_without_model(client_without_model):
    response = client_without_model.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "model_loaded": False}


def test_live_does_not_depend_on_model(client_without_model):
    response = client_without_model.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_docs_only_outside_production(client, make_settings):
    assert client.get("/docs").status_code == 200
    production = TestClient(create_app(make_settings(environment="production")))
    assert production.get("/docs").status_code == 404
    assert production.get("/openapi.json").status_code == 404


def test_cors_only_for_configured_origins(client, make_settings):
    header = "access-control-allow-origin"
    allowed = {"Origin": "https://permitido.example"}
    denied = {"Origin": "https://otro.example"}
    assert header not in client.get("/health/live", headers=allowed).headers

    settings = make_settings(cors_allowed_origins=[allowed["Origin"]])
    cors_client = TestClient(create_app(settings))
    response = cors_client.get("/health/live", headers=allowed)
    assert response.headers[header] == allowed["Origin"]
    assert header not in cors_client.get("/health/live", headers=denied).headers
