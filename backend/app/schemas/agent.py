from datetime import datetime

from pydantic import BaseModel


class TriggerAgentIn(BaseModel):
    task_title: str | None = None
    task_description: str | None = None
    metadata: dict | None = None


class TriggerAgentOut(BaseModel):
    status: str
    task_id: int | None = None
    message: str


class AgentStatusOut(BaseModel):
    agent_type: str
    last_run_at: datetime | None
    last_run_status: str | None
    tasks_today: int
    tasks_total: int
