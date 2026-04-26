"""
Abstract interfaces for external integration adapters.
Adapters in app/adapters/ must implement these contracts.
Domain and service code depend only on these interfaces — never on concrete adapters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExternalTaskRef:
    """Reference to a task created in an external system (JIRA, Azure DevOps)."""
    external_id: str
    external_url: str


class SyncAdapter(ABC):
    """
    Interface for external task management system adapters.
    Implementations: JiraAdapter, AzureDevOpsAdapter.
    """

    @abstractmethod
    def create_task(self, ticket_id: str, title: str, description: str,
                    department: str, urgency: str, cost: float | None,
                    submitter_name: str, submitter_email: str,
                    category: str | None, priority: str | None) -> ExternalTaskRef:
        """Create a new task in the external system. Returns the external reference."""

    @abstractmethod
    def update_status(self, external_id: str, portal_status: str) -> None:
        """Transition the external task to the status mapped from portal_status."""

    @abstractmethod
    def add_comment(self, external_id: str, author_name: str,
                    body: str, is_internal: bool) -> None:
        """
        Add a comment to the external task.
        Internal comments must NOT be synced — callers are responsible for filtering.
        """

    @abstractmethod
    def attach_file(self, external_id: str, filename: str,
                    file_path: str, mime_type: str) -> None:
        """Attach a file to the external task."""

    @abstractmethod
    def get_task_url(self, external_id: str) -> str:
        """Return the browser URL for the external task."""
