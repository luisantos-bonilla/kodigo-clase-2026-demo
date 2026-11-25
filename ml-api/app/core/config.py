"""Configuración centralizada mediante variables de entorno."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Evita mostrar la clave si la validación de la configuración falla.
        hide_input_in_errors=True,
    )

    app_name: str = "API de clasificación de Iris"
    api_version: str = "1.0.0"
    environment: Literal["development", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)

    # Obligatoria y sin valor predeterminado: sin clave, la API no arranca.
    api_key: SecretStr = Field(min_length=32)
    max_body_bytes: int = Field(default=10_240, ge=1)

    model_path: Path = APP_DIR / "models" / "model.joblib"
    # Huella del artefacto de confianza. Se comprueba antes de deserializar.
    model_sha256: str = Field(
        default="ee6ec66a04af33aa66237b8adab91baffbbcba5c8557652747df8eac0368c742",
        pattern=r"^[0-9a-f]{64}$",
    )

    # Lista JSON, por ejemplo: ["https://mi-frontend.example"]. Vacía = sin CORS.
    cors_allowed_origins: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()
