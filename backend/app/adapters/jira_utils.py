"""
JIRA Cloud utility functions.
ADF conversion and payload construction helpers.
"""


def to_adf(text: str) -> dict:
    """
    Convert a plain text string to minimal valid Atlassian Document Format (ADF).
    Preserves newlines as separate paragraphs.
    JIRA Cloud requires ADF for the description and comment body fields.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        paragraphs = [""]
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": para}],
            }
            for para in paragraphs
        ],
    }


def truncate_summary(ticket_id: str, title: str, max_length: int = 255) -> str:
    """
    Build a JIRA issue summary from ticket_id and title.
    Truncates to max_length characters.
    """
    prefix = f"[{ticket_id}] "
    available = max_length - len(prefix)
    truncated_title = title[:available] if len(title) > available else title
    return f"{prefix}{truncated_title}"


def build_labels(
    ticket_id: str,
    department: str,
    urgency: str,
    category: str | None = None,
    cost: float | None = None,
    director_required: bool = False,
) -> list[str]:
    """
    Build the JIRA labels list from portal ticket fields.
    Labels are the primary mechanism for storing portal metadata in JIRA
    without requiring custom field configuration.
    """
    labels = [
        f"portal-id:{ticket_id}",
        f"dept:{department}",
        f"urgency:{urgency}",
    ]
    if category:
        labels.append(f"category:{category}")
    if cost and cost > 0:
        labels.append("cost:yes")
    if director_required:
        labels.append("director-approval:required")
    return labels
