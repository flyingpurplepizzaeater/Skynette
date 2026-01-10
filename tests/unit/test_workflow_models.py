"""
Unit Tests for Workflow Models

Tests for Workflow, WorkflowNode, WorkflowExecution, etc.
"""

import pytest
from datetime import datetime
from src.core.workflow.models import (
    Workflow,
    WorkflowNode,
    WorkflowConnection,
    ExecutionResult,
    WorkflowExecution,
)


class TestWorkflowNode:
    """Tests for WorkflowNode model."""

    def test_create_node(self):
        """Test creating a workflow node."""
        node = WorkflowNode(
            type="manual_trigger",
            name="Start",
            position={"x": 100, "y": 200},
            config={"test_data": {"foo": "bar"}},
        )

        assert node.type == "manual_trigger"
        assert node.name == "Start"
        assert node.position["x"] == 100
        assert node.enabled is True
        assert node.id is not None

    def test_node_defaults(self):
        """Test node default values."""
        node = WorkflowNode(type="http_request", name="API Call")

        assert node.position == {"x": 0, "y": 0}
        assert node.config == {}
        assert node.enabled is True


class TestWorkflowConnection:
    """Tests for WorkflowConnection model."""

    def test_create_connection(self):
        """Test creating a connection between nodes."""
        conn = WorkflowConnection(
            source_node_id="node1",
            target_node_id="node2",
        )

        assert conn.source_node_id == "node1"
        assert conn.target_node_id == "node2"
        assert conn.source_port == "output"
        assert conn.target_port == "input"
        assert conn.id is not None


class TestWorkflow:
    """Tests for Workflow model."""

    def test_create_empty_workflow(self):
        """Test creating an empty workflow."""
        workflow = Workflow(
            name="Test Workflow",
            description="A test workflow",
        )

        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"
        assert workflow.version == "1.0.0"
        assert len(workflow.nodes) == 0
        assert len(workflow.connections) == 0
        assert workflow.id is not None

    def test_get_node(self):
        """Test getting a node by ID."""
        node1 = WorkflowNode(type="manual_trigger", name="Start")
        node2 = WorkflowNode(type="http_request", name="API")

        workflow = Workflow(
            name="Test",
            nodes=[node1, node2],
        )

        found = workflow.get_node(node1.id)
        assert found is not None
        assert found.id == node1.id
        assert found.name == "Start"

        not_found = workflow.get_node("invalid_id")
        assert not_found is None

    def test_get_trigger_nodes(self):
        """Test finding trigger nodes."""
        trigger1 = WorkflowNode(type="manual_trigger", name="Manual")
        trigger2 = WorkflowNode(type="schedule_trigger", name="Schedule")
        regular = WorkflowNode(type="http_request", name="API")

        workflow = Workflow(
            name="Test",
            nodes=[trigger1, regular, trigger2],
        )

        triggers = workflow.get_trigger_nodes()
        assert len(triggers) == 2
        trigger_names = [t.name for t in triggers]
        assert "Manual" in trigger_names
        assert "Schedule" in trigger_names
        assert "API" not in trigger_names

    def test_execution_order_linear(self):
        """Test execution order for linear workflow."""
        node1 = WorkflowNode(type="manual_trigger", name="Start")
        node2 = WorkflowNode(type="http_request", name="API")
        node3 = WorkflowNode(type="log_debug", name="Log")

        conn1 = WorkflowConnection(source_node_id=node1.id, target_node_id=node2.id)
        conn2 = WorkflowConnection(source_node_id=node2.id, target_node_id=node3.id)

        workflow = Workflow(
            name="Linear",
            nodes=[node1, node2, node3],
            connections=[conn1, conn2],
        )

        order = workflow.get_execution_order()
        assert len(order) == 3
        assert order[0] == node1.id
        assert order[1] == node2.id
        assert order[2] == node3.id

    def test_execution_order_branching(self):
        """Test execution order for branching workflow."""
        # Start -> A -> C
        #       -> B -> C
        start = WorkflowNode(type="manual_trigger", name="Start")
        node_a = WorkflowNode(type="http_request", name="A")
        node_b = WorkflowNode(type="http_request", name="B")
        node_c = WorkflowNode(type="log_debug", name="C")

        workflow = Workflow(
            name="Branch",
            nodes=[start, node_a, node_b, node_c],
            connections=[
                WorkflowConnection(source_node_id=start.id, target_node_id=node_a.id),
                WorkflowConnection(source_node_id=start.id, target_node_id=node_b.id),
                WorkflowConnection(source_node_id=node_a.id, target_node_id=node_c.id),
                WorkflowConnection(source_node_id=node_b.id, target_node_id=node_c.id),
            ],
        )

        order = workflow.get_execution_order()
        assert len(order) == 4
        assert order[0] == start.id
        # A and B can be in any order (parallel branches)
        assert node_a.id in order[1:3]
        assert node_b.id in order[1:3]
        # C must be last
        assert order[3] == node_c.id

    def test_yaml_serialization(self):
        """Test YAML serialization and deserialization."""
        node = WorkflowNode(type="manual_trigger", name="Start")
        workflow = Workflow(
            name="YAML Test",
            description="Test YAML",
            nodes=[node],
            variables={"api_key": "secret"},
            tags=["test", "automation"],
        )

        # Convert to YAML
        yaml_content = workflow.to_yaml()
        assert isinstance(yaml_content, str)
        assert "YAML Test" in yaml_content
        assert "manual_trigger" in yaml_content

        # Convert back from YAML
        restored = Workflow.from_yaml(yaml_content)
        assert restored.name == workflow.name
        assert restored.description == workflow.description
        assert len(restored.nodes) == 1
        assert restored.nodes[0].type == "manual_trigger"
        assert restored.variables["api_key"] == "secret"
        assert "test" in restored.tags


class TestExecutionResult:
    """Tests for ExecutionResult model."""

    def test_create_success_result(self):
        """Test creating a successful execution result."""
        result = ExecutionResult(
            node_id="node1",
            success=True,
            data={"status": 200, "message": "OK"},
            duration_ms=150.5,
        )

        assert result.node_id == "node1"
        assert result.success is True
        assert result.data["status"] == 200
        assert result.error is None
        assert result.duration_ms == 150.5

    def test_create_error_result(self):
        """Test creating a failed execution result."""
        result = ExecutionResult(
            node_id="node2",
            success=False,
            error="Connection timeout",
            duration_ms=30000,
        )

        assert result.node_id == "node2"
        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.data is None


class TestWorkflowExecution:
    """Tests for WorkflowExecution model."""

    def test_create_execution(self):
        """Test creating a workflow execution."""
        execution = WorkflowExecution(
            workflow_id="workflow1",
            status="running",
            trigger_type="manual",
            trigger_data={"user": "admin"},
        )

        assert execution.workflow_id == "workflow1"
        assert execution.status == "running"
        assert execution.trigger_type == "manual"
        assert execution.trigger_data["user"] == "admin"
        assert execution.id is not None
        assert len(execution.node_results) == 0

    def test_add_result(self):
        """Test adding node results to execution."""
        execution = WorkflowExecution(workflow_id="w1")

        result1 = ExecutionResult(node_id="n1", success=True, data={"a": 1})
        result2 = ExecutionResult(node_id="n2", success=True, data={"b": 2})

        execution.add_result(result1)
        execution.add_result(result2)

        assert len(execution.node_results) == 2
        assert execution.node_results[0].node_id == "n1"
        assert execution.node_results[1].node_id == "n2"

    def test_get_result(self):
        """Test getting a specific node result."""
        execution = WorkflowExecution(workflow_id="w1")

        result = ExecutionResult(node_id="test_node", success=True, data={"x": 10})
        execution.add_result(result)

        found = execution.get_result("test_node")
        assert found is not None
        assert found.data["x"] == 10

        not_found = execution.get_result("missing_node")
        assert not_found is None
