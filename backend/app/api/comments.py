"""
Comments router — list and create comments on tickets.
Internal comments filtered by role.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.domain.enums import SyncOperation, UserRole
from app.models.comment import CommentModel
from app.models.ticket import TicketModel
from app.models.user import UserModel
from app.schemas.comment import CreateCommentRequest
from app.schemas.ticket import CommentResponse
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)
router = APIRouter()

_IT_ROLES = {UserRole.IT_TRIAGE.value, UserRole.PLATFORM_ADMIN.value, UserRole.AUDITOR.value}


@router.get("/{ticket_id}/comments", response_model=list[CommentResponse])
def list_comments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    ticket = _get_ticket_or_403(ticket_id, current_user, db)
    show_internal = current_user.role in _IT_ROLES
    q = db.query(CommentModel).filter(CommentModel.ticket_id == ticket.id)
    if not show_internal:
        q = q.filter(CommentModel.is_internal == False)  # noqa: E712
    comments = q.order_by(CommentModel.created_at).all()
    return [_to_response(c, db) for c in comments]


@router.post("/{ticket_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    ticket_id: int,
    payload: CreateCommentRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.role == UserRole.AUDITOR.value:
        raise HTTPException(status_code=403, detail="Auditors cannot add comments.")

    ticket = _get_ticket_or_403(ticket_id, current_user, db)

    if ticket.status == "Closed":
        raise HTTPException(status_code=403, detail="Comments are disabled on closed tickets.")

    # Only IT roles can post internal comments
    is_internal = payload.is_internal
    if is_internal and current_user.role not in {UserRole.IT_TRIAGE.value, UserRole.PLATFORM_ADMIN.value}:
        raise HTTPException(status_code=403, detail="Only IT users can post internal comments.")

    comment = CommentModel(
        ticket_id=ticket.id,
        author_id=current_user.id,
        body=payload.body,
        is_internal=is_internal,
    )
    db.add(comment)

    AuditService(db).record(
        ticket_id=ticket.id,
        actor_id=current_user.id,
        event_type="comment_added",
        notes=f"{'Internal' if is_internal else 'Public'} comment added",
    )
    db.commit()
    db.refresh(comment)

    # Enqueue JIRA sync for public comments only
    if not is_internal and ticket.jira_task_id:
        import json
        SyncService(db).enqueue(
            ticket.id,
            SyncOperation.ADD_COMMENT,
            payload_json=json.dumps({"comment_id": comment.id}),
        )

    # Notify the other party
    _notify_comment(ticket, comment, current_user, db)

    return _to_response(comment, db)


def _get_ticket_or_403(ticket_id: int, user: UserModel, db: Session) -> TicketModel:
    ticket = db.get(TicketModel, ticket_id)
    if not ticket or ticket.is_deleted:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    role = user.role
    if role == UserRole.BUSINESS_USER.value and ticket.submitter_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    if role == UserRole.IT_MANAGER.value:
        if ticket.submitter_id != user.id and ticket.department_id != user.department_id:
            raise HTTPException(status_code=403, detail="Access denied.")
    return ticket


def _notify_comment(ticket: TicketModel, comment: CommentModel, author: UserModel, db: Session):
    if comment.is_internal:
        return
    notif_svc = NotificationService(db)
    if author.role in _IT_ROLES:
        # IT commented — notify submitter
        submitter = db.get(UserModel, ticket.submitter_id)
        if submitter:
            notif_svc.notify(
                event_type="comment_added",
                message=f"IT added a comment on your request '{ticket.ticket_id}'.",
                recipients=[submitter],
                ticket_id=ticket.id,
            )
    else:
        # Submitter commented — notify IT
        it_users = db.query(UserModel).filter(
            UserModel.role.in_([UserRole.IT_TRIAGE.value, UserRole.PLATFORM_ADMIN.value]),
            UserModel.is_active == True,  # noqa: E712
        ).all()
        if it_users:
            notif_svc.notify(
                event_type="comment_added",
                message=f"Submitter added a comment on ticket '{ticket.ticket_id}'.",
                recipients=it_users,
                ticket_id=ticket.id,
            )


def _to_response(comment: CommentModel, db: Session) -> CommentResponse:
    author = db.get(UserModel, comment.author_id)
    return CommentResponse(
        id=comment.id,
        author_name=author.display_name if author else "Unknown",
        author_role=author.role if author else "",
        body=comment.body,
        is_internal=comment.is_internal,
        created_at=comment.created_at,
    )
