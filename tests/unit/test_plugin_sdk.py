"""
Tests for Plugin SDK.

Tests decorators, field builders, context helpers, and template generation.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestNodeDecorator:
    """Tests for @node decorator."""

    def test_node_decorator_sets_attributes(self):
        """Test that @node decorator sets class attributes."""
        from src.plugins.sdk import node, BaseNode

        @node(
            type="test.custom-node",
            name="Custom Node",
            category="utility",
            description="A custom node",
            icon="cog",
            color="#FF0000",
        )
        class CustomNode(BaseNode):
            pass

        assert CustomNode.type == "test.custom-node"
        assert CustomNode.name == "Custom Node"
        assert CustomNode.category == "utility"
        assert CustomNode.description == "A custom node"
        assert CustomNode.icon == "cog"
        assert CustomNode.color == "#FF0000"
        assert CustomNode.is_trigger is False

    def test_node_decorator_default_values(self):
        """Test that @node decorator uses defaults."""
        from src.plugins.sdk import node, BaseNode

        @node(
            type="test.minimal",
            name="Minimal Node",
        )
        class MinimalNode(BaseNode):
            pass

        assert MinimalNode.category == "utility"
        assert MinimalNode.description == "Minimal Node node"
        assert MinimalNode.icon == "extension"
        assert MinimalNode.color == "#6B7280"
        assert MinimalNode.requires_credentials == []

    def test_node_decorator_with_inputs(self):
        """Test @node decorator wraps inputs method."""
        from src.plugins.sdk import node, BaseNode, field

        @node(type="test.with-inputs", name="With Inputs")
        class WithInputsNode(BaseNode):
            @staticmethod
            def inputs():
                return [
                    field.string("name", "Name"),
                    field.number("count", "Count"),
                ]

        # Should have get_inputs classmethod
        assert hasattr(WithInputsNode, 'get_inputs')
        inputs = WithInputsNode.get_inputs()
        assert len(inputs) == 2

    def test_node_decorator_with_credentials(self):
        """Test @node decorator with required credentials."""
        from src.plugins.sdk import node, BaseNode

        @node(
            type="test.with-creds",
            name="With Creds",
            requires_credentials=["openai", "slack"],
        )
        class WithCredsNode(BaseNode):
            pass

        assert WithCredsNode.requires_credentials == ["openai", "slack"]


class TestTriggerDecorator:
    """Tests for @trigger decorator."""

    def test_trigger_decorator_sets_attributes(self):
        """Test that @trigger decorator sets class attributes."""
        from src.plugins.sdk import trigger, TriggerNode

        @trigger(
            type="test.webhook",
            name="Webhook Trigger",
            description="Receives webhooks",
            icon="bolt",
            color="#F59E0B",
        )
        class WebhookTrigger(TriggerNode):
            pass

        assert WebhookTrigger.type == "test.webhook"
        assert WebhookTrigger.name == "Webhook Trigger"
        assert WebhookTrigger.category == "trigger"
        assert WebhookTrigger.is_trigger is True
        assert WebhookTrigger.icon == "bolt"

    def test_trigger_decorator_default_values(self):
        """Test @trigger decorator defaults."""
        from src.plugins.sdk import trigger, TriggerNode

        @trigger(type="test.simple", name="Simple")
        class SimpleTrigger(TriggerNode):
            pass

        assert SimpleTrigger.description == "Simple trigger"
        assert SimpleTrigger.color == "#F59E0B"


class TestLifecycleDecorators:
    """Tests for @on_load and @on_unload decorators."""

    def test_on_load_decorator(self):
        """Test @on_load marks function."""
        from src.plugins.sdk import on_load

        @on_load
        def setup():
            pass

        assert hasattr(setup, '_skynette_on_load')
        assert setup._skynette_on_load is True

    def test_on_unload_decorator(self):
        """Test @on_unload marks function."""
        from src.plugins.sdk import on_unload

        @on_unload
        def cleanup():
            pass

        assert hasattr(cleanup, '_skynette_on_unload')
        assert cleanup._skynette_on_unload is True


class TestFieldBuilder:
    """Tests for FieldBuilder helpers."""

    def test_field_string(self):
        """Test creating string field."""
        from src.plugins.sdk import field
        from src.core.nodes.base import FieldType

        f = field.string(
            "username",
            "Username",
            description="Enter username",
            required=True,
            default="guest",
            placeholder="e.g., john_doe",
        )

        assert f.name == "username"
        assert f.label == "Username"
        assert f.type == FieldType.STRING
        assert f.required is True
        assert f.default == "guest"
        assert f.placeholder == "e.g., john_doe"

    def test_field_text(self):
        """Test creating text (multiline) field."""
        from src.plugins.sdk import field
        from src.core.nodes.base import FieldType

        f = field.text("content", "Content", required=True)

        assert f.name == "content"
        assert f.type == FieldType.TEXT

    def test_field_number(self):
        """Test creating number field."""
        from src.plugins.sdk import field
        from src.core.nodes.base import FieldType

        f = field.number(
            "count",
            "Count",
            default=5,
            min_value=1,
            max_value=100,
        )

        assert f.name == "count"
        assert f.type == FieldType.NUMBER
        assert f.default == 5
        assert f.min_value == 1
        assert f.max_value == 100

    def test_field_boolean(self):
        """Test creating boolean field."""
        from src.plugins.sdk import field
        from src.core.nodes.base import FieldType

        f = field.boolean("enabled", "Enabled", default=True)

        assert f.name == "enabled"
        assert f.type == FieldType.BOOLEAN
        assert f.default is True
        assert f.required is False  # Booleans always have a value

    def test_field_select(self):
        """Test creating select field."""
        from src.plugins.sdk import field
        from src.core.nodes.base import FieldType

        options = [("opt1", "Option 1"), ("opt2", "Option 2")]
        f = field.select("choice", "Choice", options=options)

        assert f.name == "choice"
        assert f.type == FieldType.SELECT
        assert len(f.options) == 2
        assert f.options[0]["value"] == "opt1"
        assert f.options[0]["label"] == "Option 1"
        assert f.default == "opt1"  # Defaults to first option

    def test_field_select_custom_default(self):
        """Test select field with custom default."""
        from src.plugins.sdk import field

        options = [("a", "A"), ("b", "B"), ("c", "C")]
        f = field.select("choice", "Choice", options=options, default="b")

        assert f.default == "b"

    def test_field_multi_select(self):
        """Test creating multi-select field."""
        from src.plugins.sdk import field
        from src.core.nodes.base import FieldType

        options = [("tag1", "Tag 1"), ("tag2", "Tag 2")]
        f = field.multi_select("tags", "Tags", options=options, default=["tag1"])

        assert f.type == FieldType.MULTI_SELECT
        assert f.default == ["tag1"]

    def test_field_json(self):
        """Test creating JSON field."""
        from src.plugins.sdk import field
        from src.core.nodes.base import FieldType

        f = field.json("config", "Configuration", default={"key": "value"})

        assert f.type == FieldType.JSON
        assert f.default == {"key": "value"}

    def test_field_expression(self):
        """Test creating expression field."""
        from src.plugins.sdk import field
        from src.core.nodes.base import FieldType

        f = field.expression(
            "data",
            "Data",
            placeholder="{{$prev.output}}",
        )

        assert f.type == FieldType.EXPRESSION
        assert f.placeholder == "{{$prev.output}}"

    def test_field_file(self):
        """Test creating file field."""
        from src.plugins.sdk import field
        from src.core.nodes.base import FieldType

        f = field.file("path", "File Path", required=True)

        assert f.type == FieldType.FILE
        assert f.required is True

    def test_field_secret(self):
        """Test creating secret field."""
        from src.plugins.sdk import field
        from src.core.nodes.base import FieldType

        f = field.secret("api_key", "API Key", placeholder="sk-...")

        assert f.type == FieldType.SECRET
        assert f.placeholder == "sk-..."


class TestOutputBuilder:
    """Tests for OutputBuilder helpers."""

    def test_output_string(self):
        """Test creating string output."""
        from src.plugins.sdk import output

        o = output.string("result", "The result")

        assert o.name == "result"
        assert o.type == "string"
        assert o.description == "The result"

    def test_output_number(self):
        """Test creating number output."""
        from src.plugins.sdk import output

        o = output.number("count")

        assert o.name == "count"
        assert o.type == "number"

    def test_output_boolean(self):
        """Test creating boolean output."""
        from src.plugins.sdk import output

        o = output.boolean("success")

        assert o.type == "boolean"

    def test_output_object(self):
        """Test creating object output."""
        from src.plugins.sdk import output

        o = output.object("data", "Output data")

        assert o.type == "object"

    def test_output_array(self):
        """Test creating array output."""
        from src.plugins.sdk import output

        o = output.array("items")

        assert o.type == "array"


class TestPluginContext:
    """Tests for PluginContext helper."""

    def test_trigger_data(self):
        """Test accessing trigger data."""
        from src.plugins.sdk import PluginContext

        context = PluginContext({
            "$trigger": {"event": "push", "repo": "test/repo"},
        })

        assert context.trigger_data["event"] == "push"
        assert context.trigger_data["repo"] == "test/repo"

    def test_trigger_data_empty(self):
        """Test trigger data when not present."""
        from src.plugins.sdk import PluginContext

        context = PluginContext({})

        assert context.trigger_data == {}

    def test_variables(self):
        """Test accessing workflow variables."""
        from src.plugins.sdk import PluginContext

        context = PluginContext({
            "$vars": {"api_url": "https://api.example.com"},
        })

        assert context.variables["api_url"] == "https://api.example.com"

    def test_previous_output(self):
        """Test accessing previous node output."""
        from src.plugins.sdk import PluginContext

        context = PluginContext({
            "$prev": {"data": [1, 2, 3], "count": 3},
        })

        assert context.previous_output["data"] == [1, 2, 3]

    def test_get_node_output(self):
        """Test getting specific node output."""
        from src.plugins.sdk import PluginContext

        context = PluginContext({
            "$nodes": {
                "node-1": {"result": "success"},
                "node-2": {"items": [1, 2]},
            },
        })

        assert context.get_node_output("node-1")["result"] == "success"
        assert context.get_node_output("node-2")["items"] == [1, 2]
        assert context.get_node_output("nonexistent") is None

    def test_get_variable(self):
        """Test getting variable with default."""
        from src.plugins.sdk import PluginContext

        context = PluginContext({
            "$vars": {"existing": "value"},
        })

        assert context.get_variable("existing") == "value"
        assert context.get_variable("missing") is None
        assert context.get_variable("missing", "default") == "default"

    def test_get_arbitrary(self):
        """Test getting arbitrary context values."""
        from src.plugins.sdk import PluginContext

        context = PluginContext({
            "custom_key": "custom_value",
        })

        assert context.get("custom_key") == "custom_value"
        assert context.get("missing", "fallback") == "fallback"


class TestCredentialHelpers:
    """Tests for credential helper functions."""

    def test_get_credential_success(self):
        """Test getting credential successfully."""
        from src.plugins.sdk import get_credential

        with patch("src.data.credentials.get_api_key", return_value="sk-test-key"):
            result = get_credential("openai", "api_key")

        assert result == "sk-test-key"

    def test_get_credential_not_found(self):
        """Test getting credential that doesn't exist."""
        from src.plugins.sdk import get_credential

        with patch("src.data.credentials.get_api_key", return_value=None):
            result = get_credential("nonexistent", "api_key")

        assert result is None

    def test_get_credential_calls_with_params(self):
        """Test get_credential passes parameters correctly."""
        from src.plugins.sdk import get_credential

        with patch("src.data.credentials.get_api_key") as mock_get:
            mock_get.return_value = "test-value"
            get_credential("my_service", "custom_field")

        mock_get.assert_called_once_with("my_service", "custom_field")

    def test_require_credential_success(self):
        """Test requiring credential that exists."""
        from src.plugins.sdk import require_credential

        with patch("src.plugins.sdk.get_credential", return_value="secret-value"):
            result = require_credential("service", "key")

        assert result == "secret-value"

    def test_require_credential_missing(self):
        """Test requiring credential that doesn't exist."""
        from src.plugins.sdk import require_credential

        with patch("src.plugins.sdk.get_credential", return_value=None):
            with pytest.raises(ValueError) as exc_info:
                require_credential("missing_service", "api_key")

        assert "Missing required credential" in str(exc_info.value)
        assert "missing_service" in str(exc_info.value)


class TestRegistrationHelpers:
    """Tests for node registration helpers."""

    def test_register_node(self):
        """Test registering a single node."""
        from src.plugins.sdk import register_node, node, BaseNode

        @node(type="test.register", name="Test Register")
        class TestNode(BaseNode):
            pass

        with patch("src.plugins.sdk.NodeRegistry") as MockRegistry:
            mock_instance = MagicMock()
            MockRegistry.return_value = mock_instance

            register_node(TestNode)

            mock_instance.register.assert_called_once_with(TestNode)

    def test_register_nodes(self):
        """Test registering multiple nodes."""
        from src.plugins.sdk import register_nodes, node, BaseNode

        @node(type="test.node1", name="Node 1")
        class Node1(BaseNode):
            pass

        @node(type="test.node2", name="Node 2")
        class Node2(BaseNode):
            pass

        with patch("src.plugins.sdk.NodeRegistry") as MockRegistry:
            mock_instance = MagicMock()
            MockRegistry.return_value = mock_instance

            register_nodes([Node1, Node2])

            assert mock_instance.register.call_count == 2


class TestManifestHelper:
    """Tests for create_manifest helper."""

    def test_create_manifest_minimal(self):
        """Test creating manifest with minimal data."""
        from src.plugins.sdk import create_manifest

        manifest = create_manifest(
            id="my-plugin",
            name="My Plugin",
            version="1.0.0",
        )

        assert manifest["id"] == "my-plugin"
        assert manifest["name"] == "My Plugin"
        assert manifest["version"] == "1.0.0"
        assert manifest["nodes"] == []
        assert manifest["dependencies"] == {}

    def test_create_manifest_full(self):
        """Test creating manifest with all fields."""
        from src.plugins.sdk import create_manifest

        manifest = create_manifest(
            id="full-plugin",
            name="Full Plugin",
            version="2.0.0",
            description="A full plugin",
            author="Test Author",
            nodes=["full-plugin.node1", "full-plugin.node2"],
            dependencies={"requests": ">=2.28.0"},
            min_skynette_version="1.5.0",
        )

        assert manifest["description"] == "A full plugin"
        assert manifest["author"] == "Test Author"
        assert len(manifest["nodes"]) == 2
        assert manifest["dependencies"]["requests"] == ">=2.28.0"
        assert manifest["min_skynette_version"] == "1.5.0"


class TestHttpHelper:
    """Tests for http_request helper."""

    @pytest.mark.asyncio
    async def test_http_request_json_response(self):
        """Test HTTP request with JSON response."""
        from src.plugins.sdk import http_request

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"data": "test"}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client

            result = await http_request("GET", "https://api.example.com/data")

        assert result["status"] == 200
        assert result["ok"] is True
        assert result["data"]["data"] == "test"

    @pytest.mark.asyncio
    async def test_http_request_text_response(self):
        """Test HTTP request with text response."""
        from src.plugins.sdk import http_request

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "Plain text response"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client

            result = await http_request("GET", "https://example.com")

        assert result["data"] == "Plain text response"

    @pytest.mark.asyncio
    async def test_http_request_with_params(self):
        """Test HTTP request passes params correctly."""
        from src.plugins.sdk import http_request

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.headers = {}
        mock_response.json.return_value = {}

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client

            await http_request(
                "POST",
                "https://api.example.com",
                headers={"Authorization": "Bearer token"},
                json={"key": "value"},
            )

            mock_client.request.assert_called_once()
            call_kwargs = mock_client.request.call_args[1]
            assert call_kwargs["method"] == "POST"
            assert call_kwargs["headers"]["Authorization"] == "Bearer token"
            assert call_kwargs["json"]["key"] == "value"


class TestPluginTemplate:
    """Tests for plugin template generation."""

    def test_generate_plugin_template(self):
        """Test generating plugin template."""
        from src.plugins.sdk import generate_plugin_template

        template = generate_plugin_template(
            id="my-awesome-plugin",
            name="My Awesome Plugin",
            description="Does awesome things",
        )

        assert "My Awesome Plugin" in template
        assert "my-awesome-plugin" in template
        assert "Does awesome things" in template
        assert "@node(" in template
        assert "class ExampleNode(BaseNode):" in template
        assert "PLUGIN_NODES" in template

    def test_generate_plugin_template_default_description(self):
        """Test template with default description."""
        from src.plugins.sdk import generate_plugin_template

        template = generate_plugin_template(
            id="simple",
            name="Simple Plugin",
        )

        assert "Custom plugin for Skynette" in template


class TestExports:
    """Test that all expected items are exported."""

    def test_all_exports_exist(self):
        """Test that all __all__ items can be imported."""
        from src.plugins.sdk import (
            BaseNode,
            TriggerNode,
            AINode,
            HTTPNode,
            DataNode,
            FlowNode,
            UtilityNode,
            NodeField,
            NodeOutput,
            NodeDefinition,
            FieldType,
            node,
            trigger,
            on_load,
            on_unload,
            field,
            PluginContext,
            get_credential,
            require_credential,
            register_node,
            register_nodes,
        )

        # Just verify imports work
        assert BaseNode is not None
        assert TriggerNode is not None
        assert node is not None
        assert trigger is not None
        assert field is not None
