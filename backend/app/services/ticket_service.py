"""
Ticket service — orchestrates ticket creation, status transitions, and lifecycle actions.
Delegates business rules to domain modules.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.approval_rules import requires_director_approval
from app.domain.enums import SyncOperation, TicketStatus, UserRole
from app.domain.exceptions import (
    InvalidTransitionError,
    TicketNotFoundError,
    TicketNotDeletableError,
    UnauthorizedActionError,
)
from app.domain.ticket_lifecycle import (
    is_deletable,
    is_removable_by_submitter,
    is_valid_transition,
)
from app.models.ticket import ApprovalModel, TicketModel
from app.services.audit_service import AuditService
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)


class TicketService:
    def __init__(self, db: Session, audit: AuditService, sync: SyncService):
        self._db = db
        self._audit = audit
        self._sync = sync

    def create_ticket(
        self,
        submitter_id: int,
        title: str,
        description: str,
        department_id: int,
        urgency: str,
        cost: float | None,
        manager_id: int,
    ) -> TicketModel:
        """Create a new ticket, enqueue JIRA sync, write audit entry."""
        director_required = requires_director_approval(urgency, cost)  # type: ignore[arg-type]
        ticket_id = _generate_ticket_id()

        ticket = TicketModel(
            ticket_id=ticket_id,
            title=title,
            description=description,
            urgency=urgency,
            cost=cost,
            status=TicketStatus.PENDING.value,
            submitter_id=submitter_id,
            department_id=department_id,
            manager_id=manager_id,
            director_approval_required=director_required,
        )
        self._db.add(ticket)
        self._db.flush()  # get ticket.id before commit

        self._audit.record(
            ticket_id=ticket.id,
            actor_id=submitter_id,
            event_type="ticket_created",
            notes=f"Ticket {ticket_id} created with status Pending",
        )
        self._db.commit()
        self._db.refresh(ticket)

        self._sync.enqueue(ticket.id, SyncOperation.CREATE_TASK)
        logger.info(
            "Ticket created",
            extra={"ticket_id": ticket_id, "submitter_id": submitter_id},
        )
        return ticket

    def transition_status(
        self,
        ticket_id: int,
        new_status: TicketStatus,
        actor_id: int,
        actor_role: str,
    ) -> TicketModel:
        """Validate and apply a status transition. Enqueue JIRA sync."""
        ticket = self._get_ticket_or_raise(ticket_id)
        current = TicketStatus(ticket.status)

        if not is_valid_transition(current, new_status):
            logger.warning(
                "Invalid transition attempt",
                extra={
                    "ticket_id": ticket_id,
                    "attempted_transition": f"{current.value} → {new_status.value}",
                    "user_id": actor_id,
                },
            )
            raise InvalidTransitionError(
                f"Cannot transition from {current.value} to {new_status.value}."
            )

        old_status = ticket.status
        ticket.status = new_status.value
        ticket.updated_at = datetime.now(timezone.utc)

        self._audit.record(
            ticket_id=ticket.id,
            actor_id=actor_id,
            event_type="status_changed",
            field_name="status",
            old_value=old_status,
            new_value=new_status.value,
        )
        self._db.commit()
        self._sync.enqueue(ticket.id, SyncOperation.UPDATE_STATUS)
        return ticket

    def remove_ticket(self, ticket_id: int, submitter_id: int) -> TicketModel:
        """Submitter withdraws their own ticket (→ Removed)."""
        ticket = self._get_ticket_or_raise(ticket_id)
        if ticket.submitter_id != submitter_id:
            raise UnauthorizedActionError("Only the submitter can remove this ticket.")
        current = TicketStatus(ticket.status)
        if not is_removable_by_submitter(current):
            raise InvalidTransitionError(
                f"Ticket cannot be removed from status {current.value}."
            )
        return self.transition_status(
            ticket_id, TicketStatus.REMOVED, submitter_id, UserRole.BUSINESS_USER.value
        )

    def soft_delete(self, ticket_id: int, admin_id: int) -> TicketModel:
        """Platform Admin soft-deletes a Closed or Rejected ticket."""
        ticket = self._get_ticket_or_raise(ticket_id)
        if not is_deletable(TicketStatus(ticket.status)):
            raise TicketNotDeletableError(
                "Only Closed or Rejected tickets may be deleted."
            )
        ticket.is_deleted = True
        ticket.deleted_at = datetime.now(timezone.utc)
        self._audit.record(
            ticket_id=ticket.id,
            actor_id=admin_id,
            event_type="ticket_soft_deleted",
        )
        self._db.commit()
        return ticket

    def update_category_priority(
        self,
        ticket_id: int,
        actor_id: int,
        category: str | None = None,
        priority: str | None = None,
    ) -> TicketModel:
        """IT Triage Analyst sets or updates category and/or priority."""
        ticket = self._get_ticket_or_raise(ticket_id)
        if category is not None and category != ticket.category:
            self._audit.record(
                ticket_id=ticket.id,
                actor_id=actor_id,
                event_type="field_changed",
                field_name="category",
                old_value=ticket.category,
                new_value=category,
            )
            ticket.category = category
        if priority is not None and priority != ticket.priority:
            self._audit.record(
                ticket_id=ticket.id,
                actor_id=actor_id,
                event_type="field_changed",
                field_name="priority",
                old_value=ticket.priority,
                new_value=priority,
            )
            ticket.priority = priority
        ticket.updated_at = datetime.now(timezone.utc)
        self._db.commit()
        self._sync.enqueue(ticket.id, SyncOperation.UPDATE_STATUS)
        return ticket

    def _get_ticket_or_raise(self, ticket_id: int) -> TicketModel:
        ticket = self._db.get(TicketModel, ticket_id)
        if not ticket or ticket.is_deleted:
            raise TicketNotFoundError(f"Ticket {ticket_id} not found.")
        return ticket


def _generate_ticket_id() -> str:
    """Generate a unique ticket ID in the format TKT-XXXXXXXX."""
    return f"TKT-{uuid.uuid4().hex[:8].upper()}"
