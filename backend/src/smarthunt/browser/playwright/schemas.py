from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    provider: str = Field(..., min_length=1)


class ApplyRequest(BaseModel):
    job_url: str = Field(..., min_length=1)


class StatusResponse(BaseModel):
    status: str
    provider: Optional[str] = None
    job_url: Optional[str] = None


class ScreenshotResponse(BaseModel):
    path: str
