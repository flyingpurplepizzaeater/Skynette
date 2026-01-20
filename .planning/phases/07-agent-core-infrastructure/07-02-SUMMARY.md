---
phase: 07
plan: 02
subsystem: agent-core
tags: [tool-registry, singleton, abstract-base-class, dependency-injection]

dependency-graph:
  requires:
    - 07-01 (ToolDefinition, ToolResult models)
  provides:
    - BaseTool abstract class for tool implementations
    - AgentContext for tool execution context
    - ToolRegistry singleton for tool management
    - MockTool for testing
    - Multi-provider format conversion (OpenAI, Anthropic)
  affects:
    - 07-03 (Agent Loop uses ToolRegistry)
    - 08-XX (Built-in tools extend BaseTool)

tech-stack:
  added: []
  patterns:
    - "ABC with @abstractmethod for tool interface"
    - "Singleton pattern with _instance class variable"
    - "Module-level factory function for singleton access"
    - "Pydantic BaseModel for execution context"

key-files:
  created:
    - src/agent/registry/__init__.py
    - src/agent/registry/base_tool.py
    - src/agent/registry/tool_registry.py
    - src/agent/registry/mock_tool.py
  modified:
    - src/agent/__init__.py

decisions:
  - id: 07-02-01
    choice: "Follow NodeRegistry pattern for ToolRegistry"
    reason: "Consistency with existing codebase, proven singleton pattern"
  - id: 07-02-02
    choice: "Separate AgentContext from AgentSession"
    reason: "AgentContext is lightweight tool-facing context; AgentSession is full session state"

metrics:
  duration: ~8 minutes
  completed: 2026-01-20
---

# Phase 7 Plan 2: Tool Registry Summary

BaseTool abstract class and ToolRegistry singleton for agent tool management

## What Was Built

### Base Tool (`src/agent/registry/base_tool.py`)

**AgentContext** - Lightweight execution context:
- Fields: session_id, variables, working_directory
- Passed to tools during execution for session awareness

**BaseTool** - Abstract base class for all tools:
- Class attributes: name, description, parameters_schema
- Abstract method: `execute(params, context) -> ToolResult`
- Concrete methods: `get_definition() -> ToolDefinition`, `validate_params(params) -> (bool, error)`

### Tool Registry (`src/agent/registry/tool_registry.py`)

**ToolRegistry** - Singleton tool manager:
- Methods: register(), unregister(), get_tool(), get_all_definitions()
- Format converters: get_openai_tools(), get_anthropic_tools()
- Property: tool_names
- Auto-loads built-in tools on init

**get_tool_registry()** - Module-level factory:
- Returns global singleton instance
- Follows existing pattern from other registries

### Mock Tool (`src/agent/registry/mock_tool.py`)

**MockTool** - Testing tool:
- Name: "mock_echo"
- Echoes message back with session_id
- Used for registry and agent loop testing

## Commits

| Hash | Description |
|------|-------------|
| f9807f6 | feat(07-01): create plan, step, and tool models (Task 1 - models existed) |
| 0f0f286 | feat(07-02): add BaseTool abstract class and AgentContext |
| 16e8aae | feat(07-02): add ToolRegistry singleton with mock tool |
| b789d26 | fix(07-02): remove invalid AgentEvent imports from agent module |

## Deviations from Plan

### Prior Work

**Task 1 already complete from 07-01**
- Tool models (ToolDefinition, ToolCall, ToolResult) were created in commit f9807f6
- Plan 07-02 Task 1 was redundant; models already existed
- Proceeded directly to Task 2

### Auto-fixed Issues

**1. [Rule 1 - Bug] Invalid AgentEvent imports**
- **Found during:** Task 3 commit
- **Issue:** External sync kept adding AgentEvent imports that don't exist
- **Fix:** Removed invalid imports from agent/__init__.py
- **Commit:** b789d26

## Key Patterns Established

1. **Abstract tool pattern**: `class BaseTool(ABC)` with `@abstractmethod execute()`
2. **Singleton registry**: `_instance` class variable, check in `__new__`
3. **Factory function**: `get_tool_registry()` for clean singleton access
4. **Multi-format support**: `to_openai_format()` and `to_anthropic_format()` on definitions

## Verification Results

All success criteria met:
- [x] ToolDefinition has to_openai_format() and to_anthropic_format() methods
- [x] ToolCall and ToolResult are Pydantic models with proper fields
- [x] BaseTool is abstract class with execute(), get_definition(), validate_params()
- [x] ToolRegistry is singleton following NodeRegistry pattern
- [x] MockTool is registered and can be invoked through registry
- [x] get_tool_registry() returns global singleton

```python
# All imports work
from src.agent import (
    ToolDefinition, ToolCall, ToolResult,
    BaseTool, ToolRegistry, get_tool_registry, AgentContext
)

# Registry works
registry = get_tool_registry()
tool = registry.get_tool('mock_echo')
result = await tool.execute({'message': 'test'}, AgentContext(session_id='s1'))
```

## Next Phase Readiness

Ready for 07-03 (Agent Loop):
- ToolRegistry provides tool lookup and format conversion
- BaseTool defines execution interface
- AgentContext ready for tool invocations
- MockTool available for loop testing

Ready for Phase 8 (Built-in Tools):
- BaseTool provides inheritance interface
- ToolRegistry.register() ready for new tools
- Parameter validation via validate_params()
