# Import all ORM models here so init_db.py can register them with Base.metadata.
from app.models.user import UserModel, DepartmentModel  # noqa: F401
from app.models.ticket import TicketModel, ApprovalModel  # noqa: F401
from app.models.comment import CommentModel  # noqa: F401
from app.models.attachment import AttachmentModel  # noqa: F401
from app.models.notification import NotificationModel  # noqa: F401
from app.models.audit import AuditLogModel  # noqa: F401
from app.models.sync_queue import SyncQueueModel  # noqa: F401
