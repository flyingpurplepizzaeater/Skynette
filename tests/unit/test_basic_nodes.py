"""
Unit Tests for Basic Workflow Nodes

Tests for Phase 2 basic nodes: Manual Trigger, HTTP Request, If/Else, Set Variable, Log/Debug.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock, Mock

from src.core.nodes.triggers.manual import ManualTriggerNode
from src.core.nodes.http.request import HTTPRequestNode
from src.core.nodes.flow.if_else import IfElseNode
from src.core.nodes.flow.set_variable import SetVariableNode
from src.core.nodes.flow.log_debug import LogDebugNode


@pytest.mark.asyncio
class TestManualTriggerNode:
    """Tests for Manual Trigger Node."""

    async def test_manual_trigger_basic(self):
        """Test basic manual trigger execution."""
        node = ManualTriggerNode()
        context = {}

        result = await node.execute({}, context)

        assert "triggered_at" in result
        assert "data" in result
        assert "trigger_type" in result
        assert result["trigger_type"] == "manual"

    async def test_manual_trigger_with_test_data(self):
        """Test manual trigger with test data."""
        node = ManualTriggerNode()
        config = {
            "test_data": {"user_id": 123, "action": "test"}
        }
        context = {}

        result = await node.execute(config, context)

        assert result["data"]["user_id"] == 123
        assert result["data"]["action"] == "test"

    async def test_manual_trigger_timestamp(self):
        """Test that trigger includes valid timestamp."""
        node = ManualTriggerNode()
        result = await node.execute({}, {})

        # Should be valid ISO format timestamp
        triggered_at = result["triggered_at"]
        parsed = datetime.fromisoformat(triggered_at)
        assert isinstance(parsed, datetime)

    def test_manual_trigger_definition(self):
        """Test node definition."""
        definition = ManualTriggerNode.get_definition()

        assert definition.type == "manual_trigger"
        assert definition.name == "Manual Trigger"
        assert definition.is_trigger is True
        assert definition.category == "trigger"


@pytest.mark.asyncio
class TestHTTPRequestNode:
    """Tests for HTTP Request Node."""

    @patch("httpx.AsyncClient")
    async def test_http_get_request(self, mock_client_class):
        """Test basic GET request."""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json = Mock(return_value={"result": "success"})
        mock_response.headers = {"content-type": "application/json"}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        node = HTTPRequestNode()
        config = {
            "method": "GET",
            "url": "https://api.example.com/data",
        }

        result = await node.execute(config, {})

        assert result["status"] == 200
        assert result["ok"] is True
        assert result["body"]["result"] == "success"
        assert "content-type" in result["headers"]

    @patch("httpx.AsyncClient")
    async def test_http_post_request_with_json(self, mock_client_class):
        """Test POST request with JSON body."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.is_success = True
        mock_response.json = Mock(return_value={"id": 123, "created": True})
        mock_response.headers = {}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        node = HTTPRequestNode()
        config = {
            "method": "POST",
            "url": "https://api.example.com/create",
            "body": {"name": "Test", "value": 42},
            "body_type": "json",
        }

        result = await node.execute(config, {})

        assert result["status"] == 201
        assert result["body"]["id"] == 123
        assert result["body"]["created"] is True

    @patch("httpx.AsyncClient")
    async def test_http_request_with_headers(self, mock_client_class):
        """Test request with custom headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json = Mock(return_value={})
        mock_response.headers = {}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        node = HTTPRequestNode()
        config = {
            "method": "GET",
            "url": "https://api.example.com/secure",
            "headers": {
                "Authorization": "Bearer token123",
                "X-Custom-Header": "value",
            },
        }

        result = await node.execute(config, {})

        # Verify headers were passed to request
        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["headers"]["Authorization"] == "Bearer token123"

    @patch("httpx.AsyncClient")
    async def test_http_request_error_handling(self, mock_client_class):
        """Test HTTP error response."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.is_success = False
        mock_response.json = Mock(side_effect=Exception("Not JSON"))
        mock_response.text = "Not Found"
        mock_response.headers = {}

        mock_client = AsyncMock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        node = HTTPRequestNode()
        config = {
            "method": "GET",
            "url": "https://api.example.com/missing",
        }

        result = await node.execute(config, {})

        assert result["status"] == 404
        assert result["ok"] is False
        assert result["body"] == "Not Found"  # Falls back to text

    async def test_http_request_missing_url(self):
        """Test error when URL is missing."""
        node = HTTPRequestNode()
        config = {"method": "GET"}

        with pytest.raises(ValueError, match="URL is required"):
            await node.execute(config, {})


@pytest.mark.asyncio
class TestIfElseNode:
    """Tests for If/Else Node."""

    async def test_if_else_boolean_true(self):
        """Test boolean condition that's true."""
        node = IfElseNode()
        config = {
            "condition_type": "boolean",
            "boolean_value": True,
        }

        result = await node.execute(config, {})

        assert result["result"] is True
        assert result["branch"] == "true"

    async def test_if_else_boolean_false(self):
        """Test boolean condition that's false."""
        node = IfElseNode()
        config = {
            "condition_type": "boolean",
            "boolean_value": False,
        }

        result = await node.execute(config, {})

        assert result["result"] is False
        assert result["branch"] == "false"

    async def test_if_else_comparison_equals(self):
        """Test equals comparison."""
        node = IfElseNode()
        config = {
            "condition_type": "comparison",
            "left_value": 10,
            "operator": "equals",
            "right_value": 10,
        }

        result = await node.execute(config, {})

        assert result["result"] is True

    async def test_if_else_comparison_not_equals(self):
        """Test not equals comparison."""
        node = IfElseNode()
        config = {
            "condition_type": "comparison",
            "left_value": "hello",
            "operator": "not_equals",
            "right_value": "world",
        }

        result = await node.execute(config, {})

        assert result["result"] is True

    async def test_if_else_comparison_greater_than(self):
        """Test greater than comparison."""
        node = IfElseNode()
        config = {
            "condition_type": "comparison",
            "left_value": 100,
            "operator": "greater",
            "right_value": 50,
        }

        result = await node.execute(config, {})

        assert result["result"] is True

    async def test_if_else_comparison_contains(self):
        """Test contains comparison."""
        node = IfElseNode()
        config = {
            "condition_type": "comparison",
            "left_value": "hello world",
            "operator": "contains",
            "right_value": "world",
        }

        result = await node.execute(config, {})

        assert result["result"] is True

    async def test_if_else_expression_simple(self):
        """Test simple expression evaluation."""
        node = IfElseNode()
        config = {
            "condition_type": "expression",
            "expression": "10 == 10",
        }

        result = await node.execute(config, {})

        assert result["result"] is True

    async def test_if_else_passthrough_data(self):
        """Test that previous data passes through."""
        node = IfElseNode()
        context = {"$prev": {"value": 42, "status": "ok"}}
        config = {
            "condition_type": "boolean",
            "boolean_value": True,
        }

        result = await node.execute(config, context)

        assert result["data"]["value"] == 42
        assert result["data"]["status"] == "ok"


@pytest.mark.asyncio
class TestSetVariableNode:
    """Tests for Set Variable Node."""

    async def test_set_variable_basic(self):
        """Test basic variable setting."""
        node = SetVariableNode()
        config = {
            "variable_name": "my_var",
            "value": "test_value",
        }

        result = await node.execute(config, {})

        assert result["name"] == "my_var"
        assert result["value"] == "test_value"

    async def test_set_variable_type_conversion_string(self):
        """Test string type conversion."""
        node = SetVariableNode()
        config = {
            "variable_name": "str_var",
            "value": 123,
            "value_type": "string",
        }

        result = await node.execute(config, {})

        assert result["value"] == "123"
        assert isinstance(result["value"], str)

    async def test_set_variable_type_conversion_number(self):
        """Test number type conversion."""
        node = SetVariableNode()
        config = {
            "variable_name": "num_var",
            "value": "42",
            "value_type": "number",
        }

        result = await node.execute(config, {})

        assert result["value"] == 42
        assert isinstance(result["value"], int)

    async def test_set_variable_type_conversion_boolean(self):
        """Test boolean type conversion."""
        node = SetVariableNode()
        config = {
            "variable_name": "bool_var",
            "value": "true",
            "value_type": "boolean",
        }

        result = await node.execute(config, {})

        assert result["value"] is True

    async def test_set_variable_missing_name_error(self):
        """Test error when variable name is missing."""
        node = SetVariableNode()
        config = {"value": "test"}

        with pytest.raises(ValueError, match="Variable name is required"):
            await node.execute(config, {})

    async def test_set_variable_passthrough(self):
        """Test that previous data passes through."""
        node = SetVariableNode()
        context = {"$prev": {"original": "data"}}
        config = {
            "variable_name": "new_var",
            "value": "new_value",
        }

        result = await node.execute(config, context)

        assert result["previous"]["original"] == "data"


@pytest.mark.asyncio
class TestLogDebugNode:
    """Tests for Log/Debug Node."""

    async def test_log_debug_basic(self):
        """Test basic logging."""
        node = LogDebugNode()
        config = {
            "message": "Test log message",
            "data": {"key": "value"},
        }

        result = await node.execute(config, {})

        assert result["logged"] is True
        assert result["message"] == "Test log message"
        assert result["data"]["key"] == "value"

    async def test_log_debug_with_previous_data(self):
        """Test logging with previous node data."""
        node = LogDebugNode()
        context = {"$prev": {"status": 200, "result": "success"}}
        config = {
            "message": "API Response",
            "data": "{{$prev}}",  # Will be resolved by executor
        }

        result = await node.execute(config, context)

        assert result["logged"] is True

    async def test_log_debug_different_levels(self):
        """Test different log levels."""
        node = LogDebugNode()

        for level in ["debug", "info", "warning", "error"]:
            config = {
                "message": f"Test {level}",
                "log_level": level,
            }

            result = await node.execute(config, {})
            assert result["logged"] is True

    async def test_log_debug_timestamp(self):
        """Test logging with timestamp."""
        node = LogDebugNode()
        config = {
            "message": "Timestamped",
            "include_timestamp": True,
        }

        result = await node.execute(config, {})

        assert result["logged"] is True

    async def test_log_debug_pretty_print(self):
        """Test pretty printing JSON data."""
        node = LogDebugNode()
        config = {
            "data": {"nested": {"object": {"with": "data"}}},
            "pretty_print": True,
        }

        result = await node.execute(config, {})

        assert result["logged"] is True
        assert result["data"]["nested"]["object"]["with"] == "data"
