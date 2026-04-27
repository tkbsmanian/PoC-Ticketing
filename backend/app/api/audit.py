"""
Audit router — read-only access to audit log.
Accessible by platform_admin and auditor roles only.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.domain.enums import UserRole
from app.models.audit import AuditLogModel
from app.models.user import UserModel

router = APIRouter()


@router.get("/tickets/{ticket_id}", response_model=list[dict])
def ticket_audit(
    ticket_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(UserRole.PLATFORM_ADMIN, UserRole.AUDITOR)),
):
    entries = (
        db.query(AuditLogModel)
        .filter(AuditLogModel.ticket_id == ticket_id)
        .order_by(AuditLogModel.created_at)
        .all()
    )
    return [_to_dict(e, db) for e in entries]


@router.get("/log", response_model=list[dict])
def audit_log(
    event_type: str | None = Query(default=None),
    ticket_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_role(UserRole.PLATFORM_ADMIN, UserRole.AUDITOR)),
):
    q = db.query(AuditLogModel)
    if event_type:
        q = q.filter(AuditLogModel.event_type == event_type)
    if ticket_id:
        q = q.filter(AuditLogModel.ticket_id == ticket_id)
    entries = (
        q.order_by(AuditLogModel.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [_to_dict(e, db) for e in entries]


def _to_dict(entry: AuditLogModel, db: Session) -> dict:
    actor = db.get(UserModel, entry.actor_id) if entry.actor_id else None
    return {
        "id": entry.id,
        "ticket_id": entry.ticket_id,
        "actor_name": actor.display_name if actor else None,
        "event_type": entry.event_type,
        "field_name": entry.field_name,
        "old_value": entry.old_value,
        "new_value": entry.new_value,
        "notes": entry.notes,
        "created_at": entry.created_at.isoformat(),
    }
