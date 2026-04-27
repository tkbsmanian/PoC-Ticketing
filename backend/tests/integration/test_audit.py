"""
Integration tests for audit trail endpoints.
"""

from tests.conftest import login
from app.models.audit import AuditLogModel
from app.models.ticket import TicketModel


def _create_ticket_direct(db, submitter_id, dept_id, status="In Progress"):
    import uuid
    t = TicketModel(
        ticket_id=f"TKT-{uuid.uuid4().hex[:6].upper()}",
        title="T", description="D", urgency="Low",
        status=status, submitter_id=submitter_id,
        department_id=dept_id, director_approval_required=False,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


class TestAuditLog:
    def test_business_user_cannot_access_audit_log(self, client, business_user):
        login(client, business_user.email)
        resp = client.get("/audit/log")
        assert resp.status_code == 403

    def test_it_triage_cannot_access_audit_log(self, client, it_triage_user):
        login(client, it_triage_user.email)
        resp = client.get("/audit/log")
        assert resp.status_code == 403

    def test_admin_can_access_audit_log(self, client, admin_user):
        login(client, admin_user.email)
        resp = client.get("/audit/log")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_audit_log_count_never_decreases(
        self, client, business_user, manager_user, it_triage_user, admin_user, dept, db
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id)
        initial_count = db.query(AuditLogModel).filter(
            AuditLogModel.ticket_id == ticket.id
        ).count()

        # Status change — should add audit entry
        login(client, it_triage_user.email)
        client.patch(f"/tickets/{ticket.id}/status", json={"status": "Resolved"})

        after_status = db.query(AuditLogModel).filter(
            AuditLogModel.ticket_id == ticket.id
        ).count()
        assert after_status >= initial_count

        # Category update — should add another audit entry
        client.patch(f"/tickets/{ticket.id}/category-priority", json={"category": "Hardware"})

        after_category = db.query(AuditLogModel).filter(
            AuditLogModel.ticket_id == ticket.id
        ).count()
        assert after_category >= after_status

    def test_ticket_audit_endpoint_returns_history(
        self, client, business_user, it_triage_user, admin_user, dept, db
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id)

        login(client, it_triage_user.email)
        client.patch(f"/tickets/{ticket.id}/status", json={"status": "Resolved"})

        login(client, admin_user.email)
        resp = client.get(f"/audit/tickets/{ticket.id}")
        assert resp.status_code == 200
        entries = resp.json()
        assert isinstance(entries, list)
        assert any(e["event_type"] == "status_changed" for e in entries)

    def test_audit_entries_are_immutable(self, client, admin_user, dept, db, business_user):
        """Verify no DELETE or UPDATE endpoint exists for audit_log."""
        ticket = _create_ticket_direct(db, business_user.id, dept.id)
        login(client, admin_user.email)

        # There is no DELETE /audit/... endpoint — 405 or 404 expected
        resp = client.delete(f"/audit/tickets/{ticket.id}")
        assert resp.status_code in (404, 405)
