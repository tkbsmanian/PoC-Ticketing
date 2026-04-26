"""
Sync service — enqueues sync events for the background worker.
Does NOT call adapters directly.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.enums import SyncOperation, SyncStatus
from app.models.sync_queue import SyncQueueModel
from app.models.ticket import TicketModel

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, db: Session):
        self._db = db

    def enqueue(
        self,
        ticket_id: int,
        operation: SyncOperation,
        payload_json: str | None = None,
    ) -> SyncQueueModel | None:
        """
        Enqueue a sync event for the background worker.
        Skips if an identical pending/in_progress event already exists (deduplication).
        Skips create_task if the ticket already has a jira_task_id.
        """
        if operation == SyncOperation.CREATE_TASK:
            ticket = self._db.get(TicketModel, ticket_id)
            if ticket and ticket.jira_task_id:
                logger.debug(
                    "Skipping create_task enqueue — jira_task_id already set",
                    extra={"ticket_id": ticket_id},
                )
                return None

        existing = (
            self._db.query(SyncQueueModel)
            .filter(
                SyncQueueModel.ticket_id == ticket_id,
                SyncQueueModel.operation == operation.value,
                SyncQueueModel.status.in_(
                    [SyncStatus.PENDING.value, SyncStatus.IN_PROGRESS.value]
                ),
            )
            .first()
        )
        if existing:
            logger.debug(
                "Skipping duplicate sync enqueue",
                extra={"ticket_id": ticket_id, "operation": operation.value},
            )
            return None

        event = SyncQueueModel(
            ticket_id=ticket_id,
            operation=operation.value,
            payload_json=payload_json,
            status=SyncStatus.PENDING.value,
            attempt_count=0,
            created_at=datetime.now(timezone.utc),
        )
        self._db.add(event)
        self._db.commit()
        logger.info(
            "Sync event enqueued",
            extra={"ticket_id": ticket_id, "operation": operation.value, "sync_event_id": event.id},
        )
        return event
