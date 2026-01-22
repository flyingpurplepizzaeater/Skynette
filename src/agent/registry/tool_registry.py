"""
Tool Registry

Singleton registry for agent tools, including MCP tool integration.
"""

import logging
from typing import Optional, Type, TYPE_CHECKING

from src.agent.models.tool import ToolDefinition
from src.agent.registry.base_tool import BaseTool

if TYPE_CHECKING:
    from src.agent.mcp.adapter.tool_adapter import MCPToolAdapter
    from src.agent.mcp.models.trust import TrustLevel

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Singleton registry for agent tools."""

    _instance: Optional["ToolRegistry"] = None
    _tools: dict[str, Type[BaseTool]]
    _mcp_tools: dict[str, BaseTool]

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
        self._mcp_tools = {}
        self._load_builtin_tools()

    def _load_builtin_tools(self) -> None:
        """Load built-in tools."""
        # Testing tool
        from src.agent.registry.mock_tool import MockTool
        self.register(MockTool)

        # Built-in tools
        from src.agent.tools import (
            BrowserTool,
            CodeExecutionTool,
            FileDeleteTool,
            FileListTool,
            FileReadTool,
            FileWriteTool,
            GitHubTool,
            WebSearchTool,
        )
        self.register(WebSearchTool)
        self.register(CodeExecutionTool)
        self.register(FileReadTool)
        self.register(FileWriteTool)
        self.register(FileDeleteTool)
        self.register(FileListTool)
        self.register(BrowserTool)
        self.register(GitHubTool)

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
        """Get tool instance by name (includes MCP tools)."""
        # Check MCP tools first (instances, not classes)
        if name in self._mcp_tools:
            return self._mcp_tools[name]
        # Then check built-in tools (classes)
        tool_class = self._tools.get(name)
        return tool_class() if tool_class else None

    def get_all_definitions(self) -> list[ToolDefinition]:
        """Get all tool definitions for LLM context (includes MCP tools)."""
        definitions = [cls().get_definition() for cls in self._tools.values()]
        definitions.extend([tool.get_definition() for tool in self._mcp_tools.values()])
        return definitions

    def get_openai_tools(self) -> list[dict]:
        """Get all tools in OpenAI format."""
        return [d.to_openai_format() for d in self.get_all_definitions()]

    def get_anthropic_tools(self) -> list[dict]:
        """Get all tools in Anthropic format."""
        return [d.to_anthropic_format() for d in self.get_all_definitions()]

    @property
    def tool_names(self) -> list[str]:
        """Get all registered tool names (includes MCP tools)."""
        return list(self._tools.keys()) + list(self._mcp_tools.keys())

    # MCP tool registration methods

    def register_mcp_tool(self, tool: "MCPToolAdapter") -> None:
        """Register an MCP tool adapter instance."""
        if tool.name in self._tools or tool.name in self._mcp_tools:
            logger.warning(f"Tool {tool.name} already registered, skipping")
            return
        self._mcp_tools[tool.name] = tool
        logger.debug(f"Registered MCP tool: {tool.name}")

    def unregister_mcp_tool(self, tool_name: str) -> None:
        """Unregister an MCP tool."""
        if tool_name in self._mcp_tools:
            del self._mcp_tools[tool_name]
            logger.debug(f"Unregistered MCP tool: {tool_name}")

    def register_mcp_tools_from_server(
        self,
        server_id: str,
        server_name: str,
        trust_level: "TrustLevel",
        tools: list[dict],
    ) -> int:
        """
        Register all tools from an MCP server.

        Returns number of tools registered.
        """
        from src.agent.mcp.adapter.tool_adapter import MCPToolAdapter

        count = 0
        for mcp_tool in tools:
            adapter = MCPToolAdapter(
                mcp_tool=mcp_tool,
                server_id=server_id,
                server_name=server_name,
                trust_level=trust_level,
            )
            self.register_mcp_tool(adapter)
            count += 1

        logger.info(f"Registered {count} MCP tools from {server_name}")
        return count

    def unregister_mcp_tools_from_server(self, server_id: str) -> int:
        """
        Unregister all tools from a specific MCP server.

        Returns number of tools unregistered.
        """
        # Find tools from this server (by checking name prefix)
        prefix = f"mcp_{server_id[:8]}_"
        to_remove = [name for name in self._mcp_tools.keys() if name.startswith(prefix)]

        for name in to_remove:
            del self._mcp_tools[name]

        logger.info(f"Unregistered {len(to_remove)} MCP tools from server {server_id}")
        return len(to_remove)

    def get_mcp_tools(self) -> list["MCPToolAdapter"]:
        """Get all registered MCP tools."""
        return list(self._mcp_tools.values())


# Module-level singleton accessor
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
