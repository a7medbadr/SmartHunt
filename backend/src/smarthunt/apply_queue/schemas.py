from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApplyQueueCreate(BaseModel):
    job_id: int = Field(..., description="ID of the target job")
    provider: str = Field(..., min_length=1)
    priority: int = 1


class ApplyQueueStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1)


class ApplyQueueResponse(BaseModel):
    id: int
    job_id: int
    provider: str
    status: str
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
