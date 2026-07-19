from pydantic import BaseModel, ConfigDict


class SettingsUpdate(BaseModel):
    theme: str
    language: str
    email_notifications: bool
    job_alerts: bool


class SettingsResponse(BaseModel):
    theme: str
    language: str
    email_notifications: bool
    job_alerts: bool

    model_config = ConfigDict(from_attributes=True)
