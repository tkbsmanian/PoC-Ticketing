"""
Sync health router.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_db, require_role
from app.domain.enums import SyncStatus, UserRole
from app.models.sync_queue import SyncQueueModel

router = APIRouter()
settings = get_settings()


@router.get("/health")
def sync_health(
    db: Session = Depends(get_db),
    _=Depends(require_role(UserRole.IT_TRIAGE, UserRole.PLATFORM_ADMIN, UserRole.AUDITOR)),
):
    from sqlalchemy import func

    pending = db.query(func.count(SyncQueueModel.id)).filter(
        SyncQueueModel.status == SyncStatus.PENDING.value
    ).scalar()

    failed = db.query(func.count(SyncQueueModel.id)).filter(
        SyncQueueModel.status == SyncStatus.FAILED.value
    ).scalar()

    last_success = (
        db.query(SyncQueueModel.last_attempted_at)
        .filter(SyncQueueModel.status == SyncStatus.SUCCESS.value)
        .order_by(SyncQueueModel.last_attempted_at.desc())
        .first()
    )

    return {
        "adapter": settings.SYNC_ADAPTER,
        "pending_count": pending or 0,
        "failed_count": failed or 0,
        "last_success_at": last_success[0].isoformat() if last_success and last_success[0] else None,
    }
