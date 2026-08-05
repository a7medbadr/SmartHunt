import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl

VALID_STATUSES = {
    "Applied",
    "Interviewing",
    "Technical Interview",
    "Offered",
    "Rejected",
    "Pending",
}


class ApplicationCreate(BaseModel):
    job_title: str
    company: str
    url: HttpUrl | None = None
    status: str = "Applied"


class ApplicationUpdate(BaseModel):
    job_title: str | None = None
    company: str | None = None
    url: HttpUrl | None = None
    status: str | None = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    job_title: str
    company: str
    url: str | None = None
    status: str
    job_id: int | None = None
    created_at: datetime
    days_since_applied: int
    needs_follow_up: bool

    model_config = ConfigDict(from_attributes=True)
