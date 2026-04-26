"""
Structured logging setup.
Call configure_logging() once at application startup.
All modules use: logger = logging.getLogger(__name__)
"""

import logging
import sys
from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    if settings.LOG_FORMAT == "json" or settings.is_production():
        _configure_json_logging(level)
    else:
        _configure_text_logging(level)


def _configure_text_logging(level: int) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        stream=sys.stdout,
    )


def _configure_json_logging(level: int) -> None:
    """
    JSON logging for production.
    Uses python-json-logger if available, falls back to text.
    """
    try:
        from pythonjsonlogger import jsonlogger  # type: ignore

        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(level)
        root.handlers = [handler]
    except ImportError:
        _configure_text_logging(level)
