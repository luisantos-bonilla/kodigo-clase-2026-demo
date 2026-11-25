"""Configuración de logging hacia stdout (compatible con Cloud Run)."""

import logging
import sys


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
