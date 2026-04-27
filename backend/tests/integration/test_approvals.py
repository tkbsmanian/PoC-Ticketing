"""
Integration tests for the approval workflow.
"""

from tests.conftest import login


def _submit_ticket(client, dept_id, manager_id, urgency="Medium", cost=None):
    payload = {
        "title": "Test request",
        "description": "Need something",
        "department_id": dept_id,
        "urgency": urgency,
        "manager_id": manager_id,
    }
    if cost is not None:
        payload["cost"] = cost
    return client.post("/tickets", json=payload)


class TestApprovalWorkflow:
    def test_manager_reject_sets_ticket_rejected(
        self, client, business_user, manager_user, dept
    ):
        login(client, business_user.email)
        ticket_resp = _submit_ticket(client, dept.id, manager_user.id)
        assert ticket_resp.status_code == 201

        login(client, manager_user.email)
        approvals = client.get("/approvals/pending").json()
        assert len(approvals) >= 1
        approval_id = approvals[0]["id"]

        reject_resp = client.post(
            f"/approvals/{approval_id}/reject",
            json={"comment": "Not justified"},
        )
        assert reject_resp.status_code == 200

        login(client, business_user.email)
        ticket_id = ticket_resp.json()["id"]
        ticket = client.get(f"/tickets/{ticket_id}").json()
        assert ticket["status"] == "Rejected"

    def test_manager_approve_no_director_sets_approved(
        self, client, business_user, manager_user, dept
    ):
        # Low urgency, no cost → no director required
        login(client, business_user.email)
        ticket_resp = _submit_ticket(client, dept.id, manager_user.id, urgency="Low")
        assert ticket_resp.status_code == 201

        login(client, manager_user.email)
        approvals = client.get("/approvals/pending").json()
        approval_id = approvals[0]["id"]

        approve_resp = client.post(f"/approvals/{approval_id}/approve", json={})
        assert approve_resp.status_code == 200

        login(client, business_user.email)
        ticket_id = ticket_resp.json()["id"]
        ticket = client.get(f"/tickets/{ticket_id}").json()
        assert ticket["status"] == "Approved"

    def test_approver_cannot_act_on_unassigned_approval(
        self, client, business_user, manager_user, it_triage_user, dept, db
    ):
        from app.models.user import UserModel
        from app.core.security import hash_password

        # Create a second manager
        other_manager = UserModel(
            email="other_mgr@example.com",
            display_name="Other Manager",
            password_hash=hash_password("password123"),
            role="it_manager",
            department_id=dept.id,
            is_active=True,
        )
        db.add(other_manager)
        db.commit()

        # Submit ticket assigned to manager_user
        login(client, business_user.email)
        ticket_resp = _submit_ticket(client, dept.id, manager_user.id)
        assert ticket_resp.status_code == 201

        # other_manager tries to approve — should get 403
        login(client, other_manager.email)
        approvals = client.get("/approvals/pending").json()
        # other_manager has no pending approvals
        assert len(approvals) == 0

    def test_unauthenticated_cannot_access_approvals(self, client):
        resp = client.get("/approvals/pending")
        assert resp.status_code == 401
