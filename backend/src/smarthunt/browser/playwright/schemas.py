from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    provider: str = Field(..., min_length=1)


class ApplyRequest(BaseModel):
    job_url: str = Field(..., min_length=1)


class EasyApplyRequest(BaseModel):
    job_url: str = Field(..., min_length=1)
    application_id: Optional[str] = None


class FormFillRequest(BaseModel):
    job_url: str = Field(..., min_length=1)


class FillProfileRequest(BaseModel):
    job_url: str = Field(..., min_length=1)
    resume: str = Field(..., min_length=1)


class OpenJobRequest(BaseModel):
    job_url: str = Field(..., min_length=1)


class DetectFormRequest(BaseModel):
    job_url: str = Field(..., min_length=1)


class StatusResponse(BaseModel):
    status: str
    provider: Optional[str] = None
    job_url: Optional[str] = None


class PlaywrightStatusResponse(BaseModel):
    running: bool
    browser_started: bool
    active_contexts: int
    active_pages: int


class EasyApplyResponse(BaseModel):
    status: str
    question: Optional[str] = None


class FormFillResponse(BaseModel):
    status: str
    question: Optional[str] = None


class FillProfileResponse(BaseModel):
    status: str
    filled_fields: int
    unknown_questions: list[str]


class ScreenshotResponse(BaseModel):
    path: str


class OpenJobResponse(BaseModel):
    status: str
    title: str


class DetectFormResponse(BaseModel):
    available: bool
    easy_apply: bool
    selector: Optional[str] = None
