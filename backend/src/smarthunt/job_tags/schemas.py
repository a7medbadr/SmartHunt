from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobTagCreate(BaseModel):
    job_id: int = Field(..., description="ID of the target job")
    tag: str = Field(..., min_length=1, description="Tag label, e.g. Remote, Urgent")


class JobTagResponse(BaseModel):
    id: int
    job_id: int
    tag: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
