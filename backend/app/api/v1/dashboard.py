from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.schemas.activity import ActivityLogOut
from app.schemas.dashboard import DashboardSummary
from app.schemas.report import DailyReportOut
from app.services.activity_service import get_recent_activity
from app.services.company_service import get_company_config
from app.services.report_service import get_daily_report
from app.services.task_service import get_tasks_today_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    config = await get_company_config(db)
    tasks = await get_tasks_today_summary(db)
    today_report = await get_daily_report(db, date.today())

    return DashboardSummary(
        tasks_today_total=tasks["total"],
        tasks_today_completed=tasks["completed"],
        tasks_today_pending=tasks["pending"],
        tasks_today_failed=tasks["failed"],
        active_agents=[],  # Populated by Celery worker state in production
        kpis=config.kpis if config and config.kpis else {},
        last_report_date=str(today_report.report_date) if today_report else None,
    )


@router.get("/activity", response_model=list[ActivityLogOut])
async def get_activity(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    return await get_recent_activity(db, limit=limit, offset=offset)


@router.get("/reports/daily", response_model=DailyReportOut | None)
async def get_daily_report_endpoint(
    report_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    d = report_date or date.today()
    return await get_daily_report(db, d)
