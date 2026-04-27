from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class AuthUserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    role: str
    department_id: int | None
    department_name: str | None

    model_config = {"from_attributes": True}
