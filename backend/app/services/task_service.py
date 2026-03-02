from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import AgentRun, Task

VALID_STATUSES = {"pending", "in_progress", "completed", "failed"}
VALID_AGENT_TYPES = {
    "orchestrator",
    "business_planning",
    "competitor_research",
    "social_media",
    "ads_management",
    "email_outreach",
    "code_generation",
    "customer_support",
    "finance",
}


async def create_task(
    db: AsyncSession,
    title: str,
    agent_type: str,
    description: str | None = None,
    priority: int = 3,
    source: str = "manual",
    scheduled_date: datetime | None = None,
    metadata: dict | None = None,
) -> Task:
    task = Task(
        title=title,
        description=description,
        agent_type=agent_type,
        priority=priority,
        source=source,
        scheduled_date=scheduled_date,
        metadata_=metadata or {},
    )
    db.add(task)
    await db.flush()
    return task


async def get_task(db: AsyncSession, task_id: int) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def list_tasks(
    db: AsyncSession,
    status: str | None = None,
    agent_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Task]:
    q = select(Task).order_by(Task.created_at.desc()).offset(offset).limit(limit)
    if status:
        q = q.where(Task.status == status)
    if agent_type:
        q = q.where(Task.agent_type == agent_type)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_task_status(
    db: AsyncSession,
    task_id: int,
    status: str,
    result_summary: str | None = None,
    error_message: str | None = None,
) -> Task | None:
    task = await get_task(db, task_id)
    if not task:
        return None
    task.status = status
    if result_summary is not None:
        task.result_summary = result_summary
    if error_message is not None:
        task.error_message = error_message
    await db.flush()
    return task


async def create_agent_run(
    db: AsyncSession,
    agent_type: str,
    task_id: int | None = None,
    run_type: str = "task",
    input_context: dict | None = None,
) -> AgentRun:
    run = AgentRun(
        task_id=task_id,
        agent_type=agent_type,
        run_type=run_type,
        input_context=input_context or {},
    )
    db.add(run)
    await db.flush()
    return run


async def finish_agent_run(
    db: AsyncSession,
    run_id: int,
    status: str,
    output: dict | None = None,
    raw_log: str | None = None,
    duration_secs: float | None = None,
) -> AgentRun | None:
    result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        return None
    run.status = status
    run.output = output or {}
    run.raw_log = raw_log
    run.duration_secs = duration_secs
    run.ended_at = datetime.utcnow()
    await db.flush()
    return run


async def get_tasks_today_summary(db: AsyncSession) -> dict:
    from datetime import date
    today_start = datetime.combine(date.today(), datetime.min.time())

    result = await db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.created_at >= today_start)
        .group_by(Task.status)
    )
    counts = {row[0]: row[1] for row in result.all()}
    return {
        "total": sum(counts.values()),
        "pending": counts.get("pending", 0),
        "in_progress": counts.get("in_progress", 0),
        "completed": counts.get("completed", 0),
        "failed": counts.get("failed", 0),
    }
