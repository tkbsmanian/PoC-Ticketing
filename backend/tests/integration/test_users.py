"""
Integration tests for user and department management endpoints.
"""

from tests.conftest import login


class TestUserManagement:
    def test_admin_can_create_user(self, client, admin_user, dept):
        login(client, admin_user.email)
        resp = client.post("/users", json={
            "email": "new@example.com",
            "display_name": "New User",
            "role": "business_user",
            "department_id": dept.id,
            "password": "password123",
        })
        assert resp.status_code == 201
        assert resp.json()["email"] == "new@example.com"

    def test_non_admin_cannot_create_user(self, client, business_user, dept):
        login(client, business_user.email)
        resp = client.post("/users", json={
            "email": "x@example.com",
            "display_name": "X",
            "role": "business_user",
            "department_id": dept.id,
            "password": "password123",
        })
        assert resp.status_code == 403

    def test_admin_can_deactivate_user(self, client, admin_user, business_user):
        login(client, admin_user.email)
        resp = client.patch(f"/users/{business_user.id}", json={"is_active": False})
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_it_triage_cannot_manage_users(self, client, it_triage_user, dept):
        login(client, it_triage_user.email)
        resp = client.get("/users")
        assert resp.status_code == 403

    def test_duplicate_email_returns_400(self, client, admin_user, business_user, dept):
        login(client, admin_user.email)
        resp = client.post("/users", json={
            "email": business_user.email,
            "display_name": "Dup",
            "role": "business_user",
            "department_id": dept.id,
            "password": "password123",
        })
        assert resp.status_code == 400


class TestDepartmentManagement:
    def test_admin_can_create_department(self, client, admin_user):
        login(client, admin_user.email)
        resp = client.post("/departments", json={"name": "Finance"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "Finance"

    def test_anyone_can_list_departments(self, client, business_user):
        login(client, business_user.email)
        resp = client.get("/departments")
        assert resp.status_code == 200

    def test_non_admin_cannot_create_department(self, client, business_user):
        login(client, business_user.email)
        resp = client.post("/departments", json={"name": "HR"})
        assert resp.status_code == 403
