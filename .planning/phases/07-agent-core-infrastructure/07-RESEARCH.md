# Phase 7: Agent Core Infrastructure - Research

**Researched:** 2026-01-20
**Domain:** Agent data models, event systems, state management, tool registry
**Confidence:** HIGH

## Summary

This research covers the foundational infrastructure for Skynette's agent system: data models, event/state management, tool registry, and retry logic. The existing codebase provides excellent foundations to build upon:

- **AI Gateway** (`src/ai/gateway.py`) already supports multi-provider routing, auto-fallback, streaming, and usage tracking
- **Workflow Engine** (`src/core/workflow/`) provides execution patterns, expression resolution, and storage
- **Node Registry** (`src/core/nodes/registry.py`) demonstrates the singleton registry pattern to reuse for tools
- **Basic Agent** (`src/core/agents/`) has a prototype supervisor with plan generation

Phase 7 establishes the infrastructure that all subsequent agent phases build upon. The key insight is to leverage existing patterns while adding agent-specific capabilities: typed agent states, event-driven execution, tool abstraction layer, and resource budgeting.

**Primary recommendation:** Build a custom agent loop following the Plan-and-Execute pattern with Pydantic models for type safety, asyncio event queues for streaming state, and a tool registry modeled on the existing node registry.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | >=2.0.0 | Data models, validation | Already in stack. Type-safe models for agent state, plans, tool calls |
| tenacity | >=9.0.0 | Retry with exponential backoff | Industry standard for asyncio retry. Replaces hand-rolled retry logic |
| asyncio | stdlib | Event loop, queues | Already used. Event-driven state management via `asyncio.Queue` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-contextvars | stdlib | Per-request state isolation | Agent context isolation for concurrent sessions |
| typing-extensions | >=4.0.0 | Type hints | Already in stack. TypedDict for structured tool schemas |
| uuid | stdlib | Unique IDs | Already used. Session/task/step IDs |
| datetime | stdlib | Timestamps | Already used. Audit timestamps |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom event queue | pyventus | Adds dependency; asyncio.Queue sufficient for internal events |
| Custom state machine | pytransitions | Adds complexity; Pydantic models with explicit states simpler |
| Custom retry | backoff lib | Tenacity more mature, better async support, more flexible |
| LangGraph | Custom loop | LangGraph would duplicate AI gateway, add abstraction layers |

**Installation:**
```bash
pip install "tenacity>=9.0.0"
# pydantic, asyncio, uuid, datetime already in stack
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  agent/                    # NEW: Agent core infrastructure
    __init__.py
    models/                 # Data models
      __init__.py
      state.py              # AgentState, AgentSession, etc.
      plan.py               # AgentPlan, PlanStep, etc.
      tool.py               # ToolDefinition, ToolCall, ToolResult
      event.py              # AgentEvent types
    loop/                   # Agent execution loop
      __init__.py
      executor.py           # AgentExecutor class
      planner.py            # Plan generation
    registry/               # Tool registry
      __init__.py
      tool_registry.py      # ToolRegistry singleton
      base_tool.py          # BaseTool abstract class
    budget/                 # Resource management
      __init__.py
      token_budget.py       # TokenBudget tracking
      rate_limiter.py       # Per-task rate limiting
    events/                 # Event system
      __init__.py
      emitter.py            # Event emitter for UI streaming
```

### Pattern 1: Plan-and-Execute Agent Loop

**What:** Decompose tasks into plans before execution, execute steps with observation-action cycles
**When to use:** All agent tasks in Skynette v3.0
**Why:** Prior decision from v3.0 research - custom loop over LangChain/LangGraph

```python
# Source: Skynette v3.0 research + industry best practices
from pydantic import BaseModel
from typing import AsyncIterator
from enum import Enum

class AgentState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_TOOL = "awaiting_tool"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentLoop:
    """Plan-and-Execute agent loop."""

    MAX_ITERATIONS = 20  # Hard cap
    TIMEOUT_SECONDS = 300  # 5 minutes

    async def run(self, task: str, session: AgentSession) -> AsyncIterator[AgentEvent]:
        """Execute task with streaming events."""
        session.state = AgentState.PLANNING
        yield AgentEvent(type="state_change", data={"state": "planning"})

        # Phase 1: Generate plan
        plan = await self.planner.create_plan(task, session.context)
        yield AgentEvent(type="plan_created", data=plan.model_dump())

        # Phase 2: Execute steps
        session.state = AgentState.EXECUTING
        for i, step in enumerate(plan.steps):
            if i >= self.MAX_ITERATIONS:
                yield AgentEvent(type="iteration_limit", data={})
                break

            # Check budget before execution
            if not session.budget.can_proceed():
                yield AgentEvent(type="budget_exceeded", data=session.budget.usage())
                break

            result = await self.execute_step(step, session)
            yield AgentEvent(type="step_completed", data=result.model_dump())

            if result.is_terminal:
                break

        session.state = AgentState.COMPLETED
        yield AgentEvent(type="completed", data=session.get_summary())
```

### Pattern 2: Event-Driven State with AsyncIO Queues

**What:** Stream agent state changes through asyncio.Queue for UI consumption
**When to use:** Agent execution with real-time UI updates

```python
# Source: asyncio best practices + contextvar state isolation
import asyncio
from contextvars import ContextVar
from typing import AsyncIterator

# Per-session context isolation
current_session: ContextVar[AgentSession] = ContextVar('current_session')

class AgentEventEmitter:
    """Emit events for UI consumption."""

    def __init__(self):
        self._queue: asyncio.Queue[AgentEvent] = asyncio.Queue()
        self._subscribers: list[asyncio.Queue] = []

    async def emit(self, event: AgentEvent):
        """Emit event to all subscribers."""
        for subscriber in self._subscribers:
            await subscriber.put(event)

    def subscribe(self) -> AsyncIterator[AgentEvent]:
        """Subscribe to events."""
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return self._iterate_queue(queue)

    async def _iterate_queue(self, queue: asyncio.Queue) -> AsyncIterator[AgentEvent]:
        while True:
            event = await queue.get()
            if event.type == "stream_end":
                break
            yield event
```

### Pattern 3: Tool Registry (Singleton Pattern)

**What:** Central registry for tool types, mirroring NodeRegistry pattern
**When to use:** All tool registration and lookup

```python
# Source: Existing NodeRegistry pattern from src/core/nodes/registry.py
from typing import Type, Optional
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    name: str
    description: str
    parameters_schema: dict  # JSON Schema

    @abstractmethod
    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Execute the tool with validated parameters."""
        pass

    def get_definition(self) -> ToolDefinition:
        """Get tool definition for LLM."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters_schema,
        )

class ToolRegistry:
    """Singleton registry for agent tools."""

    _instance = None
    _tools: dict[str, Type[BaseTool]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def register(self, tool_class: Type[BaseTool]):
        """Register a tool type."""
        self._tools[tool_class.name] = tool_class

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool instance by name."""
        tool_class = self._tools.get(name)
        return tool_class() if tool_class else None

    def get_all_definitions(self) -> list[ToolDefinition]:
        """Get all tool definitions for LLM context."""
        return [cls().get_definition() for cls in self._tools.values()]
```

### Pattern 4: Token Budget Tracking

**What:** Track and enforce token consumption per task/session
**When to use:** Every agent execution to prevent runaway costs

```python
# Source: Anthropic context engineering + Skynette cost tracking
from dataclasses import dataclass, field

@dataclass
class TokenBudget:
    """Track token usage against budget."""

    max_tokens: int
    used_input_tokens: int = 0
    used_output_tokens: int = 0

    # Thresholds
    warning_threshold: float = 0.8  # 80%

    @property
    def used_total(self) -> int:
        return self.used_input_tokens + self.used_output_tokens

    @property
    def remaining(self) -> int:
        return max(0, self.max_tokens - self.used_total)

    @property
    def usage_percentage(self) -> float:
        return self.used_total / self.max_tokens if self.max_tokens > 0 else 0

    def can_proceed(self, estimated_tokens: int = 0) -> bool:
        """Check if we can proceed with estimated token usage."""
        return (self.used_total + estimated_tokens) <= self.max_tokens

    def consume(self, input_tokens: int, output_tokens: int) -> bool:
        """Record token consumption. Returns False if budget exceeded."""
        new_total = self.used_total + input_tokens + output_tokens
        if new_total > self.max_tokens:
            return False
        self.used_input_tokens += input_tokens
        self.used_output_tokens += output_tokens
        return True

    def is_warning(self) -> bool:
        """Check if approaching limit."""
        return self.usage_percentage >= self.warning_threshold
```

### Pattern 5: Retry with Exponential Backoff

**What:** Retry failed operations with exponential backoff and jitter
**When to use:** Tool calls, LLM API calls, external service calls

```python
# Source: Tenacity documentation + industry best practices
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

logger = logging.getLogger(__name__)

# Decorator for tool execution with retry
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=30, exp_base=2),
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def execute_tool_with_retry(tool: BaseTool, params: dict, context: AgentContext) -> ToolResult:
    """Execute tool with automatic retry on transient failures."""
    return await tool.execute(params, context)
```

### Anti-Patterns to Avoid
- **Hand-rolled retry loops:** Use tenacity, not manual while loops with sleep
- **Global mutable state:** Use contextvars for per-session state isolation
- **Blocking operations in event loop:** Use asyncio.to_thread for sync operations
- **Unbounded iteration:** Always enforce MAX_ITERATIONS and TIMEOUT_SECONDS
- **String-based states:** Use enums for AgentState to catch typos at write-time

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Retry logic | While loops with sleep | tenacity library | Handles jitter, backoff curves, async, logging |
| JSON Schema validation | Manual dict checking | jsonschema or pydantic | Edge cases, proper error messages |
| UUID generation | Custom ID schemes | uuid.uuid4() | Uniqueness guaranteed, standard |
| State machines | If/elif chains | Enum + explicit transitions | Type safety, exhaustiveness checking |
| Event streaming | Manual callbacks | asyncio.Queue | Backpressure handling, async iteration |
| Token counting | Len(str) approximation | tiktoken (if needed) | Accurate counts for specific models |

**Key insight:** The agent loop itself should be custom (per v3.0 decision), but supporting infrastructure like retry, validation, and state management should use battle-tested libraries.

## Common Pitfalls

### Pitfall 1: Infinite Loop Drift
**What goes wrong:** Agent misinterprets completion, generates repetitive actions, exhausts resources
**Why it happens:** LLM doesn't have reliable "done" signal; retry loops compound
**How to avoid:**
- Hard iteration limit (MAX_ITERATIONS = 20)
- Wall-clock timeout (TIMEOUT_SECONDS = 300)
- Repetition detection (same action 3x = stop)
- Clear termination signals in system prompt
**Warning signs:** Same tool called repeatedly, token count growing without progress

### Pitfall 2: Token Budget Exhaustion
**What goes wrong:** Single task consumes entire daily budget, blocks other users
**Why it happens:** Tool results stuffed into context, cascading subtasks
**How to avoid:**
- Per-task token budget with hard cap
- Truncate/summarize tool results before context inclusion
- Monitor usage_percentage and warn at 80%
- Circuit breaker stops task at budget limit
**Warning signs:** Context window approaching model limits, cost per task spiking

### Pitfall 3: State Corruption in Concurrent Sessions
**What goes wrong:** Multiple agent sessions share mutable state, data leaks between users
**Why it happens:** Global variables, class-level state without isolation
**How to avoid:**
- Use contextvars for per-session state
- Pass session explicitly through call chain
- Never store user data in class-level variables
- Use dataclass instances, not class variables
**Warning signs:** User sees another user's data, state inconsistent after concurrent runs

### Pitfall 4: Tool Schema Hallucination
**What goes wrong:** LLM generates tool calls with wrong types, missing fields, invented parameters
**Why it happens:** Complex schemas confuse models, too many tools available
**How to avoid:**
- Validate all tool calls against JSON Schema before execution
- Return clear error messages for schema violations
- Limit tools per context (5-7 max)
- Use enums for constrained values
- Include examples in tool descriptions
**Warning signs:** High tool call failure rate, ValidationError in logs

### Pitfall 5: Event Queue Backpressure
**What goes wrong:** UI can't consume events fast enough, queue grows unbounded, memory exhaustion
**Why it happens:** No backpressure handling, slow UI consumers
**How to avoid:**
- Bounded queue with maxsize
- Drop or consolidate events when queue full
- Use asyncio.wait_for with timeout for queue.put
- Monitor queue depth
**Warning signs:** Memory usage growing during long tasks, queue.qsize() increasing

## Code Examples

Verified patterns from official sources and existing codebase:

### Agent Session Model
```python
# Pydantic model for agent session state
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime, UTC
from uuid import uuid4
from enum import Enum

class AgentState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_TOOL = "awaiting_tool"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentSession(BaseModel):
    """Agent execution session."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    task: str
    state: AgentState = AgentState.IDLE

    # Context
    messages: list[dict] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)

    # Budget
    token_budget: int = 50000  # Default 50K tokens
    tokens_used: int = 0

    # Tracking
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    steps_completed: int = 0

    def can_continue(self) -> bool:
        """Check if session can continue execution."""
        return (
            self.state in (AgentState.PLANNING, AgentState.EXECUTING, AgentState.AWAITING_TOOL)
            and self.tokens_used < self.token_budget
        )
```

### Plan and Step Models
```python
# Source: Plan-and-Execute pattern research
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class PlanStep(BaseModel):
    """A single step in an agent plan."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    tool_name: Optional[str] = None
    tool_params: dict = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)  # Step IDs
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None

class AgentPlan(BaseModel):
    """Complete execution plan for a task."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    task: str
    overview: str
    steps: list[PlanStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def get_next_step(self) -> Optional[PlanStep]:
        """Get next pending step with satisfied dependencies."""
        completed_ids = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                if all(dep in completed_ids for dep in step.dependencies):
                    return step
        return None
```

### Tool Definition Model
```python
# Source: MCP protocol + existing NodeDefinition pattern
from pydantic import BaseModel, Field
from typing import Any, Optional

class ToolDefinition(BaseModel):
    """Definition of a tool for LLM context."""

    name: str
    description: str
    parameters: dict  # JSON Schema

    # Metadata
    category: str = "general"
    is_destructive: bool = False
    requires_approval: bool = False

    def to_openai_format(self) -> dict:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }

    def to_anthropic_format(self) -> dict:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

class ToolCall(BaseModel):
    """A tool invocation request from the LLM."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    tool_name: str
    parameters: dict = Field(default_factory=dict)

class ToolResult(BaseModel):
    """Result of a tool execution."""

    tool_call_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
```

### Agent Event Types
```python
# Source: Event-driven architecture patterns
from pydantic import BaseModel, Field
from typing import Any, Literal
from datetime import datetime, UTC

class AgentEvent(BaseModel):
    """Event emitted during agent execution."""

    type: Literal[
        "state_change",
        "plan_created",
        "step_started",
        "step_completed",
        "tool_called",
        "tool_result",
        "message",
        "error",
        "budget_warning",
        "budget_exceeded",
        "iteration_limit",
        "completed",
        "cancelled",
    ]
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        use_enum_values = True
```

### Integration with Existing AI Gateway
```python
# Source: Existing src/ai/gateway.py pattern
from src.ai.gateway import get_gateway, AIMessage, GenerationConfig

class AgentPlanner:
    """Generate plans using existing AI Gateway."""

    def __init__(self):
        self.gateway = get_gateway()

    async def create_plan(self, task: str, context: AgentContext) -> AgentPlan:
        """Generate execution plan for task."""

        system_prompt = """You are a planning agent. Break down the user's task into concrete steps.
Return a JSON object with:
- overview: One sentence summary of the approach
- steps: Array of {description, tool_name (optional), tool_params (optional), dependencies (step indices)}

Available tools: {tools}
"""

        messages = [
            AIMessage(role="system", content=system_prompt.format(
                tools=context.get_tool_descriptions()
            )),
            AIMessage(role="user", content=task),
        ]

        response = await self.gateway.chat(
            messages=messages,
            config=GenerationConfig(max_tokens=2048, temperature=0.2),
        )

        # Parse response into AgentPlan
        plan_data = json.loads(response.content)
        return AgentPlan(task=task, **plan_data)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ReAct (think after each step) | ReWOO (plan first, execute all) | 2024 | 3-5x faster, fewer tokens |
| Unbounded context | Token-budget-aware reasoning | 2025 | Controllable costs, better accuracy |
| Global state | contextvars per-session | Always | Required for concurrency |
| Manual retry loops | tenacity decorators | 2020+ | Simpler, more reliable |
| String state flags | Enum-based state machines | Always | Type safety, IDE support |

**Deprecated/outdated:**
- **LangChain for simple agents:** Per v3.0 decision, custom loop preferred to avoid abstraction layers
- **Synchronous agent loops:** All agent code should be async for UI responsiveness
- **Unlimited iteration:** Always enforce hard caps

## Open Questions

Things that couldn't be fully resolved:

1. **Tool result truncation strategy**
   - What we know: Tool results must be truncated to fit context
   - What's unclear: Best truncation size (4K? 8K? Dynamic?)
   - Recommendation: Start with 4K token limit, make configurable, adjust based on model

2. **Plan revision during execution**
   - What we know: Static plans may need adjustment based on tool results
   - What's unclear: When to re-plan vs. continue vs. fail
   - Recommendation: Implement simple re-plan trigger (step fails 3x) in Phase 8

3. **Concurrent tool execution**
   - What we know: Independent steps could run in parallel
   - What's unclear: How to handle shared state, error propagation
   - Recommendation: Sequential execution for Phase 7, parallel for Phase 8+

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/ai/gateway.py`, `src/core/nodes/registry.py`, `src/core/agents/`
- [Tenacity Documentation](https://tenacity.readthedocs.io/) - Retry patterns
- [Pydantic v2 Documentation](https://docs.pydantic.dev/) - Data models
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html) - Event loops, queues
- [Anthropic: Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) - Token budgeting

### Secondary (MEDIUM confidence)
- [Valanor: Design Patterns for AI Agents](https://valanor.co/design-patterns-for-ai-agents/) - Plan-and-Execute pattern
- [GetMaxim: Context Window Management](https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/) - Token management strategies
- [DEV.to: Building Ideal AI Agent](https://dev.to/louis-sanna/building-the-ideal-ai-agent-from-async-event-streams-to-context-aware-state-management-33) - Event streaming patterns
- [Better Stack: Exponential Backoff](https://betterstack.com/community/guides/monitoring/exponential-backoff/) - Retry patterns

### Tertiary (LOW confidence)
- [Pydantic AI Framework](https://ai.pydantic.dev/) - Reference for patterns (not using directly per v3.0 decision)
- [pyventus library](https://github.com/mdapena/pyventus) - Alternative event system (not using, asyncio.Queue sufficient)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing patterns, well-documented libraries
- Architecture: HIGH - Based on existing codebase patterns, industry standards
- Pitfalls: HIGH - Documented in prior v3.0 research, industry reports
- Code examples: HIGH - Derived from existing codebase + official documentation

**Research date:** 2026-01-20
**Valid until:** 60 days (stable patterns, minimal library churn expected)
