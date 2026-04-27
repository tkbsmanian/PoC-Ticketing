"""
Attachments router — upload and download ticket attachments.
"""

import logging
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.adapters.jira_mappings import ALLOWED_MIME_TYPES
from app.core.config import get_settings
from app.core.dependencies import get_db, get_current_user
from app.domain.enums import SyncOperation, UserRole
from app.models.attachment import AttachmentModel
from app.models.ticket import TicketModel
from app.models.user import UserModel
from app.schemas.ticket import AttachmentResponse
from app.services.audit_service import AuditService
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/{ticket_id}/attachments", response_model=AttachmentResponse, status_code=201)
async def upload_attachment(
    ticket_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.role == UserRole.AUDITOR.value:
        raise HTTPException(status_code=403, detail="Auditors cannot upload attachments.")

    ticket = _get_ticket_or_403(ticket_id, current_user, db)

    # Read file content to check size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB limit.")

    # Validate MIME type
    mime = file.content_type or "application/octet-stream"
    if mime not in ALLOWED_MIME_TYPES:
        logger.warning(
            "File upload rejected — disallowed MIME type",
            extra={"user_id": current_user.id, "reason": f"mime={mime}"},
        )
        raise HTTPException(status_code=422, detail=f"File type '{mime}' is not allowed.")

    # Store with UUID filename to prevent path traversal
    ext = os.path.splitext(file.filename or "")[1]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    storage_path = os.path.join(upload_dir, stored_name)

    with open(storage_path, "wb") as f:
        f.write(content)

    attachment = AttachmentModel(
        ticket_id=ticket.id,
        uploaded_by=current_user.id,
        original_filename=file.filename or stored_name,
        stored_filename=stored_name,
        storage_path=storage_path,
        mime_type=mime,
        file_size_bytes=len(content),
    )
    db.add(attachment)

    AuditService(db).record(
        ticket_id=ticket.id,
        actor_id=current_user.id,
        event_type="attachment_uploaded",
        notes=f"File '{file.filename}' uploaded ({len(content)} bytes)",
    )
    db.commit()
    db.refresh(attachment)

    # Enqueue JIRA sync
    import json
    SyncService(db).enqueue(
        ticket.id,
        SyncOperation.ATTACH_FILE,
        payload_json=json.dumps({"attachment_id": attachment.id}),
    )

    uploader = db.get(UserModel, attachment.uploaded_by)
    return AttachmentResponse(
        id=attachment.id,
        original_filename=attachment.original_filename,
        mime_type=attachment.mime_type,
        file_size_bytes=attachment.file_size_bytes,
        uploaded_by_name=uploader.display_name if uploader else "Unknown",
        uploaded_at=attachment.uploaded_at,
    )


@router.get("/{ticket_id}/attachments/{attachment_id}")
def download_attachment(
    ticket_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    ticket = _get_ticket_or_403(ticket_id, current_user, db)
    attachment = db.query(AttachmentModel).filter(
        AttachmentModel.id == attachment_id,
        AttachmentModel.ticket_id == ticket.id,
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    if not os.path.exists(attachment.storage_path):
        raise HTTPException(status_code=404, detail="File not found on disk.")

    return FileResponse(
        path=attachment.storage_path,
        filename=attachment.original_filename,
        media_type=attachment.mime_type,
    )


def _get_ticket_or_403(ticket_id: int, user: UserModel, db: Session) -> TicketModel:
    ticket = db.get(TicketModel, ticket_id)
    if not ticket or ticket.is_deleted:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    if user.role == UserRole.BUSINESS_USER.value and ticket.submitter_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    if user.role == UserRole.IT_MANAGER.value:
        if ticket.submitter_id != user.id and ticket.department_id != user.department_id:
            raise HTTPException(status_code=403, detail="Access denied.")
    return ticket
