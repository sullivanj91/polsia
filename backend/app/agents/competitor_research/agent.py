"""Competitor Research Agent — Web research and competitive intelligence."""
from typing import Any

from app.agents.base_agent import BasePolsiaAgent
from app.config import settings
from app.services.company_service import build_context_prompt

SYSTEM_PROMPT = """You are a Market Intelligence Analyst.
Research competitors and extract strategic intelligence.
Return JSON:
{
  "competitors": [
    {
      "name": "Competitor Name",
      "website": "https://...",
      "positioning": "how they position themselves",
      "pricing_summary": "pricing overview",
      "strengths": ["strength 1", "strength 2"],
      "weaknesses": ["weakness 1"],
      "key_differentiator": "what makes them unique"
    }
  ],
  "summary": "key competitive insights",
  "opportunities": ["opportunity 1", "opportunity 2"]
}
"""


class CompetitorResearchAgent(BasePolsiaAgent):
    agent_type = "competitor_research"
    default_model = "claude-sonnet-4-6"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        context_str = build_context_prompt(context)

        # In non-sandbox mode, use Tavily to get fresh competitor data
        search_results = ""
        if not settings.sandbox_mode and settings.tavily_api_key:
            try:
                from tavily import TavilyClient
                client = TavilyClient(api_key=settings.tavily_api_key)
                company = context.get("company", {})
                query = f"{company.get('industry', '')} SaaS competitors pricing features 2026"
                resp = client.search(query, max_results=5)
                search_results = "\n\n".join(
                    f"Source: {r['url']}\n{r['content']}"
                    for r in resp.get("results", [])
                )
            except Exception:
                pass

        prompt = f"""Company context:\n{context_str}\n\nTask: {task.get('title')}
{task.get('description', '')}

{f'Web search results:{chr(10)}{search_results}' if search_results else ''}

Research and analyze our main competitors."""

        result = self.call_claude_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)

        return {
            "summary": result.get("summary", "Competitor research complete"),
            "competitors": result.get("competitors", []),
            "opportunities": result.get("opportunities", []),
        }
