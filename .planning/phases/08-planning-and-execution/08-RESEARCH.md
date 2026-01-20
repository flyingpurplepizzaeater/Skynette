# Phase 8: Planning and Execution - Research

**Researched:** 2026-01-20
**Domain:** Agent observability, status display, cancellation patterns, tracing, model routing
**Confidence:** HIGH

## Summary

This research covers four core domains for Phase 8: real-time status display (AGNT-06), cancellation control (AGNT-07), execution tracing (AGNT-03), and model routing (AI-01, AI-02). The existing codebase provides strong foundations:

- **Agent Core** (`src/agent/`) from Phase 7 delivers event streaming (`AgentEventEmitter`), session management, and executor with cancellation flag
- **UI Framework** (`src/ui/views/agents.py`) shows existing patterns for ProgressRing, event streaming to UI, and card-based result display
- **Storage Layer** (`src/data/storage.py`, `src/ai/storage.py`) demonstrates SQLite schema patterns with proper indexing
- **Cost Calculator** (`src/ai/cost.py`) provides existing model pricing infrastructure for cost estimates

Phase 8 bridges the backend agent loop (Phase 7) to user-facing controls. The key insight is that status, cancellation, tracing, and routing are all views into the same event stream - no new data sources needed, just structured persistence and UI components.

**Primary recommendation:** Extend AgentEvent with richer data fields, add trace storage with SQLite, create Flet UI components for status/debug views, and build a ModelRouter that wraps the existing AI Gateway with task classification.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flet | existing | UI components | Already in stack. ProgressRing, animated containers for status |
| sqlite3 | stdlib | Trace storage | Already in stack. Existing schema patterns in `data/storage.py` |
| pydantic | >=2.0.0 | Trace models | Already in stack. Consistent with Phase 7 models |
| asyncio | stdlib | Cancellation control | Already in stack. TaskGroup, CancelledError handling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime | stdlib | Timestamps | Already used. Trace entry timestamps |
| json | stdlib | Trace data serialization | Already used. Store complex event data |
| tiktoken | existing | Token estimation | Already in stack. Estimate costs before execution |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLite trace storage | Langfuse/Phoenix | External dependency, overkill for single-user app |
| Custom status UI | Terminal spinner libs | Flet already has ProgressRing, animations built-in |
| Manual cancellation | asyncio.TaskGroup | TaskGroup better for structured cleanup, Python 3.11+ |
| Custom model router | LiteLLM/RouteLLM | External dependency, simple rule-based routing sufficient |

**Installation:**
```bash
# No new dependencies required - all existing in stack
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  agent/
    observability/          # NEW: Tracing and status
      __init__.py
      trace_store.py        # SQLite trace persistence
      trace_models.py       # TraceEntry, TraceSession models
    ui/                     # NEW: Agent UI components
      __init__.py
      status_indicator.py   # Animated status display
      trace_viewer.py       # Debug/trace view panel
      cancel_dialog.py      # Cancellation confirmation/options
    routing/                # NEW: Model routing
      __init__.py
      model_router.py       # Task classification + model selection
      routing_rules.py      # User-configurable routing rules
```

### Pattern 1: Enhanced Event Model with Full Context

**What:** Extend AgentEvent with all fields needed for tracing, status, and debugging
**When to use:** All agent execution events
**Why:** Current AgentEvent has minimal data; tracing needs full context (tokens, model, inputs/outputs)

```python
# Source: Existing src/agent/models/event.py + observability requirements
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional
from datetime import datetime, timezone

class EnhancedAgentEvent(BaseModel):
    """Event with full tracing context."""

    # Core fields (existing)
    type: Literal[
        "state_change", "plan_created", "step_started", "step_completed",
        "tool_called", "tool_result", "message", "error", "budget_warning",
        "budget_exceeded", "iteration_limit", "completed", "cancelled",
        # NEW: Additional event types for full transparency
        "model_selected", "model_switched", "approval_requested",
    ]
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: Optional[str] = None

    # NEW: Tracing fields
    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    parent_trace_id: Optional[str] = None  # For nested operations
    duration_ms: Optional[float] = None  # Set on completion

    # NEW: Token/cost tracking
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    estimated_cost_usd: Optional[float] = None

    # NEW: Full I/O for debugging
    raw_input: Optional[str] = None  # Truncated for storage
    raw_output: Optional[str] = None  # Truncated for storage
```

### Pattern 2: Cooperative Cancellation with User Choice

**What:** Cancellation flow that gives user control over behavior
**When to use:** Any user-initiated stop request
**Why:** Per CONTEXT.md - user chooses "stop now vs finish current step" and "keep vs rollback"

```python
# Source: Python asyncio best practices + user requirements
from dataclasses import dataclass
from enum import Enum
import asyncio

class CancelMode(str, Enum):
    """How to handle cancellation."""
    IMMEDIATE = "immediate"      # Stop now, mid-step
    AFTER_CURRENT = "after_current"  # Finish current step, then stop

class ResultMode(str, Enum):
    """What to do with partial results."""
    KEEP = "keep"       # Keep all completed work
    ROLLBACK = "rollback"  # Attempt to undo changes

@dataclass
class CancellationRequest:
    """User's cancellation preferences."""
    cancel_mode: CancelMode
    result_mode: ResultMode
    reason: Optional[str] = None

class CancellableExecutor:
    """Executor with cooperative cancellation."""

    def __init__(self, session: AgentSession):
        self.session = session
        self._cancel_request: Optional[CancellationRequest] = None
        self._current_step: Optional[PlanStep] = None

    def request_cancel(self, request: CancellationRequest):
        """Request cancellation with specified mode."""
        self._cancel_request = request

    async def _check_cancellation(self) -> bool:
        """Check if we should cancel. Called between steps."""
        if self._cancel_request is None:
            return False

        if self._cancel_request.cancel_mode == CancelMode.IMMEDIATE:
            return True

        # AFTER_CURRENT: Only cancel between steps
        if self._current_step is None:
            return True

        return False

    async def _handle_cancelled(self) -> dict:
        """Generate post-cancel summary."""
        return {
            "completed_steps": self._get_completed_steps(),
            "current_step": self._current_step.description if self._current_step else None,
            "cancel_mode": self._cancel_request.cancel_mode.value,
            "result_mode": self._cancel_request.result_mode.value,
            "options": ["resume", "restart", "abandon"],
        }
```

### Pattern 3: SQLite Trace Storage with Retention

**What:** Persist traces to SQLite with configurable retention and auto-cleanup
**When to use:** All agent executions for debugging
**Why:** Per CONTEXT.md - database storage with configurable retention

```python
# Source: Existing src/data/storage.py patterns + trace requirements
import sqlite3
from datetime import datetime, timedelta, timezone

class TraceStore:
    """Persist agent traces with retention management."""

    DEFAULT_RETENTION_DAYS = 30

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize trace tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Trace sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_traces (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_ms REAL,
                    parent_trace_id TEXT,
                    data TEXT,  -- JSON
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    model_used TEXT,
                    provider_used TEXT,
                    cost_usd REAL,
                    raw_input TEXT,
                    raw_output TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_session
                ON agent_traces(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_timestamp
                ON agent_traces(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_type
                ON agent_traces(type)
            """)

            # Retention settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trace_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            conn.commit()

    async def cleanup_old_traces(self, retention_days: int = None):
        """Delete traces older than retention period."""
        days = retention_days or self.DEFAULT_RETENTION_DAYS
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM agent_traces WHERE timestamp < ?",
                (cutoff.isoformat(),)
            )
            deleted = cursor.rowcount
            conn.commit()

        return deleted
```

### Pattern 4: Model Router with Task Classification

**What:** Route tasks to appropriate models based on classification rules
**When to use:** Before agent execution starts, and optionally mid-task
**Why:** Per CONTEXT.md - recommend model + confirm, user-configurable rules

```python
# Source: AI routing research + existing AI Gateway patterns
from dataclasses import dataclass
from typing import Optional
from src.ai.gateway import get_gateway, AICapability
from src.ai.cost import CostCalculator

@dataclass
class ModelRecommendation:
    """A model recommendation with reasoning."""
    provider: str
    model: str
    reason: str
    estimated_cost: float
    capabilities: list[str]
    alternatives: list["ModelRecommendation"] = None

class TaskCategory(str, Enum):
    """Categories for task classification."""
    SIMPLE_QUERY = "simple_query"      # FAQ, lookup, simple questions
    CODE_GENERATION = "code_generation"  # Writing code
    CODE_REVIEW = "code_review"         # Analyzing code
    RESEARCH = "research"               # Multi-step research
    CREATIVE = "creative"               # Writing, brainstorming
    ANALYSIS = "analysis"               # Data analysis, reasoning
    GENERAL = "general"                 # Default

class ModelRouter:
    """Route tasks to appropriate models."""

    # Default routing rules (user-configurable)
    DEFAULT_RULES = {
        TaskCategory.SIMPLE_QUERY: {
            "provider": "anthropic", "model": "claude-3-haiku",
            "reason": "Fast and cost-effective for simple queries"
        },
        TaskCategory.CODE_GENERATION: {
            "provider": "anthropic", "model": "claude-3-sonnet",
            "reason": "Strong code generation with good cost balance"
        },
        TaskCategory.RESEARCH: {
            "provider": "anthropic", "model": "claude-3-opus",
            "reason": "Best reasoning for complex multi-step research"
        },
        TaskCategory.GENERAL: {
            "provider": "anthropic", "model": "claude-3-sonnet",
            "reason": "Good all-around performance"
        },
    }

    def __init__(self, custom_rules: dict = None):
        self.rules = {**self.DEFAULT_RULES, **(custom_rules or {})}
        self.gateway = get_gateway()
        self.cost_calc = CostCalculator()

    def classify_task(self, task: str) -> TaskCategory:
        """Classify task into category."""
        task_lower = task.lower()

        # Simple keyword matching (can be enhanced with LLM)
        if any(kw in task_lower for kw in ["write code", "create function", "implement"]):
            return TaskCategory.CODE_GENERATION
        if any(kw in task_lower for kw in ["review", "analyze code", "find bugs"]):
            return TaskCategory.CODE_REVIEW
        if any(kw in task_lower for kw in ["research", "find out", "investigate"]):
            return TaskCategory.RESEARCH
        if any(kw in task_lower for kw in ["what is", "how do", "when", "where"]):
            return TaskCategory.SIMPLE_QUERY

        return TaskCategory.GENERAL

    def recommend(self, task: str, estimated_tokens: int = 4000) -> ModelRecommendation:
        """Get model recommendation for task."""
        category = self.classify_task(task)
        rule = self.rules.get(category, self.rules[TaskCategory.GENERAL])

        cost = self.cost_calc.estimate_cost(
            rule["provider"], rule["model"], estimated_tokens
        )

        return ModelRecommendation(
            provider=rule["provider"],
            model=rule["model"],
            reason=rule["reason"],
            estimated_cost=cost,
            capabilities=["chat", "tool_use"],
            alternatives=self._get_alternatives(category, estimated_tokens),
        )

    def _get_alternatives(self, category: TaskCategory, tokens: int) -> list:
        """Get alternative model options."""
        # Return cheaper and more capable alternatives
        alternatives = []

        # Add a cheaper option
        cheap_cost = self.cost_calc.estimate_cost("anthropic", "claude-3-haiku", tokens)
        alternatives.append(ModelRecommendation(
            provider="anthropic",
            model="claude-3-haiku",
            reason="Fastest and most cost-effective",
            estimated_cost=cheap_cost,
            capabilities=["chat"],
        ))

        # Add a more capable option
        if category != TaskCategory.RESEARCH:
            premium_cost = self.cost_calc.estimate_cost("anthropic", "claude-3-opus", tokens)
            alternatives.append(ModelRecommendation(
                provider="anthropic",
                model="claude-3-opus",
                reason="Most capable for complex reasoning",
                estimated_cost=premium_cost,
                capabilities=["chat", "tool_use", "vision"],
            ))

        return alternatives
```

### Pattern 5: Flet Status Indicator Component

**What:** Animated status display for agent execution state
**When to use:** Agent execution UI
**Why:** Per CONTEXT.md - animated indicator + text, dual location display

```python
# Source: Flet documentation + existing src/ui/views/agents.py patterns
import flet as ft
from src.ui.theme import Theme

class AgentStatusIndicator(ft.UserControl):
    """Animated status indicator for agent execution."""

    STATUS_CONFIG = {
        "idle": {"icon": ft.Icons.PENDING, "color": Theme.TEXT_MUTED, "animate": False},
        "planning": {"icon": ft.Icons.AUTO_AWESOME, "color": Theme.PRIMARY, "animate": True},
        "executing": {"icon": ft.Icons.PLAY_ARROW, "color": Theme.SECONDARY, "animate": True},
        "awaiting_tool": {"icon": ft.Icons.BUILD, "color": Theme.INFO, "animate": True},
        "awaiting_approval": {"icon": ft.Icons.PAUSE, "color": Theme.WARNING, "animate": False},
        "completed": {"icon": ft.Icons.CHECK_CIRCLE, "color": Theme.SUCCESS, "animate": False},
        "failed": {"icon": ft.Icons.ERROR, "color": Theme.ERROR, "animate": False},
        "cancelled": {"icon": ft.Icons.CANCEL, "color": Theme.WARNING, "animate": False},
    }

    def __init__(self, initial_status: str = "idle"):
        super().__init__()
        self.current_status = initial_status
        self._progress_ring = None
        self._icon = None
        self._text = None

    def build(self):
        config = self.STATUS_CONFIG.get(self.current_status, self.STATUS_CONFIG["idle"])

        self._progress_ring = ft.ProgressRing(
            width=20, height=20,
            stroke_width=2,
            color=config["color"],
            visible=config["animate"],
        )

        self._icon = ft.Icon(
            config["icon"],
            size=20,
            color=config["color"],
            visible=not config["animate"],
        )

        self._text = ft.Text(
            self._get_status_text(),
            size=Theme.FONT_SM,
            color=config["color"],
        )

        return ft.Row(
            controls=[
                ft.Stack([self._progress_ring, self._icon]),
                self._text,
            ],
            spacing=Theme.SPACING_SM,
        )

    def update_status(self, status: str, detail: str = None):
        """Update the status display."""
        self.current_status = status
        config = self.STATUS_CONFIG.get(status, self.STATUS_CONFIG["idle"])

        self._progress_ring.color = config["color"]
        self._progress_ring.visible = config["animate"]
        self._icon.name = config["icon"]
        self._icon.color = config["color"]
        self._icon.visible = not config["animate"]

        text = detail or self._get_status_text()
        self._text.value = text
        self._text.color = config["color"]

        self.update()

    def _get_status_text(self) -> str:
        """Get display text for current status."""
        texts = {
            "idle": "Ready",
            "planning": "Planning...",
            "executing": "Executing...",
            "awaiting_tool": "Running tool...",
            "awaiting_approval": "Waiting for approval",
            "completed": "Completed",
            "failed": "Failed",
            "cancelled": "Cancelled",
        }
        return texts.get(self.current_status, "Unknown")
```

### Anti-Patterns to Avoid
- **Blocking UI updates:** Never block the main thread; use async event streaming
- **Unbounded trace storage:** Always enforce retention; traces can grow unbounded
- **Silent cancellation:** Always provide feedback on what was cancelled and why
- **Hard-coded model selection:** Make routing rules user-configurable
- **Polling for status:** Use event-driven updates, not polling loops

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Progress animation | Custom animation loops | Flet ProgressRing | Built-in, handles timing correctly |
| Cancellation | Thread.stop() or process.kill() | asyncio.CancelledError + cooperative checks | Graceful cleanup, no resource leaks |
| Trace search | Custom string matching | SQLite FTS5 or LIKE queries | SQLite handles indexing, escaping |
| Cost estimation | Rough token count * price | Existing CostCalculator | Already handles model-specific pricing |
| Token counting | len(text.split()) | tiktoken (existing) | Accurate model-specific tokenization |
| Event broadcasting | Manual callback lists | Existing AgentEventEmitter | Already handles bounded queues, async iteration |

**Key insight:** Phase 7 built the event infrastructure; Phase 8 is about storing events (tracing) and displaying them (status/debug views). Don't rebuild the event system.

## Common Pitfalls

### Pitfall 1: Cancellation Race Conditions
**What goes wrong:** User cancels, but task continues because cancellation wasn't checked
**Why it happens:** Cancellation checks only at await points; long-running sync code ignores requests
**How to avoid:**
- Check `self._cancel_request` at start of each step
- Use `asyncio.TaskGroup` for structured cancellation (Python 3.11+)
- Emit "cancellation_requested" event immediately, "cancelled" event when complete
- Never swallow CancelledError without re-raising or calling uncancel()
**Warning signs:** User clicks cancel but execution continues, "cancel" button doesn't respond

### Pitfall 2: Trace Storage Bloat
**What goes wrong:** Database grows unbounded, queries slow down, disk fills up
**Why it happens:** Every event stored with full raw I/O, no cleanup
**How to avoid:**
- Truncate `raw_input` and `raw_output` to 4KB max
- Run cleanup on app startup and daily
- Index timestamp column for efficient cleanup queries
- Use WAL mode for concurrent read/write
**Warning signs:** Slow trace queries, large database file, out-of-disk errors

### Pitfall 3: Model Switching Mid-Step
**What goes wrong:** Model switch takes effect immediately, corrupts in-progress reasoning
**Why it happens:** Switch applied to current step instead of next step
**How to avoid:**
- Queue model changes for next step, not current
- Emit "model_switch_queued" event with when it will take effect
- Show clear UI indication that switch is pending
**Warning signs:** Inconsistent results after model switch, partial responses from wrong model

### Pitfall 4: UI Update Flooding
**What goes wrong:** UI becomes unresponsive, events pile up, memory grows
**Why it happens:** Every token/event triggers UI update, no throttling
**How to avoid:**
- Batch UI updates (max 10 updates/second for text, 30/second for progress)
- Use bounded queue (existing AgentEventEmitter has maxsize=100)
- Consolidate rapid events (multiple tokens -> single text update)
- Drop low-priority events when queue is full
**Warning signs:** Laggy UI during execution, memory growth, "Event loop is running" warnings

### Pitfall 5: Status Display Desync
**What goes wrong:** Status shows "executing" but task actually failed
**Why it happens:** Error event not propagated to UI, or UI component not subscribed
**How to avoid:**
- Always emit terminal events (completed, failed, cancelled) through same channel
- Subscribe UI to event stream at component mount, unsubscribe on unmount
- Handle all terminal event types in UI state machine
**Warning signs:** UI stuck on "executing...", user has to refresh

## Code Examples

Verified patterns from existing codebase and official sources:

### Trace Query with Filters
```python
# Source: Existing SQLite patterns in src/data/storage.py
def get_traces(
    self,
    session_id: str = None,
    event_type: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
    search_text: str = None,
    limit: int = 100,
) -> list[dict]:
    """Query traces with filters."""
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM agent_traces WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if event_type:
            query += " AND type = ?"
            params.append(event_type)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        if search_text:
            # Full-text search on data, raw_input, raw_output
            query += " AND (data LIKE ? OR raw_input LIKE ? OR raw_output LIKE ?)"
            pattern = f"%{search_text}%"
            params.extend([pattern, pattern, pattern])

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
```

### Cancel Dialog with Options
```python
# Source: Flet patterns + user requirements from CONTEXT.md
class CancelDialog(ft.AlertDialog):
    """Cancellation dialog with mode selection."""

    def __init__(self, on_cancel: callable, elapsed_seconds: float):
        self.on_cancel = on_cancel
        self.cancel_mode = CancelMode.AFTER_CURRENT
        self.result_mode = ResultMode.KEEP

        # Show confirmation for long-running tasks (>30s)
        needs_confirm = elapsed_seconds > 30

        super().__init__(
            title=ft.Text("Cancel Task?"),
            content=ft.Column([
                ft.Text("How would you like to stop?"),
                ft.RadioGroup(
                    value="after_current",
                    on_change=self._on_mode_change,
                    content=ft.Column([
                        ft.Radio(value="immediate", label="Stop immediately"),
                        ft.Radio(value="after_current", label="Finish current step, then stop"),
                    ]),
                ),
                ft.Divider(),
                ft.Text("What about completed work?"),
                ft.RadioGroup(
                    value="keep",
                    on_change=self._on_result_change,
                    content=ft.Column([
                        ft.Radio(value="keep", label="Keep changes"),
                        ft.Radio(value="rollback", label="Rollback changes"),
                    ]),
                ),
            ] + ([
                ft.Divider(),
                ft.Text(
                    f"This task has been running for {elapsed_seconds:.0f}s",
                    color=Theme.WARNING,
                ),
            ] if needs_confirm else []),
            width=400),
            actions=[
                ft.TextButton("Continue Task", on_click=self._close),
                ft.ElevatedButton("Cancel Task", on_click=self._confirm_cancel),
            ],
        )

    def _on_mode_change(self, e):
        self.cancel_mode = CancelMode(e.control.value)

    def _on_result_change(self, e):
        self.result_mode = ResultMode(e.control.value)

    def _confirm_cancel(self, e):
        self.on_cancel(CancellationRequest(
            cancel_mode=self.cancel_mode,
            result_mode=self.result_mode,
        ))
        self._close(e)

    def _close(self, e):
        self.open = False
        self.update()
```

### Model Recommendation Display
```python
# Source: Flet patterns + cost display requirements
def build_model_recommendation_card(
    recommendation: ModelRecommendation,
    on_accept: callable,
    on_change: callable,
) -> ft.Container:
    """Build UI card for model recommendation."""
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME, color=Theme.PRIMARY),
                ft.Text("Recommended Model", weight=ft.FontWeight.BOLD),
            ]),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(recommendation.model, size=Theme.FONT_LG, weight=ft.FontWeight.W_600),
                        ft.Container(
                            content=ft.Text(
                                f"${recommendation.estimated_cost:.4f}",
                                size=Theme.FONT_SM,
                            ),
                            bgcolor=Theme.BG_TERTIARY,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=Theme.RADIUS_SM,
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(recommendation.reason, size=Theme.FONT_SM, color=Theme.TEXT_SECONDARY),
                ]),
                padding=Theme.SPACING_SM,
                bgcolor=Theme.BG_TERTIARY,
                border_radius=Theme.RADIUS_SM,
            ),
            ft.Row([
                ft.TextButton(
                    "Use different model",
                    on_click=lambda e: on_change(recommendation.alternatives),
                ),
                ft.ElevatedButton(
                    "Use this model",
                    on_click=lambda e: on_accept(recommendation),
                ),
            ], alignment=ft.MainAxisAlignment.END),
        ]),
        padding=Theme.SPACING_MD,
        bgcolor=Theme.SURFACE,
        border_radius=Theme.RADIUS_MD,
        border=ft.border.all(1, Theme.BORDER),
    )
```

### Unit Test Pattern for Agent Components
```python
# Source: Existing tests/conftest.py + tests/unit/test_cost_calculator.py patterns
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestModelRouter:
    """Tests for model routing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.router = ModelRouter()

    def test_classify_simple_query(self):
        """Test classification of simple queries."""
        task = "What is the capital of France?"
        category = self.router.classify_task(task)
        assert category == TaskCategory.SIMPLE_QUERY

    def test_classify_code_generation(self):
        """Test classification of code generation tasks."""
        task = "Write code to parse JSON in Python"
        category = self.router.classify_task(task)
        assert category == TaskCategory.CODE_GENERATION

    def test_recommend_returns_valid_model(self):
        """Test recommendation returns valid model."""
        recommendation = self.router.recommend("Help me write some code")
        assert recommendation.provider in ["openai", "anthropic", "local"]
        assert recommendation.model is not None
        assert recommendation.estimated_cost >= 0

    def test_custom_rules_override_defaults(self):
        """Test custom routing rules."""
        custom_rules = {
            TaskCategory.SIMPLE_QUERY: {
                "provider": "local",
                "model": "mistral-7b",
                "reason": "Use local for simple queries",
            }
        }
        router = ModelRouter(custom_rules=custom_rules)

        rec = router.recommend("What is 2+2?")
        assert rec.provider == "local"
        assert rec.model == "mistral-7b"


class TestCancellableExecutor:
    """Tests for cancellation handling."""

    @pytest.fixture
    def mock_session(self):
        """Create mock session."""
        from src.agent.models.state import AgentSession
        return AgentSession(task="test", token_budget=10000)

    @pytest.mark.asyncio
    async def test_cancel_immediate_stops_execution(self, mock_session):
        """Test immediate cancellation stops execution."""
        executor = CancellableExecutor(mock_session)

        executor.request_cancel(CancellationRequest(
            cancel_mode=CancelMode.IMMEDIATE,
            result_mode=ResultMode.KEEP,
        ))

        assert await executor._check_cancellation() is True

    @pytest.mark.asyncio
    async def test_cancel_after_current_waits(self, mock_session):
        """Test AFTER_CURRENT mode waits for step completion."""
        executor = CancellableExecutor(mock_session)
        executor._current_step = MagicMock()  # Simulate running step

        executor.request_cancel(CancellationRequest(
            cancel_mode=CancelMode.AFTER_CURRENT,
            result_mode=ResultMode.KEEP,
        ))

        # Should NOT cancel while step is running
        assert await executor._check_cancellation() is False

        # Should cancel after step completes
        executor._current_step = None
        assert await executor._check_cancellation() is True
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| External trace services | Local SQLite + optional export | 2025 | Self-contained, no external deps |
| Polling status updates | Event-driven streaming | 2024 | Lower latency, less resource use |
| Fixed model selection | Dynamic routing with user choice | 2025 | Cost savings 40-85% per industry reports |
| Hard abort cancellation | Cooperative cancellation with options | Always | Better UX, no resource leaks |
| Separate debug tools | Integrated trace viewer | 2025 | Single pane of glass debugging |

**Deprecated/outdated:**
- **Thread.stop() / process.kill():** Causes resource leaks; use cooperative cancellation
- **External observability for single-user apps:** Overkill; local storage sufficient
- **One-size-fits-all model:** Dynamic routing is now standard practice

## Open Questions

Things that couldn't be fully resolved:

1. **Trace export format**
   - What we know: Need to store traces locally with SQLite
   - What's unclear: Should we support export to Langfuse/Phoenix/OTLP format?
   - Recommendation: Implement local-first; add export as optional feature later

2. **Model switching confirmation UX**
   - What we know: User can switch mid-task; need clear confirmation
   - What's unclear: Should switch apply to current step or next step only?
   - Recommendation: Default to "next step only" with option for immediate

3. **Rollback implementation**
   - What we know: User wants "keep vs rollback" option on cancel
   - What's unclear: How to rollback file changes or API calls?
   - Recommendation: Track reversible actions; show warning for irreversible

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/agent/`, `src/ui/views/agents.py`, `src/data/storage.py`, `src/ai/cost.py`
- [Flet ProgressRing Documentation](https://flet.dev/docs/controls/progressring/) - Status indicators
- [Flet Animations Guide](https://flet.dev/docs/guides/python/animations/) - Animation patterns
- [Python asyncio Task Documentation](https://docs.python.org/3/library/asyncio-task.html) - Cancellation handling
- [SuperFastPython: asyncio Task Cancellation Best Practices](https://superfastpython.com/asyncio-task-cancellation-best-practices/) - Cooperative cancellation

### Secondary (MEDIUM confidence)
- [SQLite WAL Mode](https://sqlite.org/wal.html) - Write-ahead logging for concurrency
- [AWS Multi-LLM Routing Strategies](https://aws.amazon.com/blogs/machine-learning/multi-llm-routing-strategies-for-generative-ai-applications-on-aws/) - Model routing patterns
- [MarkTechPost: LLM Routing Guide](https://www.marktechpost.com/2025/04/01/a-comprehensive-guide-to-llm-routing-tools-and-frameworks/) - Routing tools overview
- [Softcery: AI Observability Platforms](https://softcery.com/lab/top-8-observability-platforms-for-ai-agents-in-2025) - Tracing options

### Tertiary (LOW confidence)
- [Firecrawl: Best LLM Observability Tools 2025](https://www.firecrawl.dev/blog/best-llm-observability-tools) - Industry overview
- [Braintrust: AI Observability Platforms 2025](https://www.braintrust.dev/articles/best-ai-observability-platforms-2025) - Commercial options

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses only existing dependencies
- Architecture: HIGH - Extends proven Phase 7 patterns
- Status/cancellation: HIGH - Based on Python stdlib and Flet docs
- Tracing: HIGH - Follows existing SQLite patterns in codebase
- Model routing: MEDIUM - Patterns verified, but classification heuristics are custom

**Research date:** 2026-01-20
**Valid until:** 60 days (stable patterns, Flet/Python stdlib unlikely to change)
