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
