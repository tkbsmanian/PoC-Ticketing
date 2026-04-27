"""
Ticket repository — data access only, no business logic.
"""

from sqlalchemy.orm import Session, joinedload

from app.domain.enums import UserRole
from app.models.ticket import TicketModel


class TicketRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, ticket_id: int) -> TicketModel | None:
        return self._db.get(TicketModel, ticket_id)

    def get_by_ticket_id(self, ticket_id: str) -> TicketModel | None:
        return self._db.query(TicketModel).filter(
            TicketModel.ticket_id == ticket_id,
            TicketModel.is_deleted == False,  # noqa: E712
        ).first()

    def list_for_user(
        self,
        user_id: int,
        role: str,
        department_id: int | None,
        status: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        filter_department_id: int | None = None,
        submitter_id: int | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[TicketModel], int]:
        q = self._db.query(TicketModel).filter(TicketModel.is_deleted == False)  # noqa: E712

        # Role-scoped visibility
        if role == UserRole.BUSINESS_USER.value:
            q = q.filter(TicketModel.submitter_id == user_id)
        elif role == UserRole.IT_MANAGER.value:
            if department_id:
                q = q.filter(TicketModel.department_id == department_id)
        # it_triage, platform_admin, auditor see all

        # Filters
        if status:
            q = q.filter(TicketModel.status == status)
        if category:
            q = q.filter(TicketModel.category == category)
        if priority:
            q = q.filter(TicketModel.priority == priority)
        if filter_department_id:
            q = q.filter(TicketModel.department_id == filter_department_id)
        if submitter_id:
            q = q.filter(TicketModel.submitter_id == submitter_id)

        total = q.count()
        items = (
            q.order_by(TicketModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_detail(self, ticket_id: int) -> TicketModel | None:
        return (
            self._db.query(TicketModel)
            .options(
                joinedload(TicketModel.approvals),
            )
            .filter(TicketModel.id == ticket_id, TicketModel.is_deleted == False)  # noqa: E712
            .first()
        )
