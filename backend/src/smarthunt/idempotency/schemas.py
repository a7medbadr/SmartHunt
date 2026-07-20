from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IdempotencyResponse(BaseModel):
    key: str
    status: str
    response: str | None
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
