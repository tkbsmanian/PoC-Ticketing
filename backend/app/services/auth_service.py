"""
Authentication service.
Handles login, logout, password reset orchestration.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    generate_reset_token,
    hash_password,
    revoke_token,
    verify_password,
    verify_reset_token,
)
from app.domain.exceptions import (
    AccountInactiveError,
    InvalidCredentialsError,
    PasswordResetTokenInvalidError,
    UserNotFoundError,
)
from app.models.user import UserModel

logger = logging.getLogger(__name__)

PASSWORD_RESET_EXPIRY_HOURS = 1


class AuthService:
    def __init__(self, db: Session):
        self._db = db

    def login(self, email: str, password: str) -> str:
        """
        Validate credentials and return a signed JWT token string.
        Raises InvalidCredentialsError or AccountInactiveError on failure.
        """
        user = self._db.query(UserModel).filter(UserModel.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            logger.warning("Failed login attempt", extra={"masked_email": _mask_email(email)})
            raise InvalidCredentialsError("Invalid email or password.")
        if not user.is_active:
            raise AccountInactiveError("Account is deactivated.")
        logger.info("Successful login", extra={"user_id": user.id})
        return create_access_token(user.id, user.role)

    def logout(self, jti: str) -> None:
        """Revoke the current session token."""
        revoke_token(jti)

    def request_password_reset(self, email: str) -> tuple[str, "UserModel"] | None:
        """
        Generate a reset token for the given email.
        Returns (raw_token, user) if found, None if not (caller should not reveal this).
        """
        user = self._db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return None
        raw_token, hashed_token = generate_reset_token()
        user.reset_token = hashed_token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(
            hours=PASSWORD_RESET_EXPIRY_HOURS
        )
        self._db.commit()
        logger.info("Password reset requested", extra={"masked_email": _mask_email(email)})
        return raw_token, user

    def confirm_password_reset(self, raw_token: str, new_password: str) -> None:
        """
        Validate the reset token and update the password.
        Raises PasswordResetTokenInvalidError if invalid or expired.
        """
        user = (
            self._db.query(UserModel)
            .filter(UserModel.reset_token.isnot(None))
            .filter(UserModel.reset_token_expires > datetime.now(timezone.utc))
            .first()
        )
        if not user or not verify_reset_token(raw_token, user.reset_token):
            raise PasswordResetTokenInvalidError("Reset token is invalid or has expired.")
        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        self._db.commit()
        logger.info("Password reset completed", extra={"user_id": user.id})


def _mask_email(email: str) -> str:
    """Mask email for safe logging: jane@example.com → j***@example.com"""
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}"
