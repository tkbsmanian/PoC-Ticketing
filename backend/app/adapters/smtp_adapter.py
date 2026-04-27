"""
SMTP adapter — sends plain-text notification emails.
All email sending goes through this module exclusively.
Failures are logged and never raised to callers.
"""

import logging
import smtplib
from email.mime.text import MIMEText

from app.adapters.email_templates import build_email
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SmtpAdapter:
    def send(
        self,
        to: str,
        display_name: str,
        event_type: str,
        message: str,
        ticket_url: str | None = None,
    ) -> None:
        subject, body = build_email(display_name, event_type, message, ticket_url)
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_ADDRESS
        msg["To"] = to

        try:
            if settings.SMTP_USE_TLS:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls()
                    if settings.SMTP_USER:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    if settings.SMTP_USER:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
        except Exception as exc:
            logger.error(
                "Email send failed",
                extra={"event_type": event_type, "error": str(exc)},
            )
