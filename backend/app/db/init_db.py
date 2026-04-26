"""
Database initialisation — creates all tables on first run.
Called once at application startup.
"""

import logging

from app.db.base import Base
from app.db.session import engine

# Import all models so Base.metadata is populated before create_all
import app.models  # noqa: F401

logger = logging.getLogger(__name__)


def init_db() -> None:
    logger.info("Initialising database schema.")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema ready.")
