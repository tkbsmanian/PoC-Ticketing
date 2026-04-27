from pydantic import BaseModel, Field


class ApprovalActionRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)
