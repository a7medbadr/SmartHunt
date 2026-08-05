import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DraftEmailRequest(BaseModel):
    job_id: int


class DraftEmailResponse(BaseModel):
    recipient_email: str
    subject: str
    body: str


class SendEmailRequest(BaseModel):
    job_id: int
    recipient_email: str
    subject: str
    body: str


class EmailMessageResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    direction: str
    from_address: str
    to_address: str
    subject: str
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DraftReplyResponse(BaseModel):
    body: str


class SendReplyRequest(BaseModel):
    body: str
