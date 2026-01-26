# Phase 13: Autonomy Levels - Research

**Researched:** 2026-01-26
**Domain:** Agent autonomy configuration, approval thresholds, per-project settings, allowlist/blocklist rules
**Confidence:** HIGH

## Summary

Phase 13 configures how much human oversight the agent requires through four autonomy levels (L1-L4). The existing codebase provides strong foundations: `ActionClassifier` classifies actions into four risk levels (safe, moderate, destructive, critical), `ApprovalManager` handles HITL approval with similarity caching, `AuditStore` persists approval decisions to SQLite, and `AgentPanel` displays agent state with collapsible sections and event subscriptions.

The primary work involves: (1) creating an `AutonomyLevel` enum with threshold mappings to determine which risk levels auto-execute, (2) extending `WorkflowStorage` with a new `project_autonomy` table for per-project settings, (3) adding `AutonomyLevelService` to manage levels with allowlist/blocklist rules, (4) modifying `ActionClassifier.classify()` to consult autonomy settings before returning `requires_approval`, and (5) adding UI components to `AgentPanel` header for level indicator and quick toggle.

**Primary recommendation:** Build on existing infrastructure: extend `ActionClassifier` with autonomy awareness, use existing SQLite patterns for project settings, create `AutonomyBadge` following `RiskBadge` patterns, and integrate the quick toggle into `AgentPanel._header`.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | >=2.0 | Models for AutonomyLevel, AutonomySettings, AllowlistRule | Existing pattern in agent/models/ |
| sqlite3 | stdlib | Project autonomy settings storage | Existing WorkflowStorage pattern |
| flet | >=0.28.0 | UI components (Dropdown, Badge, Container) | Existing AgentPanel patterns |
| fnmatch | stdlib | Pattern matching for allowlist rules | Standard glob matching |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib | stdlib | Path pattern matching for file rules | Already used throughout codebase |
| re | stdlib | Regex patterns for advanced allowlist rules | Optional advanced rules |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| fnmatch glob patterns | Full regex | Glob simpler for users; regex more powerful but harder to write |
| SQLite project table | JSON file per project | SQLite enables querying across projects, better integrity |
| Literal type for levels | IntEnum | Literal matches existing RiskLevel pattern for consistency |

**Installation:**
```bash
# All dependencies already installed - no new packages needed
```

## Architecture Patterns

### Recommended Project Structure
```
src/agent/
  safety/
    autonomy.py          # AutonomyLevel, AutonomySettings, AutonomyLevelService
    allowlist.py         # AllowlistRule, BlocklistRule, RuleSet
    classification.py    # Extend with autonomy awareness (existing)
    approval.py          # Unchanged (existing)
  ui/
    autonomy_badge.py    # Level indicator component
    autonomy_toggle.py   # Quick toggle dropdown
    agent_panel.py       # Integrate badge and toggle (existing)
```

### Pattern 1: Autonomy Level Definition with Threshold Mapping
**What:** Four-tier autonomy using Literal types that map to risk level thresholds
**When to use:** Determining if an action requires approval based on current autonomy level
**Example:**
```python
# Source: Extends existing RiskLevel pattern
from typing import Literal
from pydantic import BaseModel

AutonomyLevel = Literal["L1", "L2", "L3", "L4"]

# Maps autonomy level to the highest risk level that auto-executes
AUTONOMY_THRESHOLDS: dict[AutonomyLevel, set[RiskLevel]] = {
    "L1": set(),                                    # Nothing auto-executes
    "L2": {"safe"},                                 # Only safe auto-executes
    "L3": {"safe", "moderate"},                     # Safe + moderate auto-execute
    "L4": {"safe", "moderate", "destructive"},      # Only critical requires approval
}

AUTONOMY_LABELS: dict[AutonomyLevel, str] = {
    "L1": "Assistant",
    "L2": "Collaborator",
    "L3": "Trusted",
    "L4": "Expert",
}

AUTONOMY_COLORS: dict[AutonomyLevel, str] = {
    "L1": "#3B82F6",  # Blue - most cautious
    "L2": "#10B981",  # Emerald - collaborative
    "L3": "#F59E0B",  # Amber - trusted
    "L4": "#EF4444",  # Red - expert (high autonomy)
}
```

### Pattern 2: Per-Project Settings with SQLite
**What:** Store autonomy level per project path in Skynette's SQLite DB
**When to use:** Loading/saving project-specific autonomy configuration
**Example:**
```python
# Source: Extends existing WorkflowStorage pattern
class WorkflowStorage:
    def _init_db(self):
        # ... existing tables ...

        # Project autonomy settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_autonomy (
                project_path TEXT PRIMARY KEY,
                autonomy_level TEXT NOT NULL DEFAULT 'L2',
                allowlist_rules TEXT,  -- JSON array
                blocklist_rules TEXT,  -- JSON array
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Global autonomy settings (user defaults)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autonomy_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

    def get_project_autonomy(self, project_path: str) -> str:
        """Get autonomy level for a project, or global default."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT autonomy_level FROM project_autonomy WHERE project_path = ?",
            (project_path,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return row[0]

        # Fall back to global default
        return self.get_setting("default_autonomy_level", "L2")

    def set_project_autonomy(self, project_path: str, level: str, rules: dict = None):
        """Set autonomy level and rules for a project."""
        # ... INSERT OR REPLACE ...
```

### Pattern 3: Allowlist/Blocklist Rule Matching
**What:** Pattern-based rules that override autonomy level thresholds
**When to use:** "Always allow web_search" or "Always block file_delete for /critical/*"
**Example:**
```python
# Source: Follows existing ActionClassification patterns
from dataclasses import dataclass
from fnmatch import fnmatch

@dataclass
class AutonomyRule:
    """Rule for overriding autonomy decisions."""
    rule_type: Literal["allow", "block"]
    scope: Literal["tool", "path"]  # tool-based or path-pattern-based
    pattern: str                     # e.g., "web_search" or "/src/*"
    tool_name: str | None = None     # For path rules, which tool this applies to

def matches_allowlist(
    tool_name: str,
    params: dict,
    rules: list[AutonomyRule],
) -> bool | None:
    """Check if action matches an allowlist rule.

    Returns:
        True if explicitly allowed
        False if explicitly blocked
        None if no rule matches (use autonomy level)
    """
    for rule in rules:
        if rule.scope == "tool" and fnmatch(tool_name, rule.pattern):
            return rule.rule_type == "allow"

        if rule.scope == "path" and (rule.tool_name is None or rule.tool_name == tool_name):
            path = params.get("path", "")
            if fnmatch(path, rule.pattern):
                return rule.rule_type == "allow"

    return None  # No matching rule
```

### Pattern 4: Classification with Autonomy Awareness
**What:** Modify approval requirement based on autonomy level and rules
**When to use:** Every tool action before execution
**Example:**
```python
# Source: Extends existing ActionClassifier
class ActionClassifier:
    def __init__(self, autonomy_service: AutonomyLevelService = None):
        self.autonomy_service = autonomy_service or get_autonomy_service()

    def classify(
        self,
        tool_name: str,
        parameters: dict,
        project_path: str | None = None,
    ) -> ActionClassification:
        """Classify action with autonomy awareness."""
        # Get base risk classification (existing logic)
        risk = self._get_base_risk(tool_name, parameters)

        # Get autonomy settings
        settings = self.autonomy_service.get_settings(project_path)

        # Check allowlist/blocklist first (overrides everything)
        rule_result = settings.check_rules(tool_name, parameters)
        if rule_result is not None:
            requires_approval = not rule_result  # allow=True means no approval
            return ActionClassification(
                risk_level=risk,
                reason=self._get_reason(tool_name, risk, parameters),
                requires_approval=requires_approval,
                tool_name=tool_name,
                parameters=parameters,
            )

        # Apply autonomy threshold
        auto_execute_levels = AUTONOMY_THRESHOLDS[settings.level]
        requires_approval = risk not in auto_execute_levels

        return ActionClassification(
            risk_level=risk,
            reason=self._get_reason(tool_name, risk, parameters),
            requires_approval=requires_approval,
            tool_name=tool_name,
            parameters=parameters,
        )
```

### Pattern 5: Mid-Task Level Changes
**What:** Handle autonomy level changes during execution, re-evaluating pending actions on downgrade
**When to use:** User switches level while agent is running
**Example:**
```python
# Source: Follows existing ApprovalManager patterns
class AutonomyLevelService:
    def __init__(self):
        self._current_level: dict[str, AutonomyLevel] = {}  # project_path -> level
        self._level_changed_callbacks: list[Callable] = []

    def set_level(self, project_path: str, level: AutonomyLevel):
        """Set autonomy level, triggering re-evaluation if needed."""
        old_level = self._current_level.get(project_path, "L2")
        self._current_level[project_path] = level

        # Persist to storage
        get_storage().set_project_autonomy(project_path, level)

        # Notify listeners (for re-evaluation on downgrade)
        if self._is_downgrade(old_level, level):
            for callback in self._level_changed_callbacks:
                callback(project_path, old_level, level, downgrade=True)

    def _is_downgrade(self, old: AutonomyLevel, new: AutonomyLevel) -> bool:
        """Check if level change is a downgrade (more restrictive)."""
        level_order = {"L4": 4, "L3": 3, "L2": 2, "L1": 1}
        return level_order[new] < level_order[old]
```

### Anti-Patterns to Avoid
- **Hardcoding level checks:** Use threshold mapping, not `if level == "L3": ...`
- **Storing settings in project files:** Use Skynette's DB, not `.skynette/config.yaml` in project
- **Blocking UI during level switch:** Level changes should be instant with async persistence
- **Ignoring blocklist on high autonomy:** Blocklist always overrides, even at L4

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Badge styling | Custom container with colors | Follow `RiskBadge` pattern | Consistency with existing UI |
| Dropdown in header | Custom popup menu | `ft.Dropdown` in `Row` | Existing pattern in AgentPanel |
| Settings persistence | File-based JSON | Extend `WorkflowStorage` SQLite | Querying, integrity, existing pattern |
| Pattern matching | Manual string parsing | `fnmatch.fnmatch()` | Standard, handles edge cases |
| Level color scheme | New palette | Extend existing semantic colors | Theme consistency |

**Key insight:** The pattern for settings is already established with `panel_preferences.py` using `WorkflowStorage.get_setting()`/`set_setting()`. Project autonomy extends this with a dedicated table for richer per-project data.

## Common Pitfalls

### Pitfall 1: Level Switch Not Taking Effect Immediately
**What goes wrong:** User switches to L1 but actions still auto-execute
**Why it happens:** Classifier caches level or doesn't re-query on each action
**How to avoid:** Always query current level in `classify()`, or use observer pattern with invalidation
**Warning signs:** Inconsistent behavior after level changes

### Pitfall 2: Allowlist Rules Too Broad
**What goes wrong:** User adds "always allow file_write" and agent overwrites critical files
**Why it happens:** Tool-based rules don't consider path context
**How to avoid:** Encourage path-based rules for file operations; warn when adding broad tool rules for destructive tools
**Warning signs:** Users surprised by auto-executed file modifications

### Pitfall 3: Project Path Normalization
**What goes wrong:** Same project has different autonomy levels depending on how path is specified
**Why it happens:** `/Users/foo/project` vs `/Users/foo/project/` vs resolved symlinks
**How to avoid:** Always `Path(project_path).resolve()` before storage/lookup
**Warning signs:** Settings not persisting, different behavior on same project

### Pitfall 4: Re-evaluation Race on Downgrade
**What goes wrong:** Pending actions execute before re-evaluation completes
**Why it happens:** Downgrade notification is async, executor doesn't wait
**How to avoid:** On downgrade, synchronously mark pending ApprovalRequests as needing re-evaluation; block execution until done
**Warning signs:** Actions execute immediately after downgrade

### Pitfall 5: Missing Global Default on Fresh Install
**What goes wrong:** New user has no autonomy level set, classifier fails or uses wrong default
**Why it happens:** No onboarding flow to set initial preference
**How to avoid:** Default to L2 (Collaborator) in code; onboarding prompts for preference
**Warning signs:** KeyError or unexpected L4 behavior on new install

## Code Examples

Verified patterns from existing codebase:

### AutonomyBadge Component
```python
# Source: Follows RiskBadge pattern from src/agent/ui/risk_badge.py
import flet as ft
from src.ui.theme import Theme

AUTONOMY_COLORS = {
    "L1": "#3B82F6",  # Blue
    "L2": "#10B981",  # Emerald
    "L3": "#F59E0B",  # Amber
    "L4": "#EF4444",  # Red
}

AUTONOMY_LABELS = {
    "L1": "Assistant",
    "L2": "Collaborator",
    "L3": "Trusted",
    "L4": "Expert",
}

class AutonomyBadge(ft.Container):
    """Color-coded badge showing autonomy level."""

    def __init__(self, level: AutonomyLevel, compact: bool = False):
        self.level = level
        color = AUTONOMY_COLORS.get(level, Theme.TEXT_MUTED)
        label = AUTONOMY_LABELS.get(level, level)

        if compact:
            content = ft.Container(
                width=10,
                height=10,
                border_radius=5,
                bgcolor=color,
                tooltip=f"{level}: {label}",
            )
            padding_val = 0
        else:
            content = ft.Row(
                controls=[
                    ft.Container(
                        width=8,
                        height=8,
                        border_radius=4,
                        bgcolor=color,
                    ),
                    ft.Text(
                        f"{level}",
                        color=color,
                        size=Theme.FONT_SM,
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                spacing=Theme.SPACING_XS,
            )
            padding_val = ft.padding.symmetric(
                horizontal=Theme.SPACING_SM,
                vertical=2,
            )

        super().__init__(
            content=content,
            bgcolor=f"{color}20",
            border=ft.border.all(1, color),
            border_radius=Theme.RADIUS_SM,
            padding=padding_val,
        )
```

### Quick Toggle in AgentPanel Header
```python
# Source: Extends existing AgentPanel._header from src/agent/ui/agent_panel.py
def _build_autonomy_toggle(self) -> ft.GestureDetector:
    """Build clickable autonomy level indicator that opens dropdown."""
    self._autonomy_badge = AutonomyBadge(
        level=self._current_autonomy_level,
        compact=False,
    )

    return ft.GestureDetector(
        content=self._autonomy_badge,
        on_tap=self._show_autonomy_dropdown,
        mouse_cursor=ft.MouseCursor.CLICK,
    )

def _show_autonomy_dropdown(self, e):
    """Show dropdown for quick level selection."""
    dropdown = ft.PopupMenuButton(
        items=[
            ft.PopupMenuItem(
                text=f"{level}: {AUTONOMY_LABELS[level]}",
                on_click=lambda _, l=level: self._set_autonomy_level(l),
            )
            for level in ["L1", "L2", "L3", "L4"]
        ],
    )
    # Position near the badge and show
    ...
```

### Auto-Execute Badge on Steps
```python
# Source: Extends existing StepViewSwitcher patterns
def _render_step_with_auto_badge(self, step: PlanStep, auto_executed: bool) -> ft.Control:
    """Render step with 'auto' badge if it was auto-executed."""
    step_row = self._render_step(step)  # Existing render

    if auto_executed:
        # Add subtle "auto" indicator
        auto_badge = ft.Container(
            content=ft.Text(
                "auto",
                size=Theme.FONT_XS,
                color=Theme.TEXT_MUTED,
            ),
            bgcolor=Theme.BG_TERTIARY,
            border_radius=Theme.RADIUS_SM,
            padding=ft.padding.symmetric(horizontal=4, vertical=1),
            tooltip="Auto-executed (would need approval at lower autonomy)",
        )
        step_row.controls.append(auto_badge)

    return step_row
```

### Project Settings Storage
```python
# Source: Extends WorkflowStorage from src/data/storage.py
def get_project_autonomy_settings(self, project_path: str) -> dict:
    """Get all autonomy settings for a project."""
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Normalize path
    normalized_path = str(Path(project_path).resolve())

    cursor.execute("""
        SELECT autonomy_level, allowlist_rules, blocklist_rules
        FROM project_autonomy
        WHERE project_path = ?
    """, (normalized_path,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "level": row["autonomy_level"],
            "allowlist": json.loads(row["allowlist_rules"] or "[]"),
            "blocklist": json.loads(row["blocklist_rules"] or "[]"),
        }

    # Return defaults
    return {
        "level": self.get_setting("default_autonomy_level", "L2"),
        "allowlist": json.loads(self.get_setting("global_allowlist", "[]")),
        "blocklist": json.loads(self.get_setting("global_blocklist", "[]")),
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Binary approval (destructive/safe) | Four-tier risk classification | Phase 11 | Foundation for autonomy thresholds |
| Single global approval setting | Per-project autonomy levels | Phase 13 | Better multi-project UX |
| All-or-nothing approval | Allowlist/blocklist overrides | Phase 13 | Granular control without level changes |
| Fixed approval requirements | Dynamic threshold based on level | Phase 13 | Reduced approval fatigue for experts |

**Deprecated/outdated:**
- Using `ToolDefinition.requires_approval` directly (now determined by autonomy level)
- Binary `is_destructive` flag (replaced by four-tier `RiskLevel`)

## Open Questions

Things that couldn't be fully resolved:

1. **Onboarding Flow Details**
   - What we know: New users should choose default level during onboarding
   - What's unclear: Full onboarding UX design (modal? dedicated page? tooltip?)
   - Recommendation: Use a simple modal on first launch; Claude's discretion for exact flow

2. **Rule Persistence Format**
   - What we know: Rules stored as JSON in SQLite, glob patterns for matching
   - What's unclear: Should rules support regex? Priority order for conflicting rules?
   - Recommendation: Start with glob (fnmatch); blocklist takes priority over allowlist; add regex if users request

3. **Badge in Project List**
   - What we know: CONTEXT.md says show badge in project list/switcher
   - What's unclear: Exact UI for project list (does it exist yet?)
   - Recommendation: If project list exists, add badge column; otherwise defer until that UI is built

## Sources

### Primary (HIGH confidence)
- Existing ActionClassifier: `src/agent/safety/classification.py`
- Existing ApprovalManager: `src/agent/safety/approval.py`
- Existing WorkflowStorage: `src/data/storage.py`
- Existing AgentPanel: `src/agent/ui/agent_panel.py`
- Existing RiskBadge: `src/agent/ui/risk_badge.py`
- Existing PanelPreferences: `src/agent/ui/panel_preferences.py`
- Phase 11 Research: `.planning/phases/11-safety-and-approval-systems/11-RESEARCH.md`

### Secondary (MEDIUM confidence)
- Flet Dropdown docs: https://docs.flet.dev/controls/dropdown/
- fnmatch stdlib docs: https://docs.python.org/3/library/fnmatch.html

### Tertiary (LOW confidence)
- None - all patterns verified from existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All patterns exist in codebase, no new libraries
- Architecture: HIGH - Direct extensions of existing classification/approval/storage patterns
- Pitfalls: HIGH - Based on code review of existing approval flow and storage
- UI components: HIGH - Direct application of RiskBadge and AgentPanel patterns

**Research date:** 2026-01-26
**Valid until:** 2026-02-26 (30 days - stable domain, extends existing infrastructure)
