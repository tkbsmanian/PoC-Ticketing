"""
Integration tests for ticket endpoints.
"""

import pytest
from tests.conftest import login


def _submit_ticket(client, dept_id, manager_id):
    return client.post("/tickets", json={
        "title": "Test request",
        "description": "Need a new laptop",
        "department_id": dept_id,
        "urgency": "Medium",
        "manager_id": manager_id,
    })


class TestTicketSubmission:
    def test_valid_submission_returns_201(self, client, business_user, manager_user, dept):
        login(client, business_user.email)
        resp = _submit_ticket(client, dept.id, manager_user.id)
        assert resp.status_code == 201
        data = resp.json()
        assert data["ticket_id"].startswith("TKT-")
        assert data["status"] == "Pending"

    def test_missing_title_returns_422(self, client, business_user, manager_user, dept):
        login(client, business_user.email)
        resp = client.post("/tickets", json={
            "title": "",
            "description": "Some description",
            "department_id": dept.id,
            "urgency": "Low",
            "manager_id": manager_user.id,
        })
        assert resp.status_code == 422

    def test_missing_description_returns_422(self, client, business_user, manager_user, dept):
        login(client, business_user.email)
        resp = client.post("/tickets", json={
            "title": "Valid title",
            "description": "",
            "department_id": dept.id,
            "urgency": "Low",
            "manager_id": manager_user.id,
        })
        assert resp.status_code == 422

    def test_unauthenticated_returns_401(self, client, dept, manager_user):
        resp = _submit_ticket(client, dept.id, manager_user.id)
        assert resp.status_code == 401

    def test_auditor_cannot_submit(self, client, admin_user, dept, manager_user, db):
        from app.models.user import UserModel
        from app.core.security import hash_password
        auditor = UserModel(
            email="auditor@example.com",
            display_name="Auditor",
            password_hash=hash_password("password123"),
            role="auditor",
            department_id=dept.id,
            is_active=True,
        )
        db.add(auditor)
        db.commit()
        login(client, "auditor@example.com")
        resp = _submit_ticket(client, dept.id, manager_user.id)
        assert resp.status_code == 403


class TestTicketVisibility:
    def test_business_user_sees_own_tickets(self, client, business_user, manager_user, dept):
        login(client, business_user.email)
        _submit_ticket(client, dept.id, manager_user.id)
        resp = client.get("/tickets")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_business_user_cannot_see_other_ticket(
        self, client, business_user, manager_user, it_triage_user, dept, db
    ):
        # Submit as business user
        login(client, business_user.email)
        create_resp = _submit_ticket(client, dept.id, manager_user.id)
        ticket_id = create_resp.json()["id"]

        # Create second user and try to access first user's ticket
        from app.models.user import UserModel
        from app.core.security import hash_password
        other = UserModel(
            email="other@example.com",
            display_name="Other User",
            password_hash=hash_password("password123"),
            role="business_user",
            department_id=dept.id,
            is_active=True,
        )
        db.add(other)
        db.commit()

        login(client, "other@example.com")
        resp = client.get(f"/tickets/{ticket_id}")
        assert resp.status_code == 403

    def test_it_triage_sees_all_tickets(self, client, business_user, manager_user, it_triage_user, dept):
        login(client, business_user.email)
        _submit_ticket(client, dept.id, manager_user.id)

        login(client, it_triage_user.email)
        resp = client.get("/tickets")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


class TestStatusTransitions:
    def test_invalid_transition_returns_422(self, client, business_user, manager_user, it_triage_user, dept):
        login(client, business_user.email)
        create_resp = _submit_ticket(client, dept.id, manager_user.id)
        ticket_id = create_resp.json()["id"]

        login(client, it_triage_user.email)
        # Pending → Closed is invalid
        resp = client.patch(f"/tickets/{ticket_id}/status", json={"status": "Closed"})
        assert resp.status_code == 422

    def test_business_user_cannot_update_status(self, client, business_user, manager_user, dept):
        login(client, business_user.email)
        create_resp = _submit_ticket(client, dept.id, manager_user.id)
        ticket_id = create_resp.json()["id"]
        resp = client.patch(f"/tickets/{ticket_id}/status", json={"status": "In Review"})
        assert resp.status_code == 403
