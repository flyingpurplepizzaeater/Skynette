"""
Unit Tests for Workflow Executor

Tests for WorkflowExecutor and DebugExecutor.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.core.workflow.executor import WorkflowExecutor, DebugExecutor
from src.core.workflow.models import (
    Workflow,
    WorkflowNode,
    WorkflowConnection,
)
from src.core.nodes.base import BaseNode, NodeField, FieldType


# Mock node for testing
class MockSuccessNode(BaseNode):
    """A mock node that always succeeds."""

    type = "mock_success"
    name = "Mock Success"
    category = "test"

    async def execute(self, config: dict, context: dict):
        return {"result": "success", "config": config, "context_keys": list(context.keys())}


class MockFailNode(BaseNode):
    """A mock node that always fails."""

    type = "mock_fail"
    name = "Mock Fail"
    category = "test"

    async def execute(self, config: dict, context: dict):
        raise ValueError("Mock error")


class MockDataNode(BaseNode):
    """A mock node that returns specific data."""

    type = "mock_data"
    name = "Mock Data"
    category = "test"

    async def execute(self, config: dict, context: dict):
        return config.get("return_data", {"default": "data"})


@pytest.fixture
def executor():
    """Create a workflow executor for testing."""
    executor = WorkflowExecutor()
    # Register mock nodes to the singleton registry
    executor.node_registry._handlers["mock_success"] = MockSuccessNode
    executor.node_registry._handlers["mock_fail"] = MockFailNode
    executor.node_registry._handlers["mock_data"] = MockDataNode
    yield executor
    # Cleanup - remove mock nodes after test
    executor.node_registry._handlers.pop("mock_success", None)
    executor.node_registry._handlers.pop("mock_fail", None)
    executor.node_registry._handlers.pop("mock_data", None)


@pytest.mark.asyncio
class TestWorkflowExecutor:
    """Tests for WorkflowExecutor."""

    async def test_execute_empty_workflow(self, executor):
        """Test executing an empty workflow."""
        workflow = Workflow(name="Empty")

        execution = await executor.execute(workflow)

        assert execution.workflow_id == workflow.id
        assert execution.status == "completed"
        assert len(execution.node_results) == 0
        assert execution.completed_at is not None

    async def test_execute_single_node(self, executor):
        """Test executing a workflow with one node."""
        node = WorkflowNode(type="mock_success", name="Node1")
        workflow = Workflow(name="Single", nodes=[node])

        execution = await executor.execute(workflow)

        assert execution.status == "completed"
        assert len(execution.node_results) == 1
        assert execution.node_results[0].success is True
        assert execution.node_results[0].node_id == node.id

    async def test_execute_linear_workflow(self, executor):
        """Test executing a linear workflow."""
        node1 = WorkflowNode(type="mock_success", name="Node1")
        node2 = WorkflowNode(type="mock_success", name="Node2")
        node3 = WorkflowNode(type="mock_success", name="Node3")

        workflow = Workflow(
            name="Linear",
            nodes=[node1, node2, node3],
            connections=[
                WorkflowConnection(source_node_id=node1.id, target_node_id=node2.id),
                WorkflowConnection(source_node_id=node2.id, target_node_id=node3.id),
            ],
        )

        execution = await executor.execute(workflow)

        assert execution.status == "completed"
        assert len(execution.node_results) == 3
        # All should succeed
        assert all(r.success for r in execution.node_results)

    async def test_context_data_passing(self, executor):
        """Test that data passes correctly between nodes."""
        node1 = WorkflowNode(
            type="mock_data",
            name="Node1",
            config={"return_data": {"value": 100}},
        )
        node2 = WorkflowNode(type="mock_success", name="Node2")

        workflow = Workflow(
            name="Context",
            nodes=[node1, node2],
            connections=[
                WorkflowConnection(source_node_id=node1.id, target_node_id=node2.id),
            ],
        )

        execution = await executor.execute(workflow)

        assert execution.status == "completed"
        # Node2 should have access to node1's data via context
        node2_result = execution.get_result(node2.id)
        assert node2_result is not None
        assert "$prev" in node2_result.data["context_keys"]
        assert "$nodes" in node2_result.data["context_keys"]

    async def test_trigger_data_in_context(self, executor):
        """Test that trigger data is available in context."""
        node = WorkflowNode(type="mock_success", name="Node1")
        workflow = Workflow(name="Trigger", nodes=[node])

        trigger_data = {"user_id": 123, "source": "api"}
        execution = await executor.execute(
            workflow,
            trigger_data=trigger_data,
            trigger_type="webhook",
        )

        assert execution.trigger_type == "webhook"
        assert execution.trigger_data == trigger_data

        result = execution.get_result(node.id)
        assert "$trigger" in result.data["context_keys"]

    async def test_workflow_variables(self, executor):
        """Test that workflow variables are available."""
        node = WorkflowNode(type="mock_success", name="Node1")
        workflow = Workflow(
            name="Variables",
            nodes=[node],
            variables={"api_url": "https://api.example.com", "timeout": 30},
        )

        execution = await executor.execute(workflow)

        result = execution.get_result(node.id)
        assert "$vars" in result.data["context_keys"]

    async def test_node_execution_error_stop_strategy(self, executor):
        """Test error handling with stop strategy."""
        node1 = WorkflowNode(type="mock_success", name="Node1")
        node2 = WorkflowNode(
            type="mock_fail",
            name="Node2",
            config={"on_error": "stop"},
        )
        node3 = WorkflowNode(type="mock_success", name="Node3")

        workflow = Workflow(
            name="ErrorStop",
            nodes=[node1, node2, node3],
            connections=[
                WorkflowConnection(source_node_id=node1.id, target_node_id=node2.id),
                WorkflowConnection(source_node_id=node2.id, target_node_id=node3.id),
            ],
        )

        execution = await executor.execute(workflow)

        assert execution.status == "failed"
        assert execution.error is not None
        # Node1 should succeed, Node2 should fail, Node3 should not execute
        assert len(execution.node_results) == 2
        assert execution.node_results[0].success is True
        assert execution.node_results[1].success is False

    async def test_node_execution_error_continue_strategy(self, executor):
        """Test error handling with continue strategy."""
        node1 = WorkflowNode(type="mock_success", name="Node1")
        node2 = WorkflowNode(
            type="mock_fail",
            name="Node2",
            config={"on_error": "continue"},
        )
        node3 = WorkflowNode(type="mock_success", name="Node3")

        workflow = Workflow(
            name="ErrorContinue",
            nodes=[node1, node2, node3],
            connections=[
                WorkflowConnection(source_node_id=node1.id, target_node_id=node2.id),
                WorkflowConnection(source_node_id=node2.id, target_node_id=node3.id),
            ],
        )

        execution = await executor.execute(workflow)

        # Should complete despite node2 failing
        assert execution.status == "completed"
        # All 3 nodes should have executed
        assert len(execution.node_results) == 3
        assert execution.node_results[0].success is True
        assert execution.node_results[1].success is False
        assert execution.node_results[2].success is True

    async def test_disabled_node_skipped(self, executor):
        """Test that disabled nodes are skipped."""
        node1 = WorkflowNode(type="mock_success", name="Node1")
        node2 = WorkflowNode(type="mock_success", name="Node2", enabled=False)
        node3 = WorkflowNode(type="mock_success", name="Node3")

        workflow = Workflow(
            name="Disabled",
            nodes=[node1, node2, node3],
            connections=[
                WorkflowConnection(source_node_id=node1.id, target_node_id=node2.id),
                WorkflowConnection(source_node_id=node2.id, target_node_id=node3.id),
            ],
        )

        execution = await executor.execute(workflow)

        assert execution.status == "completed"
        # Only node1 and node3 should have results
        assert len(execution.node_results) == 2
        result_node_ids = [r.node_id for r in execution.node_results]
        assert node1.id in result_node_ids
        assert node2.id not in result_node_ids
        assert node3.id in result_node_ids

    async def test_execution_timing(self, executor):
        """Test that execution timing is recorded."""
        node = WorkflowNode(type="mock_success", name="Node1")
        workflow = Workflow(name="Timing", nodes=[node])

        execution = await executor.execute(workflow)

        assert execution.started_at is not None
        assert execution.completed_at is not None
        assert execution.duration_ms > 0
        assert execution.completed_at > execution.started_at

        result = execution.get_result(node.id)
        assert result.duration_ms >= 0
        assert result.started_at is not None
        assert result.completed_at is not None

    async def test_unknown_node_type_error(self, executor):
        """Test error when node type is not registered."""
        node = WorkflowNode(type="unknown_type", name="Unknown")
        workflow = Workflow(name="Unknown", nodes=[node])

        execution = await executor.execute(workflow)

        assert execution.status == "failed"
        assert "Unknown node type" in execution.error or execution.error is not None


@pytest.mark.asyncio
class TestDebugExecutor:
    """Tests for DebugExecutor."""

    async def test_breakpoint_pauses_execution(self):
        """Test that breakpoints pause execution."""
        executor = DebugExecutor()
        executor.node_registry._handlers["mock_success"] = MockSuccessNode

        node1 = WorkflowNode(type="mock_success", name="Node1")
        node2 = WorkflowNode(type="mock_success", name="Node2")

        workflow = Workflow(
            name="Debug",
            nodes=[node1, node2],
            connections=[
                WorkflowConnection(source_node_id=node1.id, target_node_id=node2.id),
            ],
        )

        # Set breakpoint on node2
        executor.set_breakpoint(node2.id)

        # Start execution in background
        task = asyncio.create_task(executor.execute(workflow))

        # Give it time to hit the breakpoint
        await asyncio.sleep(0.1)

        # Should be paused
        assert executor.paused is True

        # Resume
        executor.resume()

        # Wait for completion
        execution = await task

        assert execution.status == "completed"
        assert len(execution.node_results) == 2

    async def test_step_mode(self):
        """Test step mode execution."""
        executor = DebugExecutor()
        executor.node_registry._handlers["mock_success"] = MockSuccessNode

        node1 = WorkflowNode(type="mock_success", name="Node1")
        node2 = WorkflowNode(type="mock_success", name="Node2")

        workflow = Workflow(
            name="Step",
            nodes=[node1, node2],
            connections=[
                WorkflowConnection(source_node_id=node1.id, target_node_id=node2.id),
            ],
        )

        # Enable step mode
        executor.step_mode = True

        # Start execution
        task = asyncio.create_task(executor.execute(workflow))

        # Give time for first node
        await asyncio.sleep(0.1)
        assert executor.paused is True

        # Step to next
        executor.step()
        await asyncio.sleep(0.1)

        # Should be paused again
        assert executor.paused is True

        # Step to complete
        executor.step()
        execution = await task

        assert execution.status == "completed"

    async def test_remove_breakpoint(self):
        """Test removing breakpoints."""
        executor = DebugExecutor()

        executor.set_breakpoint("node1")
        assert "node1" in executor.breakpoints

        executor.remove_breakpoint("node1")
        assert "node1" not in executor.breakpoints
