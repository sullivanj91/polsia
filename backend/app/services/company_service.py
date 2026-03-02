from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyConfig
from app.models.report import DailyReport
from app.models.task import Task


async def get_company_config(db: AsyncSession) -> CompanyConfig | None:
    result = await db.execute(select(CompanyConfig).limit(1))
    return result.scalar_one_or_none()


async def get_full_context(db: AsyncSession) -> dict:
    """Build the full company context dict injected into every agent's system prompt."""
    config = await get_company_config(db)
    if not config:
        return {}

    # Yesterday's report
    yesterday = date.today() - timedelta(days=1)
    report_result = await db.execute(
        select(DailyReport).where(DailyReport.report_date == yesterday)
    )
    yesterday_report = report_result.scalar_one_or_none()

    # Today's tasks
    today = date.today()
    tasks_result = await db.execute(
        select(Task).where(Task.scheduled_date >= today)
    )
    todays_tasks = tasks_result.scalars().all()

    return {
        "company": {
            "name": config.name,
            "mission": config.mission,
            "vision": config.vision,
            "description": config.description,
            "target_market": config.target_market,
            "value_prop": config.value_prop,
            "pricing_model": config.pricing_model,
            "website_url": config.website_url,
            "product_type": config.product_type,
            "industry": config.industry,
        },
        "goals": config.goals or {},
        "kpis": config.kpis or {},
        "yesterday_summary": yesterday_report.evening_summary if yesterday_report else None,
        "yesterday_insights": yesterday_report.insights if yesterday_report else [],
        "todays_tasks": [
            {"id": t.id, "title": t.title, "agent_type": t.agent_type, "status": t.status}
            for t in todays_tasks
        ],
    }


def build_context_prompt(context: dict) -> str:
    """Convert context dict into a string for agent system prompts."""
    if not context:
        return "No company context available."

    c = context.get("company", {})
    lines = [
        f"## Company: {c.get('name', 'Unknown')}",
        f"Mission: {c.get('mission', 'N/A')}",
        f"Description: {c.get('description', 'N/A')}",
        f"Target market: {c.get('target_market', 'N/A')}",
        f"Value prop: {c.get('value_prop', 'N/A')}",
        "",
        "## Current KPIs",
    ]
    for k, v in context.get("kpis", {}).items():
        lines.append(f"  {k}: {v}")

    if context.get("yesterday_summary"):
        lines += ["", "## Yesterday's Summary", context["yesterday_summary"]]

    if context.get("todays_tasks"):
        lines += ["", "## Today's Planned Tasks"]
        for t in context["todays_tasks"]:
            lines.append(f"  [{t['status']}] {t['title']} ({t['agent_type']})")

    return "\n".join(lines)
