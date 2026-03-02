from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.schemas.agent import AgentStatusOut, TriggerAgentIn, TriggerAgentOut
from app.services.task_service import VALID_AGENT_TYPES, create_task

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/{agent_type}/trigger", response_model=TriggerAgentOut, status_code=202)
async def trigger_agent(
    agent_type: str,
    body: TriggerAgentIn | None = None,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    if agent_type not in VALID_AGENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown agent type '{agent_type}'. Valid: {sorted(VALID_AGENT_TYPES)}",
        )

    body = body or TriggerAgentIn()
    title = body.task_title or f"Manual {agent_type.replace('_', ' ').title()} run"
    task = await create_task(
        db,
        title=title,
        agent_type=agent_type,
        description=body.task_description,
        priority=1,
        source="manual",
        metadata=body.metadata,
    )

    # Enqueue in Celery (import here to avoid circular import at module load time)
    try:
        from celery_app.tasks.agent_tasks import run_agent_task
        run_agent_task.delay(task.id)
    except Exception:
        pass  # Celery not available in test environments

    return TriggerAgentOut(
        status="queued",
        task_id=task.id,
        message=f"Agent '{agent_type}' task queued (id={task.id})",
    )


@router.get("/status", response_model=list[AgentStatusOut])
async def get_agent_status(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    from sqlalchemy import func, select
    from app.models.task import AgentRun, Task
    from datetime import date, datetime

    today_start = datetime.combine(date.today(), datetime.min.time())
    statuses = []

    for agent_type in sorted(VALID_AGENT_TYPES):
        last_run = await db.execute(
            select(AgentRun)
            .where(AgentRun.agent_type == agent_type)
            .order_by(AgentRun.started_at.desc())
            .limit(1)
        )
        last = last_run.scalar_one_or_none()

        tasks_today = await db.execute(
            select(func.count(Task.id))
            .where(Task.agent_type == agent_type, Task.created_at >= today_start)
        )
        tasks_total = await db.execute(
            select(func.count(Task.id)).where(Task.agent_type == agent_type)
        )

        statuses.append(
            AgentStatusOut(
                agent_type=agent_type,
                last_run_at=last.started_at if last else None,
                last_run_status=last.status if last else None,
                tasks_today=tasks_today.scalar() or 0,
                tasks_total=tasks_total.scalar() or 0,
            )
        )

    return statuses
