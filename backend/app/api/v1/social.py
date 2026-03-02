from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.social import SocialPost

router = APIRouter(prefix="/social", tags=["social"])


@router.get("/posts")
async def get_posts(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    q = select(SocialPost).order_by(SocialPost.created_at.desc()).limit(limit)
    if status:
        q = q.where(SocialPost.status == status)
    result = await db.execute(q)
    posts = result.scalars().all()
    return [
        {
            "id": p.id,
            "platform": p.platform,
            "content": p.content,
            "status": p.status,
            "tweet_id": p.tweet_id,
            "published_at": p.published_at,
            "engagement": p.engagement,
        }
        for p in posts
    ]
