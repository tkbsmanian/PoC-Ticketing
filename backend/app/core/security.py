"""
Security utilities: password hashing, JWT creation/verification, token blocklist.
No business logic here — pure cryptographic operations.
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# bcrypt cost factor 12 minimum per security steering rules
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# In-memory JTI blocklist for invalidated tokens (PoC).
# Production: replace with Redis SET with TTL.
_token_blocklist: set[str] = set()


# ── Password hashing ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_id: int, role: str) -> str:
    settings = get_settings()
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=settings.JWT_EXPIRY_HOURS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "jti": jti,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises JWTError if invalid, expired, or blocklisted.
    """
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    jti = payload.get("jti")
    if jti and jti in _token_blocklist:
        raise JWTError("Token has been revoked.")
    return payload


def revoke_token(jti: str) -> None:
    """Add a token JTI to the blocklist (logout)."""
    _token_blocklist.add(jti)


# ── Password reset tokens ─────────────────────────────────────────────────────

def generate_reset_token() -> tuple[str, str]:
    """
    Generate a password reset token.
    Returns (raw_token, hashed_token).
    raw_token is sent to the user; hashed_token is stored in the DB.
    """
    raw = secrets.token_urlsafe(32)
    hashed = hash_password(raw)
    return raw, hashed


def verify_reset_token(raw: str, hashed: str) -> bool:
    return verify_password(raw, hashed)
