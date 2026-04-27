"""
FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from app.db.init_db import init_db

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initialising database.")
    init_db()
    # Start background sync worker
    from app.workers.sync_worker import start_sync_worker, stop_sync_worker
    start_sync_worker()
    logger.info("Application ready.")
    yield
    stop_sync_worker()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="Internal Ticketing System",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if not settings.is_production() else None,
    redoc_url=None,
)

# Middleware (order matters — outermost first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.api import auth, tickets, comments, attachments, approvals, users, notifications, audit, sync, health  # noqa: E402

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
app.include_router(comments.router, prefix="/tickets", tags=["comments"])
app.include_router(attachments.router, prefix="/tickets", tags=["attachments"])
app.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
app.include_router(users.router, prefix="", tags=["users"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])
app.include_router(sync.router, prefix="/sync", tags=["sync"])
app.include_router(health.router, prefix="", tags=["health"])
