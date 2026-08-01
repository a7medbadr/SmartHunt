from pydantic import BaseModel


class ProviderInfo(BaseModel):
    name: str
    enabled: bool
    supports_login: bool
    supports_apply: bool
    supports_resume_upload: bool
    supports_cover_letter: bool
    real_discovery: bool


class ProviderSettingUpdate(BaseModel):
    enabled: bool
