"""
Unit tests for core/security.py
"""

import time
import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_reset_token,
    hash_password,
    revoke_token,
    verify_password,
    verify_reset_token,
)


# ── Password hashing ──────────────────────────────────────────────────────────

def test_hash_password_returns_hash():
    h = hash_password("secret123")
    assert h != "secret123"
    assert h.startswith("$2b$")


def test_verify_password_correct():
    h = hash_password("mypassword")
    assert verify_password("mypassword", h) is True


def test_verify_password_wrong():
    h = hash_password("mypassword")
    assert verify_password("wrongpassword", h) is False


def test_hash_is_unique_per_call():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # bcrypt salts differ


# ── JWT ───────────────────────────────────────────────────────────────────────

def test_create_and_decode_token():
    token = create_access_token(user_id=42, role="it_triage")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "it_triage"
    assert "jti" in payload
    assert "exp" in payload


def test_decode_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_access_token("not.a.valid.token")


def test_revoked_token_raises():
    token = create_access_token(user_id=1, role="business_user")
    payload = decode_access_token(token)
    jti = payload["jti"]
    revoke_token(jti)
    with pytest.raises(JWTError):
        decode_access_token(token)


# ── Reset tokens ──────────────────────────────────────────────────────────────

def test_reset_token_verify_correct():
    raw, hashed = generate_reset_token()
    assert verify_reset_token(raw, hashed) is True


def test_reset_token_verify_wrong():
    _, hashed = generate_reset_token()
    assert verify_reset_token("wrongtoken", hashed) is False


def test_reset_tokens_are_unique():
    raw1, _ = generate_reset_token()
    raw2, _ = generate_reset_token()
    assert raw1 != raw2
