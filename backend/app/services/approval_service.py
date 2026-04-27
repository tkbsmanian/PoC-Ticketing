"""
Approval service — handles Manager and Director approval/rejection actions.
Sequential flow: Manager first, then Director if director_approval_required.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.domain.enums import ApprovalDecision, ApproverRole, TicketStatus
from app.domain.exceptions import (
    ApprovalAlreadyDecidedError,
    ApprovalNotAssignedError,
    TicketNotFoundError,
)
from app.models.ticket import ApprovalModel, TicketModel
from app.models.user import UserModel
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

APPROVAL_DEADLINE_HOURS = 48


class ApprovalService:
    def __init__(self, db: Session, audit: AuditService):
        self._db = db
        self._audit = audit

    def create_manager_approval(self, ticket: TicketModel, manager_id: int) -> ApprovalModel:
        """Create the Manager approval row when a ticket is submitted."""
        approval = ApprovalModel(
            ticket_id=ticket.id,
            approver_id=manager_id,
            approver_role=ApproverRole.MANAGER.value,
            deadline=datetime.now(timezone.utc) + timedelta(hours=APPROVAL_DEADLINE_HOURS),
        )
        self._db.add(approval)
        self._db.commit()
        return approval

    def decide(
        self,
        approval_id: int,
        approver_id: int,
        decision: ApprovalDecision,
        comment: str | None = None,
    ) -> ApprovalModel:
        """
        Record an approval or rejection decision.
        On Manager approval: creates Director row if director_approval_required.
        On Manager approval (no Director needed): sets ticket to Approved.
        On any rejection: sets ticket to Rejected immediately.
        On Director approval: sets ticket to Approved.
        """
        approval = self._db.get(ApprovalModel, approval_id)
        if not approval:
            raise TicketNotFoundError(f"Approval {approval_id} not found.")
        if approval.approver_id != approver_id:
            raise ApprovalNotAssignedError("This approval is not assigned to you.")
        if approval.decision is not None:
            raise ApprovalAlreadyDecidedError("This approval has already been decided.")

        approval.decision = decision.value
        approval.comment = comment
        approval.decided_at = datetime.now(timezone.utc)

        ticket = self._db.get(TicketModel, approval.ticket_id)

        self._audit.record(
            ticket_id=approval.ticket_id,
            actor_id=approver_id,
            event_type="approval_decision",
            field_name="decision",
            new_value=decision.value,
            notes=f"{approval.approver_role} {decision.value}",
        )

        if decision == ApprovalDecision.REJECTED:
            # Immediate rejection regardless of step
            ticket.status = TicketStatus.REJECTED.value
            self._audit.record(
                ticket_id=ticket.id,
                actor_id=approver_id,
                event_type="status_changed",
                field_name="status",
                old_value=TicketStatus.PENDING.value,
                new_value=TicketStatus.REJECTED.value,
            )
        elif decision == ApprovalDecision.APPROVED:
            if approval.approver_role == ApproverRole.MANAGER.value:
                if ticket.director_approval_required:
                    # Create Director approval row — find a director
                    director = self._find_director(ticket)
                    if director:
                        director_approval = ApprovalModel(
                            ticket_id=ticket.id,
                            approver_id=director.id,
                            approver_role=ApproverRole.DIRECTOR.value,
                            deadline=datetime.now(timezone.utc) + timedelta(hours=APPROVAL_DEADLINE_HOURS),
                        )
                        self._db.add(director_approval)
                        logger.info(
                            "Director approval created",
                            extra={"ticket_id": ticket.id, "director_id": director.id},
                        )
                    else:
                        # No director found — auto-approve
                        ticket.status = TicketStatus.APPROVED.value
                else:
                    # No Director needed — ticket is fully approved
                    ticket.status = TicketStatus.APPROVED.value
                    self._audit.record(
                        ticket_id=ticket.id,
                        actor_id=approver_id,
                        event_type="status_changed",
                        field_name="status",
                        old_value=TicketStatus.PENDING.value,
                        new_value=TicketStatus.APPROVED.value,
                    )
            elif approval.approver_role == ApproverRole.DIRECTOR.value:
                # Director approved — ticket fully approved
                ticket.status = TicketStatus.APPROVED.value
                self._audit.record(
                    ticket_id=ticket.id,
                    actor_id=approver_id,
                    event_type="status_changed",
                    field_name="status",
                    old_value=TicketStatus.PENDING.value,
                    new_value=TicketStatus.APPROVED.value,
                )

        self._db.commit()
        logger.info(
            "Approval decision recorded",
            extra={
                "approval_id": approval_id,
                "approver_id": approver_id,
                "decision": decision.value,
                "ticket_id": approval.ticket_id,
            },
        )
        return approval

    def _find_director(self, ticket: TicketModel) -> UserModel | None:
        """Find an active director in the same department as the ticket."""
        from app.domain.enums import UserRole
        return (
            self._db.query(UserModel)
            .filter(
                UserModel.role == UserRole.IT_MANAGER.value,
                UserModel.department_id == ticket.department_id,
                UserModel.is_active == True,  # noqa: E712
                UserModel.id != ticket.manager_id,  # not the same as manager
            )
            .first()
        )
