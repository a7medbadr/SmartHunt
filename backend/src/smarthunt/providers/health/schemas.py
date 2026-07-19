from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderHealthUpdate(BaseModel):
    provider: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    response_time_ms: Optional[int] = None
    message: Optional[str] = None


class ProviderHealthResponse(BaseModel):
    id: int
    provider: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class ProviderHealthDetail(BaseModel):
    id: int
    provider: str
    status: str
    last_check: datetime
    response_time_ms: Optional[int] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
