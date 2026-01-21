"""
MCP Connection Wrapper

Wraps an MCP ClientSession with connection metadata and helper methods.
"""

from datetime import datetime, UTC
from typing import Optional

from mcp import ClientSession

from src.agent.mcp.models.server import MCPServerConfig, MCPServerStatus


class MCPConnection:
    """Wrapper around MCP ClientSession with connection metadata.

    Provides:
    - Tool listing with caching
    - Tool invocation with result parsing
    - Connection status reporting
    - Activity tracking
    """

    def __init__(
        self,
        server_id: str,
        session: ClientSession,
        config: MCPServerConfig,
    ):
        """Initialize connection wrapper.

        Args:
            server_id: Unique identifier for the server
            session: Active MCP ClientSession
            config: Server configuration
        """
        self.server_id = server_id
        self.session = session
        self.config = config
        self.connected_at: datetime = datetime.now(UTC)
        self.last_activity: datetime = self.connected_at
        self._tools_cache: Optional[list[dict]] = None

    async def list_tools(self) -> list[dict]:
        """List available tools from this server.

        Returns cached tools to avoid repeated calls. Call invalidate_cache()
        to force a refresh.

        Returns:
            List of tool definitions with name, description, and inputSchema
        """
        if self._tools_cache is None:
            response = await self.session.list_tools()
            self._tools_cache = [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema,
                }
                for tool in response.tools
            ]
        self.last_activity = datetime.now(UTC)
        return self._tools_cache

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on this server.

        Args:
            tool_name: Name of the tool to invoke
            arguments: Tool arguments as a dictionary

        Returns:
            Result dictionary with:
            - success: bool indicating if tool executed without error
            - content: list of content items (text, image, etc.)
            - structured: structured content if provided by server
        """
        result = await self.session.call_tool(tool_name, arguments)
        self.last_activity = datetime.now(UTC)

        # Parse result content
        is_error = getattr(result, "isError", False)
        content = []
        for item in result.content:
            if item.type == "text":
                content.append({"type": "text", "text": item.text})
            elif item.type == "image":
                content.append({
                    "type": "image",
                    "data": item.data,
                    "mimeType": item.mimeType,
                })

        return {
            "success": not is_error,
            "content": content,
            "structured": getattr(result, "structuredContent", None),
        }

    def invalidate_cache(self) -> None:
        """Invalidate tools cache.

        Call after server update or when tools list may have changed.
        """
        self._tools_cache = None

    def get_status(self) -> MCPServerStatus:
        """Get current connection status.

        Returns:
            MCPServerStatus with connection state and metadata
        """
        return MCPServerStatus(
            server_id=self.server_id,
            connected=True,
            connecting=False,
            tools_count=len(self._tools_cache) if self._tools_cache else 0,
            last_active=self.last_activity,
        )
