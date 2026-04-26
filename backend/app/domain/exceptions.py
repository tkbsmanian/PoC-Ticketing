"""
Domain-specific exceptions.
API routers map these to HTTP status codes in the central exception handler.
Never raise HTTPException from domain or service code.
"""


class InvalidTransitionError(Exception):
    """Raised when a status transition is not permitted by the lifecycle rules."""


class UnauthorizedActionError(Exception):
    """Raised when a role attempts an action it is not permitted to perform."""


class TicketNotFoundError(Exception):
    """Raised when a ticket does not exist or is not visible to the caller."""


class UserNotFoundError(Exception):
    """Raised when a user record cannot be found."""


class DepartmentNotFoundError(Exception):
    """Raised when a department record cannot be found."""


class ApprovalNotAssignedError(Exception):
    """Raised when an approver attempts to act on an approval not assigned to them."""


class ApprovalAlreadyDecidedError(Exception):
    """Raised when an approval action is attempted on an already-decided approval."""


class TicketNotDeletableError(Exception):
    """Raised when a soft-delete is attempted on a ticket that is not Closed or Rejected."""


class DuplicateSyncEventError(Exception):
    """Raised when a sync event for the same ticket+operation is already pending."""


class SyncAdapterError(Exception):
    """Raised by adapters for permanent (non-retryable) failures."""


class SyncTransientError(Exception):
    """Raised by adapters for transient (retryable) failures."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""


class AccountInactiveError(Exception):
    """Raised when a login is attempted for a deactivated account."""


class PasswordResetTokenInvalidError(Exception):
    """Raised when a password reset token is missing, invalid, or expired."""


class FileTooLargeError(Exception):
    """Raised when an uploaded file exceeds the maximum allowed size."""


class InvalidFileTypeError(Exception):
    """Raised when an uploaded file's MIME type is not on the allowlist."""
