"""
Approvals router — pending queue, approve, reject.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, require_role
from app.domain.enums import ApprovalDecision, UserRole
from app.domain.exceptions import (
    ApprovalAlreadyDecidedError,
    ApprovalNotAssignedError,
    TicketNotFoundError,
)
from app.models.ticket import ApprovalModel, TicketModel
from app.models.user import UserModel
from app.schemas.approval import ApprovalActionRequest
from app.schemas.ticket import ApprovalResponse
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/pending", response_model=list[ApprovalResponse])
def list_pending_approvals(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        require_role(UserRole.IT_MANAGER, UserRole.PLATFORM_ADMIN, UserRole.AUDITOR)
    ),
):
    approvals = (
        db.query(ApprovalModel)
        .filter(
            ApprovalModel.approver_id == current_user.id,
            ApprovalModel.decision == None,  # noqa: E711
        )
        .all()
    )
    return [_to_response(a, db) for a in approvals]


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve(
    approval_id: int,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(UserRole.IT_MANAGER)),
):
    return _decide(approval_id, ApprovalDecision.APPROVED, payload.comment, current_user, db)


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject(
    approval_id: int,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role(UserRole.IT_MANAGER)),
):
    if not payload.comment:
        raise HTTPException(status_code=422, detail="A rejection reason is required.")
    return _decide(approval_id, ApprovalDecision.REJECTED, payload.comment, current_user, db)


def _decide(
    approval_id: int,
    decision: ApprovalDecision,
    comment: str | None,
    current_user: UserModel,
    db: Session,
) -> ApprovalResponse:
    audit = AuditService(db)
    svc = ApprovalService(db, audit)
    try:
        approval = svc.decide(approval_id, current_user.id, decision, comment)
    except ApprovalNotAssignedError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ApprovalAlreadyDecidedError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    ticket = db.get(TicketModel, approval.ticket_id)
    submitter = db.get(UserModel, ticket.submitter_id) if ticket else None

    # Notify submitter of outcome
    if submitter and ticket:
        if decision == ApprovalDecision.REJECTED:
            msg = f"Your request '{ticket.ticket_id}' was rejected."
        else:
            msg = f"Your request '{ticket.ticket_id}' has been approved."
        NotificationService(db).notify(
            event_type="approval_decision",
            message=msg,
            recipients=[submitter],
            ticket_id=ticket.id,
        )

        # If fully approved, notify IT team
        if ticket.status == "Approved":
            it_users = db.query(UserModel).filter(
                UserModel.role.in_([UserRole.IT_TRIAGE.value, UserRole.PLATFORM_ADMIN.value]),
                UserModel.is_active == True,  # noqa: E712
            ).all()
            if it_users:
                NotificationService(db).notify(
                    event_type="ticket_approved",
                    message=f"Ticket '{ticket.ticket_id}' is approved and ready for IT review.",
                    recipients=it_users,
                    ticket_id=ticket.id,
                )

    return _to_response(approval, db)


def _to_response(approval: ApprovalModel, db: Session) -> ApprovalResponse:
    approver = db.get(UserModel, approval.approver_id)
    return ApprovalResponse(
        id=approval.id,
        approver_name=approver.display_name if approver else "Unknown",
        approver_role=approval.approver_role,
        decision=approval.decision,
        comment=approval.comment,
        decided_at=approval.decided_at,
        deadline=approval.deadline,
    )
