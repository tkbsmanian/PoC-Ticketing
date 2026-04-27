"""
Integration tests for notifications.
"""

from unittest.mock import patch
from tests.conftest import login
from app.models.notification import NotificationModel


class TestNotifications:
    def test_notification_created_on_ticket_submission(
        self, client, business_user, manager_user, dept, db
    ):
        login(client, business_user.email)
        resp = client.post("/tickets", json={
            "title": "Need help",
            "description": "Please assist",
            "department_id": dept.id,
            "urgency": "Low",
            "manager_id": manager_user.id,
        })
        assert resp.status_code == 201

        # Manager should have received an in-portal notification
        notifs = db.query(NotificationModel).filter(
            NotificationModel.recipient_id == manager_user.id
        ).all()
        assert len(notifs) >= 1
        assert any("approval" in n.event_type for n in notifs)

    def test_smtp_failure_does_not_block_ticket_creation(
        self, client, business_user, manager_user, dept
    ):
        # Patch SMTP to raise — ticket creation must still succeed
        with patch("app.adapters.smtp_adapter.SmtpAdapter.send", side_effect=Exception("SMTP down")):
            login(client, business_user.email)
            resp = client.post("/tickets", json={
                "title": "SMTP test",
                "description": "Should still work",
                "department_id": dept.id,
                "urgency": "Low",
                "manager_id": manager_user.id,
            })
            assert resp.status_code == 201

    def test_mark_notification_read(self, client, business_user, manager_user, dept, db):
        login(client, business_user.email)
        client.post("/tickets", json={
            "title": "T", "description": "D",
            "department_id": dept.id, "urgency": "Low",
            "manager_id": manager_user.id,
        })

        login(client, manager_user.email)
        notifs = client.get("/notifications").json()
        assert len(notifs) >= 1
        notif_id = notifs[0]["id"]

        resp = client.post(f"/notifications/{notif_id}/read")
        assert resp.status_code == 204

        updated = client.get("/notifications").json()
        target = next(n for n in updated if n["id"] == notif_id)
        assert target["is_read"] is True

    def test_mark_all_read(self, client, business_user, manager_user, dept):
        login(client, business_user.email)
        for i in range(2):
            client.post("/tickets", json={
                "title": f"T{i}", "description": "D",
                "department_id": dept.id, "urgency": "Low",
                "manager_id": manager_user.id,
            })

        login(client, manager_user.email)
        resp = client.post("/notifications/read-all")
        assert resp.status_code == 204

        notifs = client.get("/notifications").json()
        assert all(n["is_read"] for n in notifs)
