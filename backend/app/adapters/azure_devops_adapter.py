"""
Azure DevOps adapter stub.
Implements the SyncAdapter interface for future Azure DevOps integration.
Selected when SYNC_ADAPTER=azure_devops.
"""

import logging

from app.core.config import Settings
from app.domain.exceptions import SyncAdapterError
from app.domain.interfaces import ExternalTaskRef, SyncAdapter

logger = logging.getLogger(__name__)


class AzureDevOpsAdapter(SyncAdapter):
    """
    Azure DevOps Work Items REST API adapter.
    Uses JSON Patch format for work item creation and updates.
    Authentication: Personal Access Token (PAT) via Basic Auth.
    """

    def __init__(self, settings: Settings):
        # TODO: load ADO-specific settings when implementing
        raise NotImplementedError(
            "AzureDevOpsAdapter is not yet implemented. "
            "Set SYNC_ADAPTER=jira to use the JIRA adapter."
        )

    def create_task(self, ticket_id, title, description, department, urgency,
                    cost, submitter_name, submitter_email, category, priority) -> ExternalTaskRef:
        raise SyncAdapterError("AzureDevOpsAdapter not implemented.")

    def update_status(self, external_id: str, portal_status: str) -> None:
        raise SyncAdapterError("AzureDevOpsAdapter not implemented.")

    def add_comment(self, external_id: str, author_name: str,
                    body: str, is_internal: bool) -> None:
        raise SyncAdapterError("AzureDevOpsAdapter not implemented.")

    def attach_file(self, external_id: str, filename: str,
                    file_path: str, mime_type: str) -> None:
        raise SyncAdapterError("AzureDevOpsAdapter not implemented.")

    def get_task_url(self, external_id: str) -> str:
        raise SyncAdapterError("AzureDevOpsAdapter not implemented.")
