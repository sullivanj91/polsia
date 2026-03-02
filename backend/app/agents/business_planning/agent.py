"""Business Planning Agent — Strategy, KPIs, and goals."""
from typing import Any

from app.agents.base_agent import BasePolsiaAgent
from app.services.company_service import build_context_prompt

SYSTEM_PROMPT = """You are the Chief Strategy Officer of a SaaS company.
Analyze the company's current position and provide strategic recommendations.
Return JSON:
{
  "summary": "strategic assessment summary",
  "recommended_actions": [
    {"action": "specific action", "rationale": "why", "priority": 1-5, "timeline": "this week|this month|this quarter"}
  ],
  "kpi_updates": {"mrr_usd": 0, "target_customers": 0},
  "risks": ["risk 1", "risk 2"],
  "opportunities": ["opportunity 1", "opportunity 2"]
}
"""


class BusinessPlanningAgent(BasePolsiaAgent):
    agent_type = "business_planning"
    default_model = "claude-sonnet-4-6"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        context_str = build_context_prompt(context)
        prompt = f"""Company context:\n{context_str}\n\nTask: {task.get('title')}
{task.get('description', '')}

Provide strategic analysis and recommendations."""

        result = self.call_claude_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)

        return {
            "summary": result.get("summary", "Strategy analysis complete"),
            "recommended_actions": result.get("recommended_actions", []),
            "kpi_updates": result.get("kpi_updates", {}),
            "risks": result.get("risks", []),
            "opportunities": result.get("opportunities", []),
        }
