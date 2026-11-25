import hashlib
import pickle
from pathlib import Path

import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import InconsistentVersionWarning

from app.main import create_app
from app.services.prediction_service import ModelLoadError, load_model


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_real_model_loads(make_settings):
    settings = make_settings()
    model = load_model(settings.model_path, settings.model_sha256)
    assert isinstance(model, RandomForestClassifier)


def test_missing_file(tmp_path):
    with pytest.raises(ModelLoadError):
        load_model(tmp_path / "no-existe.joblib", "0" * 64)


def test_wrong_hash_is_rejected_before_deserializing(make_settings, monkeypatch):
    def must_not_run(*_):
        pytest.fail("No debe deserializarse un artefacto no verificado")

    monkeypatch.setattr(joblib, "load", must_not_run)
    with pytest.raises(ModelLoadError, match="SHA-256"):
        load_model(make_settings().model_path, "0" * 64)


def test_corrupt_file(tmp_path):
    path = tmp_path / "corrupto.joblib"
    path.write_bytes(b"esto no es un modelo")
    with pytest.raises(ModelLoadError, match="corrupto"):
        load_model(path, sha256(path))


# El segundo artefacto es un estimador sin entrenar.
@pytest.mark.parametrize("artifact", [{"no": "modelo"}, RandomForestClassifier()])
def test_incompatible_artifact(tmp_path, artifact):
    path = tmp_path / "otro.joblib"
    joblib.dump(artifact, path)
    with pytest.raises(ModelLoadError):
        load_model(path, sha256(path))


def test_other_sklearn_version_is_rejected(tmp_path, make_settings):
    # Altera la versión declarada en una copia temporal; el original no se toca.
    content = pickle.dumps(joblib.load(make_settings().model_path))
    assert b"1.6.1" in content
    path = tmp_path / "version.joblib"
    path.write_bytes(content.replace(b"1.6.1", b"1.5.2"))
    with pytest.raises(ModelLoadError) as error:
        load_model(path, sha256(path))
    assert isinstance(error.value.__cause__, InconsistentVersionWarning)


def test_startup_with_incompatible_model_is_not_ready(tmp_path, make_settings):
    path = tmp_path / "corrupto.joblib"
    path.write_bytes(b"basura")
    settings = make_settings(model_path=path, model_sha256=sha256(path))
    with TestClient(create_app(settings)) as test_client:
        assert test_client.get("/health").status_code == 503
