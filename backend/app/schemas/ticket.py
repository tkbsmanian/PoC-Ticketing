from datetime import datetime
from pydantic import BaseModel, Field


from pydantic import BaseModel, Field, field_validator


class CreateTicketRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=10000)
    department_id: int
    urgency: str = Field(pattern="^(Low|Medium|High|Critical)$")
    cost: float | None = Field(default=None, ge=0)
    manager_id: int

    @field_validator("title", "description")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank or whitespace only.")
        return v


class UpdateStatusRequest(BaseModel):
    status: str


class UpdateCategoryPriorityRequest(BaseModel):
    category: str | None = Field(default=None, max_length=120)
    priority: str | None = Field(default=None, pattern="^(Low|Medium|High|Critical)$")


class ApprovalResponse(BaseModel):
    id: int
    approver_name: str
    approver_role: str
    decision: str | None
    comment: str | None
    decided_at: datetime | None
    deadline: datetime

    model_config = {"from_attributes": True}


class AttachmentResponse(BaseModel):
    id: int
    original_filename: str
    mime_type: str
    file_size_bytes: int
    uploaded_by_name: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class CommentResponse(BaseModel):
    id: int
    author_name: str
    author_role: str
    body: str
    is_internal: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class HistoryEntryResponse(BaseModel):
    id: int
    event_type: str
    field_name: str | None
    old_value: str | None
    new_value: str | None
    actor_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketSummaryResponse(BaseModel):
    id: int
    ticket_id: str
    title: str
    status: str
    urgency: str
    priority: str | None
    category: str | None
    department_name: str | None
    submitter_name: str
    created_at: datetime
    updated_at: datetime
    sync_failed: bool
    jira_task_url: str | None

    model_config = {"from_attributes": True}


class TicketDetailResponse(TicketSummaryResponse):
    description: str
    cost: float | None
    director_approval_required: bool
    jira_task_id: str | None
    comments: list[CommentResponse] = []
    attachments: list[AttachmentResponse] = []
    history: list[HistoryEntryResponse] = []
    approvals: list[ApprovalResponse] = []


class PaginatedTicketsResponse(BaseModel):
    items: list[TicketSummaryResponse]
    total: int
    page: int
    page_size: int
