# Phase 1: Stability & Audit - Research

**Researched:** 2026-01-18
**Domain:** Software auditing, Python testing, Flet UI framework, state management refactoring
**Confidence:** HIGH (based on official documentation and established patterns)

## Summary

Phase 1 is an audit-and-fix phase focused on stabilizing three existing features (AI Chat, Model Management, Workflow Builder) and refactoring the AIHubView state management (1669 lines). The research confirms the codebase uses Flet 0.80.1 (async-first framework), pytest for testing with established fixtures/mocks structure, and follows standard Python project patterns.

The audit approach should combine manual walkthroughs with automated testing. Manual discovery first to find issues, then write regression tests to capture findings. The state management refactor should follow the State pattern and modular decomposition principles - splitting the monolithic AIHubView into focused, testable components organized by feature domain.

**Primary recommendation:** Use systematic audit methodology (static analysis + manual walkthrough + targeted testing) followed by modular refactoring of AIHubView using feature-based decomposition.

## Standard Stack

The established tools for auditing, testing, and refactoring Python/Flet applications:

### Core Testing
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=8.0.0 | Test framework | Already in pyproject.toml, fixtures/mocking support |
| pytest-asyncio | >=0.23.0 | Async test support | Required for Flet async-first model |
| pytest-cov | >=4.1.0 | Coverage reporting | Track test coverage during audit |

### Static Analysis
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| ruff | >=0.3.0 | Linting/formatting | Already configured, fast Python linter |
| mypy | >=1.8.0 | Type checking | Already in dev deps, catch type errors |
| bandit | >=1.7.0 | Security scanning | Already in dev deps, find security issues |

### Existing Test Infrastructure
The codebase already has:
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end tests with Playwright
- `tests/mocks/` - Mock providers and storage
- `tests/fixtures/` - Reusable test fixtures
- `conftest.py` files for pytest configuration

**Installation:** Already installed via `pip install -e ".[dev]"`

## Architecture Patterns

### Current Codebase Structure (Relevant to Audit)
```
src/
├── ai/
│   ├── gateway.py          # AIGateway - unified AI interface
│   ├── providers/          # Provider implementations
│   └── models/             # Model management (hub.py, sources/)
├── ui/
│   ├── views/
│   │   ├── ai_hub.py       # AIHubView - 1669 lines (refactor target)
│   │   ├── workflow_editor.py
│   │   ├── simple_mode.py
│   │   └── workflows.py
│   ├── theme.py
│   └── app.py              # Main Flet application
├── core/
│   ├── workflow/
│   │   ├── models.py       # Workflow, WorkflowNode, etc.
│   │   └── executor.py     # WorkflowExecutor
│   └── nodes/              # Node implementations
└── data/
    └── storage.py          # Data persistence
```

### Recommended Refactored AIHubView Structure
```
src/ui/views/
├── ai_hub/
│   ├── __init__.py         # AIHubView (coordinator)
│   ├── wizard.py           # Setup wizard (steps 1-3)
│   ├── providers.py        # Provider management tab
│   ├── model_library.py    # Model library (My Models, HF, Ollama, Import)
│   ├── ollama_tab.py       # Ollama-specific functionality
│   ├── huggingface_tab.py  # Hugging Face integration
│   ├── import_tab.py       # Local file import
│   └── state.py            # Shared state container
```

### Pattern 1: Feature-Based Module Decomposition
**What:** Split large files by logical feature domains, not arbitrary line counts
**When to use:** Files exceed 500 lines AND contain multiple distinct features
**Example:**
```python
# src/ui/views/ai_hub/__init__.py
# Source: Python project structuring best practices

from .wizard import SetupWizard
from .providers import ProvidersTab
from .model_library import ModelLibraryTab

class AIHubView(ft.Column):
    """AI Model Hub - coordinates tabs but delegates to specialized components."""

    def __init__(self, page: ft.Page = None):
        super().__init__()
        self._page = page
        self.wizard = SetupWizard(page=page, on_complete=self._on_wizard_complete)
        self.providers = ProvidersTab(page=page)
        self.library = ModelLibraryTab(page=page)

    def build(self):
        # Thin coordinator - each tab is a self-contained component
        return ft.Tabs(...)
```

### Pattern 2: State Container Pattern
**What:** Centralize shared state in a dedicated class with clear mutation methods
**When to use:** Multiple components need to share and update the same state
**Example:**
```python
# src/ui/views/ai_hub/state.py
# Source: State design pattern

from dataclasses import dataclass, field
from typing import Callable

@dataclass
class AIHubState:
    """Centralized state for AI Hub components."""
    wizard_step: int = 0
    selected_providers: list[str] = field(default_factory=list)
    provider_configs: dict = field(default_factory=dict)

    _listeners: list[Callable] = field(default_factory=list, repr=False)

    def add_listener(self, callback: Callable):
        self._listeners.append(callback)

    def notify(self):
        for listener in self._listeners:
            listener()

    def set_wizard_step(self, step: int):
        self.wizard_step = step
        self.notify()
```

### Pattern 3: Audit-First Testing
**What:** Write tests that capture discovered bugs before fixing them
**When to use:** During audit phase - proves bug exists, then proves fix works
**Example:**
```python
# tests/unit/test_ai_hub_audit.py
# Source: pytest best practices

import pytest

class TestAIHubAuditFindings:
    """Tests documenting bugs found during audit."""

    @pytest.mark.xfail(reason="BUG: Wizard doesn't persist state on back button")
    def test_wizard_back_button_preserves_selections(self, ai_hub_view):
        """Regression test for wizard state persistence."""
        # Arrange - select providers
        ai_hub_view.selected_providers = ["openai", "anthropic"]
        ai_hub_view._wizard_next_step()

        # Act - go back
        ai_hub_view._wizard_prev_step()

        # Assert - selections should be preserved
        assert ai_hub_view.selected_providers == ["openai", "anthropic"]
```

### Anti-Patterns to Avoid
- **God Classes:** AIHubView at 1669 lines violates single responsibility. Split by feature.
- **Global Mutable State:** Current `wizard_step`, `selected_providers` as instance variables without clear mutation boundaries. Use State Container pattern.
- **Dialog-in-Method:** Creating dialogs inline makes testing difficult. Extract to methods/classes.
- **Async/Sync Mixing Without Clarity:** Flet 0.80+ is async-first. Be consistent about which methods are async.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test fixtures | Manual setup in each test | pytest fixtures in conftest.py | Reuse, proper teardown |
| Mocking AI providers | Ad-hoc mock classes | `tests/mocks/ai_providers.py` (exists) | Already built, consistent |
| Async testing | Manual event loop management | pytest-asyncio with `async def test_` | Proper async test lifecycle |
| Code coverage | Manual tracking | pytest-cov with `--cov=src` | Accurate, integrates with CI |
| Type checking | Manual review | mypy with existing config | Catches bugs static analysis misses |
| Security audit | Manual code review only | bandit scan first, then manual | Automated catches common issues |

**Key insight:** The test infrastructure is already in place. Focus on using existing fixtures/mocks rather than creating new test utilities.

## Common Pitfalls

### Pitfall 1: Testing Flet UI Without Isolation
**What goes wrong:** Tests try to render full Flet UI, causing slow tests and flaky failures
**Why it happens:** Flet components depend on `page` object and event loop
**How to avoid:**
- Mock `page` object in unit tests
- Test view logic separately from rendering
- Use e2e tests only for critical user flows
**Warning signs:** Tests take >1s each, random failures on CI

### Pitfall 2: Async/Sync Confusion in Flet 0.80+
**What goes wrong:** Mixing `time.sleep()` with async code freezes UI
**Why it happens:** Flet 0.80+ is async-first, blocking calls freeze event loop
**How to avoid:**
- Use `asyncio.sleep()` instead of `time.sleep()`
- Use `page.run_task()` for background operations
- Mark event handlers appropriately (sync or async)
**Warning signs:** UI freezes during operations, tests hang

### Pitfall 3: Incomplete Audit Coverage
**What goes wrong:** Finding surface bugs but missing deep issues
**Why it happens:** Only testing happy paths, not edge cases
**How to avoid:**
- Use static analysis (ruff, mypy, bandit) first
- Test error paths explicitly
- Test with large data (1000+ messages, many models)
- Test concurrent operations
**Warning signs:** Bugs resurface after "fixed", users find issues you didn't

### Pitfall 4: Refactoring Without Tests
**What goes wrong:** Refactoring breaks functionality without detection
**Why it happens:** Moving code without regression tests
**How to avoid:**
- Write characterization tests BEFORE refactoring
- Run tests after each small change
- Prefer small, incremental refactors over big-bang rewrites
**Warning signs:** "It worked before I refactored" situations

### Pitfall 5: Over-Mocking Leads to False Confidence
**What goes wrong:** Tests pass but real integrations fail
**Why it happens:** Mocks don't match real provider behavior
**How to avoid:**
- Keep integration tests with real (or realistic) providers
- Update mocks when provider behavior changes
- Use fixtures that mirror real data structures
**Warning signs:** Tests green but manual testing shows failures

## Code Examples

Verified patterns for the audit phase:

### Running Static Analysis (Existing Tools)
```bash
# Source: pyproject.toml configuration
# Run ruff for linting
ruff check src/ tests/

# Run mypy for type checking
mypy src/

# Run bandit for security
bandit -r src/ -x tests/
```

### Audit Test Pattern
```python
# Source: pytest best practices
# tests/unit/test_ai_chat_audit.py

import pytest
from unittest.mock import AsyncMock, MagicMock

class TestAIChatAudit:
    """Audit tests for AI Chat functionality (STAB-01)."""

    @pytest.fixture
    def mock_page(self):
        """Mock Flet page for testing."""
        page = MagicMock()
        page.update = MagicMock()
        page.run_task = MagicMock()
        return page

    @pytest.fixture
    def mock_gateway(self):
        """Mock AI Gateway."""
        gateway = AsyncMock()
        gateway.chat = AsyncMock(return_value=AIResponse(
            content="Test response",
            provider="mock",
            model="test-model",
            usage={"total_tokens": 100}
        ))
        return gateway

    @pytest.mark.asyncio
    async def test_send_message_updates_ui(self, mock_page, mock_gateway):
        """Verify message send updates UI properly."""
        # Test implementation
        pass

    @pytest.mark.asyncio
    async def test_large_conversation_history_performance(self, mock_page, mock_gateway):
        """STAB-04: Large conversation history doesn't degrade."""
        # Generate 1000 messages
        messages = [AIMessage(role="user", content=f"Message {i}") for i in range(1000)]
        # Measure time to render/update
        pass
```

### Refactoring: Extracting a Component
```python
# Source: Python modular decomposition patterns
# BEFORE: Inline wizard in AIHubView (500+ lines)
# AFTER: Extracted to src/ui/views/ai_hub/wizard.py

import flet as ft
from src.ui.theme import Theme

class SetupWizard(ft.Column):
    """AI Provider setup wizard - steps 1 through 3."""

    def __init__(self, page: ft.Page = None, on_complete=None):
        super().__init__()
        self._page = page
        self.on_complete = on_complete
        self.step = 0
        self.selected_providers: list[str] = []
        self.provider_configs: dict = {}

    def build(self):
        """Build current wizard step."""
        builders = [
            self._build_step1_provider_selection,
            self._build_step2_configure_providers,
            self._build_step3_completion,
        ]
        return builders[min(self.step, len(builders) - 1)]()

    def _build_step1_provider_selection(self) -> ft.Container:
        # Extracted from AIHubView._build_wizard_step1_provider_selection
        pass

    # ... other methods
```

### Using Existing Mocks
```python
# tests/unit/test_model_management.py
# Source: Existing test infrastructure

from tests.mocks.ai_providers import MockProvider
from tests.mocks.storage import MockStorage

def test_model_list_displays_local_models(mock_page):
    """STAB-02: Model list shows local models correctly."""
    # Use existing mock infrastructure
    storage = MockStorage()
    storage.set_setting("configured_providers", '["local"]')

    # Test model display
    pass
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sync Flet | Async-first Flet | Flet 0.21.0+ | Must use async patterns |
| `time.sleep()` | `asyncio.sleep()` | Flet 0.21.0+ | Blocking freezes UI |
| Monolithic views | Feature-based modules | Best practice | Better testability |
| Ad-hoc testing | pytest fixtures/mocks | Standard | Consistent test patterns |

**Deprecated/outdated:**
- Sync-only Flet apps: Flet 0.80+ is async-first, sync methods run in threads
- `google-generativeai`: Use `google-genai>=1.59.0` (per prior research)

## Open Questions

Things that couldn't be fully resolved:

1. **Exact bug list for each feature**
   - What we know: Phase requires auditing AI Chat, Model Management, Workflow Builder
   - What's unclear: Specific bugs not yet discovered (that's the audit's job)
   - Recommendation: Use systematic audit methodology; document as discovered

2. **AIHubView performance baseline**
   - What we know: 1669 lines is flagged as concern, but no actual performance issues reported
   - What's unclear: Whether current implementation actually has performance problems
   - Recommendation: Establish baseline metrics before refactoring

3. **Flet testing best practices maturity**
   - What we know: Flet roadmap includes test suite development for 1.0
   - What's unclear: Official testing patterns not yet standardized
   - Recommendation: Follow pytest-asyncio patterns; mock page object for unit tests

## Sources

### Primary (HIGH confidence)
- [Flet Async Apps Documentation](https://flet.dev/docs/getting-started/async-apps/) - Official async patterns
- [Flet Roadmap](https://flet.dev/roadmap/) - Testing is focus for 2025
- [pytest Best Practices](https://pytest-with-eric.com/pytest-best-practices/pytest-organize-tests/) - Test organization
- [pytest Official Good Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) - Test structure
- [Real Python pytest Guide](https://realpython.com/pytest-python-testing/) - Comprehensive pytest guide

### Secondary (MEDIUM confidence)
- [FletX Reactive Patterns](https://medium.com/@einswilligoeh/fletx-bring-reactive-power-to-your-python-ui-with-getx-like-simplicity-61d186ebc58a) - State management approach
- [pytest-asyncio](https://articles.mergify.com/pytest-asyncio/) - Async testing patterns
- [Python Module Organization](https://docs.python-guide.org/writing/structure/) - Hitchhiker's Guide
- [STX Next Code Audit Guide](https://www.stxnext.com/blog/how-to-audit-the-quality-of-your-python-code) - Python audit checklist

### Tertiary (LOW confidence)
- WebSearch results on code audit methodology - general guidance, verify against codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Already in pyproject.toml, verified installed
- Architecture patterns: HIGH - Standard Python/pytest patterns
- Audit methodology: MEDIUM - Based on industry best practices, not Flet-specific
- Pitfalls: MEDIUM - Based on Flet docs and community patterns

**Research date:** 2026-01-18
**Valid until:** 60 days (stable patterns, mature tooling)
