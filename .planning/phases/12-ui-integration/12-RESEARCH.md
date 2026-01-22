# Phase 12: UI Integration - Research

**Researched:** 2026-01-22
**Domain:** Flet UI framework, agent event subscription, async UI patterns
**Confidence:** HIGH

## Summary

Phase 12 integrates existing agent backend capabilities (Phase 7-8) and safety systems (Phase 11) into the Flet UI. The primary challenge is wiring async event streams to synchronous UI updates while maintaining responsiveness.

The codebase already establishes strong patterns: `AgentEventEmitter` with async subscription (bounded queues, auto-unsubscribe on terminal events), existing safety UI components (`ApprovalSheet`, `RiskBadge`, `AgentStatusIndicator`, `CancelDialog`), and a clear theme system. The CONTEXT.md specifies user-configurable views (checklist/timeline/cards for steps, list/tree/flowchart for plans) and a resizable right sidebar with auto-expand for approvals.

**Primary recommendation:** Build an `AgentPanel` component that subscribes to `AgentEventEmitter`, dispatches events to child views (status, steps, audit), and manages the approval workflow via the existing `ApprovalManager` singleton.

## Standard Stack

### Core (Already in Project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flet | >=0.25.0 | UI framework | Already project framework |
| pydantic | >=2.0 | Data models | Already used for all agent models |
| asyncio | stdlib | Async coordination | Used throughout agent system |

### Supporting (Already in Project)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlite3 | stdlib | Settings persistence | Store panel width, view preferences |
| json | stdlib | Settings serialization | User configuration |

### No New Dependencies Required

All UI components use existing Flet controls. No additional libraries needed.

**Installation:**
```bash
# No new dependencies - all requirements already satisfied
```

## Architecture Patterns

### Recommended Project Structure

```
src/
├── agent/
│   └── ui/                    # Exists - extend this
│       ├── agent_panel.py     # NEW: Main panel component
│       ├── step_views.py      # NEW: Checklist/timeline/cards
│       ├── plan_views.py      # NEW: List/tree/flowchart
│       ├── audit_view.py      # NEW: Scrollable audit trail
│       ├── task_history.py    # NEW: History list with replay
│       ├── approval_sheet.py  # EXISTS: Extend for modify
│       ├── risk_badge.py      # EXISTS: No changes
│       ├── status_indicator.py # EXISTS: Minor updates
│       └── cancel_dialog.py   # EXISTS: No changes
└── ui/
    └── app.py                 # EXISTS: Add panel integration
```

### Pattern 1: Event-Driven UI Updates

**What:** Subscribe to AgentEventEmitter, dispatch to UI components
**When to use:** Whenever UI needs to reflect agent state changes

```python
# Source: Existing pattern from src/agent/ui/status_indicator.py
class AgentPanel(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self._subscription: Optional[EventSubscription] = None

    async def _event_loop(self, executor: AgentExecutor):
        """Subscribe and process events."""
        self._subscription = executor.emitter.subscribe(maxsize=100)

        async for event in self._subscription:
            # Route event to appropriate handler
            if event.type == "plan_created":
                self._handle_plan_created(event)
            elif event.type == "step_started":
                self._handle_step_started(event)
            elif event.type == "approval_requested":
                await self._show_approval_dialog(event)
            # ... etc

            # Update UI
            self._page.update()
```

### Pattern 2: Resizable Right Sidebar

**What:** GestureDetector with horizontal drag for panel resize
**When to use:** Agent panel docked to right side

```python
# Source: Existing pattern from src/ui/components/code_editor/resizable_panel.py
class AgentSidebar(ft.Row):
    MIN_WIDTH = 280
    MAX_WIDTH = 600
    DEFAULT_WIDTH = 350

    def __init__(self, content: ft.Control, on_resize: Callable[[int], None] = None):
        super().__init__()
        self._width = self.DEFAULT_WIDTH
        self._on_resize = on_resize
        self._container: ft.Container = None

        # Divider with drag
        self._divider = ft.GestureDetector(
            content=ft.Container(width=4, bgcolor=Theme.BORDER),
            on_horizontal_drag_update=self._on_drag,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        )

    def _on_drag(self, e: ft.DragUpdateEvent):
        # Note: For right sidebar, subtract delta (moving left = wider)
        new_width = self._width - e.delta_x
        new_width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, new_width))
        if new_width != self._width:
            self._width = int(new_width)
            self._container.width = self._width
            self._container.update()
            if self._on_resize:
                self._on_resize(self._width)
```

### Pattern 3: Approval Flow with asyncio.Event

**What:** Block agent execution until UI receives user decision
**When to use:** approval_requested events

```python
# Source: Existing pattern from src/agent/safety/approval.py
async def _show_approval_dialog(self, event: AgentEvent):
    """Show approval sheet and wait for decision."""
    # Get pending request from approval manager
    request = self._get_pending_request(event.data["request_id"])

    def on_approve(approve_similar: bool):
        request.set_result(ApprovalResult(
            decision="approved",
            approve_similar=approve_similar,
        ))
        sheet.hide()

    def on_reject():
        request.set_result(ApprovalResult(decision="rejected"))
        sheet.hide()

    sheet = ApprovalSheet(
        request=request,
        on_approve=on_approve,
        on_reject=on_reject,
    )
    sheet.show(self._page)
```

### Pattern 4: User Preference Storage

**What:** Persist panel width, view mode, visibility using WorkflowStorage
**When to use:** Any user-configurable setting

```python
# Source: Existing pattern from src/data/storage.py
def _save_panel_preferences(self):
    """Save panel state to settings."""
    storage = get_storage()
    storage.set_setting("agent_panel_width", str(self._width))
    storage.set_setting("agent_panel_visible", "1" if self._visible else "0")
    storage.set_setting("agent_panel_step_view", self._step_view_mode)  # "checklist"|"timeline"|"cards"
    storage.set_setting("agent_panel_plan_view", self._plan_view_mode)  # "list"|"tree"|"flowchart"

def _load_panel_preferences(self):
    """Load panel state from settings."""
    storage = get_storage()
    self._width = int(storage.get_setting("agent_panel_width", str(self.DEFAULT_WIDTH)))
    self._visible = storage.get_setting("agent_panel_visible", "1") == "1"
    self._step_view_mode = storage.get_setting("agent_panel_step_view", "checklist")
    self._plan_view_mode = storage.get_setting("agent_panel_plan_view", "list")
```

### Pattern 5: View Switcher with AnimatedSwitcher

**What:** Smooth transitions between view modes
**When to use:** User toggles between checklist/timeline/cards

```python
# Source: Flet docs - AnimatedSwitcher
class StepViewSwitcher(ft.AnimatedSwitcher):
    def __init__(self):
        super().__init__(
            content=ft.Container(),  # Initial placeholder
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=200,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
        )

    def set_view_mode(self, mode: str, steps: list[PlanStep]):
        """Switch to new view mode with animation."""
        if mode == "checklist":
            self.content = StepChecklistView(steps)
        elif mode == "timeline":
            self.content = StepTimelineView(steps)
        elif mode == "cards":
            self.content = StepCardsView(steps)
        self.update()
```

### Anti-Patterns to Avoid

- **Blocking the event loop:** Never use `time.sleep()` in UI handlers. Use `await asyncio.sleep()` or Flet's animation system.
- **Direct state mutation from events:** Always route through UI update methods, call `page.update()` after changes.
- **Multiple subscriptions:** Only one subscription per panel instance to prevent memory leaks and duplicate updates.
- **Polling for approval decisions:** Use `asyncio.Event` (already in ApprovalRequest) instead of polling.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Event subscription | Custom event system | `AgentEventEmitter.subscribe()` | Handles bounded queues, auto-cleanup |
| Approval blocking | Polling loop | `ApprovalRequest.wait_for_decision()` | Uses asyncio.Event properly |
| Risk display | Custom badge | `RiskBadge` component | Already styled with theme colors |
| Cancel modes | Simple cancel button | `CancelDialog` | Handles IMMEDIATE vs AFTER_CURRENT |
| Settings storage | JSON file | `WorkflowStorage.get/set_setting()` | Consistent with app, thread-safe |
| Kill switch | Custom stop flag | `get_kill_switch()` singleton | Uses multiprocessing.Event for safety |
| Audit queries | Manual SQL | `AuditStore.query()` | Handles filtering, pagination |

**Key insight:** The agent backend (Phase 7-8, 11) provides complete functionality. Phase 12 is purely UI wiring - use existing singletons and patterns.

## Common Pitfalls

### Pitfall 1: UI Updates from Background Tasks

**What goes wrong:** Calling `control.update()` from non-UI thread causes crashes or silent failures
**Why it happens:** Flet (like Flutter) requires UI updates on the main thread
**How to avoid:** Always use `page.update()` from the async event loop, not control-level updates
**Warning signs:** "Not attached to page" errors, UI not reflecting state changes

### Pitfall 2: Memory Leaks from Unsubscribed Events

**What goes wrong:** Panel removed but subscription stays active, accumulating events
**Why it happens:** Forgetting to call `subscription.close()` when panel unmounts
**How to avoid:** Implement `dispose()` method that closes subscription; call from parent
**Warning signs:** Increasing memory usage, events processed after panel hidden

### Pitfall 3: Approval Timeout Blocking Forever

**What goes wrong:** User closes app or navigates away, approval never resolves
**Why it happens:** No timeout on `wait_for_decision()`, or timeout not handled
**How to avoid:** Always pass timeout parameter (60s default per CONTEXT.md), handle timeout result
**Warning signs:** Agent hangs on "awaiting approval" state indefinitely

### Pitfall 4: Race Condition in Plan Updates

**What goes wrong:** Plan view shows stale data after replan during execution
**Why it happens:** UI rebuilt from old plan object while executor updated the plan
**How to avoid:** Store plan reference, update on `plan_created` events, re-render on each event
**Warning signs:** Step counts mismatch, completed steps not shown

### Pitfall 5: BottomSheet Not Dismissing

**What goes wrong:** ApprovalSheet stays visible after approve/reject
**Why it happens:** Forgetting to call `sheet.open = False` and `sheet.update()`
**How to avoid:** Follow existing pattern: set `open = False`, then `update()`, then callback
**Warning signs:** Multiple sheets stacked, UI frozen behind sheet

## Code Examples

### Event Handler Routing (Core Pattern)

```python
# Source: Based on existing patterns in agent/ui/status_indicator.py
async def _process_event(self, event: AgentEvent):
    """Route event to appropriate handler."""
    handlers = {
        "state_change": self._on_state_change,
        "plan_created": self._on_plan_created,
        "step_started": self._on_step_started,
        "step_completed": self._on_step_completed,
        "tool_called": self._on_tool_called,
        "tool_result": self._on_tool_result,
        "action_classified": self._on_action_classified,
        "approval_requested": self._on_approval_requested,
        "approval_received": self._on_approval_received,
        "kill_switch_triggered": self._on_kill_switch,
        "completed": self._on_completed,
        "error": self._on_error,
        "cancelled": self._on_cancelled,
    }

    handler = handlers.get(event.type)
    if handler:
        if asyncio.iscoroutinefunction(handler):
            await handler(event)
        else:
            handler(event)

    # Always update page after event processing
    self._page.update()
```

### Step Checklist View

```python
# Source: Pattern from existing code + Flet docs
class StepChecklistView(ft.ListView):
    """Vertical list with checkmarks for each step."""

    def __init__(self, steps: list[PlanStep]):
        super().__init__(
            spacing=Theme.SPACING_XS,
            auto_scroll=True,
            expand=True,
        )
        self._steps = steps
        self._build_list()

    def _build_list(self):
        self.controls = [self._build_step_row(i, step)
                         for i, step in enumerate(self._steps)]

    def _build_step_row(self, index: int, step: PlanStep) -> ft.Container:
        status_icon = {
            StepStatus.PENDING: ft.Icons.RADIO_BUTTON_UNCHECKED,
            StepStatus.RUNNING: ft.Icons.PLAY_CIRCLE,
            StepStatus.COMPLETED: ft.Icons.CHECK_CIRCLE,
            StepStatus.FAILED: ft.Icons.ERROR,
            StepStatus.SKIPPED: ft.Icons.SKIP_NEXT,
        }
        status_color = {
            StepStatus.PENDING: Theme.TEXT_MUTED,
            StepStatus.RUNNING: Theme.PRIMARY,
            StepStatus.COMPLETED: Theme.SUCCESS,
            StepStatus.FAILED: Theme.ERROR,
            StepStatus.SKIPPED: Theme.TEXT_SECONDARY,
        }

        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    status_icon.get(step.status, ft.Icons.HELP),
                    color=status_color.get(step.status, Theme.TEXT_MUTED),
                    size=18,
                ),
                ft.Text(
                    f"{index + 1}. {step.description}",
                    color=Theme.TEXT_PRIMARY if step.status == StepStatus.RUNNING
                          else Theme.TEXT_SECONDARY,
                    expand=True,
                ),
            ], spacing=Theme.SPACING_SM),
            padding=Theme.SPACING_XS,
            on_click=lambda e, s=step: self._show_step_detail(s),
        )

    def update_step(self, step_id: str, status: StepStatus):
        """Update a specific step's status."""
        for i, step in enumerate(self._steps):
            if step.id == step_id:
                step.status = status
                self.controls[i] = self._build_step_row(i, step)
                break
```

### Audit Trail View

```python
# Source: Pattern from trace_viewer.py + existing UI patterns
class AuditTrailView(ft.ListView):
    """Scrollable, filterable audit log."""

    def __init__(self, session_id: str):
        super().__init__(
            spacing=Theme.SPACING_XS,
            auto_scroll=False,  # User controls scroll position
            expand=True,
        )
        self._session_id = session_id
        self._audit_store = get_audit_store()
        self._filter_risk: Optional[RiskLevel] = None

    def refresh(self):
        """Reload entries from audit store."""
        entries = self._audit_store.query(
            session_id=self._session_id,
            risk_level=self._filter_risk,
            limit=100,
        )
        self.controls = [self._build_entry_row(e) for e in entries]

    def _build_entry_row(self, entry: AuditEntry) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    RiskBadge(entry.risk_level, compact=True),
                    ft.Text(entry.tool_name, weight=ft.FontWeight.W_500),
                    ft.Container(expand=True),
                    ft.Text(
                        entry.timestamp.strftime("%H:%M:%S"),
                        color=Theme.TEXT_MUTED,
                        size=Theme.FONT_XS,
                    ),
                ], spacing=Theme.SPACING_XS),
                ft.Text(
                    f"Duration: {entry.duration_ms:.0f}ms | "
                    f"Approval: {entry.approval_decision}",
                    color=Theme.TEXT_SECONDARY,
                    size=Theme.FONT_XS,
                ),
            ], spacing=2, tight=True),
            padding=Theme.SPACING_SM,
            bgcolor=Theme.BG_TERTIARY,
            border_radius=Theme.RADIUS_SM,
            on_click=lambda e, ent=entry: self._show_detail(ent),
        )
```

### Task History with Replay

```python
# Source: Pattern from trace_store.py + trace_viewer.py
class TaskHistoryView(ft.Column):
    """List of past agent tasks with replay capability."""

    def __init__(self, on_replay: Callable[[str], None]):
        super().__init__(expand=True)
        self._trace_store = TraceStore()
        self._on_replay = on_replay
        self._build()

    def _build(self):
        sessions = self._trace_store.get_sessions(limit=20)

        self.controls = [
            ft.Text("Recent Tasks", weight=ft.FontWeight.BOLD),
            ft.ListView(
                controls=[self._build_session_row(s) for s in sessions],
                expand=True,
                spacing=Theme.SPACING_XS,
            ),
        ]

    def _build_session_row(self, session: TraceSession) -> ft.Container:
        status_color = {
            "completed": Theme.SUCCESS,
            "failed": Theme.ERROR,
            "cancelled": Theme.WARNING,
            "running": Theme.PRIMARY,
        }

        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.HISTORY,
                    color=status_color.get(session.status, Theme.TEXT_MUTED),
                    size=16,
                ),
                ft.Column([
                    ft.Text(
                        session.task[:50] + ("..." if len(session.task) > 50 else ""),
                        size=Theme.FONT_SM,
                    ),
                    ft.Text(
                        session.started_at.strftime("%Y-%m-%d %H:%M"),
                        color=Theme.TEXT_MUTED,
                        size=Theme.FONT_XS,
                    ),
                ], spacing=2, expand=True),
                ft.IconButton(
                    icon=ft.Icons.REPLAY,
                    icon_size=16,
                    tooltip="Replay this task",
                    on_click=lambda e, s=session: self._on_replay(s.task),
                ),
            ], spacing=Theme.SPACING_SM),
            padding=Theme.SPACING_SM,
            bgcolor=Theme.BG_SECONDARY,
            border_radius=Theme.RADIUS_SM,
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Imperative UI updates | Declarative UI (Flet 1.0) | Oct 2025 | Optional - can still use imperative |
| Thread-per-handler | Single async loop | Flet 0.25+ | Better performance, simpler code |
| Manual overlay management | `page.show_dialog()` | Flet 0.25+ | Handles overlay stack automatically |

**Deprecated/outdated:**
- `page.dialog` property: Use `page.show_dialog()` / `page.pop_dialog()` instead
- Thread-based event handlers: Prefer async handlers for agent events

## Open Questions

Things that couldn't be fully resolved:

1. **Flowchart/diagram view for plans**
   - What we know: CONTEXT.md requests flowchart option for plan visualization
   - What's unclear: Flet has no built-in graph/flowchart control
   - Recommendation: Start with list and tree views (can build with ListView + indentation). Flowchart as future enhancement requiring custom Canvas drawing or embedded web component.

2. **Plan editing UI**
   - What we know: CONTEXT.md requests editable plan with reorder/remove/add/edit
   - What's unclear: How agent executor handles plan modifications mid-execution
   - Recommendation: Implement view-only first, then add editing for pre-execution approval. Editing during execution requires careful coordination with executor.

3. **Batch approval grouping**
   - What we know: CONTEXT.md wants "Approve 5 similar file reads?" grouped cards
   - What's unclear: ApprovalManager handles similarity internally but doesn't expose batch requests
   - Recommendation: Extend ApprovalManager to expose pending similar actions, build UI to show grouped card with expandable list.

## Sources

### Primary (HIGH confidence)
- `src/agent/events/emitter.py` - Event subscription pattern
- `src/agent/safety/approval.py` - Approval flow with asyncio.Event
- `src/agent/ui/approval_sheet.py` - Existing approval UI
- `src/agent/ui/status_indicator.py` - Event-to-UI update pattern
- `src/ui/components/code_editor/resizable_panel.py` - Resizable panel pattern
- `src/data/storage.py` - Settings persistence pattern
- `src/ui/theme.py` - Theme system
- `src/agent/observability/trace_store.py` - History/trace patterns
- `src/agent/safety/audit.py` - Audit trail storage

### Secondary (MEDIUM confidence)
- [Flet Animations Documentation](https://docs.flet.dev/cookbook/animations/) - AnimatedSwitcher, implicit animations
- [Flet GestureDetector Documentation](https://docs.flet.dev/controls/gesturedetector/) - Drag handling for resize
- [Flet BottomSheet Documentation](https://docs.flet.dev/controls/bottomsheet/) - Modal sheet patterns
- [Flet ListView Documentation](https://docs.flet.dev/controls/listview/) - Large list performance

### Tertiary (LOW confidence)
- Flet 1.0 declarative UI patterns (new, limited production examples)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in project, well-documented
- Architecture: HIGH - Clear patterns established in codebase
- Pitfalls: HIGH - Identified from existing code and Flet documentation
- Flowchart view: LOW - No built-in solution, requires research

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - Flet is stable, patterns established)
