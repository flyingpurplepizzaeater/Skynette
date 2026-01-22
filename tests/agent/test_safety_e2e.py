"""
E2E Tests for Safety and Approval Systems

Tests QUAL-04: E2E tests for critical agent workflows
"""

import asyncio
import gc
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent import (
    ActionClassifier,
    ActionClassification,
    RiskLevel,
    ApprovalManager,
    ApprovalRequest,
    ApprovalResult,
    KillSwitch,
    get_kill_switch,
    AuditStore,
    AuditEntry,
)
from src.agent.loop.executor import AgentExecutor
from src.agent.models.state import AgentSession, AgentState


class TestClassificationE2E:
    """E2E tests for action classification."""

    def test_builtin_tools_classified_correctly(self):
        """Verify all built-in tools have correct risk classification."""
        classifier = ActionClassifier()

        # Safe tools
        assert classifier.classify("file_read", {"path": "/tmp/test.txt"}).risk_level == "safe"
        assert classifier.classify("file_list", {"path": "/tmp"}).risk_level == "safe"
        assert classifier.classify("web_search", {"query": "python"}).risk_level == "safe"
        assert classifier.classify("rag_query", {"query": "test"}).risk_level == "safe"
        assert classifier.classify("mock_echo", {"message": "hi"}).risk_level == "safe"

        # Moderate tools
        assert classifier.classify("browser", {"url": "https://example.com"}).risk_level == "moderate"

        # Destructive tools
        assert classifier.classify("file_write", {"path": "/tmp/test.txt"}).risk_level == "destructive"
        assert classifier.classify("code_execute", {"code": "print('hi')"}).risk_level == "destructive"
        assert classifier.classify("github", {"operation": "create_repo"}).risk_level == "destructive"

        # Critical tools
        assert classifier.classify("file_delete", {"path": "/tmp/test.txt"}).risk_level == "critical"

    def test_unknown_tool_defaults_moderate(self):
        """Unknown/MCP tools should default to moderate."""
        classifier = ActionClassifier()
        result = classifier.classify("custom_mcp_tool", {"param": "value"})

        assert result.risk_level == "moderate"
        assert result.requires_approval == False  # Moderate doesn't require by default

    def test_classification_includes_context_in_reason(self):
        """Classification reason should include parameter context."""
        classifier = ActionClassifier()

        result = classifier.classify("file_delete", {"path": "/important/data.txt"})
        assert "/important/data.txt" in result.reason

        result = classifier.classify("file_write", {"path": "/src/app.py"})
        assert "/src/app.py" in result.reason

    def test_approval_required_by_risk_level(self):
        """Destructive and critical require approval, safe and moderate don't."""
        classifier = ActionClassifier()

        assert classifier.classify("file_read", {}).requires_approval == False
        assert classifier.classify("browser", {}).requires_approval == False
        assert classifier.classify("file_write", {}).requires_approval == True
        assert classifier.classify("file_delete", {}).requires_approval == True
