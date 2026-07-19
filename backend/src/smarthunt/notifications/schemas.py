from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: str
    is_read: bool

    model_config = ConfigDict(from_attributes=True)
