from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.ads import AdCampaign, AdMetric

router = APIRouter(prefix="/ads", tags=["ads"])


@router.get("/campaigns")
async def get_campaigns(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        select(AdCampaign).order_by(AdCampaign.created_at.desc())
    )
    return result.scalars().all()


@router.get("/metrics")
async def get_metrics(
    campaign_id: int | None = Query(None),
    limit: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    q = select(AdMetric).order_by(AdMetric.date.desc()).limit(limit)
    if campaign_id:
        q = q.where(AdMetric.campaign_id == campaign_id)
    result = await db.execute(q)
    return result.scalars().all()
