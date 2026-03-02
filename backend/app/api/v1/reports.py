from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.report import DailyReport
from app.schemas.report import DailyReportOut

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily", response_model=list[DailyReportOut])
async def list_daily_reports(
    limit: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        select(DailyReport).order_by(DailyReport.report_date.desc()).limit(limit)
    )
    return list(result.scalars().all())
