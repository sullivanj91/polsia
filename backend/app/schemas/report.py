from datetime import date, datetime

from pydantic import BaseModel


class DailyReportOut(BaseModel):
    id: int
    report_date: date
    morning_plan: str | None
    evening_summary: str | None
    tasks_planned: int
    tasks_completed: int
    tasks_failed: int
    metrics_snapshot: dict | None
    insights: list[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}
