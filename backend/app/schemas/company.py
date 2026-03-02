from datetime import datetime

from pydantic import BaseModel


class CompanyConfigOut(BaseModel):
    id: int
    name: str
    mission: str | None
    vision: str | None
    description: str | None
    target_market: str | None
    value_prop: str | None
    pricing_model: dict | None
    goals: dict | None
    kpis: dict | None
    website_url: str | None
    github_repo: str | None
    product_type: str | None
    industry: str | None
    timezone: str
    daily_cycle_hour: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyConfigUpdate(BaseModel):
    name: str | None = None
    mission: str | None = None
    vision: str | None = None
    description: str | None = None
    target_market: str | None = None
    value_prop: str | None = None
    pricing_model: dict | None = None
    goals: dict | None = None
    kpis: dict | None = None
    website_url: str | None = None
    github_repo: str | None = None
    product_type: str | None = None
    industry: str | None = None
    timezone: str | None = None
    daily_cycle_hour: int | None = None
