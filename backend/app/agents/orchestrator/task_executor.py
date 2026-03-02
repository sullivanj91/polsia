"""Routes tasks to the correct agent based on agent_type."""
from typing import Any

from app.agents.crew_factory import run_agent_for_task


def execute_task(task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    agent_type = task.get("agent_type", "orchestrator")
    return run_agent_for_task(agent_type, task, context)
