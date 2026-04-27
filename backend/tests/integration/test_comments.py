"""
Integration tests for comments endpoint.
"""

from tests.conftest import login
from app.models.ticket import TicketModel
from app.models.comment import CommentModel


def _create_ticket_direct(db, submitter_id, dept_id, status="In Progress"):
    """Create a ticket directly in DB for test setup."""
    import uuid
    t = TicketModel(
        ticket_id=f"TKT-{uuid.uuid4().hex[:6].upper()}",
        title="Test", description="Desc",
        urgency="Low", status=status,
        submitter_id=submitter_id, department_id=dept_id,
        director_approval_required=False,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


class TestComments:
    def test_public_comment_visible_to_all(
        self, client, business_user, it_triage_user, manager_user, dept, db
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id)

        # IT adds public comment
        login(client, it_triage_user.email)
        resp = client.post(
            f"/tickets/{ticket.id}/comments",
            json={"body": "Working on it", "is_internal": False},
        )
        assert resp.status_code == 201

        # Business user can see it
        login(client, business_user.email)
        comments = client.get(f"/tickets/{ticket.id}/comments").json()
        assert any(c["body"] == "Working on it" for c in comments)

    def test_internal_comment_hidden_from_business_user(
        self, client, business_user, it_triage_user, dept, db
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id)

        login(client, it_triage_user.email)
        resp = client.post(
            f"/tickets/{ticket.id}/comments",
            json={"body": "Internal note", "is_internal": True},
        )
        assert resp.status_code == 201

        # Business user cannot see internal comment
        login(client, business_user.email)
        comments = client.get(f"/tickets/{ticket.id}/comments").json()
        assert not any(c["body"] == "Internal note" for c in comments)

    def test_internal_comment_visible_to_it(
        self, client, business_user, it_triage_user, dept, db
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id)

        login(client, it_triage_user.email)
        client.post(
            f"/tickets/{ticket.id}/comments",
            json={"body": "IT only note", "is_internal": True},
        )

        comments = client.get(f"/tickets/{ticket.id}/comments").json()
        assert any(c["body"] == "IT only note" for c in comments)

    def test_comment_on_closed_ticket_returns_403(
        self, client, business_user, dept, db
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id, status="Closed")

        login(client, business_user.email)
        resp = client.post(
            f"/tickets/{ticket.id}/comments",
            json={"body": "Too late", "is_internal": False},
        )
        assert resp.status_code == 403

    def test_business_user_cannot_post_internal_comment(
        self, client, business_user, dept, db
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id)

        login(client, business_user.email)
        resp = client.post(
            f"/tickets/{ticket.id}/comments",
            json={"body": "Trying internal", "is_internal": True},
        )
        assert resp.status_code == 403

    def test_auditor_cannot_post_comment(
        self, client, business_user, dept, db
    ):
        from app.models.user import UserModel
        from app.core.security import hash_password
        auditor = UserModel(
            email="aud@example.com", display_name="Auditor",
            password_hash=hash_password("password123"),
            role="auditor", department_id=dept.id, is_active=True,
        )
        db.add(auditor)
        db.commit()

        ticket = _create_ticket_direct(db, business_user.id, dept.id)
        login(client, "aud@example.com")
        resp = client.post(
            f"/tickets/{ticket.id}/comments",
            json={"body": "Auditor comment", "is_internal": False},
        )
        assert resp.status_code == 403
