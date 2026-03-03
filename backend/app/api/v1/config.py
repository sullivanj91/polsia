from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_api_key
from app.schemas.company import CompanyConfigOut, CompanyConfigUpdate
from app.services.company_service import get_company_config

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=CompanyConfigOut)
async def get_config(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    config = await get_company_config(db)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No company config found")
    return config


@router.put("", response_model=CompanyConfigOut)
async def update_config(
    updates: CompanyConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    config = await get_company_config(db)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No company config found")

    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(config, field, value)

    await db.flush()
    await db.refresh(config)
    return config
