"""
Notifications router — in-portal notification feed.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.notification import NotificationModel
from app.models.user import UserModel

router = APIRouter()


@router.get("", response_model=list[dict])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    notifications = (
        db.query(NotificationModel)
        .filter(NotificationModel.recipient_id == current_user.id)
        .order_by(NotificationModel.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": n.id,
            "ticket_id": n.ticket_id,
            "event_type": n.event_type,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifications
    ]


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    n = db.query(NotificationModel).filter(
        NotificationModel.id == notification_id,
        NotificationModel.recipient_id == current_user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found.")
    n.is_read = True
    db.commit()


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    db.query(NotificationModel).filter(
        NotificationModel.recipient_id == current_user.id,
        NotificationModel.is_read == False,  # noqa: E712
    ).update({"is_read": True})
    db.commit()
