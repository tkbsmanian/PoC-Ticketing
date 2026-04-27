from pydantic import BaseModel, Field


class CreateCommentRequest(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    is_internal: bool = False
