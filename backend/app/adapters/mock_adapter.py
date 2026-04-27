"""
Mock sync adapter for local development and testing.
Logs all operations instead of calling external APIs.
Switch to real adapter by setting SYNC_ADAPTER=jira in .env.
"""

import logging
import uuid

from app.domain.interfaces import ExternalTaskRef, SyncAdapter

logger = logging.getLogger(__name__)


class MockSyncAdapter(SyncAdapter):
    """
    Logs sync operations locally. No external calls made.
    Useful for PoC demos without JIRA credentials.
    """

    def create_task(self, ticket_id, title, description, department, urgency,
                    cost, submitter_name, submitter_email, category, priority) -> ExternalTaskRef:
        mock_id = f"MOCK-{uuid.uuid4().hex[:6].upper()}"
        mock_url = f"https://mock-jira.local/browse/{mock_id}"
        logger.info(
            "MockAdapter: create_task",
            extra={"ticket_id": ticket_id, "mock_jira_id": mock_id, "title": title},
        )
        return ExternalTaskRef(external_id=mock_id, external_url=mock_url)

    def update_status(self, external_id: str, portal_status: str) -> None:
        logger.info(
            "MockAdapter: update_status",
            extra={"external_id": external_id, "portal_status": portal_status},
        )

    def add_comment(self, external_id: str, author_name: str,
                    body: str, is_internal: bool) -> None:
        if is_internal:
            return  # internal comments never synced
        logger.info(
            "MockAdapter: add_comment",
            extra={"external_id": external_id, "author": author_name},
        )

    def attach_file(self, external_id: str, filename: str,
                    file_path: str, mime_type: str) -> None:
        logger.info(
            "MockAdapter: attach_file",
            extra={"external_id": external_id, "filename": filename},
        )

    def get_task_url(self, external_id: str) -> str:
        return f"https://mock-jira.local/browse/{external_id}"
