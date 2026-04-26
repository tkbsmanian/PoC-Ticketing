---
inclusion: always
---

# Domain Logic Standards

Business rules live exclusively in `backend/app/domain/`. Nothing outside that package may re-implement or duplicate domain logic.

## What Belongs in Domain

- Ticket lifecycle: valid status transitions, terminal state detection
- Approval routing: `director_approval_required` computation, sequential step ordering
- Role permission checks: what actions each role may perform on a ticket in a given state
- Field validation rules beyond Pydantic schema constraints (e.g., cost must be non-negative)
- Ticket ID generation format
- Comment visibility rules (internal vs public per role)
- Soft-delete eligibility (only Closed or Rejected tickets)
- Re-open eligibility (only Resolved, not Closed)

## Ticket Lifecycle Module

`domain/ticket_lifecycle.py` MUST define the transition table as a constant — not scattered if/else logic:

```python
from app.domain.enums import TicketStatus

# Maps each status to the set of statuses it can transition TO
VALID_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.PENDING: {
        TicketStatus.APPROVED,
        TicketStatus.REJECTED,
        TicketStatus.REMOVED,
    },
    TicketStatus.APPROVED: {
        TicketStatus.IN_REVIEW,
        TicketStatus.REJECTED,  # Director rejection
    },
    TicketStatus.IN_REVIEW: {
        TicketStatus.IN_PROGRESS,
        TicketStatus.REMOVED,
    },
    TicketStatus.IN_PROGRESS: {
        TicketStatus.RESOLVED,
        TicketStatus.IN_REVIEW,
    },
    TicketStatus.RESOLVED: {
        TicketStatus.CLOSED,
        TicketStatus.IN_PROGRESS,  # re-open
    },
    # Terminal states — no outbound transitions
    TicketStatus.CLOSED: set(),
    TicketStatus.REJECTED: set(),
    TicketStatus.REMOVED: set(),
}

def is_valid_transition(current: TicketStatus, target: TicketStatus) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())

def is_terminal(status: TicketStatus) -> bool:
    return VALID_TRANSITIONS.get(status) == set()
```

Any code that needs to validate a status transition MUST call `is_valid_transition()` — never re-implement the check inline.

## Director Approval Computation

`domain/approval_rules.py` MUST define this as a pure function:

```python
from app.domain.enums import UrgencyLevel

DIRECTOR_REQUIRED_URGENCIES = {UrgencyLevel.HIGH, UrgencyLevel.CRITICAL}

def requires_director_approval(urgency: UrgencyLevel, cost: float | None) -> bool:
    """
    Director approval is required if any cost is entered OR
    urgency is High or Critical.
    """
    has_cost = cost is not None and cost > 0
    high_urgency = urgency in DIRECTOR_REQUIRED_URGENCIES
    return has_cost or high_urgency
```

This function is the single source of truth. It MUST be used by `TicketService` at submission time and tested exhaustively in `tests/unit/test_approval_rules.py`.

## Enums

All status, role, urgency, and priority values MUST be defined as Python `Enum` classes in `domain/enums.py`. String literals for these values are forbidden outside of serialization layers (Pydantic schemas, ORM models).

```python
from enum import Enum

class TicketStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    IN_REVIEW = "In Review"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    REJECTED = "Rejected"
    REMOVED = "Removed"

class UserRole(str, Enum):
    BUSINESS_USER = "business_user"
    IT_MANAGER = "it_manager"
    IT_TRIAGE = "it_triage"
    PLATFORM_ADMIN = "platform_admin"
    AUDITOR = "auditor"

class UrgencyLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class PriorityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
```

## Domain Exceptions

Domain-specific exceptions MUST be defined in `domain/exceptions.py` and raised by domain/service code. API routers catch these and map them to HTTP responses.

```python
class InvalidTransitionError(Exception):
    """Raised when a status transition is not permitted."""

class UnauthorizedActionError(Exception):
    """Raised when a role attempts a prohibited action."""

class TicketNotFoundError(Exception):
    """Raised when a ticket does not exist or is not visible to the caller."""

class ApprovalNotAssignedError(Exception):
    """Raised when an approver attempts to act on an approval not assigned to them."""

class SyncAdapterError(Exception):
    """Raised by adapters for permanent (non-retryable) failures."""

class SyncTransientError(Exception):
    """Raised by adapters for transient (retryable) failures."""
```

The API layer maps these to HTTP status codes in a central exception handler — not in individual route handlers.

## What Domain Must NOT Contain

- No SQLAlchemy imports or database queries
- No FastAPI imports or HTTP concerns
- No `httpx`, `requests`, or any network I/O
- No references to JIRA, Azure DevOps, or any external system
- No environment variable reads (`os.environ`, `settings`)
- No logging setup (domain functions may accept a logger as a parameter if needed, but must not configure one)
