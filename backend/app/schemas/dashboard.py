from pydantic import BaseModel


class DashboardSummary(BaseModel):
    tasks_today_total: int
    tasks_today_completed: int
    tasks_today_pending: int
    tasks_today_failed: int
    active_agents: list[str]
    kpis: dict
    last_report_date: str | None
