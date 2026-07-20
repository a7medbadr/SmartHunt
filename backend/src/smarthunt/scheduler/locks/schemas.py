from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SchedulerLockResponse(BaseModel):
    id: int
    job_id: str
    owner_id: str
    acquired_at: datetime
    expires_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
