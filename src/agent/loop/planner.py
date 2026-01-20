"""
Agent Planner

Generates execution plans from user tasks using the AI Gateway.
"""

import json
import logging
from typing import Optional

from src.ai.gateway import get_gateway, AIMessage, GenerationConfig
from src.agent.models.plan import AgentPlan, PlanStep
from src.agent.registry import get_tool_registry

logger = logging.getLogger(__name__)


class AgentPlanner:
    """Generate execution plans from user tasks."""

    SYSTEM_PROMPT = '''You are a planning agent. Break down the user's task into concrete, executable steps.

Available tools:
{tools}

Return a JSON object with:
- "overview": One sentence summary of your approach
- "steps": Array of step objects, each with:
  - "description": What this step accomplishes
  - "tool_name": Name of tool to use (optional, null if no tool needed)
  - "tool_params": Parameters for the tool (optional, empty object if no tool)
  - "dependencies": Array of step indices (0-based) that must complete first

Guidelines:
- Keep plans simple: 3-7 steps typically sufficient
- Each step should be atomic and verifiable
- Use tools when available; describe manual reasoning otherwise
- Order steps logically with correct dependencies

Return ONLY valid JSON, no markdown formatting.'''

    def __init__(self):
        self.gateway = get_gateway()
        self.registry = get_tool_registry()

    def _get_tools_description(self) -> str:
        """Get formatted tool descriptions for prompt."""
        definitions = self.registry.get_all_definitions()
        if not definitions:
            return "No tools available."

        lines = []
        for d in definitions:
            params = json.dumps(d.parameters, indent=2)
            lines.append(f"- {d.name}: {d.description}\n  Parameters: {params}")
        return "\n".join(lines)

    async def create_plan(self, task: str, context: Optional[dict] = None) -> AgentPlan:
        """
        Generate an execution plan for the given task.

        Args:
            task: User's task description
            context: Optional context (e.g., prior conversation)

        Returns:
            AgentPlan with steps
        """
        tools_desc = self._get_tools_description()
        system_content = self.SYSTEM_PROMPT.format(tools=tools_desc)

        messages = [
            AIMessage(role="system", content=system_content),
            AIMessage(role="user", content=f"Task: {task}")
        ]

        try:
            response = await self.gateway.chat(
                messages=messages,
                config=GenerationConfig(max_tokens=2048, temperature=0.2)
            )

            # Parse response
            text = response.content.strip()

            # Clean potential markdown wrapping
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [line for line in lines if not line.startswith("```")]
                text = "\n".join(lines)

            data = json.loads(text)

            # Build plan
            plan = AgentPlan(
                task=task,
                overview=data.get("overview", "Plan generated")
            )

            # Convert step indices to UUIDs for dependencies
            raw_steps = data.get("steps", [])
            step_ids = []

            for i, step_data in enumerate(raw_steps):
                step = PlanStep(
                    description=step_data.get("description", f"Step {i+1}"),
                    tool_name=step_data.get("tool_name"),
                    tool_params=step_data.get("tool_params", {}),
                )
                step_ids.append(step.id)
                plan.steps.append(step)

            # Resolve dependencies (indices to IDs)
            for i, step_data in enumerate(raw_steps):
                dep_indices = step_data.get("dependencies", [])
                for idx in dep_indices:
                    if 0 <= idx < len(step_ids) and idx != i:
                        plan.steps[i].dependencies.append(step_ids[idx])

            logger.info(f"Created plan with {len(plan.steps)} steps for task: {task[:50]}...")
            return plan

        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            # Fallback: single-step plan
            return AgentPlan(
                task=task,
                overview=f"Fallback plan (planning failed: {e})",
                steps=[
                    PlanStep(
                        description=f"Execute task directly: {task}",
                        tool_name=None,
                        tool_params={}
                    )
                ]
            )
