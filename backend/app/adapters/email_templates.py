"""
Email message templates — all notification text defined as constants here.
Never use inline f-strings for email content in service code.
"""

EVENT_SUBJECTS = {
    "approval_required": "Action Required: Request Awaiting Your Approval",
    "approval_decision": "Update: Your Request Has Been Reviewed",
    "status_changed": "Update: Your Request Status Has Changed",
    "comment_added": "New Comment on Your Request",
    "ticket_approved": "New Ticket Ready for IT Review",
    "ticket_reopened": "Ticket Re-opened",
    "approval_timeout": "Reminder: Approval Pending",
    "password_reset_requested": "Password Reset Request",
    "sync_failed": "JIRA Sync Failure — Action Required",
}

FOOTER = "\n\nThis is an automated message from the Internal Ticketing Portal."


def build_email(
    display_name: str,
    event_type: str,
    message: str,
    ticket_url: str | None = None,
) -> tuple[str, str]:
    """Return (subject, body) for a notification email."""
    subject = EVENT_SUBJECTS.get(event_type, "Notification from IT Request Portal")
    body_parts = [f"Hello {display_name},", "", message]
    if ticket_url:
        body_parts += ["", f"View details: {ticket_url}"]
    body_parts.append(FOOTER)
    return subject, "\n".join(body_parts)
