"""
FastAPI dependency providers.
All shared dependencies (auth, DB session, adapter) are defined here.
"""

import logging
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.domain.enums import UserRole
from app.domain.interfaces import SyncAdapter

logger = logging.getLogger(__name__)


# ── Database session ──────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


# ── Current user ──────────────────────────────────────────────────────────────

def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """
    Extract and validate the JWT from the httpOnly cookie.
    Returns the authenticated user ORM model.
    Raises 401 if missing or invalid.
    """
    from app.models.user import UserModel  # avoid circular import

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )
    try:
        payload = decode_access_token(access_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    user_id = int(payload["sub"])
    user = db.get(UserModel, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )
    return user


CurrentUser = Annotated[object, Depends(get_current_user)]


def require_role(*roles: UserRole):
    """
    Dependency factory that enforces one or more allowed roles.
    Usage: Depends(require_role(UserRole.IT_TRIAGE, UserRole.PLATFORM_ADMIN))
    """
    def _check(current_user=Depends(get_current_user)):
        if current_user.role not in [r.value for r in roles]:
            logger.warning(
                "Authorization failure",
                extra={
                    "user_id": current_user.id,
                    "role": current_user.role,
                    "required_roles": [r.value for r in roles],
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user
    return _check


# ── Sync adapter ──────────────────────────────────────────────────────────────

_adapter_instance: SyncAdapter | None = None


def get_sync_adapter(settings: Settings = Depends(get_settings)) -> SyncAdapter:
    """
    Return the configured sync adapter singleton.
    Adapter is selected by SYNC_ADAPTER environment variable.
    """
    global _adapter_instance
    if _adapter_instance is None:
        if settings.SYNC_ADAPTER == "jira":
            from app.adapters.jira_adapter import JiraAdapter
            _adapter_instance = JiraAdapter(settings)
        elif settings.SYNC_ADAPTER == "azure_devops":
            from app.adapters.azure_devops_adapter import AzureDevOpsAdapter
            _adapter_instance = AzureDevOpsAdapter(settings)
        else:
            raise RuntimeError(f"Unknown SYNC_ADAPTER: {settings.SYNC_ADAPTER}")
    return _adapter_instance
