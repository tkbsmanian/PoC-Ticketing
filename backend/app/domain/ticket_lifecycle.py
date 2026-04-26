"""
Ticket lifecycle rules.
Single source of truth for valid status transitions and terminal state detection.
No I/O, no framework imports.
"""

from app.domain.enums import TicketStatus

# Maps each status to the set of statuses it may transition TO.
# Terminal states map to an empty set.
VALID_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.PENDING: {
        TicketStatus.APPROVED,
        TicketStatus.REJECTED,
        TicketStatus.REMOVED,
    },
    TicketStatus.APPROVED: {
        TicketStatus.IN_REVIEW,
        TicketStatus.REJECTED,  # Director rejection step
    },
    TicketStatus.IN_REVIEW: {
        TicketStatus.IN_PROGRESS,
        TicketStatus.REMOVED,
    },
    TicketStatus.IN_PROGRESS: {
        TicketStatus.RESOLVED,
        TicketStatus.IN_REVIEW,  # send back
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
    """Return True if transitioning from current to target is permitted."""
    return target in VALID_TRANSITIONS.get(current, set())


def is_terminal(status: TicketStatus) -> bool:
    """Return True if the status has no valid outbound transitions."""
    return VALID_TRANSITIONS.get(status, set()) == set()


def get_valid_next_statuses(current: TicketStatus) -> set[TicketStatus]:
    """Return the set of statuses reachable from the current status."""
    return VALID_TRANSITIONS.get(current, set())


def is_deletable(status: TicketStatus) -> bool:
    """Return True if a ticket in this status may be soft-deleted by Platform Admin."""
    return status in {TicketStatus.CLOSED, TicketStatus.REJECTED}


def is_removable_by_submitter(status: TicketStatus) -> bool:
    """Return True if the submitter may withdraw (Remove) a ticket in this status."""
    return status in {TicketStatus.PENDING, TicketStatus.IN_REVIEW}


def is_reopenable(status: TicketStatus) -> bool:
    """Return True if a ticket in this status may be re-opened."""
    return status == TicketStatus.RESOLVED
