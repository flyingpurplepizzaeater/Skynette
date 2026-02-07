"""
Plugin SDK - Development kit for creating Skynette plugins.

This SDK provides everything needed to create custom nodes, triggers,
and integrations for Skynette workflows.

Quick Start:
    from src.plugins.sdk import (
        node, trigger, field,
        BaseNode, TriggerNode,
        get_credential, require_credential,
        PluginContext
    )

    @node(
        type="my-plugin.hello",
        name="Hello World",
        category="utility",
        icon="hand-wave",
    )
    class HelloNode(BaseNode):
        @staticmethod
        def inputs():
            return [
                field.string("name", "Name", default="World"),
            ]

        async def execute(self, config: dict, context: dict) -> dict:
            return {"greeting": f"Hello, {config['name']}!"}
"""

import builtins
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, List, Optional, Type

# Re-export base classes for plugin developers
from src.core.nodes.base import (
    AINode,
    BaseNode,
    DataNode,
    FieldType,
    FlowNode,
    HTTPNode,
    NodeDefinition,
    NodeField,
    NodeOutput,
    TriggerNode,
    UtilityNode,
)
from src.core.nodes.registry import NodeRegistry

logger = logging.getLogger(__name__)

__all__ = [
    # Base classes
    "BaseNode",
    "TriggerNode",
    "AINode",
    "HTTPNode",
    "DataNode",
    "FlowNode",
    "UtilityNode",
    # Definitions
    "NodeField",
    "NodeOutput",
    "NodeDefinition",
    "FieldType",
    # Decorators
    "node",
    "trigger",
    "on_load",
    "on_unload",
    # Field helpers
    "field",
    # Context and credentials
    "PluginContext",
    "get_credential",
    "require_credential",
    # Registration
    "register_node",
    "register_nodes",
]


# =============================================================================
# DECORATORS
# =============================================================================


def node(
    type: str,
    name: str,
    category: str = "utility",
    description: str = "",
    icon: str = "extension",
    color: str = "#6B7280",
    requires_credentials: list[str] = None,
):
    """
    Decorator for creating custom nodes.

    Usage:
        @node(
            type="my-plugin.my-node",
            name="My Custom Node",
            category="utility",
            description="Does something useful",
            icon="cog",
            color="#3B82F6",
        )
        class MyNode(BaseNode):
            @staticmethod
            def inputs():
                return [field.string("input_name", "Label")]

            async def execute(self, config, context):
                return {"result": config["input_name"]}
    """

    def decorator(cls: builtins.type[BaseNode]) -> builtins.type[BaseNode]:
        cls.type = type
        cls.name = name
        cls.category = category
        cls.description = description or f"{name} node"
        cls.icon = icon
        cls.color = color
        cls.requires_credentials = requires_credentials or []
        cls.is_trigger = False

        # Handle inputs() method if defined
        if hasattr(cls, "inputs") and callable(getattr(cls, "inputs")):
            original_inputs = cls.inputs

            @classmethod
            def get_inputs(klass) -> list[NodeField]:
                result = original_inputs()
                return result if isinstance(result, list) else []

            cls.get_inputs = get_inputs

        # Handle outputs() method if defined
        if hasattr(cls, "outputs") and callable(getattr(cls, "outputs")):
            original_outputs = cls.outputs

            @classmethod
            def get_outputs(klass) -> list[NodeOutput]:
                result = original_outputs()
                return result if isinstance(result, list) else []

            cls.get_outputs = get_outputs

        return cls

    return decorator


def trigger(
    type: str,
    name: str,
    description: str = "",
    icon: str = "bolt",
    color: str = "#F59E0B",
    requires_credentials: list[str] = None,
):
    """
    Decorator for creating trigger nodes.

    Triggers are special nodes that initiate workflow execution.

    Usage:
        @trigger(
            type="my-plugin.webhook",
            name="My Webhook Trigger",
            icon="webhook",
        )
        class WebhookTrigger(TriggerNode):
            @staticmethod
            def inputs():
                return [field.string("path", "Webhook Path")]

            async def execute(self, config, context):
                return context.get("$trigger", {})
    """

    def decorator(cls: builtins.type[TriggerNode]) -> builtins.type[TriggerNode]:
        cls.type = type
        cls.name = name
        cls.description = description or f"{name} trigger"
        cls.category = "trigger"
        cls.icon = icon
        cls.color = color
        cls.is_trigger = True
        cls.requires_credentials = requires_credentials or []

        # Handle inputs() method if defined
        if hasattr(cls, "inputs") and callable(getattr(cls, "inputs")):
            original_inputs = cls.inputs

            @classmethod
            def get_inputs(klass) -> list[NodeField]:
                result = original_inputs()
                return result if isinstance(result, list) else []

            cls.get_inputs = get_inputs

        return cls

    return decorator


def on_load(func: Callable):
    """
    Decorator to mark a function to run when the plugin loads.

    Usage:
        @on_load
        def setup():
            print("Plugin loaded!")
    """
    func._skynette_on_load = True
    return func


def on_unload(func: Callable):
    """
    Decorator to mark a function to run when the plugin unloads.

    Usage:
        @on_unload
        def cleanup():
            print("Plugin unloaded!")
    """
    func._skynette_on_unload = True
    return func


# =============================================================================
# FIELD HELPERS
# =============================================================================


class FieldBuilder:
    """
    Helper class for building node input fields.

    Provides convenient methods for creating typed input fields.
    """

    @staticmethod
    def string(
        name: str,
        label: str,
        description: str = "",
        required: bool = False,
        default: str = "",
        placeholder: str = "",
    ) -> NodeField:
        """Create a string input field."""
        return NodeField(
            name=name,
            label=label,
            type=FieldType.STRING,
            description=description,
            required=required,
            default=default,
            placeholder=placeholder,
        )

    @staticmethod
    def text(
        name: str,
        label: str,
        description: str = "",
        required: bool = False,
        default: str = "",
        placeholder: str = "",
    ) -> NodeField:
        """Create a multi-line text input field."""
        return NodeField(
            name=name,
            label=label,
            type=FieldType.TEXT,
            description=description,
            required=required,
            default=default,
            placeholder=placeholder,
        )

    @staticmethod
    def number(
        name: str,
        label: str,
        description: str = "",
        required: bool = False,
        default: float = 0,
        min_value: float = None,
        max_value: float = None,
    ) -> NodeField:
        """Create a number input field."""
        return NodeField(
            name=name,
            label=label,
            type=FieldType.NUMBER,
            description=description,
            required=required,
            default=default,
            min_value=min_value,
            max_value=max_value,
        )

    @staticmethod
    def boolean(
        name: str,
        label: str,
        description: str = "",
        default: bool = False,
    ) -> NodeField:
        """Create a boolean toggle field."""
        return NodeField(
            name=name,
            label=label,
            type=FieldType.BOOLEAN,
            description=description,
            required=False,
            default=default,
        )

    @staticmethod
    def select(
        name: str,
        label: str,
        options: list[tuple[str, str]],
        description: str = "",
        required: bool = False,
        default: str = None,
    ) -> NodeField:
        """
        Create a dropdown select field.

        Args:
            options: List of (value, label) tuples
        """
        return NodeField(
            name=name,
            label=label,
            type=FieldType.SELECT,
            description=description,
            required=required,
            default=default or (options[0][0] if options else None),
            options=[{"value": v, "label": l} for v, l in options],
        )

    @staticmethod
    def multi_select(
        name: str,
        label: str,
        options: list[tuple[str, str]],
        description: str = "",
        default: list[str] = None,
    ) -> NodeField:
        """
        Create a multi-select field.

        Args:
            options: List of (value, label) tuples
        """
        return NodeField(
            name=name,
            label=label,
            type=FieldType.MULTI_SELECT,
            description=description,
            required=False,
            default=default or [],
            options=[{"value": v, "label": l} for v, l in options],
        )

    @staticmethod
    def json(
        name: str,
        label: str,
        description: str = "",
        required: bool = False,
        default: Any = None,
    ) -> NodeField:
        """Create a JSON input field."""
        return NodeField(
            name=name,
            label=label,
            type=FieldType.JSON,
            description=description,
            required=required,
            default=default or {},
        )

    @staticmethod
    def expression(
        name: str,
        label: str,
        description: str = "",
        required: bool = False,
        default: str = "",
        placeholder: str = "{{$prev.data}}",
    ) -> NodeField:
        """Create a field that supports {{expressions}}."""
        return NodeField(
            name=name,
            label=label,
            type=FieldType.EXPRESSION,
            description=description,
            required=required,
            default=default,
            placeholder=placeholder,
        )

    @staticmethod
    def file(
        name: str,
        label: str,
        description: str = "",
        required: bool = False,
    ) -> NodeField:
        """Create a file path input field."""
        return NodeField(
            name=name,
            label=label,
            type=FieldType.FILE,
            description=description,
            required=required,
        )

    @staticmethod
    def secret(
        name: str,
        label: str,
        description: str = "",
        required: bool = False,
        placeholder: str = "••••••••",
    ) -> NodeField:
        """Create a secret/password input field (masked)."""
        return NodeField(
            name=name,
            label=label,
            type=FieldType.SECRET,
            description=description,
            required=required,
            placeholder=placeholder,
        )


# Global field builder instance
field = FieldBuilder()


# =============================================================================
# OUTPUT HELPERS
# =============================================================================


class OutputBuilder:
    """Helper for defining node outputs."""

    @staticmethod
    def string(name: str, description: str = "") -> NodeOutput:
        return NodeOutput(name=name, type="string", description=description)

    @staticmethod
    def number(name: str, description: str = "") -> NodeOutput:
        return NodeOutput(name=name, type="number", description=description)

    @staticmethod
    def boolean(name: str, description: str = "") -> NodeOutput:
        return NodeOutput(name=name, type="boolean", description=description)

    @staticmethod
    def object(name: str = "output", description: str = "") -> NodeOutput:
        return NodeOutput(name=name, type="object", description=description)

    @staticmethod
    def array(name: str, description: str = "") -> NodeOutput:
        return NodeOutput(name=name, type="array", description=description)


output = OutputBuilder()


# =============================================================================
# CONTEXT AND CREDENTIALS
# =============================================================================


class PluginContext:
    """
    Helper for accessing execution context in nodes.

    Provides convenient access to trigger data, variables, and previous
    node outputs within the workflow execution context.
    """

    def __init__(self, context: dict):
        self._context = context

    @property
    def trigger_data(self) -> dict:
        """Get the trigger data that started this execution."""
        return self._context.get("$trigger", {})

    @property
    def variables(self) -> dict:
        """Get workflow variables."""
        return self._context.get("$vars", {})

    @property
    def previous_output(self) -> Any:
        """Get the output from the previous node."""
        return self._context.get("$prev")

    def get_node_output(self, node_id: str) -> Any:
        """Get output from a specific node by ID."""
        return self._context.get("$nodes", {}).get(node_id)

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a workflow variable by name."""
        return self.variables.get(name, default)

    def get(self, key: str, default: Any = None) -> Any:
        """Get any value from context."""
        return self._context.get(key, default)


def get_credential(service: str, field_name: str = "api_key") -> str | None:
    """
    Get a credential value from the credential vault.

    Args:
        service: Service name (e.g., 'openai', 'slack')
        field_name: Field name in credential data (default: 'api_key')

    Returns:
        The credential value or None if not found
    """
    try:
        from src.data.credentials import get_api_key

        return get_api_key(service, field_name)
    except ImportError:
        logger.warning("Credential vault not available")
        return None


def require_credential(service: str, field_name: str = "api_key") -> str:
    """
    Get a required credential, raising an error if not found.

    Args:
        service: Service name
        field_name: Field name in credential data

    Returns:
        The credential value

    Raises:
        ValueError: If credential is not found
    """
    value = get_credential(service, field_name)
    if value is None:
        raise ValueError(
            f"Missing required credential '{field_name}' for service '{service}'. "
            f"Please add it using: skynette credentials add {service}"
        )
    return value


# =============================================================================
# REGISTRATION HELPERS
# =============================================================================


def register_node(node_class: type[BaseNode]) -> None:
    """
    Register a node class with the global registry.

    This is called automatically when using the @node decorator
    during plugin initialization.

    Args:
        node_class: The node class to register
    """
    registry = NodeRegistry()
    registry.register(node_class)
    logger.debug(f"Plugin registered node: {node_class.type}")


def register_nodes(node_classes: list[type[BaseNode]]) -> None:
    """
    Register multiple node classes at once.

    Args:
        node_classes: List of node classes to register
    """
    registry = NodeRegistry()
    for node_class in node_classes:
        registry.register(node_class)
    logger.info(f"Plugin registered {len(node_classes)} nodes")


# =============================================================================
# PLUGIN MANIFEST HELPERS
# =============================================================================


def create_manifest(
    id: str,
    name: str,
    version: str,
    description: str = "",
    author: str = "",
    nodes: list[str] = None,
    dependencies: dict[str, str] = None,
    min_skynette_version: str = "1.0.0",
) -> dict:
    """
    Helper to create a plugin manifest dictionary.

    Usage:
        manifest = create_manifest(
            id="my-awesome-plugin",
            name="My Awesome Plugin",
            version="1.0.0",
            description="Does awesome things",
            author="Your Name",
            nodes=["my-plugin.node1", "my-plugin.node2"],
        )
    """
    return {
        "id": id,
        "name": name,
        "version": version,
        "description": description,
        "author": author,
        "nodes": nodes or [],
        "dependencies": dependencies or {},
        "min_skynette_version": min_skynette_version,
    }


# =============================================================================
# HTTP HELPERS
# =============================================================================


async def http_request(
    method: str,
    url: str,
    headers: dict = None,
    params: dict = None,
    json: dict = None,
    data: Any = None,
    timeout: float = 30.0,
) -> dict:
    """
    Make an HTTP request with standardized error handling.

    Returns:
        dict with 'status', 'headers', 'data', and 'ok' fields
    """
    import httpx

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data,
        )

        # Try to parse JSON response
        try:
            response_data = response.json()
        except Exception:
            response_data = response.text

        return {
            "status": response.status_code,
            "ok": response.is_success,
            "headers": dict(response.headers),
            "data": response_data,
        }


# =============================================================================
# EXAMPLE PLUGIN TEMPLATE
# =============================================================================

PLUGIN_TEMPLATE = '''
"""
{name} Plugin for Skynette

{description}
"""

from src.plugins.sdk import (
    node, trigger, field, output,
    BaseNode, TriggerNode,
    get_credential, require_credential,
    PluginContext,
    register_nodes,
)


# Define your nodes
@node(
    type="{id}.example",
    name="Example Node",
    category="utility",
    description="An example node from {name}",
    icon="star",
    color="#3B82F6",
)
class ExampleNode(BaseNode):
    """Example node implementation."""

    @staticmethod
    def inputs():
        return [
            field.string("message", "Message", required=True, placeholder="Enter message"),
            field.number("count", "Repeat Count", default=1, min_value=1, max_value=10),
        ]

    @staticmethod
    def outputs():
        return [
            output.string("result", "The processed message"),
        ]

    async def execute(self, config: dict, context: dict) -> dict:
        message = config.get("message", "")
        count = int(config.get("count", 1))

        result = " ".join([message] * count)

        return {{"result": result}}


# List all nodes to export
PLUGIN_NODES = [
    ExampleNode,
]


# Plugin lifecycle hooks
def on_load():
    """Called when plugin is loaded."""
    register_nodes(PLUGIN_NODES)
    print("{name} plugin loaded!")


def on_unload():
    """Called when plugin is unloaded."""
    print("{name} plugin unloaded!")
'''


def generate_plugin_template(
    id: str,
    name: str,
    description: str = "",
) -> str:
    """
    Generate a plugin template string.

    Args:
        id: Plugin ID (e.g., 'my-awesome-plugin')
        name: Human-readable plugin name
        description: Plugin description

    Returns:
        Plugin template as a string
    """
    return PLUGIN_TEMPLATE.format(
        id=id,
        name=name,
        description=description or "Custom plugin for Skynette",
    )
