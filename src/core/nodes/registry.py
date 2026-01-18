"""
Node Registry

Central registry for all available node types.
"""

from typing import Optional, Type
import logging

from src.core.nodes.base import BaseNode, NodeDefinition

logger = logging.getLogger(__name__)


class NodeRegistry:
    """Registry for node types."""

    _instance = None
    _handlers: dict[str, Type[BaseNode]] = {}

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._handlers = {}
        self._load_builtin_nodes()

    def _load_builtin_nodes(self):
        """Load all built-in nodes."""
        # Import and register built-in nodes
        from src.core.nodes.triggers.manual import ManualTriggerNode
        from src.core.nodes.triggers.schedule import ScheduleTriggerNode
        from src.core.nodes.http.request import HTTPRequestNode
        from src.core.nodes.flow.if_else import IfElseNode
        from src.core.nodes.flow.set_variable import SetVariableNode
        from src.core.nodes.data.read_file import ReadFileNode
        from src.core.nodes.data.write_file import WriteFileNode
        from src.core.nodes.flow.log_debug import LogDebugNode

        builtin_nodes = [
            ManualTriggerNode,
            ScheduleTriggerNode,
            HTTPRequestNode,
            IfElseNode,
            SetVariableNode,
            ReadFileNode,
            WriteFileNode,
            LogDebugNode,
        ]

        for node_class in builtin_nodes:
            self.register(node_class)

        # Load AI nodes
        try:
            from src.core.nodes.ai import AI_NODES
            for node_class in AI_NODES:
                self.register(node_class)
            logger.info(f"Loaded {len(AI_NODES)} AI nodes")
        except ImportError as e:
            logger.warning(f"Could not load AI nodes: {e}")

        # Load App integration nodes
        try:
            from src.core.nodes.apps import APP_NODES
            for node_class in APP_NODES:
                self.register(node_class)
            logger.info(f"Loaded {len(APP_NODES)} App nodes")
        except ImportError as e:
            logger.warning(f"Could not load App nodes: {e}")

        # Load Utility nodes
        try:
            from src.core.nodes.utility import UTILITY_NODES
            for node_class in UTILITY_NODES:
                self.register(node_class)
            logger.info(f"Loaded {len(UTILITY_NODES)} Utility nodes")
        except ImportError as e:
            logger.warning(f"Could not load Utility nodes: {e}")

        # Load Coding/Development nodes
        try:
            from src.core.nodes.coding import CODING_NODES
            for node_class in CODING_NODES:
                self.register(node_class)
            logger.info(f"Loaded {len(CODING_NODES)} Coding nodes")
        except ImportError as e:
            logger.warning(f"Could not load Coding nodes: {e}")

        # Load Execution nodes
        try:
            from src.core.nodes.execution import EXECUTION_NODES
            for node_class in EXECUTION_NODES:
                self.register(node_class)
            logger.info(f"Loaded {len(EXECUTION_NODES)} Execution nodes")
        except ImportError as e:
            logger.warning(f"Could not load Execution nodes: {e}")

        logger.info(f"Total: {len(self._handlers)} nodes registered")

    def register(self, node_class: Type[BaseNode]):
        """Register a node type."""
        if not issubclass(node_class, BaseNode):
            raise TypeError(f"{node_class} must be a subclass of BaseNode")

        self._handlers[node_class.type] = node_class
        logger.debug(f"Registered node: {node_class.type}")

    def unregister(self, node_type: str):
        """Unregister a node type."""
        if node_type in self._handlers:
            del self._handlers[node_type]

    def get_handler(self, node_type: str) -> Optional[BaseNode]:
        """Get a node handler instance by type."""
        handler_class = self._handlers.get(node_type)
        if handler_class:
            return handler_class()
        return None

    def get_definition(self, node_type: str) -> Optional[NodeDefinition]:
        """Get the node definition by type."""
        handler_class = self._handlers.get(node_type)
        if handler_class:
            return handler_class.get_definition()
        return None

    def get_all_definitions(self) -> list[NodeDefinition]:
        """Get all registered node definitions."""
        return [cls.get_definition() for cls in self._handlers.values()]

    def get_by_category(self, category: str) -> list[NodeDefinition]:
        """Get all nodes in a category."""
        return [
            cls.get_definition()
            for cls in self._handlers.values()
            if cls.category == category
        ]

    def get_triggers(self) -> list[NodeDefinition]:
        """Get all trigger nodes."""
        return [
            cls.get_definition()
            for cls in self._handlers.values()
            if cls.is_trigger
        ]

    @property
    def node_types(self) -> list[str]:
        """Get all registered node types."""
        return list(self._handlers.keys())

    @property
    def categories(self) -> list[str]:
        """Get all unique categories."""
        return list(set(cls.category for cls in self._handlers.values()))
