import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sklearn.datasets import load_iris

from app.main import create_app
from app.schemas.prediction import PredictionRequest
from app.services.prediction_service import PredictionService
from tests.conftest import AUTH

FIELDS = ["sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm"]
JSON_HEADERS = {"Content-Type": "application/json"}


def test_valid_prediction(client, payload):
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json() == {
        "class_id": 0,
        "class_name": "setosa",
        "probabilities": {"setosa": 1.0, "versicolor": 0.0, "virginica": 0.0},
        "out_of_range_features": [],
    }


@pytest.mark.parametrize("field", FIELDS)
def test_missing_field(client, payload, field):
    del payload[field]
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", field]


@pytest.mark.parametrize("value", ["5.1", True, None, [5.1], {"v": 5.1}])
def test_invalid_type(client, payload, value):
    payload["sepal_length_cm"] = value
    assert client.post("/predict", json=payload).status_code == 422


def test_integer_json_number_is_accepted(client, payload):
    payload["sepal_length_cm"] = 5
    assert client.post("/predict", json=payload).status_code == 200


@pytest.mark.parametrize("value", [0, -1.0, 30.01, 1e308])
def test_out_of_allowed_range(client, payload, value):
    payload["petal_width_cm"] = value
    assert client.post("/predict", json=payload).status_code == 422


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_numbers(client, literal):
    body = (
        '{"sepal_length_cm": %s, "sepal_width_cm": 3.5, '
        '"petal_length_cm": 1.4, "petal_width_cm": 0.2}' % literal
    )
    response = client.post("/predict", content=body, headers=JSON_HEADERS)
    assert response.status_code == 422


def test_unknown_field_rejected(client, payload):
    payload["model_path"] = "/etc/passwd"
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert "/etc/passwd" not in response.text


def test_malformed_json(client):
    response = client.post("/predict", content="{", headers=JSON_HEADERS)
    assert response.status_code == 422


def test_out_of_training_range_is_reported(client, payload):
    payload["sepal_length_cm"] = 12.0
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json()["out_of_range_features"] == ["sepal_length_cm"]


def test_numpy_values_become_native_types(make_settings, payload):
    settings = make_settings()
    service = PredictionService(settings.model_path, settings.model_sha256)
    service.load()
    result = service.predict(PredictionRequest(**payload))
    assert type(result.class_id) is int
    assert all(type(p) is float for p in result.probabilities.values())


def test_api_matches_direct_model_on_whole_dataset(client, make_settings):
    model = joblib.load(make_settings().model_path)
    features = load_iris().data
    labels = model.predict(features)
    probabilities = model.predict_proba(features)
    for row, label, expected in zip(features, labels, probabilities):
        body = client.post("/predict", json=dict(zip(FIELDS, row.tolist()))).json()
        assert body["class_id"] == label
        np.testing.assert_allclose(
            list(body["probabilities"].values()), expected, rtol=0, atol=1e-12
        )


def test_json_key_order_does_not_matter(client, payload):
    reordered = dict(reversed(payload.items()))
    assert (
        client.post("/predict", json=reordered).json()
        == client.post("/predict", json=payload).json()
    )


def test_predict_without_model(client_without_model, payload):
    response = client_without_model.post("/predict", json=payload)
    assert response.status_code == 503
    assert response.json() == {"detail": "Servicio de inferencia no disponible"}


def _fail(*_):
    raise RuntimeError("detalle interno C:/secreto")


def test_inference_failure_hides_details(make_settings, payload, monkeypatch):
    app = create_app(make_settings())
    with TestClient(app, headers=AUTH) as test_client:
        model = app.state.prediction_service._model
        monkeypatch.setattr(model, "predict_proba", _fail)
        response = test_client.post("/predict", json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "Error interno del servidor"}


def test_unexpected_failure_hides_details(make_settings, payload, monkeypatch):
    app = create_app(make_settings())
    with TestClient(app, headers=AUTH, raise_server_exceptions=False) as test_client:
        monkeypatch.setattr(app.state.prediction_service, "predict", _fail)
        response = test_client.post("/predict", json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "Error interno del servidor"}


def test_model_is_loaded_once(make_settings, payload, monkeypatch):
    calls = []
    original = joblib.load

    def counting_load(source):
        calls.append(source)
        return original(source)

    monkeypatch.setattr(joblib, "load", counting_load)
    with TestClient(create_app(make_settings()), headers=AUTH) as test_client:
        for _ in range(3):
            assert test_client.post("/predict", json=payload).status_code == 200
    assert len(calls) == 1
