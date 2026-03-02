"""Code Generation Agent — Write code, commit, and deploy."""
from typing import Any

from app.agents.base_agent import BasePolsiaAgent
from app.config import settings
from app.services.company_service import build_context_prompt

SYSTEM_PROMPT = """You are a Full-Stack Engineer.
Write production-ready code based on the task requirements.
Return JSON:
{
  "summary": "what was built and why",
  "files": [
    {"path": "relative/path/file.py", "content": "file content here", "description": "what this file does"}
  ],
  "commit_message": "feat: short description of change",
  "deployment_notes": "any notes about deployment"
}
Write clean, well-commented code. Follow existing patterns.
"""


class CodeGenerationAgent(BasePolsiaAgent):
    agent_type = "code_generation"
    default_model = "claude-sonnet-4-6"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        context_str = build_context_prompt(context)
        prompt = f"""Company context:\n{context_str}\n\nTask: {task.get('title')}
{task.get('description', '')}

Write the required code."""

        result = self.call_claude_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        files = result.get("files", [])

        if settings.sandbox_mode:
            return {
                "summary": f"[SANDBOX] Generated {len(files)} file(s) (not committed)",
                "files": files,
                "commit_message": result.get("commit_message", ""),
                "committed": False,
            }

        # Real mode — commit to GitHub
        committed = False
        if settings.github_token and settings.github_repo:
            try:
                from github import Github
                g = Github(settings.github_token)
                repo = g.get_repo(settings.github_repo)
                for f in files:
                    try:
                        existing = repo.get_contents(f["path"])
                        repo.update_file(
                            f["path"],
                            result.get("commit_message", "Update file"),
                            f["content"],
                            existing.sha,
                        )
                    except Exception:
                        repo.create_file(
                            f["path"],
                            result.get("commit_message", "Add file"),
                            f["content"],
                        )
                committed = True
            except Exception as e:
                return {"summary": f"GitHub error: {e}", "files": files, "committed": False}

        return {
            "summary": result.get("summary", f"Generated and committed {len(files)} file(s)"),
            "files": files,
            "commit_message": result.get("commit_message", ""),
            "committed": committed,
        }
