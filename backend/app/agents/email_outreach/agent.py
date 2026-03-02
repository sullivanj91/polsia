"""Email Outreach Agent — Prospect finding and personalized cold email."""
from typing import Any

from app.agents.base_agent import BasePolsiaAgent
from app.config import settings
from app.services.company_service import build_context_prompt

SYSTEM_PROMPT = """You are a Sales Development Representative.
Write personalized, concise cold emails that get replies.
Return JSON:
{
  "summary": "what you did",
  "emails": [
    {
      "to": "prospect@company.com",
      "first_name": "Name",
      "company": "Company",
      "subject": "subject line",
      "body": "email body (3-4 sentences max, personal, specific)"
    }
  ]
}
Keep emails under 100 words. Lead with value, not features.
"""


class EmailOutreachAgent(BasePolsiaAgent):
    agent_type = "email_outreach"
    default_model = "claude-sonnet-4-6"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        context_str = build_context_prompt(context)
        prompt = f"""Company context:\n{context_str}\n\nTask: {task.get('title')}
{task.get('description', '')}

Write 3 personalized outreach emails for potential customers in our target market."""

        result = self.call_claude_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        emails = result.get("emails", [])

        if settings.sandbox_mode:
            return {
                "summary": f"[SANDBOX] Drafted {len(emails)} emails (not sent)",
                "emails": emails,
                "sent": False,
            }

        # Real mode — send via SendGrid
        sent = []
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            sg = SendGridAPIClient(api_key=settings.sendgrid_api_key)
            for email in emails:
                msg = Mail(
                    from_email=settings.sendgrid_from_email,
                    to_emails=email["to"],
                    subject=email["subject"],
                    plain_text_content=email["body"],
                )
                sg.send(msg)
                sent.append(email["to"])
        except Exception as e:
            return {"summary": f"SendGrid error: {e}", "emails": emails, "sent": False}

        return {
            "summary": f"Sent {len(sent)} outreach emails",
            "emails": emails,
            "sent_to": sent,
            "sent": True,
        }
