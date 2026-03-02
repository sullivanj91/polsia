from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.schemas.task import TaskCreate, TaskOut
from app.services.task_service import create_task, get_task, list_tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def get_tasks(
    status: str | None = Query(None),
    agent_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    return await list_tasks(db, status=status, agent_type=agent_type, limit=limit, offset=offset)


@router.post("", response_model=TaskOut, status_code=201)
async def create_task_endpoint(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    return await create_task(
        db,
        title=task_in.title,
        agent_type=task_in.agent_type,
        description=task_in.description,
        priority=task_in.priority,
        source=task_in.source,
        scheduled_date=task_in.scheduled_date,
        metadata=task_in.metadata_,
    )


@router.get("/{task_id}", response_model=TaskOut)
async def get_task_endpoint(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    from fastapi import HTTPException, status
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task
