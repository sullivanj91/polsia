from datetime import datetime

from pydantic import BaseModel


class ActivityLogOut(BaseModel):
    id: int
    agent_type: str
    action: str
    summary: str
    detail: dict | None
    level: str
    created_at: datetime

    model_config = {"from_attributes": True}
