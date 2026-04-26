---
inclusion: always
---

# Integration Boundary Standards

All external integrations must be isolated behind adapter interfaces. No service or domain code may directly call external APIs.

## The SyncAdapter Interface

All external task management integrations (JIRA, Azure DevOps) MUST implement the interface defined in `backend/app/domain/interfaces.py`:

```python
from abc import ABC, abstractmethod
from app.domain.entities import Ticket, Comment, Attachment, ExternalTaskRef

class SyncAdapter(ABC):
    @abstractmethod
    def create_task(self, ticket: Ticket) -> ExternalTaskRef: ...

    @abstractmethod
    def update_status(self, external_id: str, portal_status: str) -> None: ...

    @abstractmethod
    def add_comment(self, external_id: str, comment: Comment) -> None: ...

    @abstractmethod
    def attach_file(self, external_id: str, attachment: Attachment) -> None: ...

    @abstractmethod
    def get_task_url(self, external_id: str) -> str: ...
```

## Adapter Selection

The active adapter is instantiated once at application startup in `core/dependencies.py`:

```python
def get_sync_adapter() -> SyncAdapter:
    adapter_name = settings.SYNC_ADAPTER  # "jira" or "azure_devops"
    if adapter_name == "jira":
        return JiraAdapter(settings)
    elif adapter_name == "azure_devops":
        return AzureDevOpsAdapter(settings)
    raise ValueError(f"Unknown SYNC_ADAPTER: {adapter_name}")
```

The adapter instance is injected into `SyncWorker` via dependency injection — never instantiated inline in service code.

## JIRA Adapter Rules

- ALL JIRA REST API calls MUST go through `adapters/jira_adapter.py` — no `httpx` or `requests` calls to JIRA URLs anywhere else
- The `to_adf()` utility for Atlassian Document Format conversion MUST live in `adapters/jira_utils.py`
- JIRA status/priority mapping tables MUST be defined as constants in `adapters/jira_mappings.py` — not inline dicts
- Reporter lookup (email → JIRA AccountId) MUST be cached in the adapter instance — not re-fetched per request
- Create metadata discovery MUST be cached with a 1-hour TTL — not fetched on every issue creation
- Transition ID lookup MUST be dynamic (fetched from JIRA) — never hardcoded

## Azure DevOps Adapter Rules

- ALL Azure DevOps REST API calls MUST go through `adapters/azure_devops_adapter.py`
- JSON Patch document construction MUST live in `adapters/azure_devops_utils.py`
- Field mappings (portal priority → ADO priority integer) MUST be defined as constants in `adapters/azure_devops_mappings.py`

## SMTP / Notification Adapter Rules

- ALL email sending MUST go through `adapters/smtp_adapter.py`
- Email templates MUST be defined as string constants in `adapters/email_templates.py` — not inline f-strings in service code
- SMTP failures MUST be caught and logged — they MUST NOT propagate exceptions that block the main request flow

## What Adapters Must NOT Do

- Adapters MUST NOT import from `services/`, `api/`, or `repositories/`
- Adapters MUST NOT write to the database directly — they return results to the service layer which handles persistence
- Adapters MUST NOT contain business logic — only protocol translation (portal concepts → external API concepts)
- Adapters MUST NOT raise HTTP exceptions (FastAPI `HTTPException`) — raise domain-specific exceptions that the service layer handles

## Sync Queue Contract

Services enqueue sync events by calling `SyncWorker.enqueue(ticket_id, operation, payload)`. They MUST NOT call adapter methods directly. The worker owns the retry loop and failure handling.

Operations are typed strings: `create_task`, `update_status`, `add_comment`, `attach_file`. No other operation strings are valid.
