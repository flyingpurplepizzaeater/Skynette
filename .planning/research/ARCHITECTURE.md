# Architecture Research: v3.0 Agent Integration

**Project:** Skynette v3.0 Agent Milestone
**Researched:** 2026-01-20
**Mode:** Architecture-focused research for agent system integration
**Overall Confidence:** HIGH (existing architecture well-documented, agent patterns well-established)

## Executive Summary

This research examines how to integrate an autonomous agent system into Skynette's existing Python/Flet architecture. The key findings are:

1. **Use Plan-and-Execute pattern** over ReAct for Skynette's use case (multi-step tasks, clear progress feedback, cost efficiency)
2. **MCP integration** is the standard for tool extensibility (adopted by OpenAI/Anthropic in 2025)
3. **Leverage existing systems** - AIGateway, RAG, and workflow engine can all be agent tools
4. **UI integration** requires async event streaming for responsive progress feedback
5. **Build order** follows dependencies: core loop first, then tools, then UI, then safety

---

## Agent Loop Pattern

### Recommendation: Hybrid Plan-and-Execute with ReAct Fallback

**Confidence:** HIGH (based on LangGraph tutorials, LangChain blog, production implementations)

#### Pattern Selection Rationale

| Pattern | Pros | Cons | Fit for Skynette |
|---------|------|------|------------------|
| **ReAct** | Adaptive, good for exploration | Expensive (LLM call per step), poor at long-term planning | MEDIUM - good for simple queries |
| **Plan-and-Execute** | Explicit planning visible to user, cheaper execution, better for multi-step | Less adaptive to surprises | HIGH - matches UI requirements |
| **Hybrid** | Plan first, ReAct for sub-tasks | More complex implementation | HIGH - best of both |

**Recommended Architecture:**

```
User Request
    |
    v
[Planner Agent] -- Uses large model (Claude/GPT-4)
    |
    v
Execution Plan (visible to user)
    |
    v
[Executor Loop] -- Can use smaller models
    |
    +---> [Tool Call] --> Result --> Update Plan
    |
    +---> [Sub-Agent] --> ReAct for complex sub-tasks
    |
    v
Progress Events --> UI
    |
    v
Final Result
```

**Why Plan-and-Execute for Skynette:**

1. **Visual Progress Feedback** - Users can see the plan before execution
2. **Cost Efficiency** - Planner uses large model, executors can use smaller models
3. **Approval Workflow** - Plans can be reviewed/modified before execution
4. **Debuggability** - Clear step-by-step execution matches existing workflow model
5. **Parallel Execution** - Independent steps can run concurrently

**Sources:**
- [Plan-and-Execute Agents - LangChain Blog](https://www.blog.langchain.com/planning-agents/)
- [Plan-and-Execute Tutorial - LangGraph](https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/)
- [ReAct vs Plan-and-Execute - DEV Community](https://dev.to/jamesli/react-vs-plan-and-execute-a-practical-comparison-of-llm-agent-patterns-4gh9)

#### Implementation Sketch

```python
# src/agents/planner.py

@dataclass
class AgentPlan:
    """User-visible execution plan."""
    goal: str
    steps: list[PlanStep]
    estimated_time: str
    requires_approval: list[str]  # Step IDs needing approval

@dataclass
class PlanStep:
    id: str
    description: str
    tool: str
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    depends_on: list[str]  # Step IDs this depends on
    approval_level: Literal["auto", "moderate", "manual"]

class AgentPlanner:
    """Creates execution plans from user requests."""

    async def create_plan(
        self,
        request: str,
        context: AgentContext,
        available_tools: list[ToolDefinition]
    ) -> AgentPlan:
        """Generate plan using large model."""
        # 1. Analyze request
        # 2. Determine required tools
        # 3. Create step sequence with dependencies
        # 4. Classify approval levels
        # 5. Return structured plan
```

---

## Component Integration

### Existing Systems to Expose as Agent Tools

Skynette has significant existing functionality that should be accessible to the agent:

| System | Location | Agent Tool Use |
|--------|----------|----------------|
| AIGateway | `src/ai/gateway.py` | Text generation, chat, embeddings |
| RAG Service | `src/rag/service.py` | Knowledge search, document queries |
| Code Executor | `src/core/nodes/execution/` | Run Python/JS/Bash scripts |
| File Operations | `src/core/nodes/data/` | Read/write files |
| HTTP Requests | `src/core/nodes/http/` | API calls, web requests |
| Git Operations | `src/core/coding/git_ops.py` | Clone, commit, push |

### MCP Integration Architecture

**Confidence:** HIGH (MCP is now industry standard, adopted by OpenAI March 2025)

```
Skynette Agent
    |
    |-- [Built-in Tools] -- Wrapped existing Skynette functions
    |       |
    |       +-- ai_generate (AIGateway.generate)
    |       +-- ai_chat (AIGateway.chat)
    |       +-- rag_query (RAGService.query)
    |       +-- code_execute (CodeRunner)
    |       +-- file_read/write
    |       +-- http_request
    |       +-- git_operations
    |
    |-- [MCP Client] -- Connects to external MCP servers
            |
            +-- [stdio transport] -- Local processes
            +-- [HTTP transport] -- Remote servers
            +-- Tool Discovery --> ToolRegistry
```

**MCP Client Implementation:**

```python
# src/agents/mcp/client.py

class MCPClient:
    """Connects to MCP servers and exposes their tools."""

    async def connect(self, server_config: MCPServerConfig) -> None:
        """Connect to MCP server via configured transport."""
        if server_config.transport == "stdio":
            self.transport = StdioTransport(server_config.command)
        elif server_config.transport == "http":
            self.transport = HTTPTransport(server_config.url)

        await self.transport.connect()
        self.tools = await self._discover_tools()

    async def _discover_tools(self) -> list[ToolDefinition]:
        """Fetch available tools from server."""
        response = await self.transport.request("tools/list")
        return [ToolDefinition.from_mcp(t) for t in response.tools]

    async def call_tool(self, name: str, args: dict) -> ToolResult:
        """Execute tool on MCP server."""
        response = await self.transport.request(
            "tools/call",
            {"name": name, "arguments": args}
        )
        return ToolResult.from_mcp(response)
```

**Sources:**
- [Model Context Protocol - Official Docs](https://modelcontextprotocol.io/)
- [mcp-agent GitHub](https://github.com/lastmile-ai/mcp-agent)
- [OpenAI Agents SDK - MCP](https://openai.github.io/openai-agents-python/mcp/)

### Tool Registry Pattern

```python
# src/agents/tools/registry.py

@dataclass
class ToolDefinition:
    """Unified tool definition (internal and MCP)."""
    name: str
    description: str
    parameters: dict  # JSON Schema
    category: str
    approval_level: Literal["auto", "moderate", "manual"]
    source: Literal["builtin", "mcp"]

class ToolRegistry:
    """Central registry for all agent tools."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, Callable] = {}
        self._mcp_clients: dict[str, MCPClient] = {}

    def register_builtin(
        self,
        name: str,
        handler: Callable,
        schema: dict,
        approval_level: str = "auto"
    ):
        """Register a built-in tool."""
        self._tools[name] = ToolDefinition(
            name=name,
            description=schema.get("description", ""),
            parameters=schema,
            category="builtin",
            approval_level=approval_level,
            source="builtin"
        )
        self._handlers[name] = handler

    async def connect_mcp_server(self, config: MCPServerConfig):
        """Connect to MCP server and register its tools."""
        client = MCPClient()
        await client.connect(config)

        for tool in client.tools:
            tool.source = "mcp"
            tool.approval_level = config.default_approval_level
            self._tools[f"{config.name}.{tool.name}"] = tool

        self._mcp_clients[config.name] = client

    async def call(self, name: str, args: dict) -> ToolResult:
        """Execute any tool (builtin or MCP)."""
        if name in self._handlers:
            return await self._handlers[name](**args)

        # MCP tool call (name format: "server.tool")
        server_name, tool_name = name.split(".", 1)
        return await self._mcp_clients[server_name].call_tool(tool_name, args)
```

---

## Data Flow

### Agent Execution Flow

```
1. User Input (via AgentsView or Code Editor)
         |
         v
2. [AgentOrchestrator.execute(request)]
         |
         v
3. [AgentPlanner.create_plan(request, context, tools)]
         |
    yield PlanCreatedEvent
         |
         v
4. User Approval (if required)
         |
         v
5. [AgentExecutor.execute_plan(plan)]
         |
    For each step:
         |
         +---> Check approval
         |         |
         |    yield ApprovalRequiredEvent (if needed)
         |         |
         +---> [ToolRegistry.call(tool_name, args)]
         |         |
         |    yield ToolStartEvent
         |         |
         |    <--- ToolResult
         |         |
         |    yield StepCompletedEvent
         |
         v
6. [Summarize results]
         |
    yield CompletionEvent
```

### State Management

**Confidence:** MEDIUM (patterns established but context window management is ongoing challenge)

| State Type | Storage | Lifetime | Implementation |
|------------|---------|----------|----------------|
| **Session State** | In-memory | Per conversation | `AgentSession` dataclass |
| **Plan State** | In-memory + SQLite | Per task | `AgentPlan` with persistence |
| **Conversation History** | In-memory with pruning | Per session | Sliding window + summarization |
| **Long-term Memory** | SQLite + RAG | Cross-session | Optional semantic retrieval |
| **MCP Server State** | In-memory | Application lifetime | `MCPClient` connections |

**Session State Model:**

```python
# src/agents/state.py

@dataclass
class AgentSession:
    """Manages state for an agent conversation."""
    id: str
    started_at: datetime

    # Conversation
    messages: list[AgentMessage]
    context_window_used: int
    max_context_window: int

    # Current task
    current_plan: Optional[AgentPlan] = None
    pending_approvals: list[ApprovalRequest] = field(default_factory=list)

    # Tool state
    tool_results: dict[str, ToolResult] = field(default_factory=dict)

    def add_message(self, msg: AgentMessage):
        """Add message with context window management."""
        self.messages.append(msg)
        self.context_window_used += msg.token_count

        # Prune if needed
        if self.context_window_used > self.max_context_window * 0.8:
            self._prune_old_messages()

    def _prune_old_messages(self):
        """Remove old messages, keeping system prompt and recent context."""
        # Keep: system, last N messages, tool results referenced in recent messages
        pass
```

**Sources:**
- [Memory Overview - LangChain Docs](https://docs.langchain.com/oss/python/concepts/memory)
- [Sessions - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/sessions/)
- [Context Engineering - OpenAI Cookbook](https://cookbook.openai.com/examples/agents_sdk/session_memory)

---

## UI Integration

### Async Event Streaming for Progress Feedback

**Confidence:** HIGH (Flet async patterns well-documented, matches existing chat streaming)

Skynette already has streaming in ChatPanel (`chat_stream`). Agent UI extends this pattern.

**Event Types:**

```python
# src/agents/events.py

@dataclass
class AgentEvent:
    """Base event for agent progress updates."""
    timestamp: datetime
    event_type: str

@dataclass
class PlanCreatedEvent(AgentEvent):
    event_type: str = "plan_created"
    plan: AgentPlan

@dataclass
class StepStartedEvent(AgentEvent):
    event_type: str = "step_started"
    step_id: str
    step_description: str

@dataclass
class ToolCallEvent(AgentEvent):
    event_type: str = "tool_call"
    tool_name: str
    arguments: dict

@dataclass
class ToolResultEvent(AgentEvent):
    event_type: str = "tool_result"
    tool_name: str
    result: Any
    success: bool

@dataclass
class ApprovalRequiredEvent(AgentEvent):
    event_type: str = "approval_required"
    step_id: str
    action_description: str
    risk_level: str

@dataclass
class ThinkingEvent(AgentEvent):
    event_type: str = "thinking"
    content: str  # Reasoning text to display

@dataclass
class CompletionEvent(AgentEvent):
    event_type: str = "completion"
    final_result: str
    steps_completed: int
    steps_total: int
```

**UI Component Architecture:**

```python
# src/ui/views/agents.py (extension of existing)

class AgentPanel(ft.Column):
    """Agent interaction panel with progress visualization."""

    def __init__(self, page: ft.Page, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
        self.plan_display: PlanCard | None = None
        self.progress_list: ft.ListView = ft.ListView(...)
        self.approval_dialog: ApprovalDialog | None = None

    async def execute_task(self, request: str):
        """Execute agent task with UI updates."""
        async for event in self.orchestrator.execute(request):
            await self._handle_event(event)

    async def _handle_event(self, event: AgentEvent):
        """Route events to UI updates."""
        match event.event_type:
            case "plan_created":
                self._show_plan(event.plan)
            case "step_started":
                self._update_step_status(event.step_id, "running")
            case "tool_call":
                self._add_progress_item(f"Calling: {event.tool_name}")
            case "approval_required":
                await self._show_approval_dialog(event)
            case "thinking":
                self._update_thinking_indicator(event.content)
            case "completion":
                self._show_completion(event)

        self.page.update()
```

**Existing Pattern Reference:** `src/ui/views/code_editor/ai_panel/chat_panel.py` line 500-576 shows the streaming pattern.

**Sources:**
- [Async Apps - Flet](https://flet.dev/docs/getting-started/async-apps/)
- [Streaming - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/streaming/)
- [Flet 1.0 Alpha](https://flet.dev/blog/introducing-flet-1-0-alpha/)

### Approval Dialog Design

```python
# src/ui/dialogs/approval_dialog.py

class ApprovalDialog(ft.AlertDialog):
    """Dialog for approving risky agent actions."""

    def __init__(
        self,
        action: str,
        risk_level: str,
        details: str,
        on_approve: Callable,
        on_reject: Callable,
        on_modify: Callable
    ):
        self.modal = True
        self.title = ft.Text(f"Approval Required ({risk_level})")
        self.content = ft.Column([
            ft.Text(action, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Text(details, selectable=True),
                bgcolor=Theme.BG_TERTIARY,
                padding=10,
                border_radius=8
            ),
            ft.Text("Options:", weight=ft.FontWeight.W_500),
            ft.Text("- Approve: Execute this action"),
            ft.Text("- Modify: Edit the action before execution"),
            ft.Text("- Skip: Skip this step and continue"),
            ft.Text("- Cancel: Stop the entire task"),
        ])
        self.actions = [
            ft.TextButton("Approve", on_click=lambda _: on_approve()),
            ft.TextButton("Modify", on_click=lambda _: on_modify()),
            ft.TextButton("Skip", on_click=lambda _: on_reject("skip")),
            ft.TextButton("Cancel", on_click=lambda _: on_reject("cancel")),
        ]
```

---

## Suggested Build Order

Based on dependency analysis, here is the recommended implementation sequence:

### Phase 1: Core Agent Infrastructure

**Duration:** 2-3 weeks
**Dependencies:** None (builds on existing AIGateway)

| Component | Why First |
|-----------|-----------|
| `AgentMessage`, `AgentEvent` models | Foundation for all communication |
| `AgentSession` state management | Needed by planner and executor |
| `ToolDefinition`, `ToolRegistry` | Planner needs to know available tools |
| Built-in tool wrappers | Wrap existing Skynette functions |

**Deliverables:**
- `src/agents/models.py` - Data models
- `src/agents/events.py` - Event types
- `src/agents/state.py` - Session management
- `src/agents/tools/registry.py` - Tool registration
- `src/agents/tools/builtin.py` - Built-in tool wrappers

### Phase 2: Planning and Execution

**Duration:** 2-3 weeks
**Dependencies:** Phase 1

| Component | Why This Order |
|-----------|---------------|
| `AgentPlanner` | Creates plans that executor runs |
| `AgentExecutor` | Runs plans step by step |
| `AgentOrchestrator` | Coordinates planner + executor |

**Deliverables:**
- `src/agents/planner.py` - Plan generation
- `src/agents/executor.py` - Plan execution
- `src/agents/orchestrator.py` - Main coordinator

### Phase 3: MCP Integration

**Duration:** 2 weeks
**Dependencies:** Phase 1 (ToolRegistry)

| Component | Why This Order |
|-----------|---------------|
| MCP transport layer | Connect before discovering tools |
| `MCPClient` | Manages server connections |
| MCP tool registration | Extends ToolRegistry |

**Deliverables:**
- `src/agents/mcp/transport.py` - stdio/HTTP transports
- `src/agents/mcp/client.py` - MCP server client
- `src/agents/mcp/config.py` - Server configuration

### Phase 4: UI Integration

**Duration:** 2-3 weeks
**Dependencies:** Phase 2 (events to display)

| Component | Why This Order |
|-----------|---------------|
| Progress display | Shows plan execution |
| Approval dialogs | User interaction |
| AgentPanel view | Main interface |
| Settings integration | MCP server management |

**Deliverables:**
- `src/ui/components/agent/` - Agent UI components
- `src/ui/dialogs/approval_dialog.py` - Approval UI
- Update `src/ui/views/agents.py` - Enhanced view

### Phase 5: Safety and Control

**Duration:** 1-2 weeks
**Dependencies:** Phase 4 (approval UI exists)

| Component | Why Last |
|-----------|----------|
| Action classification | Needs full tool context |
| Audit logging | Needs working execution |
| Kill switch | Needs running tasks to stop |
| YOLO mode | Needs safety defaults first |

**Deliverables:**
- `src/agents/safety/classifier.py` - Action risk classification
- `src/agents/safety/audit.py` - Action logging
- `src/agents/safety/controls.py` - Kill switch, YOLO mode

### Dependency Diagram

```
Phase 1: Infrastructure
    |
    +---> Phase 2: Planning/Execution
    |         |
    |         +---> Phase 4: UI
    |                   |
    +---> Phase 3: MCP  |
              |         |
              +---------+---> Phase 5: Safety
```

---

## Integration Points with Existing Code

### Files to Modify

| File | Modification |
|------|-------------|
| `src/ai/gateway.py` | Add `get_tool_schemas()` method |
| `src/rag/service.py` | Add `query_with_context()` for agent use |
| `src/core/nodes/execution/code_runner.py` | Expose as agent tool |
| `src/ui/views/agents.py` | Replace/extend current Supervisor UI |
| `src/ui/app.py` | Add agent panel routing |
| `src/ui/views/settings.py` | Add MCP server management section |

### New Modules

```
src/agents/
    __init__.py
    models.py           # AgentPlan, AgentMessage, etc.
    events.py           # Event types for UI streaming
    state.py            # AgentSession management
    planner.py          # Plan generation
    executor.py         # Plan execution
    orchestrator.py     # Main coordinator
    tools/
        __init__.py
        registry.py     # ToolRegistry
        builtin.py      # Built-in tool wrappers
    mcp/
        __init__.py
        transport.py    # stdio, HTTP transports
        client.py       # MCPClient
        config.py       # Server configuration
    safety/
        __init__.py
        classifier.py   # Action risk classification
        audit.py        # Action logging
        controls.py     # Kill switch, YOLO mode
```

---

## Anti-Patterns to Avoid

### 1. Single LLM Call Per Tool Use (ReAct Trap)

**What goes wrong:** Every tool call requires a full LLM inference, making tasks expensive and slow.

**Prevention:** Use Plan-and-Execute. Plan once with large model, execute with smaller models or deterministic code.

### 2. Unbounded Context Growth

**What goes wrong:** Conversation history + tool results overflow context window.

**Prevention:**
- Sliding window for conversation history
- Summarize old tool results
- Store full results in session state, only include summaries in prompt

### 3. MCP Server Connection Pooling

**What goes wrong:** Creating new connections per tool call causes latency and resource exhaustion.

**Prevention:**
- Keep connections alive in `MCPClient`
- Reconnect on failure with backoff
- Monitor connection health

### 4. Blocking UI During Execution

**What goes wrong:** Agent execution blocks Flet's async loop, freezing the UI.

**Prevention:**
- All agent code is `async`
- Use `asyncio.to_thread()` for CPU-bound operations
- Stream events instead of waiting for completion

### 5. Approval Fatigue

**What goes wrong:** Asking for approval on every action trains users to click "approve" without reading.

**Prevention:**
- Smart defaults based on action classification
- Batch similar approvals
- YOLO mode for power users
- Remember approval decisions for similar actions

---

## Open Questions

| Question | Impact | Suggested Resolution |
|----------|--------|---------------------|
| How to handle MCP server failures mid-task? | Medium | Retry with backoff, skip step, or abort based on criticality |
| Should agent have its own conversation history separate from chat? | Low | Yes, AgentSession separate from ChatState |
| How to handle parallel step execution in Plan-and-Execute? | Medium | Use `asyncio.gather()` for independent steps |
| What context to include for plan generation? | High | Current file, project RAG, recent conversation |

---

## Sources

### Agent Patterns
- [Plan-and-Execute Agents - LangChain Blog](https://www.blog.langchain.com/planning-agents/)
- [ReAct vs Plan-and-Execute - DEV Community](https://dev.to/jamesli/react-vs-plan-and-execute-a-practical-comparison-of-llm-agent-patterns-4gh9)
- [LangGraph Plan-and-Execute Tutorial](https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/)
- [How to create a ReAct agent from scratch - LangGraph](https://langchain-ai.github.io/langgraph/how-tos/react-agent-from-scratch/)

### MCP Integration
- [Model Context Protocol - Official](https://modelcontextprotocol.io/)
- [MCP - Wikipedia](https://en.wikipedia.org/wiki/Model_Context_Protocol)
- [mcp-agent - GitHub](https://github.com/lastmile-ai/mcp-agent)
- [OpenAI Agents SDK - MCP](https://openai.github.io/openai-agents-python/mcp/)
- [PydanticAI MCP Docs](https://ai.pydantic.dev/mcp/)

### Tool Calling
- [Function Calling in AI Agents - Prompt Engineering Guide](https://www.promptingguide.ai/agents/function-calling)
- [Function Calling - Martin Fowler](https://martinfowler.com/articles/function-call-LLM.html)
- [Best Practices for Function Calling - Scalifiai](https://www.scalifiai.com/blog/function-calling-tool-call-best%20practices)

### Memory and State
- [Memory Overview - LangChain](https://docs.langchain.com/oss/python/concepts/memory)
- [Sessions - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/sessions/)
- [Context Engineering - OpenAI Cookbook](https://cookbook.openai.com/examples/agents_sdk/session_memory)

### UI Integration
- [Async Apps - Flet](https://flet.dev/docs/getting-started/async-apps/)
- [Streaming - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/streaming/)
- [Flet 1.0 Alpha Blog](https://flet.dev/blog/introducing-flet-1-0-alpha/)

---

*Research completed: 2026-01-20*
