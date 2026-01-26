# Phase 14: YOLO Mode - Research

**Researched:** 2026-01-26
**Domain:** L5 (Observer/YOLO) autonomous execution mode with confirmation dialogs, sandbox detection, enhanced audit logging
**Confidence:** HIGH

## Summary

Phase 14 adds L5 (YOLO) mode to the existing L1-L4 autonomy system from Phase 13. The existing infrastructure provides strong foundations: `AutonomyLevel` is a `Literal["L1", "L2", "L3", "L4"]` type with threshold mappings, `AutonomyLevelService` manages per-project levels with change callbacks, `AutonomyToggle` provides a `PopupMenuButton` for level selection, and `AuditStore` persists action logs to SQLite.

The primary work involves: (1) extending `AutonomyLevel` to include "L5" with special bypass behavior, (2) adding a confirmation dialog with warning when selecting L5 (unlike instant L1-L4 switches), (3) implementing sandbox detection heuristics for Docker/WSL/VM/cloud environments, (4) adding visual indicators (purple badge, panel border) when YOLO is active, (5) implementing session-only default behavior where L5 resets on app close, and (6) enhancing audit logging with extra verbosity for YOLO sessions.

**Primary recommendation:** Extend existing `AutonomyLevel` Literal to include "L5", add special handling in `AutonomyToggle` to show confirmation dialog, implement `SandboxDetector` utility class, create `YoloConfirmationDialog` following `CancelDialog` patterns, use purple (#8B5CF6) for YOLO styling, and add `yolo_mode` column to audit entries for enhanced logging.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| flet | >=0.28.0 | AlertDialog for confirmation, Container border styling | Existing dialog patterns |
| sqlite3 | stdlib | Enhanced audit logging, settings persistence | Existing AuditStore pattern |
| pydantic | >=2.0 | Extended AutonomyLevel, YoloSettings models | Existing pattern in agent/models/ |
| pathlib | stdlib | Path detection for sandbox heuristics | Already used throughout codebase |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| os | stdlib | Environment variable checks for sandbox detection | Detecting CODESPACES, GITPOD |
| platform | stdlib | System/platform detection | Detecting virtualization hints |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib sandbox detection | py_vmdetect library | External dependency vs simpler stdlib heuristics |
| Session-only via in-memory flag | SQLite with `session_id` column | In-memory simpler for session reset; SQLite enables cross-session analysis |
| Custom dialog | ft.AlertDialog directly | Custom dialog enables consistent styling and state management |

**Installation:**
```bash
# All dependencies already installed - no new packages needed
```

## Architecture Patterns

### Recommended Project Structure
```
src/agent/
  safety/
    autonomy.py          # Extended with L5, YoloSettings
    sandbox.py           # NEW: SandboxDetector class
    classification.py    # Extend for L5 bypass behavior
    audit.py             # Enhanced logging for YOLO mode
  ui/
    yolo_dialog.py       # NEW: Confirmation dialog
    autonomy_badge.py    # Extended with L5 purple styling
    autonomy_toggle.py   # Extended with L5 confirmation flow
    agent_panel.py       # Border styling when YOLO active
```

### Pattern 1: L5 Autonomy Level Extension
**What:** Extend AutonomyLevel Literal to include "L5" with special threshold behavior
**When to use:** When checking if any action auto-executes
**Example:**
```python
# Source: Extends existing src/agent/safety/autonomy.py
from typing import Literal

# Extended autonomy level type
AutonomyLevel = Literal["L1", "L2", "L3", "L4", "L5"]

# L5 threshold: ALL risk levels auto-execute (no approvals)
AUTONOMY_THRESHOLDS: dict[AutonomyLevel, set[RiskLevel]] = {
    "L1": set(),                                    # Nothing auto-executes
    "L2": {"safe"},                                 # Only safe auto-executes
    "L3": {"safe", "moderate"},                     # Safe + moderate auto-execute
    "L4": {"safe", "moderate", "destructive"},      # Only critical requires approval
    "L5": {"safe", "moderate", "destructive", "critical"},  # EVERYTHING auto-executes
}

AUTONOMY_LABELS: dict[AutonomyLevel, str] = {
    "L1": "Assistant",
    "L2": "Collaborator",
    "L3": "Trusted",
    "L4": "Expert",
    "L5": "YOLO",  # Distinctive name for power users
}

AUTONOMY_COLORS: dict[AutonomyLevel, str] = {
    "L1": "#3B82F6",  # Blue
    "L2": "#10B981",  # Emerald
    "L3": "#F59E0B",  # Amber
    "L4": "#EF4444",  # Red
    "L5": "#8B5CF6",  # Purple - power mode, not warning
}
```

### Pattern 2: Confirmation Dialog for L5 Selection
**What:** Modal dialog with warning when user selects L5
**When to use:** Only when switching TO L5 (not from L5 to lower levels)
**Example:**
```python
# Source: Follows CancelDialog pattern from src/agent/ui/cancel_dialog.py
import flet as ft
from src.ui.theme import Theme

class YoloConfirmationDialog(ft.AlertDialog):
    """
    Confirmation dialog when enabling YOLO mode.

    Shows warning and options:
    - Proceed anyway
    - Don't warn again (sets global preference)
    """

    def __init__(
        self,
        is_sandboxed: bool,
        on_confirm: Callable[[], None],
        on_dont_warn_again: Callable[[], None] | None = None,
    ):
        self._on_confirm = on_confirm
        self._on_dont_warn_again = on_dont_warn_again

        # Build content based on sandbox status
        warning_content = [
            ft.Text(
                "Actions will execute without approval prompts",
                color=Theme.TEXT_SECONDARY,
                size=Theme.FONT_SM,
            ),
        ]

        # Add sandbox warning if not sandboxed
        if not is_sandboxed:
            warning_content.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.WARNING_AMBER, color=Theme.WARNING, size=16),
                        ft.Text(
                            "Not detected as sandboxed environment",
                            color=Theme.WARNING,
                            size=Theme.FONT_SM,
                        ),
                    ], spacing=Theme.SPACING_XS),
                    padding=Theme.SPACING_SM,
                    bgcolor=f"{Theme.WARNING}20",
                    border_radius=Theme.RADIUS_SM,
                    margin=ft.margin.only(top=Theme.SPACING_SM),
                )
            )

        # Actions based on sandbox status
        actions = [
            ft.TextButton("Cancel", on_click=self._close),
            ft.ElevatedButton(
                "Enable YOLO Mode",
                on_click=self._confirm,
                bgcolor="#8B5CF6",  # Purple
                color=Theme.TEXT_PRIMARY,
            ),
        ]

        # Add "Don't warn again" only for non-sandboxed
        if not is_sandboxed and on_dont_warn_again:
            actions.insert(1, ft.TextButton(
                "Don't warn again",
                on_click=self._dont_warn_again,
            ))

        super().__init__(
            modal=True,
            title=ft.Text("Enable YOLO Mode?", weight=ft.FontWeight.BOLD),
            content=ft.Column(controls=warning_content, tight=True),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )
```

### Pattern 3: Sandbox Detection Heuristics
**What:** Detect Docker, WSL, VM, and cloud dev environments
**When to use:** Before showing YOLO warning dialog; determines if warning is needed
**Example:**
```python
# Source: Based on WebSearch findings for environment detection
import os
from pathlib import Path
from dataclasses import dataclass

@dataclass
class SandboxInfo:
    """Result of sandbox detection."""
    is_sandboxed: bool
    environment: str | None  # "docker", "wsl", "vm", "codespaces", "gitpod", etc.
    confidence: str  # "high", "medium", "low"

class SandboxDetector:
    """
    Detects sandboxed/isolated execution environments.

    Checks for:
    - Docker containers (/.dockerenv, cgroup)
    - WSL (/proc/version containing "microsoft")
    - Cloud IDEs (CODESPACES, GITPOD environment variables)
    - VMs (basic heuristics)
    """

    @staticmethod
    def detect() -> SandboxInfo:
        """Detect if running in a sandboxed environment."""
        # Check Docker
        if Path("/.dockerenv").exists():
            return SandboxInfo(True, "docker", "high")

        # Check cgroup for container indicators (Linux)
        cgroup_path = Path("/proc/1/cgroup")
        if cgroup_path.exists():
            try:
                content = cgroup_path.read_text()
                if "docker" in content or "containerd" in content:
                    return SandboxInfo(True, "docker", "high")
                if "lxc" in content:
                    return SandboxInfo(True, "lxc", "high")
            except PermissionError:
                pass

        # Check WSL
        proc_version = Path("/proc/version")
        if proc_version.exists():
            try:
                content = proc_version.read_text().lower()
                if "microsoft" in content or "wsl" in content:
                    return SandboxInfo(True, "wsl", "high")
            except PermissionError:
                pass

        # Check cloud dev environments
        if os.environ.get("CODESPACES") == "true":
            return SandboxInfo(True, "codespaces", "high")

        if os.environ.get("GITPOD_WORKSPACE_ID"):
            return SandboxInfo(True, "gitpod", "high")

        if os.environ.get("REMOTE_CONTAINERS") == "true":
            return SandboxInfo(True, "devcontainer", "high")

        # Check for common VM indicators (lower confidence)
        # These are heuristics and may have false positives
        try:
            import platform
            machine = platform.machine().lower()
            if "virtual" in machine:
                return SandboxInfo(True, "vm", "medium")
        except Exception:
            pass

        return SandboxInfo(False, None, "high")
```

### Pattern 4: Session-Only YOLO with Configurable Persistence
**What:** Default to resetting L5 on app close, with user option to persist
**When to use:** Storing/loading YOLO state
**Example:**
```python
# Source: Extends existing AutonomyLevelService pattern
@dataclass
class YoloSettings:
    """Settings specific to YOLO mode."""
    session_only: bool = True  # Default: YOLO resets when app closes
    persist_choice: bool = False  # If True, YOLO persists across sessions
    dont_warn_sandbox: bool = False  # Global: don't warn about non-sandboxed

class AutonomyLevelService:
    def __init__(self) -> None:
        # ... existing init ...
        self._session_yolo_projects: set[str] = set()  # In-memory L5 tracking

    def set_level(self, project_path: str, level: AutonomyLevel) -> None:
        """Set autonomy level, with special handling for L5."""
        normalized = str(Path(project_path).resolve())

        if level == "L5":
            # Check if session-only mode
            yolo_settings = self._get_yolo_settings(normalized)
            if yolo_settings.session_only:
                # Store in memory only (will reset on app close)
                self._session_yolo_projects.add(normalized)
                self._current_levels[normalized] = level
                # Don't persist to storage
            else:
                # Persist to storage if user chose to
                self._current_levels[normalized] = level
                get_storage().set_project_autonomy(normalized, level)
        else:
            # Remove from session YOLO tracking if downgrading
            self._session_yolo_projects.discard(normalized)
            # ... existing level setting logic ...
```

### Pattern 5: Enhanced Audit Logging for YOLO Mode
**What:** Extra verbosity and longer retention for YOLO sessions
**When to use:** When logging actions executed in L5 mode
**Example:**
```python
# Source: Extends existing src/agent/safety/audit.py
class AuditEntry(BaseModel):
    # ... existing fields ...

    # YOLO-specific fields
    yolo_mode: bool = False  # True if executed in L5 mode
    full_parameters: Optional[str] = None  # Untruncated params for YOLO

    def to_dict(self) -> dict:
        data = {
            # ... existing fields ...
            "yolo_mode": self.yolo_mode,
        }

        # For YOLO mode, include full parameters without truncation
        if self.yolo_mode and self.full_parameters:
            data["full_parameters"] = self.full_parameters

        return data

class AuditStore:
    # Extended default retention for YOLO sessions
    YOLO_RETENTION_DAYS = 90  # Longer retention for YOLO actions

    def log(self, entry: AuditEntry):
        """Log an audit entry with YOLO awareness."""
        # If YOLO mode, store full parameters without truncation
        if entry.yolo_mode:
            entry.full_parameters = json.dumps(entry.parameters)  # No truncation

        # ... existing log logic ...

    def cleanup_old_entries(
        self,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        yolo_retention_days: int = YOLO_RETENTION_DAYS,
    ) -> int:
        """Delete old entries, keeping YOLO entries longer."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Regular entries: standard retention
        regular_cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        cursor.execute(
            "DELETE FROM agent_audit WHERE timestamp < ? AND yolo_mode = 0",
            (regular_cutoff.isoformat(),)
        )
        regular_deleted = cursor.rowcount

        # YOLO entries: longer retention
        yolo_cutoff = datetime.now(timezone.utc) - timedelta(days=yolo_retention_days)
        cursor.execute(
            "DELETE FROM agent_audit WHERE timestamp < ? AND yolo_mode = 1",
            (yolo_cutoff.isoformat(),)
        )
        yolo_deleted = cursor.rowcount

        conn.commit()
        conn.close()
        return regular_deleted + yolo_deleted
```

### Pattern 6: Visual YOLO Indicators
**What:** Purple badge + panel border when YOLO is active
**When to use:** UI rendering when autonomy level is L5
**Example:**
```python
# Source: Extends existing src/agent/ui/autonomy_badge.py
YOLO_COLOR = "#8B5CF6"  # Purple

class AutonomyBadge(ft.Container):
    def __init__(self, level: AutonomyLevel, compact: bool = False):
        # ... existing init ...

        # Special styling for L5/YOLO
        if level == "L5":
            # Add pulsing effect indicator (optional)
            self.animate_opacity = ft.animation.Animation(
                1000, ft.AnimationCurve.EASE_IN_OUT
            )

# In AgentPanel
def _update_yolo_styling(self, is_yolo: bool) -> None:
    """Update panel border when YOLO mode changes."""
    if is_yolo:
        self._panel_container.border = ft.border.all(2, YOLO_COLOR)
        self._panel_container.bgcolor = f"{YOLO_COLOR}10"  # Subtle purple tint
    else:
        self._panel_container.border = ft.border.all(1, Theme.BORDER)
        self._panel_container.bgcolor = Theme.BG_SECONDARY
    self._panel_container.update()
```

### Pattern 7: Startup Reminder for Active YOLO
**What:** Show reminder when opening project that has YOLO active
**When to use:** On project load if L5 is persisted
**Example:**
```python
# Source: Follows existing SkynetteApp initialization patterns
class SkynetteApp:
    def initialize(self):
        # ... existing init ...

        # Check for active YOLO on startup
        self._check_yolo_startup_reminder()

    def _check_yolo_startup_reminder(self):
        """Show reminder if project has YOLO mode active."""
        if not self.current_project_path:
            return

        svc = get_autonomy_service()
        settings = svc.get_settings(self.current_project_path)

        if settings.level == "L5":
            # Show non-modal reminder banner or snackbar
            self.page.show_snack_bar(ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME, color=YOLO_COLOR),
                    ft.Text("YOLO mode is active for this project"),
                ]),
                bgcolor=f"{YOLO_COLOR}20",
                duration=5000,  # 5 seconds
            ))
```

### Anti-Patterns to Avoid
- **Mixing L5 with allowlist/blocklist evaluation:** L5 bypasses rules completely (true YOLO)
- **Persisting L5 by default:** Session-only prevents accidental persistence across reboots
- **Blocking dialog for sandboxed environments:** Only show warning if NOT sandboxed
- **Disabling kill switch in YOLO:** Kill switch ALWAYS remains active regardless of autonomy
- **Truncating YOLO audit logs:** Full parameters needed for post-incident analysis

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Confirmation dialog | Custom popup | `ft.AlertDialog` following CancelDialog | Consistent with existing patterns |
| Docker detection | Shell out to `docker info` | Check `/.dockerenv` and `/proc/1/cgroup` | No external dependency |
| WSL detection | Registry checks | `/proc/version` contains "microsoft" | Cross-platform, simple |
| Session state | Custom flag file | In-memory set in AutonomyLevelService | Automatically clears on process exit |
| Purple color | New color constant | Use existing NODE_COLORS["ai"] (#8B5CF6) | Theme consistency |

**Key insight:** The session-only behavior is elegantly achieved by NOT persisting L5 to SQLite by default. When the app closes, in-memory state is lost, effectively resetting to the persisted level (L2 default or user's previous choice).

## Common Pitfalls

### Pitfall 1: Kill Switch Disabled in YOLO Mode
**What goes wrong:** YOLO mode accidentally bypasses the emergency kill switch
**Why it happens:** Implementing YOLO as "bypass all safety" instead of "bypass approvals only"
**How to avoid:** Kill switch check happens at execution level, BEFORE any autonomy check. Never modify kill switch behavior based on autonomy level.
**Warning signs:** Unable to stop runaway agent in YOLO mode

### Pitfall 2: YOLO Persists After Unintended App Crash
**What goes wrong:** App crashes while in YOLO mode, persisted L5 is restored on restart
**Why it happens:** Session-only flag was ignored during level save
**How to avoid:** Ensure L5 is NEVER written to `project_autonomy` table unless user explicitly chooses "persist across sessions"
**Warning signs:** User surprised by YOLO being active after restart

### Pitfall 3: Sandbox Detection False Positives
**What goes wrong:** User is in sandboxed environment but warning still shows
**Why it happens:** Detection heuristics don't cover all sandbox types
**How to avoid:** Be generous with sandbox detection (err toward "sandboxed"); provide "don't warn again" escape hatch
**Warning signs:** Users complaining about unnecessary warnings in known safe environments

### Pitfall 4: Allowlist/Blocklist Still Evaluated in L5
**What goes wrong:** A blocklist rule prevents action even in YOLO mode
**Why it happens:** Classification still checks rules before threshold
**How to avoid:** In classification, if level is L5, return `requires_approval=False` immediately WITHOUT checking rules
**Warning signs:** "Blocked" actions in YOLO mode

### Pitfall 5: Missing YOLO Indicator During Task
**What goes wrong:** User forgets they're in YOLO mode, surprised by auto-executed actions
**Why it happens:** Badge only shows when panel is visible, no persistent indicator
**How to avoid:** Add panel border color change, consider taskbar/title indicator
**Warning signs:** Users reporting unexpected auto-execution

### Pitfall 6: Confirmation Dialog Every Time
**What goes wrong:** User has to confirm L5 selection every session, even though they're a power user
**Why it happens:** "Don't warn again" preference not being checked
**How to avoid:** Store global `dont_warn_sandbox` preference; check it before showing dialog
**Warning signs:** Power users frustrated by repeated confirmations

## Code Examples

Verified patterns from existing codebase:

### Extended AutonomyToggle with L5 Confirmation
```python
# Source: Extends existing src/agent/ui/autonomy_toggle.py
class AutonomyToggle(ft.Container):
    def _select_level(self, level: str):
        """Handle level selection from menu."""
        if level == "L5" and self._level != "L5":
            # L5 requires confirmation dialog
            self._show_yolo_confirmation()
        elif level in ("L1", "L2", "L3", "L4") and level != self._level:
            # L1-L4 switch is instant (existing behavior)
            self._apply_level_change(level)

    def _show_yolo_confirmation(self):
        """Show confirmation dialog for YOLO mode."""
        # Check if user has opted out of warnings
        storage = get_storage()
        dont_warn = storage.get_setting("yolo_dont_warn_sandbox", "false") == "true"

        # Detect sandbox
        sandbox_info = SandboxDetector.detect()

        # Skip dialog if sandboxed or user opted out
        if sandbox_info.is_sandboxed or dont_warn:
            self._apply_level_change("L5")
            return

        # Show confirmation dialog
        dialog = YoloConfirmationDialog(
            is_sandboxed=sandbox_info.is_sandboxed,
            on_confirm=lambda: self._apply_level_change("L5"),
            on_dont_warn_again=self._set_dont_warn_again,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _set_dont_warn_again(self):
        """Store preference to not warn about sandbox."""
        storage = get_storage()
        storage.set_setting("yolo_dont_warn_sandbox", "true")
```

### Classification with L5 Bypass
```python
# Source: Extends existing src/agent/safety/classification.py
class ActionClassifier:
    def classify(
        self,
        tool_name: str,
        parameters: dict,
        project_path: str | None = None,
    ) -> ActionClassification:
        """Classify action with YOLO awareness."""
        # Get base risk classification (existing logic)
        risk = self._get_base_risk(tool_name, parameters)

        # Get autonomy settings
        settings = self.autonomy_service.get_settings(project_path)

        # L5/YOLO: bypass ALL approval requirements
        if settings.level == "L5":
            return ActionClassification(
                risk_level=risk,
                reason=self._get_reason(tool_name, risk, parameters),
                requires_approval=False,  # Never requires approval in YOLO
                tool_name=tool_name,
                parameters=parameters,
            )

        # L1-L4: existing logic with allowlist/blocklist
        # ... existing code ...
```

### Settings View Extension for YOLO
```python
# Source: Extends existing src/ui/views/settings.py
def _build_autonomy_settings(self):
    """Build autonomy settings section."""
    # Load current settings
    storage = get_storage()
    yolo_session_only = storage.get_setting("yolo_session_only", "true") == "true"
    yolo_dont_warn = storage.get_setting("yolo_dont_warn_sandbox", "false") == "true"

    return ft.Column(
        controls=[
            # Existing default level dropdown...
            ft.Divider(height=1, color=Theme.BORDER),
            # YOLO-specific settings
            ft.Text(
                "YOLO Mode Settings",
                size=14,
                weight=ft.FontWeight.W_600,
                color=Theme.TEXT_PRIMARY,
            ),
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("Session-only by default", size=14, weight=ft.FontWeight.W_500),
                            ft.Text(
                                "YOLO mode resets when Skynette closes",
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                        expand=True,
                        spacing=2,
                    ),
                    ft.Switch(
                        value=yolo_session_only,
                        active_color="#8B5CF6",  # Purple
                        on_change=lambda e: storage.set_setting(
                            "yolo_session_only", "true" if e.control.value else "false"
                        ),
                    ),
                ],
            ),
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("Skip sandbox warning", size=14, weight=ft.FontWeight.W_500),
                            ft.Text(
                                "Don't warn when enabling YOLO outside sandbox",
                                size=12,
                                color=Theme.TEXT_SECONDARY,
                            ),
                        ],
                        expand=True,
                        spacing=2,
                    ),
                    ft.Switch(
                        value=yolo_dont_warn,
                        active_color="#8B5CF6",
                        on_change=lambda e: storage.set_setting(
                            "yolo_dont_warn_sandbox", "true" if e.control.value else "false"
                        ),
                    ),
                ],
            ),
        ],
        spacing=Theme.SPACING_MD,
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Binary safe/destructive | Four-tier risk (Phase 11) | Phase 11 | Foundation for thresholds |
| Single autonomy setting | L1-L4 per-project (Phase 13) | Phase 13 | Granular control |
| L4 max autonomy | L5 YOLO mode (Phase 14) | Phase 14 | Full autonomous execution |
| Standard audit retention | Enhanced YOLO retention | Phase 14 | Better post-incident analysis |

**Deprecated/outdated:**
- Using "fully autonomous" without kill switch - NEVER disable kill switch
- Persisting high autonomy by default - session-only is safer default

## Open Questions

Things that couldn't be fully resolved:

1. **Exact Purple Shade**
   - What we know: CONTEXT.md says purple, not red/amber (power mode, not warning)
   - What's unclear: Exact hex code that harmonizes with existing palette
   - Recommendation: Use #8B5CF6 (matches existing NODE_COLORS["ai"] for consistency)

2. **Execution Stats on Badge**
   - What we know: CONTEXT.md marks this as Claude's discretion
   - What's unclear: What stats are most useful? (actions/minute? total auto-executed?)
   - Recommendation: Start without stats; add if users request. Badge already conveys "YOLO is active"

3. **Allowlist/Blocklist in YOLO Mode**
   - What we know: CONTEXT.md marks this as Claude's discretion
   - What's unclear: Should blocklist rules still apply even in YOLO?
   - Recommendation: True YOLO = bypass everything. If user wants restrictions, they shouldn't use L5. Blocklist rules are for L1-L4.

4. **Auto-deactivation Trigger**
   - What we know: CONTEXT.md says auto-deactivation is user-configurable
   - What's unclear: What triggers auto-deactivation? Time? Action count? Error?
   - Recommendation: Defer auto-deactivation to future enhancement; focus on session-only as the safety mechanism

## Sources

### Primary (HIGH confidence)
- Existing AutonomyLevelService: `src/agent/safety/autonomy.py`
- Existing AutonomyToggle: `src/agent/ui/autonomy_toggle.py`
- Existing AutonomyBadge: `src/agent/ui/autonomy_badge.py`
- Existing AuditStore: `src/agent/safety/audit.py`
- Existing CancelDialog: `src/agent/ui/cancel_dialog.py`
- Existing CollectionDialog: `src/ui/dialogs/collection_dialog.py`
- Phase 13 Research: `.planning/phases/13-autonomy-levels/13-RESEARCH.md`
- Phase 14 Context: `.planning/phases/14-yolo-mode/14-CONTEXT.md`

### Secondary (MEDIUM confidence)
- [Flet AlertDialog docs](https://flet.dev/docs/controls/alertdialog/)
- [Flet examples - confirmation dialogs](https://github.com/flet-dev/examples/blob/main/python/controls/dialogs-alerts-panels/alert-dialog/dialogs.py)
- [py_vmdetect library](https://github.com/kepsic/py_vmdetect) - VM detection approaches
- [vmdetect toolkit](https://github.com/PerryWerneck/vmdetect/) - Cross-platform detection

### Tertiary (LOW confidence)
- [WebSearch: Docker/WSL/VM detection](https://www.cyberciti.biz/faq/linux-determine-virtualization-technology-command/) - Linux-specific approaches
- [WebSearch: Codespaces/Gitpod detection](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers) - Environment variables

## Metadata

**Confidence breakdown:**
- L5 level extension: HIGH - Direct extension of existing L1-L4 pattern
- Confirmation dialog: HIGH - Follows existing CancelDialog and CollectionDialog patterns
- Sandbox detection: MEDIUM - Heuristics may need refinement based on user feedback
- Visual indicators: HIGH - Direct extension of existing badge/panel styling
- Session-only behavior: HIGH - Simple in-memory vs persisted pattern
- Enhanced audit: HIGH - Direct extension of existing AuditStore

**Research date:** 2026-01-26
**Valid until:** 2026-02-26 (30 days - stable domain, extends existing Phase 13 infrastructure)
