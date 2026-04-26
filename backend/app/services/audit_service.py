"""
Audit service — append-only writes to audit_log.
Never issues UPDATE or DELETE against audit_log.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import AuditLogModel

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, db: Session):
        self._db = db

    def record(
        self,
        event_type: str,
        ticket_id: int | None = None,
        actor_id: int | None = None,
        field_name: str | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        notes: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLogModel:
        """
        Write an immutable audit log entry.
        This method only ever INSERTs — never updates existing rows.
        """
        entry = AuditLogModel(
            ticket_id=ticket_id,
            actor_id=actor_id,
            event_type=event_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            notes=notes,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc),
        )
        self._db.add(entry)
        # Caller is responsible for committing the transaction
        return entry
