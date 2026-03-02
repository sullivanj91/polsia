"""Customer Support Agent — Inbox monitoring and reply drafting."""
from typing import Any

from app.agents.base_agent import BasePolsiaAgent
from app.config import settings
from app.services.company_service import build_context_prompt

SYSTEM_PROMPT = """You are a Customer Success Manager.
Draft empathetic, helpful replies to customer emails.
Return JSON:
{
  "summary": "what you did",
  "replies": [
    {
      "to": "customer@email.com",
      "subject": "Re: ...",
      "body": "reply body",
      "sentiment": "positive|neutral|negative|urgent",
      "category": "billing|feature|bug|general"
    }
  ]
}
Be concise, friendly, and solution-focused.
"""


class CustomerSupportAgent(BasePolsiaAgent):
    agent_type = "customer_support"
    default_model = "claude-haiku-4-5-20251001"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        context_str = build_context_prompt(context)

        # In real mode, fetch emails from IMAP
        emails_text = ""
        if not settings.sandbox_mode and settings.imap_user:
            emails_text = self._fetch_emails()

        prompt = f"""Company context:\n{context_str}\n\nTask: {task.get('title')}

{f'Incoming emails:{chr(10)}{emails_text}' if emails_text else 'No new emails — draft sample responses for common support queries.'}

Draft helpful replies."""

        result = self.call_claude_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        replies = result.get("replies", [])

        if settings.sandbox_mode:
            return {
                "summary": f"[SANDBOX] Drafted {len(replies)} support replies (not sent)",
                "replies": replies,
                "sent": False,
            }

        return {
            "summary": result.get("summary", f"Processed {len(replies)} support emails"),
            "replies": replies,
            "sent": True,
        }

    def _fetch_emails(self) -> str:
        try:
            import imaplib
            import email as email_lib
            from email.header import decode_header

            mail = imaplib.IMAP4_SSL(settings.imap_host)
            mail.login(settings.imap_user, settings.imap_password)
            mail.select("inbox")
            _, msgs = mail.search(None, "UNSEEN")
            emails = []
            for num in msgs[0].split()[:5]:  # Max 5 unread
                _, data = mail.fetch(num, "(RFC822)")
                msg = email_lib.message_from_bytes(data[0][1])
                subject, _ = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()[:500]
                else:
                    body = msg.get_payload(decode=True).decode()[:500]
                emails.append(f"From: {msg['From']}\nSubject: {subject}\n{body}")
            mail.logout()
            return "\n\n---\n\n".join(emails)
        except Exception:
            return ""
