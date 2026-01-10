"""
Workflow fixtures for testing.

Factory functions for creating test workflows with various configurations.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from src.core.workflow.models import (
    Workflow,
    WorkflowNode,
    WorkflowConnection,
    WorkflowExecution,
    ExecutionResult,
)


def create_test_workflow(
    name: str = "Test Workflow",
    description: str = "A test workflow for automated testing",
    with_trigger: bool = True,
    with_steps: int = 2,
    workflow_id: Optional[str] = None,
) -> Workflow:
    """
    Factory for creating test workflows.

    Args:
        name: Workflow name
        description: Workflow description
        with_trigger: Whether to include a manual trigger
        with_steps: Number of AI steps to add
        workflow_id: Optional specific ID

    Returns:
        A configured Workflow instance
    """
    workflow = Workflow(
        id=workflow_id or str(uuid4()),
        name=name,
        description=description,
        version="1.0.0",
        tags=["test", "automated"],
    )

    prev_node = None

    # Add trigger node
    if with_trigger:
        trigger = WorkflowNode(
            id=f"trigger-{uuid4().hex[:8]}",
            type="manual_trigger",
            name="Manual Trigger",
            position={"x": 100, "y": 100},
            config={},
        )
        workflow.nodes.append(trigger)
        prev_node = trigger

    # Add step nodes
    for i in range(with_steps):
        node = WorkflowNode(
            id=f"step-{i+1}-{uuid4().hex[:8]}",
            type="ai_chat",
            name=f"AI Step {i + 1}",
            position={"x": 300 + i * 200, "y": 100},
            config={
                "prompt": f"Step {i + 1} prompt",
                "model": "mock-model",
            },
        )
        workflow.nodes.append(node)

        # Connect to previous node
        if prev_node:
            connection = WorkflowConnection(
                source_node_id=prev_node.id,
                target_node_id=node.id,
                source_port="output",
                target_port="input",
            )
            workflow.connections.append(connection)

        prev_node = node

    return workflow


def create_empty_workflow(name: str = "Empty Workflow") -> Workflow:
    """Create an empty workflow with no nodes."""
    return Workflow(
        name=name,
        description="An empty workflow",
        tags=["test"],
    )


def create_complex_workflow(name: str = "Complex Workflow") -> Workflow:
    """
    Create a more complex workflow with multiple node types.

    Includes trigger, HTTP request, AI processing, and conditional logic.
    """
    workflow = Workflow(
        name=name,
        description="A complex workflow with multiple node types",
        tags=["test", "complex"],
    )

    # Trigger
    trigger = WorkflowNode(
        id="trigger-1",
        type="manual_trigger",
        name="Start",
        position={"x": 100, "y": 200},
    )

    # HTTP Request
    http_node = WorkflowNode(
        id="http-1",
        type="http_request",
        name="Fetch Data",
        position={"x": 300, "y": 200},
        config={
            "url": "https://api.example.com/data",
            "method": "GET",
        },
    )

    # AI Processing
    ai_node = WorkflowNode(
        id="ai-1",
        type="ai_chat",
        name="Process with AI",
        position={"x": 500, "y": 200},
        config={
            "prompt": "Analyze this data: {{$prev.data}}",
        },
    )

    # Conditional
    if_node = WorkflowNode(
        id="if-1",
        type="if_else",
        name="Check Result",
        position={"x": 700, "y": 200},
        config={
            "condition": "{{$prev.success}} == true",
        },
    )

    # Success path
    success_node = WorkflowNode(
        id="success-1",
        type="set_variable",
        name="Handle Success",
        position={"x": 900, "y": 100},
        config={
            "variable": "result",
            "value": "Success!",
        },
    )

    # Failure path
    failure_node = WorkflowNode(
        id="failure-1",
        type="set_variable",
        name="Handle Failure",
        position={"x": 900, "y": 300},
        config={
            "variable": "result",
            "value": "Failed",
        },
    )

    # Add all nodes
    workflow.nodes = [trigger, http_node, ai_node, if_node, success_node, failure_node]

    # Add connections
    workflow.connections = [
        WorkflowConnection(source_node_id="trigger-1", target_node_id="http-1"),
        WorkflowConnection(source_node_id="http-1", target_node_id="ai-1"),
        WorkflowConnection(source_node_id="ai-1", target_node_id="if-1"),
        WorkflowConnection(
            source_node_id="if-1",
            source_port="true",
            target_node_id="success-1"
        ),
        WorkflowConnection(
            source_node_id="if-1",
            source_port="false",
            target_node_id="failure-1"
        ),
    ]

    return workflow


def create_test_execution(
    workflow_id: str,
    status: str = "completed",
    success: bool = True,
    duration_ms: float = 1234.5,
) -> WorkflowExecution:
    """
    Create a test execution record.

    Args:
        workflow_id: ID of the associated workflow
        status: Execution status
        success: Whether execution was successful
        duration_ms: Duration in milliseconds

    Returns:
        A WorkflowExecution instance
    """
    now = datetime.utcnow()

    execution = WorkflowExecution(
        id=str(uuid4()),
        workflow_id=workflow_id,
        status=status,
        trigger_type="manual",
        trigger_data={},
        started_at=now - timedelta(milliseconds=duration_ms),
        completed_at=now if status in ("completed", "failed") else None,
        duration_ms=duration_ms,
        error=None if success else "Test error message",
    )

    # Add some mock node results
    execution.node_results = [
        ExecutionResult(
            node_id="trigger-1",
            success=True,
            data={"triggered": True},
            duration_ms=10.0,
            started_at=now - timedelta(milliseconds=duration_ms),
            completed_at=now - timedelta(milliseconds=duration_ms - 10),
        ),
        ExecutionResult(
            node_id="step-1",
            success=success,
            data={"result": "Mock result"} if success else None,
            error=None if success else "Step failed",
            duration_ms=duration_ms - 10,
            started_at=now - timedelta(milliseconds=duration_ms - 10),
            completed_at=now,
        ),
    ]

    return execution


def create_multiple_workflows(count: int = 3) -> list[Workflow]:
    """Create multiple test workflows for list view testing."""
    workflows = []
    for i in range(count):
        workflow = create_test_workflow(
            name=f"Test Workflow {i + 1}",
            description=f"Description for workflow {i + 1}",
            with_steps=i + 1,  # Varying complexity
        )
        # Stagger creation times
        workflow.created_at = datetime.utcnow() - timedelta(days=count - i)
        workflow.updated_at = datetime.utcnow() - timedelta(hours=count - i)
        workflows.append(workflow)
    return workflows


def create_multiple_executions(
    workflow_id: str,
    count: int = 5,
    mix_statuses: bool = True,
) -> list[WorkflowExecution]:
    """
    Create multiple test executions for history view testing.

    Args:
        workflow_id: ID of the associated workflow
        count: Number of executions to create
        mix_statuses: Whether to vary statuses

    Returns:
        List of WorkflowExecution instances
    """
    executions = []
    statuses = ["completed", "failed", "completed", "completed", "running"]

    for i in range(count):
        status = statuses[i % len(statuses)] if mix_statuses else "completed"
        success = status == "completed"

        execution = create_test_execution(
            workflow_id=workflow_id,
            status=status,
            success=success,
            duration_ms=1000 + i * 500,
        )

        # Stagger times
        offset = timedelta(hours=count - i)
        execution.started_at = datetime.utcnow() - offset
        if execution.completed_at:
            execution.completed_at = execution.started_at + timedelta(
                milliseconds=execution.duration_ms
            )

        executions.append(execution)

    return executions
