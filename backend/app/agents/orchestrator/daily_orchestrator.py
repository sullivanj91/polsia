"""Daily Orchestrator Agent — Chief Operating Officer of the autonomous company."""
from typing import Any

from app.agents.base_agent import BasePolsiaAgent
from app.services.company_service import build_context_prompt

MORNING_SYSTEM_PROMPT = """You are the Chief Operating Officer of an autonomous AI company.
Your job is to create a prioritized daily task plan based on the company context.
Return a JSON object with:
{
  "summary": "brief morning plan summary",
  "tasks": [
    {
      "title": "task title",
      "description": "what to do and why",
      "agent_type": "one of: business_planning|competitor_research|social_media|ads_management|email_outreach|code_generation|customer_support|finance",
      "priority": 1-5
    }
  ],
  "key_focus": "the #1 priority theme for today"
}
Generate 5-8 tasks. Ensure at least one revenue-generating task daily.
"""

EVENING_SYSTEM_PROMPT = """You are the Chief Operating Officer reviewing today's performance.
Based on the context provided, write an evening summary.
Return a JSON object with:
{
  "summary": "2-3 sentence performance summary",
  "insights": ["insight 1", "insight 2", "insight 3"],
  "tomorrow_priorities": ["priority 1", "priority 2"]
}
"""


class DailyOrchestratorAgent(BasePolsiaAgent):
    agent_type = "orchestrator"
    default_model = "claude-sonnet-4-6"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        context_str = build_context_prompt(context)
        title = task.get("title", "")

        if "morning" in title.lower() or "plan" in title.lower():
            return self._morning_plan(context_str, context)
        else:
            return self._evening_summary(context_str, context)

    def _morning_plan(self, context_str: str, context: dict) -> dict[str, Any]:
        prompt = f"""Company context:\n{context_str}\n\nCreate today's task plan."""

        result = self.call_claude_json(
            prompt=prompt,
            system_prompt=MORNING_SYSTEM_PROMPT,
        )

        return {
            "summary": result.get("summary", "Morning plan generated"),
            "tasks": result.get("tasks", []),
            "key_focus": result.get("key_focus", ""),
            "type": "morning_plan",
        }

    def _evening_summary(self, context_str: str, context: dict) -> dict[str, Any]:
        prompt = f"""Company context:\n{context_str}\n\nSummarize today's performance."""

        result = self.call_claude_json(
            prompt=prompt,
            system_prompt=EVENING_SYSTEM_PROMPT,
        )

        return {
            "summary": result.get("summary", "Evening summary generated"),
            "insights": result.get("insights", []),
            "tomorrow_priorities": result.get("tomorrow_priorities", []),
            "type": "evening_summary",
        }
