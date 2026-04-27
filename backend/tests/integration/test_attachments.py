"""
Integration tests for attachment upload endpoint.
"""

import io
import os
import pytest
from tests.conftest import login
from app.models.ticket import TicketModel


def _create_ticket_direct(db, submitter_id, dept_id):
    import uuid
    t = TicketModel(
        ticket_id=f"TKT-{uuid.uuid4().hex[:6].upper()}",
        title="T", description="D", urgency="Low",
        status="In Progress", submitter_id=submitter_id,
        department_id=dept_id, director_approval_required=False,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


class TestAttachments:
    def test_valid_pdf_upload_succeeds(
        self, client, business_user, dept, db, tmp_path
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id)
        login(client, business_user.email)

        content = b"%PDF-1.4 small pdf content"
        resp = client.post(
            f"/tickets/{ticket.id}/attachments",
            files={"file": ("report.pdf", io.BytesIO(content), "application/pdf")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["original_filename"] == "report.pdf"
        assert data["mime_type"] == "application/pdf"

    def test_file_over_10mb_returns_413(
        self, client, business_user, dept, db
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id)
        login(client, business_user.email)

        big_content = b"x" * (10 * 1024 * 1024 + 1)
        resp = client.post(
            f"/tickets/{ticket.id}/attachments",
            files={"file": ("big.pdf", io.BytesIO(big_content), "application/pdf")},
        )
        assert resp.status_code == 413

    def test_disallowed_mime_type_returns_422(
        self, client, business_user, dept, db
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id)
        login(client, business_user.email)

        resp = client.post(
            f"/tickets/{ticket.id}/attachments",
            files={"file": ("script.exe", io.BytesIO(b"MZ"), "application/x-msdownload")},
        )
        assert resp.status_code == 422

    def test_stored_filename_is_uuid_not_original(
        self, client, business_user, dept, db
    ):
        ticket = _create_ticket_direct(db, business_user.id, dept.id)
        login(client, business_user.email)

        content = b"hello world"
        resp = client.post(
            f"/tickets/{ticket.id}/attachments",
            files={"file": ("my_secret_name.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.status_code == 201

        from app.models.attachment import AttachmentModel
        att = db.query(AttachmentModel).filter(
            AttachmentModel.ticket_id == ticket.id
        ).first()
        assert att is not None
        assert att.original_filename == "my_secret_name.txt"
        # Stored filename must be UUID-based, not the original
        assert att.stored_filename != "my_secret_name.txt"
        assert len(att.stored_filename) > 10  # UUID hex

    def test_auditor_cannot_upload(self, client, business_user, dept, db):
        from app.models.user import UserModel
        from app.core.security import hash_password
        auditor = UserModel(
            email="aud2@example.com", display_name="Auditor",
            password_hash=hash_password("password123"),
            role="auditor", department_id=dept.id, is_active=True,
        )
        db.add(auditor)
        db.commit()

        ticket = _create_ticket_direct(db, business_user.id, dept.id)
        login(client, "aud2@example.com")
        resp = client.post(
            f"/tickets/{ticket.id}/attachments",
            files={"file": ("f.txt", io.BytesIO(b"data"), "text/plain")},
        )
        assert resp.status_code == 403
