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
from src.agent.models.cancel import (
    CancelMode,
    CancellationRequest,
    CancellationResult,
    ResultMode,
)
from src.agent.observability import TraceEntry, TraceSession, TraceStore, TraceViewer
from src.agent.registry import (
    AgentContext,
    BaseTool,
    ToolRegistry,
    get_tool_registry,
)
from src.agent.routing import (
    ModelRecommendation,
    ModelRouter,
    RoutingRule,
    RoutingRules,
    TaskCategory,
)
from src.agent.safety import KillSwitch, get_kill_switch
from src.agent.ui import AgentStatusIndicator, CancelDialog

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
    # Observability
    "TraceEntry",
    "TraceSession",
    "TraceStore",
    "TraceViewer",
    # Cancellation
    "CancelMode",
    "ResultMode",
    "CancellationRequest",
    "CancellationResult",
    # Routing
    "ModelRouter",
    "ModelRecommendation",
    "TaskCategory",
    "RoutingRules",
    "RoutingRule",
    # UI Components
    "AgentStatusIndicator",
    "CancelDialog",
    # Safety
    "KillSwitch",
    "get_kill_switch",
]
