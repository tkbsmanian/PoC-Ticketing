"""
JIRA Cloud field mapping constants.
All portal → JIRA value translations are defined here as constants.
Never use inline dicts in adapter code.
"""

# Portal status → JIRA status name (custom statuses configured in JIRA project)
PORTAL_STATUS_TO_JIRA: dict[str, str] = {
    "Pending": "Pending",
    "Approved": "Approved",
    "In Review": "In Review",
    "In Progress": "In Progress",
    "Resolved": "Resolved",
    "Closed": "Closed",
    "Rejected": "Rejected",
    "Removed": "Removed",
}

# Portal priority → JIRA priority name
# Note: JIRA Cloud uses "Highest" not "Critical"
PORTAL_PRIORITY_TO_JIRA: dict[str, str] = {
    "Low": "Low",
    "Medium": "Medium",
    "High": "High",
    "Critical": "Highest",
}

# JIRA priority name → portal priority (for any future read-back)
JIRA_PRIORITY_TO_PORTAL: dict[str, str] = {v: k for k, v in PORTAL_PRIORITY_TO_JIRA.items()}

# MIME types allowed for attachment upload
ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/gif",
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
)
