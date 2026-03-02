import hashlib
import hmac
from datetime import date

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.ads import AdCampaign
from app.models.finance import ExpenseRecord, RevenueSnapshot, StripeEvent
from app.schemas.finance import (
    ExpenseRecordOut,
    FinanceSummary,
    RevenueSnapshotOut,
    StripeEventOut,
)

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/summary", response_model=FinanceSummary)
async def get_finance_summary(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    # Latest revenue snapshot
    snap_result = await db.execute(
        select(RevenueSnapshot).order_by(RevenueSnapshot.snapshot_date.desc()).limit(1)
    )
    snap = snap_result.scalar_one_or_none()

    # Total ad spend
    ad_spend = await db.execute(select(func.sum(AdCampaign.total_spent_usd)))
    total_ad_spend = float(ad_spend.scalar() or 0)

    # Month expenses
    today = date.today()
    month_start = today.replace(day=1)
    exp_total = await db.execute(
        select(func.sum(ExpenseRecord.amount_cents)).where(
            ExpenseRecord.date >= month_start
        )
    )
    total_expenses = int(exp_total.scalar() or 0)

    return FinanceSummary(
        mrr_cents=snap.mrr_cents if snap else 0,
        arr_cents=snap.arr_cents if snap else 0,
        active_subscribers=snap.active_subscribers if snap else 0,
        total_ad_spend_usd=total_ad_spend,
        total_expenses_month_cents=total_expenses,
        stripe_balance_cents=snap.stripe_balance_cents if snap else 0,
        last_snapshot_date=snap.snapshot_date if snap else None,
    )


@router.get("/revenue", response_model=list[RevenueSnapshotOut])
async def get_revenue_snapshots(
    limit: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        select(RevenueSnapshot).order_by(RevenueSnapshot.snapshot_date.desc()).limit(limit)
    )
    return list(result.scalars().all())


@router.get("/expenses", response_model=list[ExpenseRecordOut])
async def get_expenses(
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    q = select(ExpenseRecord).order_by(ExpenseRecord.date.desc()).limit(limit)
    if category:
        q = q.where(ExpenseRecord.category == category)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/events", response_model=list[StripeEventOut])
async def get_stripe_events(
    event_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    q = select(StripeEvent).order_by(StripeEvent.processed_at.desc()).limit(limit)
    if event_type:
        q = q.where(StripeEvent.event_type == event_type)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("/stripe/webhook", status_code=200)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive and validate Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe webhook secret not configured",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe signature"
        )

    event_data = event.get("data", {}).get("object", {})
    stripe_event = StripeEvent(
        stripe_event_id=event["id"],
        event_type=event["type"],
        customer_id=event_data.get("customer"),
        amount_cents=event_data.get("amount"),
        currency=event_data.get("currency"),
        status="processed",
        raw_payload=dict(event),
    )

    try:
        db.add(stripe_event)
        await db.flush()
    except Exception:
        pass  # Duplicate event — idempotent

    return {"received": True}
