from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SchedulerHistoryCreate(BaseModel):
    provider: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    jobs_found: int = 0
    message: Optional[str] = None


class SchedulerHistoryResponse(BaseModel):
    id: int
    provider: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    jobs_found: int
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
