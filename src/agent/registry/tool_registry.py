"""
Tool Registry

Singleton registry for agent tools.
"""

import logging
from typing import Optional, Type

from src.agent.models.tool import ToolDefinition
from src.agent.registry.base_tool import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Singleton registry for agent tools."""

    _instance: Optional["ToolRegistry"] = None
    _tools: dict[str, Type[BaseTool]]

    def __new__(cls) -> "ToolRegistry":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._tools = {}
        self._load_builtin_tools()

    def _load_builtin_tools(self) -> None:
        """Load built-in tools. Extended in later phases."""
        # Register mock tool for testing
        from src.agent.registry.mock_tool import MockTool
        self.register(MockTool)
        logger.info(f"Loaded {len(self._tools)} built-in tools")

    def register(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool type."""
        if not issubclass(tool_class, BaseTool):
            raise TypeError(f"{tool_class} must be a subclass of BaseTool")
        self._tools[tool_class.name] = tool_class
        logger.debug(f"Registered tool: {tool_class.name}")

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool."""
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool instance by name."""
        tool_class = self._tools.get(name)
        return tool_class() if tool_class else None

    def get_all_definitions(self) -> list[ToolDefinition]:
        """Get all tool definitions for LLM context."""
        return [cls().get_definition() for cls in self._tools.values()]

    def get_openai_tools(self) -> list[dict]:
        """Get all tools in OpenAI format."""
        return [d.to_openai_format() for d in self.get_all_definitions()]

    def get_anthropic_tools(self) -> list[dict]:
        """Get all tools in Anthropic format."""
        return [d.to_anthropic_format() for d in self.get_all_definitions()]

    @property
    def tool_names(self) -> list[str]:
        """Get all registered tool names."""
        return list(self._tools.keys())


# Module-level singleton accessor
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
