"""
Unit tests for domain/approval_rules.py
Tests all 8 urgency × cost combinations.
"""

import pytest
from app.domain.approval_rules import requires_director_approval
from app.domain.enums import UrgencyLevel


@pytest.mark.parametrize("urgency,cost,expected", [
    # No cost, low urgency → no director
    (UrgencyLevel.LOW,      None,  False),
    (UrgencyLevel.LOW,      0,     False),
    (UrgencyLevel.MEDIUM,   None,  False),
    (UrgencyLevel.MEDIUM,   0,     False),
    # High/Critical urgency → director required regardless of cost
    (UrgencyLevel.HIGH,     None,  True),
    (UrgencyLevel.HIGH,     0,     True),
    (UrgencyLevel.CRITICAL, None,  True),
    (UrgencyLevel.CRITICAL, 0,     True),
    # Any cost > 0 → director required regardless of urgency
    (UrgencyLevel.LOW,      100,   True),
    (UrgencyLevel.MEDIUM,   0.01,  True),
    (UrgencyLevel.HIGH,     500,   True),
    (UrgencyLevel.CRITICAL, 1,     True),
])
def test_requires_director_approval(urgency, cost, expected):
    assert requires_director_approval(urgency, cost) == expected
