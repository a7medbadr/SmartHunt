from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobNoteCreate(BaseModel):
    job_id: int = Field(..., description="ID of the target job")
    note: str = Field(..., min_length=1, description="Note content")


class JobNoteUpdate(BaseModel):
    note: str = Field(..., min_length=1, description="Updated note content")


class JobNoteResponse(BaseModel):
    id: int
    job_id: int
    note: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
