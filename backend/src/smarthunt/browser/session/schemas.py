from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BrowserSessionCreate(BaseModel):
    provider: str = Field(..., min_length=1)


class BrowserSessionResponse(BaseModel):
    id: int
    provider: str
    status: str
    started_at: datetime
    closed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
