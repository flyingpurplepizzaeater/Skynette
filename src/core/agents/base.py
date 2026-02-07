"""
Agents Module - Base definitions for Skynette Autonomous Agents.
Ported from AgentOrchestrator.
"""

from pydantic import BaseModel

from src.ai.gateway import AIMessage, get_gateway


class AgentResponse(BaseModel):
    agent_name: str
    result: str
    status: str = "success"


class BaseAgent:
    """Base class for all Skynette agents."""

    def __init__(self, name: str, role: str, instructions: str):
        self.name = name
        self.role = role
        self.instructions = instructions
        self.gateway = get_gateway()

    async def run(self, task: str) -> AgentResponse:
        raise NotImplementedError


class SkynetteAgent(BaseAgent):
    """Standard AI Agent using Skynette's AI Gateway."""

    async def run(self, task: str) -> AgentResponse:
        try:
            # Construct messages
            messages = [
                AIMessage(
                    role="system",
                    content=f"You are {self.name}. Role: {self.role}.\nInstructions: {self.instructions}",
                ),
                AIMessage(role="user", content=task),
            ]

            # Use gateway to chat
            response = await self.gateway.chat(messages)

            return AgentResponse(agent_name=self.name, result=response.content, status="success")
        except Exception as e:
            return AgentResponse(
                agent_name=self.name, result=f"Error executing task: {str(e)}", status="error"
            )


class AgentFactory:
    """Factory to create agents on the fly."""

    @staticmethod
    def create_agent(name: str, role: str) -> BaseAgent:
        instructions = f"You are an expert autonomous agent named {name}. Your role is: {role}. perform tasks thoroughly and concisely."
        return SkynetteAgent(name, role, instructions)
