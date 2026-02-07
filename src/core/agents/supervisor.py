"""
Supervisor Agent - Orchestrates multi-agent tasks.
Ported and adapted from AgentOrchestrator for Skynette.
"""

import asyncio
import json
from collections.abc import AsyncIterator

from pydantic import BaseModel

from src.ai.gateway import AIMessage, get_gateway
from src.core.agents.base import AgentFactory


class SubTask(BaseModel):
    agent_name: str
    agent_role: str
    task_description: str


class SupervisorPlan(BaseModel):
    plan_overview: str
    subtasks: list[SubTask]


class Supervisor:
    """
    The Supervisor breaks down complex user requests into subtasks
    and delegates them to specialized agents.
    """

    def __init__(self):
        self.gateway = get_gateway()

    async def create_plan(self, user_prompt: str) -> SupervisorPlan:
        """Generate a plan using the AI Gateway."""

        system_prompt = """
You are a Supervisor Agent for the Skynette Platform.
Your goal is to break down a complex user request into parallelizable subtasks.
Identify the specialized agents needed (e.g., Coder, Historian, Analyst).

Return the response strictly as valid JSON matching this schema:
{
    "plan_overview": "One sentence summary",
    "subtasks": [
        {"agent_name": "Name", "agent_role": "Role description", "task_description": "Specific task"}
    ]
}
Do not include markdown formatting like ```json ... ```. Just the raw JSON.
"""

        try:
            messages = [
                AIMessage(role="system", content=system_prompt),
                AIMessage(role="user", content=f"User Request: {user_prompt}"),
            ]

            # Use gateway to generate plan
            response = await self.gateway.chat(messages)
            text = response.content.strip()

            # Clean potential markdown
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines)

            data = json.loads(text)
            return SupervisorPlan(**data)

        except Exception as e:
            # Fallback plan
            print(f"Plan generation failed: {e}")
            return SupervisorPlan(
                plan_overview="Plan generation failed. Executing as single task.",
                subtasks=[
                    SubTask(
                        agent_name="GeneralBot",
                        agent_role="General Assistant",
                        task_description=user_prompt,
                    )
                ],
            )

    async def execute(self, user_prompt: str) -> AsyncIterator[dict]:
        """Execute the supervisor loop, yielding events."""

        # 1. Plan
        plan = await self.create_plan(user_prompt)
        yield {"type": "plan", "data": plan}

        # 2. Create Agents & Tasks
        agents = []
        tasks = []
        for subtask in plan.subtasks:
            agent = AgentFactory.create_agent(subtask.agent_name, subtask.agent_role)
            agents.append(agent)
            tasks.append(subtask.task_description)

        # 3. Execute in Parallel
        # Create coroutines
        coroutines = [agent.run(task) for agent, task in zip(agents, tasks)]

        # Yield results as they complete
        for completed_task in asyncio.as_completed(coroutines):
            result = await completed_task
            yield {"type": "result", "data": result}
