# Phase 11: Safety and Approval Systems - Research

**Researched:** 2026-01-22
**Domain:** Agent safety, human-in-the-loop approval, action classification, audit logging, kill switch
**Confidence:** HIGH

## Summary

Phase 11 implements safety controls for the Skynette agent, covering action classification, human-in-the-loop (HITL) approval, audit trails, kill switch, and batch approval. The existing codebase already has strong foundations: `ToolDefinition` has `is_destructive` and `requires_approval` fields, `AgentState` includes `AWAITING_APPROVAL`, `TraceStore` provides SQLite-based event logging, and `CancelDialog`/`CancellationRequest` show established patterns for user-controlled interruption.

The primary work involves: (1) extending the classification system from binary destructive/non-destructive to four risk levels, (2) building an approval flow using Flet's BottomSheet for the UI, (3) enhancing the existing trace store to capture comprehensive audit data, (4) implementing a kill switch that works outside the agent event loop, and (5) adding similarity matching for batch approval of related actions.

**Primary recommendation:** Build on existing patterns (ToolDefinition flags, TraceStore, CancelDialog) rather than introducing new libraries. Use Flet's BottomSheet for approval UI, multiprocessing.Event for the kill switch, and extend TraceEntry with approval/risk metadata for the audit trail.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flet | >=0.28.0 | UI components (BottomSheet, badges) | Already used throughout codebase |
| pydantic | >=2.0 | Data models for classification, approval | Existing pattern in agent/models/ |
| sqlite3 | stdlib | Audit trail storage | TraceStore already uses SQLite+WAL |
| asyncio | stdlib | Async approval flow, event handling | Existing agent loop pattern |
| multiprocessing | stdlib | Kill switch inter-process communication | Standard for process control |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pystray | >=0.19 | System tray icon | Optional kill switch access method |
| keyboard | >=0.13 | Global hotkey registration | Optional kill switch shortcut |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| multiprocessing.Event | signal handlers | Signals are Unix-focused; Event is cross-platform |
| SQLite audit trail | File-based logging | SQLite provides querying, filtering, retention management |
| Custom bottom sheet | AlertDialog | BottomSheet better for approval with details; less modal disruption |

**Installation:**
```bash
# Core - already installed
# Optional for enhanced kill switch:
pip install pystray keyboard
```

## Architecture Patterns

### Recommended Project Structure
```
src/agent/
  safety/
    __init__.py
    classification.py    # RiskLevel enum, Classifier class
    approval.py          # ApprovalRequest, ApprovalResult, ApprovalManager
    audit.py             # AuditEntry, AuditStore (extends TraceStore)
    kill_switch.py       # KillSwitch class with Event-based communication
  ui/
    approval_sheet.py    # Flet BottomSheet for approval UI
    risk_badge.py        # Risk level badge component
    audit_viewer.py      # Tree view for audit trail (extends trace_viewer)
```

### Pattern 1: Risk Classification with Literal Types
**What:** Four-tier risk classification using Literal types (consistent with 07-01 decision)
**When to use:** Classifying any tool action before execution
**Example:**
```python
# Source: Extends existing ToolDefinition pattern
from typing import Literal

RiskLevel = Literal["safe", "moderate", "destructive", "critical"]

class ActionClassification(BaseModel):
    """Classification result for an agent action."""
    risk_level: RiskLevel
    reason: str  # Human-readable explanation
    requires_approval: bool
    tool_name: str
    parameters: dict

def classify_action(tool_name: str, params: dict) -> ActionClassification:
    """Classify action risk based on tool and parameters."""
    # Built-in tools have static classification
    # MCP tools default to moderate until approved
    ...
```

### Pattern 2: Approval Flow with State Machine
**What:** Approval request lifecycle with async continuation
**When to use:** Any flagged action requiring user decision
**Example:**
```python
# Source: Extends existing AgentState.AWAITING_APPROVAL pattern
from dataclasses import dataclass
from asyncio import Event

@dataclass
class ApprovalRequest:
    id: str
    classification: ActionClassification
    step_id: str
    session_id: str
    approved: Event = field(default_factory=Event)
    result: Optional[ApprovalResult] = None

class ApprovalManager:
    """Manages pending approval requests."""
    _pending: dict[str, ApprovalRequest] = {}

    async def request_approval(self, req: ApprovalRequest) -> ApprovalResult:
        """Block execution until user approves/rejects."""
        self._pending[req.id] = req
        await req.approved.wait()
        return req.result

    def approve(self, req_id: str, approve_similar: bool = False):
        """User approves the action."""
        req = self._pending.pop(req_id)
        req.result = ApprovalResult(approved=True, approve_similar=approve_similar)
        req.approved.set()
```

### Pattern 3: Kill Switch with Inter-Process Event
**What:** Process-external stop mechanism using multiprocessing.Event
**When to use:** Emergency stop that works even if agent loop is blocked
**Example:**
```python
# Source: https://superfastpython.com/safely-stop-a-process-in-python/
import multiprocessing

class KillSwitch:
    """Kill switch that operates outside agent process."""

    def __init__(self):
        self._stop_event = multiprocessing.Event()
        self._registered = False

    def trigger(self):
        """Trigger kill switch (can be called from any thread/process)."""
        self._stop_event.set()

    def is_triggered(self) -> bool:
        """Check if kill switch was triggered."""
        return self._stop_event.is_set()

    def reset(self):
        """Reset for next execution."""
        self._stop_event.clear()
```

### Pattern 4: Similarity Matching for Batch Approval
**What:** Match "similar" actions for batch approval
**When to use:** "Approve All Similar" functionality
**Example:**
```python
def are_similar_actions(a1: ActionClassification, a2: ActionClassification) -> bool:
    """Check if two actions are similar enough for batch approval."""
    # Same tool
    if a1.tool_name != a2.tool_name:
        return False

    # For file operations: same parent directory
    if a1.tool_name in ("file_write", "file_read"):
        path1 = Path(a1.parameters.get("path", ""))
        path2 = Path(a2.parameters.get("path", ""))
        return path1.parent == path2.parent or path2.is_relative_to(path1.parent)

    # For other tools: exact parameter match
    return a1.parameters == a2.parameters
```

### Anti-Patterns to Avoid
- **Blocking the UI thread:** Never await approval in the main Flet thread; use callbacks
- **Global signal handlers:** SIGINT/SIGTERM handlers affect the entire process; use Events for selective control
- **Over-classification:** Don't mark read-only operations as destructive; this causes approval fatigue
- **Storing raw secrets in audit log:** Redact sensitive parameters before logging

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Modal bottom sheet | Custom overlay positioning | `ft.BottomSheet` | Handles animations, scrim, dismiss gestures |
| Async event waiting | Polling loops | `asyncio.Event.wait()` | Efficient, no busy-waiting |
| Process communication | Shared files | `multiprocessing.Event` | Atomic, cross-platform, no race conditions |
| Audit trail queries | Manual SQL string building | Parameterized queries (existing TraceStore pattern) | SQL injection prevention |
| Risk level colors | Hardcoded hex values | Theme class extension | Consistency with light/dark mode |

**Key insight:** The codebase already has TraceStore, CancelDialog, and event emitter patterns. Extend these rather than creating parallel implementations.

## Common Pitfalls

### Pitfall 1: UI Blocking During Approval
**What goes wrong:** Agent loop blocks waiting for approval, freezing the UI
**Why it happens:** Calling `await approval_event.wait()` in a Flet event handler
**How to avoid:** Run agent loop in separate task; UI just sets approval result and signals event
**Warning signs:** "Not responding" dialog, frozen progress indicators

### Pitfall 2: Kill Switch Ineffective During Tight Loops
**What goes wrong:** Kill switch is triggered but agent continues executing
**Why it happens:** Agent only checks cancellation between steps, not during tool execution
**How to avoid:** Check kill switch at multiple points; use cooperative cancellation in tools; consider task.cancel() for immediate effect
**Warning signs:** Delay between kill switch trigger and actual stop

### Pitfall 3: Approval Fatigue from Over-Classification
**What goes wrong:** Users disable approval system because everything requires approval
**Why it happens:** Conservative classification marks safe operations as moderate/destructive
**How to avoid:** File reads are safe; only writes/deletes are destructive; read-only MCP tools should be safe after first approval
**Warning signs:** Users requesting "approve all" for entire session

### Pitfall 4: Audit Log Performance with Large Entries
**What goes wrong:** Audit queries slow down as log grows
**Why it happens:** No pagination, indexes missing, or raw_output not truncated
**How to avoid:** Use existing MAX_RAW_LENGTH truncation; ensure indexes on session_id, timestamp, risk_level; paginate queries
**Warning signs:** Slow startup, UI lag when viewing audit trail

### Pitfall 5: Race Condition in Similar Action Approval
**What goes wrong:** User approves "all similar" but next similar action still prompts
**Why it happens:** Approval cache not updated before next action is classified
**How to avoid:** Update similarity cache synchronously before returning from approve(); use dict keyed by (tool_name, path_pattern)
**Warning signs:** Redundant approval prompts after "Approve All Similar"

## Code Examples

Verified patterns from official sources and existing codebase:

### Flet BottomSheet for Approval
```python
# Source: https://docs.flet.dev/controls/bottomsheet/
import flet as ft
from src.ui.theme import Theme

class ApprovalSheet(ft.BottomSheet):
    """Bottom sheet for action approval."""

    def __init__(
        self,
        classification: ActionClassification,
        on_approve: Callable[[bool], None],  # bool = approve_similar
        on_reject: Callable[[], None],
    ):
        self.classification = classification
        self.on_approve = on_approve
        self.on_reject = on_reject

        super().__init__(
            content=self._build_content(),
            enable_drag=True,
            show_drag_handle=True,
            dismiss_on_click_outside=False,  # Require explicit decision
        )

    def _build_content(self) -> ft.Control:
        return ft.Container(
            padding=Theme.SPACING_LG,
            content=ft.Column([
                # Risk badge and action name
                ft.Row([
                    RiskBadge(self.classification.risk_level),
                    ft.Text(self.classification.tool_name, weight=ft.FontWeight.BOLD),
                ]),
                # Reason
                ft.Text(
                    self.classification.reason,
                    color=Theme.TEXT_SECONDARY,
                    size=Theme.FONT_SM,
                ),
                # Parameters preview (truncated)
                ft.Container(
                    bgcolor=Theme.BG_TERTIARY,
                    border_radius=Theme.RADIUS_SM,
                    padding=Theme.SPACING_SM,
                    content=ft.Text(
                        json.dumps(self.classification.parameters, indent=2)[:500],
                        font_family="monospace",
                        size=Theme.FONT_XS,
                    ),
                ),
                ft.Divider(),
                # Action buttons
                ft.Row([
                    ft.OutlinedButton("Reject", on_click=lambda _: self.on_reject()),
                    ft.FilledButton("Approve", on_click=lambda _: self.on_approve(False)),
                    ft.FilledTonalButton(
                        "Approve All Similar",
                        on_click=lambda _: self.on_approve(True),
                    ),
                ], alignment=ft.MainAxisAlignment.END),
            ]),
        )
```

### Risk Badge Component
```python
# Source: Follows existing Theme pattern
from src.ui.theme import Theme

RISK_COLORS = {
    "safe": Theme.SUCCESS,       # Green
    "moderate": Theme.WARNING,   # Yellow/Amber
    "destructive": "#F97316",    # Orange
    "critical": Theme.ERROR,     # Red
}

RISK_LABELS = {
    "safe": "Safe",
    "moderate": "Moderate",
    "destructive": "Destructive",
    "critical": "Critical",
}

class RiskBadge(ft.Container):
    """Color-coded badge showing risk level."""

    def __init__(self, risk_level: RiskLevel):
        color = RISK_COLORS.get(risk_level, Theme.TEXT_MUTED)
        label = RISK_LABELS.get(risk_level, risk_level)

        super().__init__(
            bgcolor=f"{color}20",  # 20% opacity background
            border=ft.border.all(1, color),
            border_radius=Theme.RADIUS_SM,
            padding=ft.padding.symmetric(horizontal=Theme.SPACING_SM, vertical=2),
            content=ft.Row([
                ft.Container(
                    width=8,
                    height=8,
                    border_radius=4,
                    bgcolor=color,
                ),
                ft.Text(label, color=color, size=Theme.FONT_SM, weight=ft.FontWeight.W_500),
            ], spacing=Theme.SPACING_XS),
        )
```

### Kill Switch Integration
```python
# Source: Extends existing AgentExecutor pattern
import multiprocessing

class AgentExecutor:
    def __init__(self, session: AgentSession, kill_switch: KillSwitch):
        self.kill_switch = kill_switch
        # ... existing init

    async def run(self, task: str) -> AsyncIterator[AgentEvent]:
        # ... existing run logic
        while not plan.is_complete() and not plan.has_failed():
            # Check kill switch (works even if UI is sluggish)
            if self.kill_switch.is_triggered():
                self.session.state = AgentState.CANCELLED
                yield AgentEvent(
                    type="cancelled",
                    data={
                        "status": "kill_switch",
                        "completed_steps": self._completed_steps,
                        "cancelled_step": self._current_step.description if self._current_step else None,
                    },
                    session_id=self.session.id
                )
                return

            # ... existing step execution
```

### Audit Entry Extension
```python
# Source: Extends existing TraceEntry pattern
class AuditEntry(TraceEntry):
    """Extended trace entry with safety-specific fields."""

    risk_level: Optional[RiskLevel] = None
    approval_required: bool = False
    approval_decision: Optional[Literal["approved", "rejected", "auto"]] = None
    approved_by: Optional[str] = None  # "user" or "similar_match"
    approval_time_ms: Optional[float] = None
    parent_step_id: Optional[str] = None  # Link to plan step
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Binary is_destructive | Four-tier risk classification | 2025 | Better granularity, reduced approval fatigue |
| Modal AlertDialog | BottomSheet for approvals | Flet 0.28+ | Less disruptive, better mobile UX |
| SIGINT handlers | multiprocessing.Event | Always | Cross-platform, doesn't affect entire process |
| Post-execution audit | Pre/post action capture | 2025 best practice | Full context for compliance |

**Deprecated/outdated:**
- Using `page.dialog` directly (use `page.show_dialog()` helper instead)
- Synchronous approval flows (block event loop; use async with Event)

## Open Questions

Things that couldn't be fully resolved:

1. **Timeout Duration for Fallback**
   - What we know: CONTEXT.md says "skip to safer alternative if available, otherwise pause"
   - What's unclear: How long to wait before fallback? 30 seconds? Configurable?
   - Recommendation: Default 60 seconds, configurable in settings; planner should use Claude's discretion

2. **Similarity Matching Scope**
   - What we know: File writes to same directory should match
   - What's unclear: How deep should subdirectory matching go? /src matches /src/components?
   - Recommendation: Match if child is_relative_to parent; one level deep by default

3. **System Tray Kill Switch on macOS/Linux**
   - What we know: pystray works cross-platform, but behavior varies
   - What's unclear: Flet desktop packaging behavior with tray icons
   - Recommendation: Implement as optional; primary kill switch is in-app button + keyboard shortcut

## Sources

### Primary (HIGH confidence)
- Flet BottomSheet docs: https://docs.flet.dev/controls/bottomsheet/
- Existing TraceStore implementation: `src/agent/observability/trace_store.py`
- Existing CancelDialog implementation: `src/agent/ui/cancel_dialog.py`
- Existing ToolDefinition model: `src/agent/models/tool.py`

### Secondary (MEDIUM confidence)
- [FlowHunt HITL Pattern](https://www.flowhunt.io/blog/human-in-the-loop-middleware-python-safe-ai-agents/)
- [LangChain HITL Docs](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [Graceful Shutdown Patterns](https://superfastpython.com/safely-stop-a-process-in-python/)
- [SQLite Audit Trail Guide](https://en.ittrip.xyz/python/sqlite-logging-audit-trail)

### Tertiary (LOW confidence)
- System tray integration examples (needs validation with Flet packaging)
- Global hotkey libraries (cross-platform support varies)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses existing codebase patterns and stdlib
- Architecture: HIGH - Extends existing models (ToolDefinition, TraceEntry, CancelDialog)
- Pitfalls: HIGH - Based on real patterns in codebase and HITL literature
- Kill switch specifics: MEDIUM - multiprocessing.Event is standard but integration with Flet needs testing

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable domain)
