from pydantic import BaseModel, EmailStr, Field


class CreateUserRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=120)
    role: str
    department_id: int | None = None
    password: str = Field(min_length=8, max_length=128)


class UpdateUserRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    role: str | None = None
    department_id: int | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    role: str
    department_name: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class CreateDepartmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class UpdateDepartmentRequest(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    is_active: bool

    model_config = {"from_attributes": True}
