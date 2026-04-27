"""
Unit tests for domain/ticket_lifecycle.py
Tests every valid and invalid transition pair.
"""

import pytest
from app.domain.enums import TicketStatus
from app.domain.ticket_lifecycle import (
    get_valid_next_statuses,
    is_deletable,
    is_removable_by_submitter,
    is_reopenable,
    is_terminal,
    is_valid_transition,
)

# ── Valid transitions ─────────────────────────────────────────────────────────

VALID_PAIRS = [
    (TicketStatus.PENDING,      TicketStatus.APPROVED),
    (TicketStatus.PENDING,      TicketStatus.REJECTED),
    (TicketStatus.PENDING,      TicketStatus.REMOVED),
    (TicketStatus.APPROVED,     TicketStatus.IN_REVIEW),
    (TicketStatus.APPROVED,     TicketStatus.REJECTED),
    (TicketStatus.IN_REVIEW,    TicketStatus.IN_PROGRESS),
    (TicketStatus.IN_REVIEW,    TicketStatus.REMOVED),
    (TicketStatus.IN_PROGRESS,  TicketStatus.RESOLVED),
    (TicketStatus.IN_PROGRESS,  TicketStatus.IN_REVIEW),
    (TicketStatus.RESOLVED,     TicketStatus.CLOSED),
    (TicketStatus.RESOLVED,     TicketStatus.IN_PROGRESS),
]

@pytest.mark.parametrize("current,target", VALID_PAIRS)
def test_valid_transition(current, target):
    assert is_valid_transition(current, target) is True


# ── Invalid transitions ───────────────────────────────────────────────────────

INVALID_PAIRS = [
    # Terminal states reject everything
    (TicketStatus.CLOSED,       TicketStatus.IN_PROGRESS),
    (TicketStatus.CLOSED,       TicketStatus.RESOLVED),
    (TicketStatus.CLOSED,       TicketStatus.PENDING),
    (TicketStatus.REJECTED,     TicketStatus.APPROVED),
    (TicketStatus.REJECTED,     TicketStatus.PENDING),
    (TicketStatus.REMOVED,      TicketStatus.PENDING),
    (TicketStatus.REMOVED,      TicketStatus.IN_REVIEW),
    # Skipping states
    (TicketStatus.PENDING,      TicketStatus.IN_PROGRESS),
    (TicketStatus.PENDING,      TicketStatus.CLOSED),
    (TicketStatus.APPROVED,     TicketStatus.RESOLVED),
    (TicketStatus.IN_REVIEW,    TicketStatus.RESOLVED),
    (TicketStatus.IN_REVIEW,    TicketStatus.CLOSED),
    (TicketStatus.IN_PROGRESS,  TicketStatus.CLOSED),
    (TicketStatus.RESOLVED,     TicketStatus.REJECTED),
]

@pytest.mark.parametrize("current,target", INVALID_PAIRS)
def test_invalid_transition(current, target):
    assert is_valid_transition(current, target) is False


# ── Terminal states ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("status", [
    TicketStatus.CLOSED, TicketStatus.REJECTED, TicketStatus.REMOVED
])
def test_is_terminal(status):
    assert is_terminal(status) is True


@pytest.mark.parametrize("status", [
    TicketStatus.PENDING, TicketStatus.APPROVED,
    TicketStatus.IN_REVIEW, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED
])
def test_not_terminal(status):
    assert is_terminal(status) is False


# ── Deletable ─────────────────────────────────────────────────────────────────

def test_closed_is_deletable():
    assert is_deletable(TicketStatus.CLOSED) is True

def test_rejected_is_deletable():
    assert is_deletable(TicketStatus.REJECTED) is True

@pytest.mark.parametrize("status", [
    TicketStatus.PENDING, TicketStatus.APPROVED,
    TicketStatus.IN_REVIEW, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED
])
def test_non_terminal_not_deletable(status):
    assert is_deletable(status) is False


# ── Removable by submitter ────────────────────────────────────────────────────

def test_pending_removable():
    assert is_removable_by_submitter(TicketStatus.PENDING) is True

def test_in_review_removable():
    assert is_removable_by_submitter(TicketStatus.IN_REVIEW) is True

@pytest.mark.parametrize("status", [
    TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED,
    TicketStatus.CLOSED, TicketStatus.REJECTED
])
def test_not_removable(status):
    assert is_removable_by_submitter(status) is False


# ── Reopenable ────────────────────────────────────────────────────────────────

def test_resolved_is_reopenable():
    assert is_reopenable(TicketStatus.RESOLVED) is True

def test_closed_not_reopenable():
    assert is_reopenable(TicketStatus.CLOSED) is False
