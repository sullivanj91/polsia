from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import publish_activity
from app.models.report import ActivityLog


async def log_activity(
    db: AsyncSession,
    agent_type: str,
    action: str,
    summary: str,
    detail: dict[str, Any] | None = None,
    level: str = "info",
) -> ActivityLog:
    entry = ActivityLog(
        agent_type=agent_type,
        action=action,
        summary=summary,
        detail=detail or {},
        level=level,
    )
    db.add(entry)
    await db.flush()  # Get the ID without full commit

    event = {
        "id": entry.id,
        "agent_type": agent_type,
        "action": action,
        "summary": summary,
        "level": level,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }
    await publish_activity(event)
    return entry


async def get_recent_activity(
    db: AsyncSession, limit: int = 50, offset: int = 0
) -> list[ActivityLog]:
    result = await db.execute(
        select(ActivityLog).order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all())
