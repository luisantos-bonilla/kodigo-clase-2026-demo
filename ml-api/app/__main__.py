"""Punto de entrada: `python -m app`. Respeta HOST y PORT."""

import uvicorn

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    # log_config=None: Uvicorn usa el logging de la aplicación (stdout).
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_config=None,
        server_header=False,
    )


if __name__ == "__main__":
    main()
