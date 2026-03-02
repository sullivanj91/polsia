from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.outreach import EmailCampaign, Prospect

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.get("/prospects")
async def get_prospects(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    q = select(Prospect).order_by(Prospect.created_at.desc()).limit(limit)
    if status:
        q = q.where(Prospect.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/campaigns")
async def get_campaigns(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        select(EmailCampaign).order_by(EmailCampaign.created_at.desc())
    )
    return result.scalars().all()
