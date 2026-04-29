"""
Auth router — login, logout, password reset, current user.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.core.config import get_settings
from app.domain.exceptions import (
    AccountInactiveError,
    InvalidCredentialsError,
    PasswordResetTokenInvalidError,
)
from app.models.user import UserModel
from app.schemas.auth import (
    AuthUserResponse,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=AuthUserResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    svc = AuthService(db)
    try:
        token = svc.login(payload.email, payload.password)
    except (InvalidCredentialsError, AccountInactiveError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    # Determine if original request was HTTPS (behind proxy)
    is_secure = request.headers.get("x-forwarded-proto") == "https" or settings.is_production()

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.JWT_EXPIRY_HOURS * 3600,
        path="/",
    )
    user = db.query(UserModel).filter(UserModel.email == payload.email).first()
    dept_name = user.department.name if user and user.department else None
    return AuthUserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        department_id=user.department_id,
        department_name=dept_name,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from jose import jwt as jose_jwt
    token = request.cookies.get("access_token", "")
    try:
        payload = jose_jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        jti = payload.get("jti", "")
        AuthService(db).logout(jti)
    except Exception:
        pass
    response.delete_cookie("access_token")


@router.get("/me", response_model=AuthUserResponse)
def me(current_user: UserModel = Depends(get_current_user)):
    dept_name = current_user.department.name if current_user.department else None
    return AuthUserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
        department_id=current_user.department_id,
        department_name=dept_name,
    )


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    svc = AuthService(db)
    result = svc.request_password_reset(payload.email)
    if result:
        raw_token, user = result
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        NotificationService(db).notify(
            event_type="password_reset_requested",
            message=f"Reset your password: {reset_url}",
            recipients=[user],
            ticket_url=reset_url,
        )
    # Always return 204 — never reveal whether email exists


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    try:
        AuthService(db).confirm_password_reset(payload.token, payload.new_password)
    except PasswordResetTokenInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
