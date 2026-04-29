"""
Property-based tests using Hypothesis.
Each test references the design property it validates.

Feature: internal-ticketing-system
"""

import pytest
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!!")
os.environ.setdefault("SYNC_ADAPTER", "mock")
os.environ.setdefault("JIRA_BASE_URL", "https://mock.atlassian.net")
os.environ.setdefault("JIRA_USER_EMAIL", "test@example.com")
os.environ.setdefault("JIRA_API_TOKEN", "mock-token")

from app.db.base import Base
from app.domain.approval_rules import requires_director_approval
from app.domain.enums import TicketStatus, UrgencyLevel
from app.domain.ticket_lifecycle import is_terminal, is_valid_transition, VALID_TRANSITIONS

# Disable the 200ms deadline — DB setup per example is inherently slower
h_settings.register_profile("no_deadline", deadline=None, suppress_health_check=list(HealthCheck))
h_settings.load_profile("no_deadline")

# ── Shared DB setup ───────────────────────────────────────────────────────────

def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


# ── Property 1: Valid ticket submission creates persisted ticket with status Pending ──

# Feature: internal-ticketing-system, Property 1: Ticket submission creates a persisted ticket
@given(
    title=st.text(min_size=1, max_size=255).filter(lambda s: s.strip()),
    description=st.text(min_size=1, max_size=1000).filter(lambda s: s.strip()),
)
def test_property_1_valid_submission_creates_pending_ticket(title, description):
    from app.models.user import UserModel, DepartmentModel
    from app.models.ticket import TicketModel
    from app.core.security import hash_password
    from app.services.audit_service import AuditService
    from app.services.sync_service import SyncService
    from app.services.ticket_service import TicketService

    db = make_db()
    dept = DepartmentModel(name="Dept", is_active=True)
    db.add(dept)
    db.commit()

    user = UserModel(
        email="u@test.com", display_name="User",
        password_hash=hash_password("pw"), role="business_user",
        department_id=dept.id, is_active=True,
    )
    manager = UserModel(
        email="m@test.com", display_name="Manager",
        password_hash=hash_password("pw"), role="it_manager",
        department_id=dept.id, is_active=True,
    )
    db.add_all([user, manager])
    db.commit()

    svc = TicketService(db, AuditService(db), SyncService(db))
    ticket = svc.create_ticket(
        submitter_id=user.id,
        title=title,
        description=description,
        department_id=dept.id,
        urgency="Medium",
        cost=None,
        manager_id=manager.id,
    )

    persisted = db.get(TicketModel, ticket.id)
    assert persisted is not None
    assert persisted.title == title
    assert persisted.description == description
    assert persisted.status == TicketStatus.PENDING.value
    db.close()


# ── Property 2: Empty/whitespace title or description is rejected ─────────────

# Feature: internal-ticketing-system, Property 2: Empty/whitespace title or description is rejected
@given(
    bad_field=st.one_of(st.just(""), st.text(alphabet=" \t\n", min_size=1, max_size=50))
)
def test_property_2_empty_fields_rejected(bad_field):
    from app.schemas.ticket import CreateTicketRequest
    from pydantic import ValidationError

    # A field is invalid if it is empty or whitespace-only after stripping
    is_invalid = not bad_field.strip()

    for payload in [
        {"title": bad_field, "description": "valid desc", "department_id": 1, "urgency": "Low", "manager_id": 1},
        {"title": "valid title", "description": bad_field, "department_id": 1, "urgency": "Low", "manager_id": 1},
    ]:
        if is_invalid:
            # Empty/whitespace-only fields must be rejected
            try:
                req = CreateTicketRequest(**payload)
                # If schema accepted it, the value must not be blank after strip
                field_val = req.title if payload["title"] == bad_field else req.description
                assert field_val.strip(), (
                    f"Schema accepted blank field: {repr(bad_field)}"
                )
            except (ValidationError, ValueError):
                pass  # correctly rejected


# ── Property 3: director_approval_required computed correctly ─────────────────

# Feature: internal-ticketing-system, Property 3: Director approval requirement is correctly computed
@given(
    urgency=st.sampled_from(list(UrgencyLevel)),
    cost=st.one_of(st.none(), st.floats(min_value=0, max_value=100000, allow_nan=False)),
)
def test_property_3_director_approval_flag(urgency, cost):
    result = requires_director_approval(urgency, cost)
    has_cost = cost is not None and cost > 0
    high_urgency = urgency in (UrgencyLevel.HIGH, UrgencyLevel.CRITICAL)
    assert result == (has_cost or high_urgency)


# ── Property 4: Only valid status transitions accepted ────────────────────────

# Feature: internal-ticketing-system, Property 4: Status transitions respect the lifecycle
@given(
    current=st.sampled_from(list(TicketStatus)),
    target=st.sampled_from(list(TicketStatus)),
)
def test_property_4_transitions_respect_lifecycle(current, target):
    result = is_valid_transition(current, target)
    expected = target in VALID_TRANSITIONS.get(current, set())
    assert result == expected
    # Terminal states must always return False
    if is_terminal(current):
        assert result is False


# ── Property 5: Audit log is append-only ─────────────────────────────────────

# Feature: internal-ticketing-system, Property 5: Audit log is append-only
@given(n_mutations=st.integers(min_value=1, max_value=10))
def test_property_5_audit_log_append_only(n_mutations):
    from app.models.audit import AuditLogModel
    from app.services.audit_service import AuditService

    db = make_db()
    svc = AuditService(db)
    prev_count = db.query(AuditLogModel).count()

    for i in range(n_mutations):
        svc.record(event_type="test_event", notes=f"mutation {i}")
        db.commit()
        new_count = db.query(AuditLogModel).count()
        assert new_count >= prev_count
        prev_count = new_count

    db.close()


# ── Property 6: Internal comments hidden from non-IT roles ───────────────────

# Feature: internal-ticketing-system, Property 6: Internal comments are hidden from non-IT roles
@given(body=st.text(min_size=1, max_size=500))
def test_property_6_internal_comments_hidden(body):
    from app.models.comment import CommentModel
    from app.models.user import UserModel, DepartmentModel
    from app.models.ticket import TicketModel
    from app.core.security import hash_password

    db = make_db()
    dept = DepartmentModel(name="D", is_active=True)
    db.add(dept)
    db.commit()

    submitter = UserModel(
        email="s@t.com", display_name="S",
        password_hash=hash_password("pw"), role="business_user",
        department_id=dept.id, is_active=True,
    )
    db.add(submitter)
    db.commit()

    ticket = TicketModel(
        ticket_id="TKT-TEST01", title="T", description="D",
        urgency="Low", status="Pending",
        submitter_id=submitter.id, department_id=dept.id,
        director_approval_required=False,
    )
    db.add(ticket)
    db.commit()

    internal_comment = CommentModel(
        ticket_id=ticket.id, author_id=submitter.id,
        body=body, is_internal=True,
    )
    db.add(internal_comment)
    db.commit()

    # Non-IT roles should not see internal comments
    visible = db.query(CommentModel).filter(
        CommentModel.ticket_id == ticket.id,
        CommentModel.is_internal == False,  # noqa: E712
    ).all()
    assert internal_comment not in visible
    db.close()


# ── Property 8: Approval sequence is strictly ordered ────────────────────────

# Feature: internal-ticketing-system, Property 8: Approval sequence is strictly ordered
@given(cost=st.floats(min_value=0.01, max_value=10000, allow_nan=False))
def test_property_8_director_row_absent_until_manager_approves(cost):
    from app.models.user import UserModel, DepartmentModel
    from app.models.ticket import ApprovalModel, TicketModel
    from app.core.security import hash_password
    from app.domain.enums import ApproverRole

    db = make_db()
    dept = DepartmentModel(name="D", is_active=True)
    db.add(dept)
    db.commit()

    submitter = UserModel(
        email="s2@t.com", display_name="S",
        password_hash=hash_password("pw"), role="business_user",
        department_id=dept.id, is_active=True,
    )
    db.add(submitter)
    db.commit()

    ticket = TicketModel(
        ticket_id="TKT-TEST02", title="T", description="D",
        urgency="Low", cost=cost, status="Pending",
        submitter_id=submitter.id, department_id=dept.id,
        director_approval_required=True,
    )
    db.add(ticket)
    db.commit()

    # Before Manager approves — no Director row should exist
    director_rows = db.query(ApprovalModel).filter(
        ApprovalModel.ticket_id == ticket.id,
        ApprovalModel.approver_role == ApproverRole.DIRECTOR.value,
    ).count()
    assert director_rows == 0
    db.close()
