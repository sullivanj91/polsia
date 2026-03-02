"""Agent registry and task dispatcher."""
from typing import Any

from app.agents.base_agent import BasePolsiaAgent


def _lazy_import(module_path: str, class_name: str) -> type[BasePolsiaAgent]:
    """Lazy-import an agent class to avoid circular imports."""
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


AGENT_MAP: dict[str, tuple[str, str]] = {
    "orchestrator": ("app.agents.orchestrator.daily_orchestrator", "DailyOrchestratorAgent"),
    "business_planning": ("app.agents.business_planning.agent", "BusinessPlanningAgent"),
    "competitor_research": ("app.agents.competitor_research.agent", "CompetitorResearchAgent"),
    "social_media": ("app.agents.social_media.agent", "SocialMediaAgent"),
    "ads_management": ("app.agents.ads_management.agent", "AdsManagementAgent"),
    "email_outreach": ("app.agents.email_outreach.agent", "EmailOutreachAgent"),
    "code_generation": ("app.agents.code_generation.agent", "CodeGenerationAgent"),
    "customer_support": ("app.agents.customer_support.agent", "CustomerSupportAgent"),
    "finance": ("app.agents.finance.agent", "FinanceAgent"),
}


def get_agent(agent_type: str) -> BasePolsiaAgent:
    if agent_type not in AGENT_MAP:
        raise ValueError(f"Unknown agent type: {agent_type}. Valid: {sorted(AGENT_MAP)}")
    module_path, class_name = AGENT_MAP[agent_type]
    cls = _lazy_import(module_path, class_name)
    return cls()


def run_agent_for_task(agent_type: str, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Instantiate the agent and run it. Returns the result dict."""
    agent = get_agent(agent_type)
    return agent.timed_run(task, context)
