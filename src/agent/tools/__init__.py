"""
Skynette Agent Built-in Tools

This module provides the built-in tools available to the agent:
- WebSearchTool: Search the web via DuckDuckGo
- FileReadTool, FileWriteTool, FileDeleteTool, FileListTool: Filesystem operations
- CodeExecutionTool: Execute code in Python, Node.js, shell
- BrowserTool: Web automation with Playwright
- GitHubTool: GitHub API integration
- RAGQueryTool: Query Skynette's RAG knowledge base
"""

from src.agent.tools.base import (
    FileSystemValidator,
    backup_before_modify,
    cleanup_old_backups,
)
from src.agent.tools.browser import BrowserTool
from src.agent.tools.code_execution import CodeExecutionTool
from src.agent.tools.filesystem import (
    FileDeleteTool,
    FileListTool,
    FileReadTool,
    FileWriteTool,
)
from src.agent.tools.github import GitHubTool
from src.agent.tools.skynette_tools import RAGQueryTool
from src.agent.tools.web_search import WebSearchTool

__all__ = [
    # Base utilities
    "FileSystemValidator",
    "backup_before_modify",
    "cleanup_old_backups",
    # Web tools
    "WebSearchTool",
    "BrowserTool",
    # Filesystem tools
    "FileReadTool",
    "FileWriteTool",
    "FileDeleteTool",
    "FileListTool",
    # Code tools
    "CodeExecutionTool",
    # Integration tools
    "GitHubTool",
    "RAGQueryTool",
]
