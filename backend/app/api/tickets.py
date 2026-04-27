"""
Tickets router — CRUD, status transitions, lifecycle actions.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, require_role
from app.domain.enums import SyncOperation, TicketStatus, UserRole
from app.domain.exceptions import (
    InvalidTransitionError,
    TicketNotDeletableError,
    TicketNotFoundError,
    UnauthorizedActionError,
)
from app.models.audit import AuditLogModel
from app.models.comment import CommentModel
from app.models.attachment import AttachmentModel
from app.models.ticket import ApprovalModel, TicketModel
from app.models.user import UserModel
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import (
    CreateTicketRequest,
    PaginatedTicketsResponse,
    TicketDetailResponse,
    TicketSummaryResponse,
    UpdateCategoryPriorityRequest,
    UpdateStatusRequest,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.sync_service import SyncService
from app.services.ticket_service import TicketService

logger = logging.getLogger(__name__)
router = APIRouter()


def _make_services(db: Session):
    audit = AuditService(db)
    sync = SyncService(db)
    return TicketService(db, audit, sync), audit, sync


@router.get("", response_model=PaginatedTicketsResponse)
def list_tickets(
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    priority: str | None = None,
    department_id: int | None = None,
    submitter_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    repo = TicketRepository(db)
    items, total = repo.list_for_user(
        user_id=current_user.id,
        role=current_user.role,
        department_id=current_user.department_id,
        status=status_filter,
        category=category,
        priority=priority,
        filter_department_id=department_id,
        submitter_id=submitter_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedTicketsResponse(
        items=[_to_summary(t, db) for t in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: CreateTicketRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.role == UserRole.AUDITOR.value:
        raise HTTPException(status_code=403, detail="Auditors cannot submit tickets.")

    svc, audit, sync = _make_services(db)
    ticket = svc.create_ticket(
        submitter_id=current_user.id,
        title=payload.title,
        description=payload.description,
        department_id=payload.department_id,
        urgency=payload.urgency,
        cost=payload.cost,
        manager_id=payload.manager_id,
    )

    # Create manager approval row
    from app.services.approval_service import ApprovalService
    ApprovalService(db, audit).create_manager_approval(ticket, payload.manager_id)

    # Notify manager
    manager = db.get(UserModel, payload.manager_id)
    if manager:
        ticket_url = f"/portal/tickets/{ticket.id}"
        NotificationService(db).notify(
            event_type="approval_required",
            message=f"New request '{ticket.ticket_id}' requires your approval.",
            recipients=[manager],
            ticket_id=ticket.id,
            ticket_url=ticket_url,
        )

    return _to_detail(ticket, db, current_user.role)


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    ticket = _get_authorized_ticket(ticket_id, current_user, db)
    return _to_detail(ticket, db, current_user.role)


@router.patch("/{ticket_id}/status", response_model=TicketDetailResponse)
def update_status(
    ticket_id: int,
    payload: UpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role(UserRole.IT_TRIAGE, UserRole.PLATFORM_ADMIN)
    ),
):
    svc, _, _ = _make_services(db)
    try:
        ticket = svc.transition_status(
            ticket_id=ticket_id,
            new_status=TicketStatus(payload.status),
            actor_id=current_user.id,
            actor_role=current_user.role,
        )
    except (InvalidTransitionError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # Notify submitter
    submitter = db.get(UserModel, ticket.submitter_id)
    if submitter:
        NotificationService(db).notify(
            event_type="status_changed",
            message=f"Your request '{ticket.ticket_id}' status changed to {ticket.status}.",
            recipients=[submitter],
            ticket_id=ticket.id,
        )
    return _to_detail(ticket, db, current_user.role)


@router.patch("/{ticket_id}/category-priority", response_model=TicketDetailResponse)
def update_category_priority(
    ticket_id: int,
    payload: UpdateCategoryPriorityRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role(UserRole.IT_TRIAGE, UserRole.PLATFORM_ADMIN)
    ),
):
    svc, _, _ = _make_services(db)
    try:
        ticket = svc.update_category_priority(
            ticket_id=ticket_id,
            actor_id=current_user.id,
            category=payload.category,
            priority=payload.priority,
        )
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _to_detail(ticket, db, current_user.role)


@router.post("/{ticket_id}/remove", response_model=TicketDetailResponse)
def remove_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    svc, _, _ = _make_services(db)
    try:
        ticket = svc.remove_ticket(ticket_id, current_user.id)
    except (InvalidTransitionError, UnauthorizedActionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _to_detail(ticket, db, current_user.role)


@router.post("/{ticket_id}/reopen", response_model=TicketDetailResponse)
def reopen_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    svc, _, _ = _make_services(db)
    try:
        ticket = svc.transition_status(
            ticket_id=ticket_id,
            new_status=TicketStatus.IN_PROGRESS,
            actor_id=current_user.id,
            actor_role=current_user.role,
        )
    except (InvalidTransitionError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # Notify IT team
    from app.models.user import UserModel as UM
    it_users = db.query(UM).filter(
        UM.role.in_([UserRole.IT_TRIAGE.value, UserRole.PLATFORM_ADMIN.value]),
        UM.is_active == True,  # noqa: E712
    ).all()
    if it_users:
        NotificationService(db).notify(
            event_type="ticket_reopened",
            message=f"Ticket '{ticket.ticket_id}' was re-opened.",
            recipients=it_users,
            ticket_id=ticket.id,
        )
    return _to_detail(ticket, db, current_user.role)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(UserRole.PLATFORM_ADMIN)),
):
    svc, _, _ = _make_services(db)
    try:
        svc.soft_delete(ticket_id, current_user.id)
    except TicketNotDeletableError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_authorized_ticket(ticket_id: int, user: UserModel, db: Session) -> TicketModel:
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


def _to_summary(ticket: TicketModel, db: Session) -> TicketSummaryResponse:
    submitter = db.get(UserModel, ticket.submitter_id)
    dept = ticket.department_id and db.query(
        __import__("app.models.user", fromlist=["DepartmentModel"]).DepartmentModel
    ).get(ticket.department_id)
    return TicketSummaryResponse(
        id=ticket.id,
        ticket_id=ticket.ticket_id,
        title=ticket.title,
        status=ticket.status,
        urgency=ticket.urgency,
        priority=ticket.priority,
        category=ticket.category,
        department_name=dept.name if dept else None,
        submitter_name=submitter.display_name if submitter else "Unknown",
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        sync_failed=ticket.sync_failed,
        jira_task_url=ticket.jira_task_url,
    )


def _to_detail(ticket: TicketModel, db: Session, viewer_role: str) -> TicketDetailResponse:
    from app.schemas.ticket import (
        ApprovalResponse, AttachmentResponse, CommentResponse, HistoryEntryResponse
    )

    submitter = db.get(UserModel, ticket.submitter_id)
    from app.models.user import DepartmentModel
    dept = db.get(DepartmentModel, ticket.department_id) if ticket.department_id else None

    # Comments — filter internal for non-IT roles
    show_internal = viewer_role in (
        UserRole.IT_TRIAGE.value, UserRole.PLATFORM_ADMIN.value, UserRole.AUDITOR.value
    )
    comments_q = db.query(CommentModel).filter(CommentModel.ticket_id == ticket.id)
    if not show_internal:
        comments_q = comments_q.filter(CommentModel.is_internal == False)  # noqa: E712
    comments = comments_q.order_by(CommentModel.created_at).all()

    attachments = db.query(AttachmentModel).filter(
        AttachmentModel.ticket_id == ticket.id
    ).all()

    history = db.query(AuditLogModel).filter(
        AuditLogModel.ticket_id == ticket.id
    ).order_by(AuditLogModel.created_at).all()

    approvals = db.query(ApprovalModel).filter(
        ApprovalModel.ticket_id == ticket.id
    ).all()

    def comment_resp(c: CommentModel) -> CommentResponse:
        author = db.get(UserModel, c.author_id)
        return CommentResponse(
            id=c.id,
            author_name=author.display_name if author else "Unknown",
            author_role=author.role if author else "",
            body=c.body,
            is_internal=c.is_internal,
            created_at=c.created_at,
        )

    def attach_resp(a: AttachmentModel) -> AttachmentResponse:
        uploader = db.get(UserModel, a.uploaded_by)
        return AttachmentResponse(
            id=a.id,
            original_filename=a.original_filename,
            mime_type=a.mime_type,
            file_size_bytes=a.file_size_bytes,
            uploaded_by_name=uploader.display_name if uploader else "Unknown",
            uploaded_at=a.uploaded_at,
        )

    def history_resp(h: AuditLogModel) -> HistoryEntryResponse:
        actor = db.get(UserModel, h.actor_id) if h.actor_id else None
        return HistoryEntryResponse(
            id=h.id,
            event_type=h.event_type,
            field_name=h.field_name,
            old_value=h.old_value,
            new_value=h.new_value,
            actor_name=actor.display_name if actor else "System",
            created_at=h.created_at,
        )

    def approval_resp(a: ApprovalModel) -> ApprovalResponse:
        approver = db.get(UserModel, a.approver_id)
        return ApprovalResponse(
            id=a.id,
            approver_name=approver.display_name if approver else "Unknown",
            approver_role=a.approver_role,
            decision=a.decision,
            comment=a.comment,
            decided_at=a.decided_at,
            deadline=a.deadline,
        )

    return TicketDetailResponse(
        id=ticket.id,
        ticket_id=ticket.ticket_id,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        urgency=ticket.urgency,
        cost=ticket.cost,
        priority=ticket.priority,
        category=ticket.category,
        department_name=dept.name if dept else None,
        submitter_name=submitter.display_name if submitter else "Unknown",
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        sync_failed=ticket.sync_failed,
        jira_task_url=ticket.jira_task_url,
        jira_task_id=ticket.jira_task_id,
        director_approval_required=ticket.director_approval_required,
        comments=[comment_resp(c) for c in comments],
        attachments=[attach_resp(a) for a in attachments],
        history=[history_resp(h) for h in history],
        approvals=[approval_resp(a) for a in approvals],
    )
