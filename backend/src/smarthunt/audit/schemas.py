from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    actor_id: int | None
    action: str
    resource_type: str
    resource_id: str | None
    old_value: str | None
    new_value: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
