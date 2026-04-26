"""
Approval service — handles Manager and Director approval/rejection actions.
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
        Raises ApprovalNotAssignedError if the approver doesn't own this approval.
        Raises ApprovalAlreadyDecidedError if already decided.
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

        self._audit.record(
            ticket_id=approval.ticket_id,
            actor_id=approver_id,
            event_type="approval_decision",
            field_name="decision",
            new_value=decision.value,
            notes=f"{approval.approver_role} {decision.value}",
        )
        self._db.commit()
        logger.info(
            "Approval decision recorded",
            extra={
                "approval_id": approval_id,
                "approver_id": approver_id,
                "decision": decision.value,
            },
        )
        return approval
