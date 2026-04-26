from enum import Enum


class TicketStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    IN_REVIEW = "In Review"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    REJECTED = "Rejected"
    REMOVED = "Removed"


class UserRole(str, Enum):
    BUSINESS_USER = "business_user"
    IT_MANAGER = "it_manager"
    IT_TRIAGE = "it_triage"
    PLATFORM_ADMIN = "platform_admin"
    AUDITOR = "auditor"


class UrgencyLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class PriorityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class SyncOperation(str, Enum):
    CREATE_TASK = "create_task"
    UPDATE_STATUS = "update_status"
    ADD_COMMENT = "add_comment"
    ATTACH_FILE = "attach_file"


class SyncStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


class ApproverRole(str, Enum):
    MANAGER = "Manager"
    DIRECTOR = "Director"


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
