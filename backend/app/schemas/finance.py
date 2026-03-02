from datetime import date, datetime

from pydantic import BaseModel


class StripeEventOut(BaseModel):
    id: int
    stripe_event_id: str
    event_type: str
    customer_id: str | None
    amount_cents: int | None
    currency: str | None
    status: str
    processed_at: datetime

    model_config = {"from_attributes": True}


class RevenueSnapshotOut(BaseModel):
    id: int
    snapshot_date: date
    mrr_cents: int
    arr_cents: int
    active_subscribers: int
    churned_today: int
    new_today: int
    total_revenue_month_cents: int
    stripe_balance_cents: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseRecordOut(BaseModel):
    id: int
    category: str
    vendor: str
    amount_cents: int
    currency: str
    description: str | None
    date: date
    external_ref: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FinanceSummary(BaseModel):
    mrr_cents: int
    arr_cents: int
    active_subscribers: int
    total_ad_spend_usd: float
    total_expenses_month_cents: int
    stripe_balance_cents: int
    last_snapshot_date: date | None
