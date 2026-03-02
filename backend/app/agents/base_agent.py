"""Base agent class — all 9 agents inherit from this.

LLM calls go through the Claude Code CLI (`claude -p`) as a subprocess.
Set CLAUDE_CLI_MOCK=true to bypass the real CLI in tests / CI.
"""
import json
import os
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Any

from app.config import settings


class BasePolsiaAgent(ABC):
    """Abstract base for all Polsia agents."""

    agent_type: str = "base"
    default_model: str = "claude-sonnet-4-6"

    def call_claude(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
        session_id: str | None = None,
        timeout: int = 120,
    ) -> str:
        """Call the Claude CLI in headless mode and return the text response.

        In CI / tests, set CLAUDE_CLI_MOCK=true to skip the real binary.
        """
        if os.getenv("CLAUDE_CLI_MOCK") or settings.claude_cli_mock:
            mock_resp = os.getenv("CLAUDE_CLI_MOCK_RESPONSE") or settings.claude_cli_mock_response
            try:
                return json.loads(mock_resp)["result"]
            except (json.JSONDecodeError, KeyError):
                return mock_resp

        model = model or self.default_model
        cmd = [
            settings.claude_cli_path,
            "-p", prompt,
            "--output-format", "json",
            "--model", model,
        ]
        if system_prompt:
            cmd += ["--system-prompt", system_prompt]
        if session_id:
            cmd += ["--resume", session_id]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Claude CLI exited {result.returncode}: {result.stderr[:500]}"
            )

        try:
            data = json.loads(result.stdout)
            return data.get("result", result.stdout)
        except json.JSONDecodeError:
            return result.stdout

    def call_claude_json(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
    ) -> dict[str, Any]:
        """Call Claude and parse response as JSON dict."""
        raw = self.call_claude(
            prompt=prompt + "\n\nRespond with valid JSON only.",
            system_prompt=system_prompt,
            model=model,
        )
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(raw)

    @abstractmethod
    def run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's primary task. Must return a result dict."""
        ...

    def timed_run(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Wrap run() with timing."""
        start = time.monotonic()
        result = self.run(task, context)
        result["duration_secs"] = round(time.monotonic() - start, 2)
        return result
