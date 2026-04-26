"""
Notification service — writes in-portal notifications and sends emails.
Email failures are logged but never block the main request flow.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification import NotificationModel
from app.models.user import UserModel

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Session):
        self._db = db

    def notify(
        self,
        event_type: str,
        message: str,
        recipients: list[UserModel],
        ticket_id: int | None = None,
        ticket_url: str | None = None,
    ) -> None:
        """
        Write in-portal notification rows and send emails to all recipients.
        Email failures are caught and logged — they do not raise.
        """
        for user in recipients:
            self._write_in_portal(user.id, ticket_id, event_type, message)
            self._send_email(user.email, user.display_name, event_type, message, ticket_url)

    def _write_in_portal(
        self,
        recipient_id: int,
        ticket_id: int | None,
        event_type: str,
        message: str,
    ) -> None:
        notification = NotificationModel(
            recipient_id=recipient_id,
            ticket_id=ticket_id,
            event_type=event_type,
            message=message,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        self._db.add(notification)
        self._db.commit()

    def _send_email(
        self,
        to_email: str,
        display_name: str,
        event_type: str,
        message: str,
        ticket_url: str | None,
    ) -> None:
        """Fire-and-forget email. Failures are logged, not raised."""
        try:
            from app.adapters.smtp_adapter import SmtpAdapter
            SmtpAdapter().send(
                to=to_email,
                display_name=display_name,
                event_type=event_type,
                message=message,
                ticket_url=ticket_url,
            )
        except Exception as exc:
            logger.error(
                "Email notification failed",
                extra={"event_type": event_type, "error": str(exc)},
            )
