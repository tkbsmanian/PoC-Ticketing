"""
Property-based tests — Properties 7, 9, 10.
Feature: internal-ticketing-system
"""

import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!!")
os.environ.setdefault("SYNC_ADAPTER", "mock")
os.environ.setdefault("JIRA_BASE_URL", "https://mock.atlassian.net")
os.environ.setdefault("JIRA_USER_EMAIL", "test@example.com")
os.environ.setdefault("JIRA_API_TOKEN", "mock-token")

from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.domain.enums import TicketStatus, UserRole

# Disable the 200ms deadline — DB setup per example is inherently slower
h_settings.register_profile("no_deadline", deadline=None, suppress_health_check=list(HealthCheck))
h_settings.load_profile("no_deadline")


def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _seed_user(db, email, role, dept_id):
    from app.models.user import UserModel
    from app.core.security import hash_password
    u = UserModel(
        email=email, display_name=email,
        password_hash=hash_password("pw"),
        role=role, department_id=dept_id, is_active=True,
    )
    db.add(u)
    db.commit()
    return u


def _seed_ticket(db, submitter_id, dept_id, status=TicketStatus.CLOSED.value):
    from app.models.ticket import TicketModel
    import uuid
    t = TicketModel(
        ticket_id=f"TKT-{uuid.uuid4().hex[:6].upper()}",
        title="T", description="D", urgency="Low",
        status=status, submitter_id=submitter_id,
        department_id=dept_id, director_approval_required=False,
    )
    db.add(t)
    db.commit()
    return t


# ── Property 7: Soft-delete restricts visibility without data loss ────────────

# Feature: internal-ticketing-system, Property 7: Soft-delete restricts visibility without data loss
@given(st.just(True))  # parameterised to run via hypothesis
def test_property_7_soft_delete_hides_ticket(_):
    from app.models.user import DepartmentModel
    from app.models.ticket import TicketModel
    from app.repositories.ticket_repository import TicketRepository
    from datetime import datetime, timezone

    db = make_db()
    dept = DepartmentModel(name="D", is_active=True)
    db.add(dept)
    db.commit()

    submitter = _seed_user(db, "s@t.com", UserRole.BUSINESS_USER.value, dept.id)
    ticket = _seed_ticket(db, submitter.id, dept.id, TicketStatus.CLOSED.value)

    # Soft-delete
    ticket.is_deleted = True
    ticket.deleted_at = datetime.now(timezone.utc)
    db.commit()

    # Business user should not see it
    repo = TicketRepository(db)
    items, total = repo.list_for_user(
        user_id=submitter.id,
        role=UserRole.BUSINESS_USER.value,
        department_id=dept.id,
    )
    assert total == 0
    assert all(t.id != ticket.id for t in items)

    # Data still in DB
    raw = db.get(TicketModel, ticket.id)
    assert raw is not None
    assert raw.is_deleted is True
    db.close()


# ── Property 9: Comment round-trip preserves content and authorship ───────────

# Feature: internal-ticketing-system, Property 9: Comment round-trip preserves content and authorship
@given(body=st.text(min_size=1, max_size=500).filter(lambda s: s.strip()))
def test_property_9_comment_round_trip(body):
    from app.models.user import DepartmentModel
    from app.models.comment import CommentModel

    db = make_db()
    dept = DepartmentModel(name="D", is_active=True)
    db.add(dept)
    db.commit()

    author = _seed_user(db, "a@t.com", UserRole.BUSINESS_USER.value, dept.id)
    ticket = _seed_ticket(db, author.id, dept.id, TicketStatus.IN_PROGRESS.value)

    comment = CommentModel(
        ticket_id=ticket.id,
        author_id=author.id,
        body=body,
        is_internal=False,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    retrieved = db.get(CommentModel, comment.id)
    assert retrieved is not None
    assert retrieved.body == body
    assert retrieved.author_id == author.id
    assert retrieved.created_at is not None
    db.close()


# ── Property 10: Ticket list is role-scoped ───────────────────────────────────

# Feature: internal-ticketing-system, Property 10: Ticket list is role-scoped
@given(
    role=st.sampled_from([
        UserRole.BUSINESS_USER.value,
        UserRole.IT_TRIAGE.value,
        UserRole.PLATFORM_ADMIN.value,
    ])
)
def test_property_10_ticket_list_role_scoped(role):
    from app.models.user import DepartmentModel
    from app.repositories.ticket_repository import TicketRepository

    db = make_db()
    dept = DepartmentModel(name="D", is_active=True)
    db.add(dept)
    db.commit()

    owner = _seed_user(db, "owner@t.com", UserRole.BUSINESS_USER.value, dept.id)
    other = _seed_user(db, "other@t.com", UserRole.BUSINESS_USER.value, dept.id)
    viewer = _seed_user(db, f"viewer_{role}@t.com", role, dept.id)

    # Create ticket owned by 'owner'
    ticket = _seed_ticket(db, owner.id, dept.id, TicketStatus.PENDING.value)

    repo = TicketRepository(db)
    items, total = repo.list_for_user(
        user_id=viewer.id,
        role=role,
        department_id=dept.id,
    )

    if role == UserRole.BUSINESS_USER.value:
        # Viewer is not the owner — should see 0 tickets
        assert all(t.submitter_id == viewer.id for t in items)
    else:
        # IT roles see all tickets
        assert any(t.id == ticket.id for t in items)

    db.close()
