"""
Users and departments router.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.core.security import hash_password
from app.domain.enums import UserRole
from app.models.user import DepartmentModel, UserModel
from app.schemas.user import (
    CreateDepartmentRequest,
    CreateUserRequest,
    DepartmentResponse,
    UpdateDepartmentRequest,
    UpdateUserRequest,
    UserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _=Depends(require_role(UserRole.PLATFORM_ADMIN)),
):
    users = db.query(UserModel).all()
    return [_user_response(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role(UserRole.PLATFORM_ADMIN)),
):
    existing = db.query(UserModel).filter(UserModel.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = UserModel(
        email=payload.email,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        department_id=payload.department_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("User created", extra={"user_id": user.id, "role": user.role})
    return _user_response(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UpdateUserRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role(UserRole.PLATFORM_ADMIN)),
):
    user = db.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.role is not None:
        user.role = payload.role
    if payload.department_id is not None:
        user.department_id = payload.department_id
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return _user_response(user)


@router.get("/users/managers", response_model=list[UserResponse])
def list_managers(db: Session = Depends(get_db)):
    managers = db.query(UserModel).filter(
        UserModel.role == UserRole.IT_MANAGER.value,
        UserModel.is_active == True,  # noqa: E712
    ).all()
    return [_user_response(u) for u in managers]


# ── Departments ───────────────────────────────────────────────────────────────

@router.get("/departments", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    return db.query(DepartmentModel).all()


@router.post("/departments", response_model=DepartmentResponse, status_code=201)
def create_department(
    payload: CreateDepartmentRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role(UserRole.PLATFORM_ADMIN)),
):
    dept = DepartmentModel(name=payload.name, is_active=True)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.patch("/departments/{dept_id}", response_model=DepartmentResponse)
def update_department(
    dept_id: int,
    payload: UpdateDepartmentRequest,
    db: Session = Depends(get_db),
    _=Depends(require_role(UserRole.PLATFORM_ADMIN)),
):
    dept = db.get(DepartmentModel, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")
    if payload.name is not None:
        dept.name = payload.name
    if payload.is_active is not None:
        dept.is_active = payload.is_active
    db.commit()
    db.refresh(dept)
    return dept


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    from app.models.ticket import TicketModel
    from sqlalchemy import func
    rows = (
        db.query(TicketModel.status, func.count(TicketModel.id))
        .filter(TicketModel.is_deleted == False)  # noqa: E712
        .group_by(TicketModel.status)
        .all()
    )
    by_status = {r[0]: r[1] for r in rows}
    open_statuses = {"Pending", "Approved", "In Review", "In Progress"}
    total_open = sum(v for k, v in by_status.items() if k in open_statuses)
    return {"by_status": by_status, "total_open": total_open}


# ── Helper ────────────────────────────────────────────────────────────────────

def _user_response(user: UserModel) -> UserResponse:
    dept_name = user.department.name if user.department else None
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        department_name=dept_name,
        is_active=user.is_active,
    )
