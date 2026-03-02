"""Finance Agent — Revenue monitoring, expense tracking, Stripe integration."""
from datetime import date
from typing import Any

from app.agents.base_agent import BasePolsiaAgent
from app.config import settings
from app.services.company_service import build_context_prompt

SYSTEM_PROMPT = """You are the CFO of a SaaS company.
Analyze financial metrics and provide actionable insights.
Return JSON:
{
  "summary": "financial health summary",
  "mrr_cents": 0,
  "arr_cents": 0,
  "active_subscribers": 0,
  "stripe_balance_cents": 0,
  "new_today": 0,
  "churned_today": 0,
  "total_revenue_month_cents": 0,
  "alerts": ["alert if any payment failures or anomalies"],
  "recommendations": ["recommendation 1"]
}
"""


class FinanceAgent(BasePolsiaAgent):
    agent_type = "finance"
    default_model = "claude-sonnet-4-6"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        stripe_data = self._fetch_stripe_data()
        context_str = build_context_prompt(context)

        prompt = f"""Company context:\n{context_str}\n\nTask: {task.get('title')}

Stripe data (today {date.today()}):
{stripe_data}

Analyze our financial position and provide insights."""

        result = self.call_claude_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)

        if settings.sandbox_mode:
            # Return mock data in sandbox
            return {
                "summary": f"[SANDBOX] {result.get('summary', 'Finance analysis complete')}",
                "mrr_cents": result.get("mrr_cents", 0),
                "arr_cents": result.get("arr_cents", 0),
                "active_subscribers": result.get("active_subscribers", 0),
                "stripe_balance_cents": result.get("stripe_balance_cents", 0),
                "new_today": result.get("new_today", 0),
                "churned_today": result.get("churned_today", 0),
                "total_revenue_month_cents": result.get("total_revenue_month_cents", 0),
                "alerts": result.get("alerts", []),
                "recommendations": result.get("recommendations", []),
                "saved_snapshot": False,
            }

        # Save revenue snapshot to DB
        self._save_snapshot(result)

        return {
            "summary": result.get("summary", "Finance snapshot saved"),
            "mrr_cents": result.get("mrr_cents", 0),
            "arr_cents": result.get("arr_cents", 0),
            "alerts": result.get("alerts", []),
            "recommendations": result.get("recommendations", []),
            "saved_snapshot": True,
        }

    def _fetch_stripe_data(self) -> str:
        if settings.sandbox_mode or not settings.stripe_secret_key:
            return "Sandbox mode — no real Stripe data. Assume $0 MRR, 0 subscribers."

        try:
            import stripe
            stripe.api_key = settings.stripe_secret_key

            # Get balance
            balance = stripe.Balance.retrieve()
            available = sum(b["amount"] for b in balance["available"])

            # Get recent charges
            charges = stripe.Charge.list(limit=10, created={"gte": self._month_start_ts()})
            total_month = sum(c["amount"] for c in charges["data"] if c["paid"])
            failed_count = sum(1 for c in charges["data"] if not c["paid"])

            # Get subscriptions
            subs = stripe.Subscription.list(status="active", limit=100)
            active_count = len(subs["data"])
            mrr = sum(
                s["items"]["data"][0]["price"]["unit_amount"] or 0
                for s in subs["data"]
                if s["items"]["data"]
            )

            return (
                f"Balance: {available} cents\n"
                f"Active subscriptions: {active_count}\n"
                f"MRR (cents): {mrr}\n"
                f"Revenue this month (cents): {total_month}\n"
                f"Failed charges this month: {failed_count}"
            )
        except Exception as e:
            return f"Stripe API error: {e}"

    def _month_start_ts(self) -> int:
        import calendar
        today = date.today()
        month_start = date(today.year, today.month, 1)
        return int(calendar.timegm(month_start.timetuple()))

    def _save_snapshot(self, result: dict) -> None:
        """Persist revenue snapshot to DB (sync call from agent context)."""
        import asyncio
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
        from app.models.finance import RevenueSnapshot

        async def _inner():
            engine = create_async_engine(settings.database_url)
            Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with Session() as db:
                snap = RevenueSnapshot(
                    snapshot_date=date.today(),
                    mrr_cents=result.get("mrr_cents", 0),
                    arr_cents=result.get("arr_cents", 0),
                    active_subscribers=result.get("active_subscribers", 0),
                    churned_today=result.get("churned_today", 0),
                    new_today=result.get("new_today", 0),
                    total_revenue_month_cents=result.get("total_revenue_month_cents", 0),
                    stripe_balance_cents=result.get("stripe_balance_cents", 0),
                )
                db.add(snap)
                try:
                    await db.commit()
                except Exception:
                    await db.rollback()  # Already exists for today
            await engine.dispose()

        asyncio.run(_inner())
