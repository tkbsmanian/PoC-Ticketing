"""
Approval routing rules.
Single source of truth for director approval requirement computation.
No I/O, no framework imports.
"""

from app.domain.enums import UrgencyLevel

# Urgency levels that trigger Director approval regardless of cost.
DIRECTOR_REQUIRED_URGENCIES: frozenset[UrgencyLevel] = frozenset(
    {UrgencyLevel.HIGH, UrgencyLevel.CRITICAL}
)


def requires_director_approval(
    urgency: UrgencyLevel,
    cost: float | None,
) -> bool:
    """
    Director approval is required when:
      - Any cost amount is entered (cost > 0), OR
      - Urgency is High or Critical.

    This is the single source of truth. All callers must use this function.
    """
    has_cost = cost is not None and cost > 0
    high_urgency = urgency in DIRECTOR_REQUIRED_URGENCIES
    return has_cost or high_urgency
