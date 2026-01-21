"""MCP Tool Adapter - wraps MCP tools as BaseTool instances."""

import logging
from typing import Optional

from src.agent.registry.base_tool import BaseTool, AgentContext
from src.agent.models.tool import ToolDefinition, ToolResult
from src.agent.mcp.models.trust import TrustLevel

logger = logging.getLogger(__name__)


class MCPToolAdapter(BaseTool):
    """Adapter that wraps an MCP tool as a BaseTool for ToolRegistry integration."""

    def __init__(
        self,
        mcp_tool: dict,  # From MCP list_tools response
        server_id: str,
        server_name: str,
        trust_level: TrustLevel,
    ):
        """
        Initialize adapter for an MCP tool.

        Args:
            mcp_tool: Tool dict from MCP list_tools (name, description, inputSchema)
            server_id: ID of the server providing this tool
            server_name: Human-readable server name for display
            trust_level: Trust level of the source server
        """
        self._mcp_tool = mcp_tool
        self._server_id = server_id
        self._server_name = server_name
        self._trust_level = trust_level

        # BaseTool class attributes - namespaced to prevent conflicts
        self.name = f"mcp_{server_id[:8]}_{mcp_tool['name']}"
        self.description = self._build_description(mcp_tool)
        self.parameters_schema = mcp_tool.get('inputSchema', {
            "type": "object",
            "properties": {}
        })

        # MCP-specific metadata for UI
        self.source_server_id = server_id
        self.source_server_name = server_name
        self.original_name = mcp_tool['name']
        self.original_description = mcp_tool.get('description', '')

    def _build_description(self, mcp_tool: dict) -> str:
        """Build description with source attribution."""
        desc = mcp_tool.get('description', 'No description provided')
        return f"[{self._server_name}] {desc}"

    async def execute(self, params: dict, context: AgentContext) -> ToolResult:
        """Execute the MCP tool via MCPClientManager."""
        from src.agent.mcp.client.manager import get_mcp_client_manager

        manager = get_mcp_client_manager()

        try:
            result = await manager.call_tool(
                self._server_id,
                self.original_name,  # Use original name for MCP call
                params,
            )

            if result.get('success', True):
                # Extract text content for compatibility
                content = result.get('content', [])
                data = content[0].get('text', '') if content else result.get('structured')
                return ToolResult.success_result(
                    tool_call_id=context.session_id,
                    data=data,
                )
            else:
                error_content = result.get('content', [])
                error_msg = error_content[0].get('text', 'Unknown error') if error_content else 'Tool execution failed'
                return ToolResult.failure_result(
                    tool_call_id=context.session_id,
                    error=error_msg,
                )

        except Exception as e:
            logger.error(f"MCP tool execution failed: {e}")
            return ToolResult.failure_result(
                tool_call_id=context.session_id,
                error=str(e),
            )

    def get_definition(self) -> ToolDefinition:
        """Get tool definition with MCP metadata."""
        # Determine approval requirement based on trust level
        requires_approval = self._trust_level == "user_added"

        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters_schema,
            category=f"mcp:{self._server_name.lower().replace(' ', '_')}",
            is_destructive=False,  # Conservative default, can be enhanced later
            requires_approval=requires_approval,
        )

    def get_mcp_metadata(self) -> dict:
        """Get MCP-specific metadata for UI display."""
        return {
            "server_id": self._server_id,
            "server_name": self._server_name,
            "original_name": self.original_name,
            "original_description": self.original_description,
            "trust_level": self._trust_level,
        }
