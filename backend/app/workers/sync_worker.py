"""
Background worker — JIRA sync queue processor and approval timeout checker.
Runs as an in-process APScheduler job started at application startup.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler: BackgroundScheduler | None = None


def start_sync_worker() -> None:
    global _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _process_sync_queue,
        "interval",
        seconds=settings.JIRA_SYNC_POLL_INTERVAL_SECONDS,
        id="sync_queue_processor",
        max_instances=1,
    )
    _scheduler.add_job(
        _check_approval_timeouts,
        "interval",
        minutes=15,
        id="approval_timeout_checker",
        max_instances=1,
    )
    _scheduler.start()
    logger.info("Sync worker started.")


def stop_sync_worker() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Sync worker stopped.")


def _process_sync_queue() -> None:
    """Poll sync_queue for pending events and dispatch to the configured adapter."""
    from app.db.session import SessionLocal
    from app.domain.enums import SyncStatus
    from app.models.sync_queue import SyncQueueModel
    from app.models.ticket import TicketModel
    from app.core.dependencies import get_sync_adapter

    db = SessionLocal()
    try:
        adapter = get_sync_adapter()
        pending = (
            db.query(SyncQueueModel)
            .filter(SyncQueueModel.status == SyncStatus.PENDING.value)
            .order_by(SyncQueueModel.created_at)
            .limit(20)
            .all()
        )
        for event in pending:
            _dispatch_event(event, adapter, db)
    except Exception as exc:
        logger.error("Sync worker error", extra={"error": str(exc)})
    finally:
        db.close()


def _dispatch_event(event, adapter, db) -> None:
    from app.domain.enums import SyncOperation, SyncStatus
    from app.models.sync_queue import SyncQueueModel
    from app.models.ticket import TicketModel
    from app.models.user import UserModel
    from app.models.comment import CommentModel
    from app.models.attachment import AttachmentModel
    import json

    RETRY_DELAYS = [10, 30, 90]
    max_attempts = settings.JIRA_MAX_RETRY_ATTEMPTS

    event.status = SyncStatus.IN_PROGRESS.value
    event.last_attempted_at = datetime.now(timezone.utc)
    db.commit()

    ticket = db.get(TicketModel, event.ticket_id)
    if not ticket:
        event.status = SyncStatus.FAILED.value
        event.last_error = "Ticket not found"
        db.commit()
        return

    try:
        op = event.operation
        if op == SyncOperation.CREATE_TASK.value:
            submitter = db.get(UserModel, ticket.submitter_id)
            from app.models.user import DepartmentModel
            dept = db.get(DepartmentModel, ticket.department_id) if ticket.department_id else None
            ref = adapter.create_task(
                ticket_id=ticket.ticket_id,
                title=ticket.title,
                description=ticket.description,
                department=dept.name if dept else "",
                urgency=ticket.urgency,
                cost=ticket.cost,
                submitter_name=submitter.display_name if submitter else "",
                submitter_email=submitter.email if submitter else "",
                category=ticket.category,
                priority=ticket.priority,
            )
            ticket.jira_task_id = ref.external_id
            ticket.jira_task_url = ref.external_url
            ticket.sync_failed = False

        elif op == SyncOperation.UPDATE_STATUS.value:
            if ticket.jira_task_id:
                adapter.update_status(ticket.jira_task_id, ticket.status)

        elif op == SyncOperation.ADD_COMMENT.value:
            payload = json.loads(event.payload_json or "{}")
            comment_id = payload.get("comment_id")
            if comment_id and ticket.jira_task_id:
                comment = db.get(CommentModel, comment_id)
                if comment and not comment.is_internal:
                    author = db.get(UserModel, comment.author_id)
                    adapter.add_comment(
                        ticket.jira_task_id,
                        author.display_name if author else "Unknown",
                        comment.body,
                        comment.is_internal,
                    )

        elif op == SyncOperation.ATTACH_FILE.value:
            payload = json.loads(event.payload_json or "{}")
            attachment_id = payload.get("attachment_id")
            if attachment_id and ticket.jira_task_id:
                att = db.get(AttachmentModel, attachment_id)
                if att:
                    adapter.attach_file(
                        ticket.jira_task_id,
                        att.original_filename,
                        att.storage_path,
                        att.mime_type,
                    )

        event.status = SyncStatus.SUCCESS.value
        db.commit()
        logger.info(
            "Sync event processed",
            extra={"sync_event_id": event.id, "ticket_id": event.ticket_id, "operation": op},
        )

    except Exception as exc:
        from app.domain.exceptions import SyncAdapterError
        event.attempt_count += 1
        event.last_error = str(exc)[:500]

        is_permanent = isinstance(exc, SyncAdapterError)
        if is_permanent or event.attempt_count >= max_attempts:
            event.status = SyncStatus.FAILED.value
            ticket.sync_failed = True
            logger.error(
                "Sync event permanently failed",
                extra={
                    "sync_event_id": event.id,
                    "ticket_id": event.ticket_id,
                    "operation": event.operation,
                    "attempt_count": event.attempt_count,
                    "error": str(exc)[:200],
                },
            )
        else:
            event.status = SyncStatus.PENDING.value
            logger.warning(
                "Sync event retry scheduled",
                extra={
                    "sync_event_id": event.id,
                    "attempt_number": event.attempt_count,
                    "error_type": type(exc).__name__,
                },
            )
        db.commit()


def _check_approval_timeouts() -> None:
    """Re-notify approvers who have not acted within 48 hours."""
    from app.db.session import SessionLocal
    from app.models.ticket import ApprovalModel
    from app.models.user import UserModel
    from app.services.notification_service import NotificationService
    from app.services.audit_service import AuditService

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        overdue = (
            db.query(ApprovalModel)
            .filter(
                ApprovalModel.decision == None,  # noqa: E711
                ApprovalModel.deadline < now,
            )
            .all()
        )
        for approval in overdue:
            approver = db.get(UserModel, approval.approver_id)
            if not approver:
                continue
            ticket = db.get(__import__("app.models.ticket", fromlist=["TicketModel"]).TicketModel, approval.ticket_id)
            if not ticket:
                continue

            AuditService(db).record(
                ticket_id=approval.ticket_id,
                actor_id=None,
                event_type="approval_timeout_escalation",
                notes=f"{approval.approver_role} approval overdue — re-notified",
            )
            NotificationService(db).notify(
                event_type="approval_timeout",
                message=f"Reminder: ticket '{ticket.ticket_id}' is awaiting your approval.",
                recipients=[approver],
                ticket_id=approval.ticket_id,
            )
            # Extend deadline by another 48h to avoid repeated spam
            approval.deadline = datetime.now(timezone.utc).replace(
                hour=now.hour, minute=now.minute
            )
            from datetime import timedelta
            approval.deadline = now + timedelta(hours=48)
            db.commit()
            logger.info(
                "Approval timeout escalation",
                extra={"approval_id": approval.id, "approver_id": approval.approver_id},
            )
    except Exception as exc:
        logger.error("Approval timeout checker error", extra={"error": str(exc)})
    finally:
        db.close()
