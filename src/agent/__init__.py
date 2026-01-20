"""
Agent Module

Core agent infrastructure for autonomous task execution.
"""

from src.agent.budget import TokenBudget
from src.agent.events import AgentEventEmitter, EventSubscription
from src.agent.loop import AgentExecutor, AgentPlanner, ToolExecutionError
from src.agent.models import (
    AgentEvent,
    AgentPlan,
    AgentSession,
    AgentState,
    PlanStep,
    StepStatus,
    ToolCall,
    ToolDefinition,
    ToolResult,
)
from src.agent.registry import (
    AgentContext,
    BaseTool,
    ToolRegistry,
    get_tool_registry,
)

__all__ = [
    # State models
    "AgentState",
    "AgentSession",
    # Plan models
    "StepStatus",
    "PlanStep",
    "AgentPlan",
    # Event models
    "AgentEvent",
    # Tool models
    "ToolDefinition",
    "ToolCall",
    "ToolResult",
    # Budget
    "TokenBudget",
    # Events
    "AgentEventEmitter",
    "EventSubscription",
    # Loop
    "AgentExecutor",
    "AgentPlanner",
    "ToolExecutionError",
    # Registry
    "AgentContext",
    "BaseTool",
    "ToolRegistry",
    "get_tool_registry",
]
