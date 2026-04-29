"""
SQLAlchemy engine and session factory.
Reads DATABASE_URL directly from environment so tests can override it
before this module is imported.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/ticketing.db")

# SQLite needs check_same_thread=False; URI mode needs uri=True
_is_sqlite = "sqlite" in _DATABASE_URL
_is_uri_mode = "?uri=true" in _DATABASE_URL or _DATABASE_URL.startswith("sqlite:///file:")

_connect_args: dict = {}
if _is_sqlite:
    _connect_args["check_same_thread"] = False
if _is_uri_mode:
    _connect_args["uri"] = True

engine = create_engine(_DATABASE_URL, connect_args=_connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
