"""Ads Management Agent — Google + Meta campaign management."""
from typing import Any

from app.agents.base_agent import BasePolsiaAgent
from app.config import settings
from app.services.company_service import build_context_prompt

SYSTEM_PROMPT = """You are a Performance Marketing Manager.
Analyze ad performance and recommend optimizations.
Return JSON:
{
  "summary": "performance assessment and actions taken",
  "recommendations": [
    {"campaign": "campaign name", "action": "increase budget|pause|create|optimize", "reason": "why", "budget_change_usd": 0}
  ],
  "new_campaigns": [
    {"name": "campaign name", "platform": "google|meta", "goal": "awareness|leads|conversions", "budget_usd": 50, "targeting": "description"}
  ]
}
Focus on ROAS > 3x and CAC < LTV/3.
"""


class AdsManagementAgent(BasePolsiaAgent):
    agent_type = "ads_management"
    default_model = "claude-sonnet-4-6"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        context_str = build_context_prompt(context)
        prompt = f"""Company context:\n{context_str}\n\nTask: {task.get('title')}
{task.get('description', '')}

Analyze current ad performance and recommend optimizations."""

        result = self.call_claude_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)

        if settings.sandbox_mode:
            return {
                "summary": f"[SANDBOX] {result.get('summary', 'Ad analysis complete')}",
                "recommendations": result.get("recommendations", []),
                "new_campaigns": result.get("new_campaigns", []),
                "applied": False,
            }

        return {
            "summary": result.get("summary", "Ad management complete"),
            "recommendations": result.get("recommendations", []),
            "new_campaigns": result.get("new_campaigns", []),
            "applied": True,
        }
