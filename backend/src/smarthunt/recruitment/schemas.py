import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from smarthunt.recruitment.models import ApplicationStatus


class ApplicationCreate(BaseModel):
    job_title: str
    company: str
    url: Optional[str] = None
    status: Optional[ApplicationStatus] = ApplicationStatus.APPLIED


class ApplicationUpdateStatus(BaseModel):
    status: ApplicationStatus


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID | str
    job_title: str
    company: str
    url: Optional[str] = None
    status: str
    created_at: datetime
