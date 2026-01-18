"""
Workflow Data Models

Pydantic models for workflow definitions.
"""

from datetime import datetime, UTC
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from uuid import uuid4


class WorkflowNode(BaseModel):
    """Represents a single node in a workflow."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str  # e.g., "manual_trigger", "http_request", "smart_ai"
    name: str
    position: dict = Field(default_factory=lambda: {"x": 0, "y": 0})
    config: dict = Field(default_factory=dict)  # Node-specific configuration
    enabled: bool = True


class WorkflowConnection(BaseModel):
    """Represents a connection between two nodes."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_node_id: str
    source_port: str = "output"
    target_node_id: str
    target_port: str = "input"


class Workflow(BaseModel):
    """Represents a complete workflow definition."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    version: str = "1.0.0"
    nodes: list[WorkflowNode] = Field(default_factory=list)
    connections: list[WorkflowConnection] = Field(default_factory=list)
    variables: dict = Field(default_factory=dict)  # Workflow-level variables
    settings: dict = Field(default_factory=dict)  # Workflow settings
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tags: list[str] = Field(default_factory=list)

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_trigger_nodes(self) -> list[WorkflowNode]:
        """Get all trigger nodes in the workflow."""
        trigger_types = [
            "manual_trigger",
            "schedule_trigger",
            "webhook_trigger",
            "file_watcher_trigger",
            "email_trigger",
        ]
        return [node for node in self.nodes if node.type in trigger_types]

    def get_execution_order(self) -> list[str]:
        """Get the order of node execution (topological sort)."""
        # Build adjacency list
        graph: dict[str, list[str]] = {node.id: [] for node in self.nodes}
        in_degree: dict[str, int] = {node.id: 0 for node in self.nodes}

        for conn in self.connections:
            graph[conn.source_node_id].append(conn.target_node_id)
            in_degree[conn.target_node_id] += 1

        # Kahn's algorithm for topological sort
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        order = []

        while queue:
            node_id = queue.pop(0)
            order.append(node_id)

            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order

    def to_yaml(self) -> str:
        """Convert workflow to YAML format."""
        import yaml

        return yaml.dump(self.model_dump(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "Workflow":
        """Create workflow from YAML content."""
        import yaml

        data = yaml.safe_load(yaml_content)
        return cls(**data)

    def to_python_dsl(self) -> str:
        """Convert workflow to Python DSL format.

        Generates readable Python-like code for editing.

        Returns:
            Python DSL representation of workflow.
        """
        lines = [
            "# Workflow Python DSL",
            "# Edit and save to update workflow",
            "",
            f'workflow = Workflow(name="{self.name}")',
        ]

        if self.description:
            lines.append(f'workflow.description = "{self.description}"')

        if self.version != "1.0.0":
            lines.append(f'workflow.version = "{self.version}"')

        lines.append("")

        # Add nodes
        if self.nodes:
            lines.append("# Nodes")
            for node in self.nodes:
                config_str = ", ".join(
                    f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}"
                    for k, v in node.config.items()
                )
                if config_str:
                    lines.append(
                        f'workflow.add_node("{node.type}", name="{node.name}", '
                        f"id=\"{node.id}\", config={{{config_str}}})"
                    )
                else:
                    lines.append(
                        f'workflow.add_node("{node.type}", name="{node.name}", '
                        f'id="{node.id}")'
                    )
            lines.append("")

        # Add connections
        if self.connections:
            lines.append("# Connections")
            for conn in self.connections:
                lines.append(
                    f'workflow.connect("{conn.source_node_id}", "{conn.target_node_id}")'
                )
            lines.append("")

        # Add variables
        if self.variables:
            lines.append("# Variables")
            for key, value in self.variables.items():
                if isinstance(value, str):
                    lines.append(f'workflow.variables["{key}"] = "{value}"')
                else:
                    lines.append(f'workflow.variables["{key}"] = {value}')
            lines.append("")

        # Add tags
        if self.tags:
            lines.append(f"workflow.tags = {self.tags}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def from_python_dsl(cls, code: str) -> "Workflow":
        """Create workflow from Python DSL code.

        Parses the DSL using restricted exec to prevent arbitrary code execution.

        Args:
            code: Python DSL code.

        Returns:
            Workflow instance.

        Raises:
            ValueError: If DSL is invalid or contains unsafe code.
        """
        # Create a minimal Workflow class for the DSL context
        workflow = cls(name="Untitled")
        nodes_by_name: dict[str, WorkflowNode] = {}

        def add_node(
            node_type: str,
            name: str,
            id: str | None = None,
            config: dict | None = None,
        ) -> None:
            """Add node to workflow."""
            node = WorkflowNode(
                type=node_type,
                name=name,
                config=config or {},
            )
            if id:
                node.id = id
            workflow.nodes.append(node)
            nodes_by_name[name] = node

        def connect(source_id: str, target_id: str) -> None:
            """Connect two nodes."""
            conn = WorkflowConnection(
                source_node_id=source_id,
                target_node_id=target_id,
            )
            workflow.connections.append(conn)

        # DSL context wrapper
        class WorkflowDSL:
            def __init__(self, name: str):
                workflow.name = name

            @property
            def description(self) -> str:
                return workflow.description

            @description.setter
            def description(self, value: str) -> None:
                workflow.description = value

            @property
            def version(self) -> str:
                return workflow.version

            @version.setter
            def version(self, value: str) -> None:
                workflow.version = value

            @property
            def variables(self) -> dict:
                return workflow.variables

            @variables.setter
            def variables(self, value: dict) -> None:
                workflow.variables = value

            @property
            def tags(self) -> list[str]:
                return workflow.tags

            @tags.setter
            def tags(self, value: list[str]) -> None:
                workflow.tags = value

            def add_node(
                self,
                node_type: str,
                name: str,
                id: str | None = None,
                config: dict | None = None,
            ) -> None:
                add_node(node_type, name, id, config)

            def connect(self, source_id: str, target_id: str) -> None:
                connect(source_id, target_id)

        # Restricted globals - only allow safe builtins
        restricted_globals = {
            "__builtins__": {
                "True": True,
                "False": False,
                "None": None,
            },
            "Workflow": WorkflowDSL,
        }

        try:
            exec(code, restricted_globals)
        except Exception as e:
            raise ValueError(f"Invalid Python DSL: {e}")

        return workflow


class ExecutionResult(BaseModel):
    """Result of a single node execution."""

    node_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_ms: float = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None


class WorkflowExecution(BaseModel):
    """Represents a workflow execution instance."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    status: str = "pending"  # pending, running, completed, failed, cancelled
    trigger_type: str = "manual"
    trigger_data: dict = Field(default_factory=dict)
    node_results: list[ExecutionResult] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    duration_ms: float = 0

    def add_result(self, result: ExecutionResult):
        """Add a node execution result."""
        self.node_results.append(result)

    def get_result(self, node_id: str) -> Optional[ExecutionResult]:
        """Get result for a specific node."""
        for result in self.node_results:
            if result.node_id == node_id:
                return result
        return None
