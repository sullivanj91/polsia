from datetime import datetime

from pydantic import BaseModel


class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    agent_type: str
    priority: int
    status: str
    source: str
    scheduled_date: datetime | None
    result_summary: str | None
    error_message: str | None
    metadata_: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    agent_type: str
    priority: int = 3
    source: str = "manual"
    scheduled_date: datetime | None = None
    metadata_: dict | None = None
