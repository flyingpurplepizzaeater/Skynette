"""
Base Node Classes

Abstract base class and utilities for node implementations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel


class FieldType(str, Enum):
    """Types of node configuration fields."""

    STRING = "string"
    TEXT = "text"  # Multi-line string
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    JSON = "json"
    EXPRESSION = "expression"  # Supports {{expressions}}
    FILE = "file"
    SECRET = "secret"  # For passwords/API keys
    CREDENTIAL = "credential"  # Reference to saved credential


class NodeField(BaseModel):
    """Definition of a node configuration field."""

    name: str
    label: str
    type: FieldType
    description: str = ""
    required: bool = False
    default: Any = None
    placeholder: str = ""
    options: list[dict] = []  # For select fields: [{"label": "...", "value": "..."}]
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    validation_pattern: Optional[str] = None
    credential_service: Optional[str] = None  # For CREDENTIAL fields: filter by service


class NodeOutput(BaseModel):
    """Definition of a node output."""

    name: str
    type: str  # string, number, boolean, object, array
    description: str = ""


class NodeDefinition(BaseModel):
    """Complete definition of a node type."""

    type: str
    name: str
    description: str
    category: str
    icon: str = "extension"
    color: str = "#6B7280"
    inputs: list[NodeField] = []
    outputs: list[NodeOutput] = []
    is_trigger: bool = False
    requires_credentials: list[str] = []


class BaseNode(ABC):
    """Abstract base class for all nodes."""

    # Override in subclass
    type: str = "base"
    name: str = "Base Node"
    description: str = "Base node class"
    category: str = "utility"
    icon: str = "extension"
    color: str = "#6B7280"
    is_trigger: bool = False
    requires_credentials: list[str] = []

    @classmethod
    def get_inputs(cls) -> list[NodeField]:
        """Get the input field definitions for this node."""
        return []

    @classmethod
    def get_outputs(cls) -> list[NodeOutput]:
        """Get the output definitions for this node."""
        return [NodeOutput(name="output", type="object", description="Node output")]

    @classmethod
    def get_definition(cls) -> NodeDefinition:
        """Get the complete node definition."""
        return NodeDefinition(
            type=cls.type,
            name=cls.name,
            description=cls.description,
            category=cls.category,
            icon=cls.icon,
            color=cls.color,
            inputs=cls.get_inputs(),
            outputs=cls.get_outputs(),
            is_trigger=cls.is_trigger,
            requires_credentials=cls.requires_credentials,
        )

    @abstractmethod
    async def execute(self, config: dict, context: dict) -> Any:
        """
        Execute the node with the given configuration and context.

        Args:
            config: The resolved node configuration
            context: Execution context with data from previous nodes

        Returns:
            The node output data
        """
        pass


class TriggerNode(BaseNode):
    """Base class for trigger nodes."""

    is_trigger: bool = True
    category: str = "trigger"
    color: str = "#F59E0B"  # Amber


class AINode(BaseNode):
    """Base class for AI-related nodes."""

    category: str = "ai"
    color: str = "#8B5CF6"  # Violet


class HTTPNode(BaseNode):
    """Base class for HTTP-related nodes."""

    category: str = "http"
    color: str = "#3B82F6"  # Blue


class DataNode(BaseNode):
    """Base class for data/file nodes."""

    category: str = "data"
    color: str = "#10B981"  # Emerald


class FlowNode(BaseNode):
    """Base class for flow control nodes."""

    category: str = "flow"
    color: str = "#EC4899"  # Pink


class UtilityNode(BaseNode):
    """Base class for utility nodes."""

    category: str = "utility"
    color: str = "#6B7280"  # Gray
