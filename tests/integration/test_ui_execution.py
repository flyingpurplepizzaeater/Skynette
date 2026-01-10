"""
Integration Tests for UI Workflow Execution

Tests the integration between UI layer and WorkflowExecutor for workflow execution.
"""

import pytest
from pathlib import Path

from src.core.workflow.models import Workflow, WorkflowNode, WorkflowConnection
from src.core.workflow.executor import WorkflowExecutor
from src.data.storage import WorkflowStorage


@pytest.fixture
def storage(temp_data_dir: Path) -> WorkflowStorage:
    """Create a WorkflowStorage instance with temp directory."""
    return WorkflowStorage(data_dir=str(temp_data_dir))


@pytest.fixture
def executor() -> WorkflowExecutor:
    """Create a WorkflowExecutor instance."""
    return WorkflowExecutor()


@pytest.fixture
def simple_workflow() -> Workflow:
    """Create a simple workflow for execution testing."""
    workflow = Workflow(
        name="Simple Execution Test",
        description="A simple workflow for execution testing",
        variables={"counter": 0},
    )

    # Manual trigger
    trigger = WorkflowNode(
        id="trigger-1",
        type="manual_trigger",
        name="Start",
        position={"x": 100, "y": 100},
        config={"test_data": {"user_id": 123, "action": "test"}},
    )

    # Set variable
    set_var = WorkflowNode(
        id="set-1",
        type="set_variable",
        name="Set Counter",
        position={"x": 300, "y": 100},
        config={"variable_name": "counter", "value": 42},
    )

    # Log debug
    log = WorkflowNode(
        id="log-1",
        type="log_debug",
        name="Log Result",
        position={"x": 500, "y": 100},
        config={"message": "Counter is: {{$vars.counter}}"},
    )

    workflow.nodes = [trigger, set_var, log]

    # Add connections
    workflow.connections = [
        WorkflowConnection(source_node_id="trigger-1", target_node_id="set-1"),
        WorkflowConnection(source_node_id="set-1", target_node_id="log-1"),
    ]

    return workflow


@pytest.fixture
def complex_workflow() -> Workflow:
    """Create a complex multi-node workflow."""
    workflow = Workflow(
        name="Complex Multi-Node Workflow",
        description="Tests complex execution paths with multiple nodes",
        variables={"status": "pending", "count": 0},
    )

    # Manual trigger
    trigger = WorkflowNode(
        id="trigger-1",
        type="manual_trigger",
        name="Start",
        position={"x": 100, "y": 100},
        config={"test_data": {"user_id": 123}},
    )

    # Set first variable
    set_status = WorkflowNode(
        id="set-1",
        type="set_variable",
        name="Set Status",
        position={"x": 300, "y": 100},
        config={"variable_name": "status", "value": "processing"},
    )

    # Set second variable
    set_count = WorkflowNode(
        id="set-2",
        type="set_variable",
        name="Set Count",
        position={"x": 500, "y": 100},
        config={"variable_name": "count", "value": 10},
    )

    # Log intermediate result
    log_intermediate = WorkflowNode(
        id="log-1",
        type="log_debug",
        name="Log Intermediate",
        position={"x": 700, "y": 100},
        config={"message": "Status: {{$vars.status}}, Count: {{$vars.count}}"},
    )

    # Set final status
    set_final = WorkflowNode(
        id="set-3",
        type="set_variable",
        name="Set Final Status",
        position={"x": 900, "y": 100},
        config={"variable_name": "status", "value": "completed"},
    )

    # Log final result
    log_final = WorkflowNode(
        id="log-2",
        type="log_debug",
        name="Log Final",
        position={"x": 1100, "y": 100},
        config={"message": "Final status: {{$vars.status}}"},
    )

    workflow.nodes = [trigger, set_status, set_count, log_intermediate, set_final, log_final]

    # Add linear connections
    workflow.connections = [
        WorkflowConnection(source_node_id="trigger-1", target_node_id="set-1"),
        WorkflowConnection(source_node_id="set-1", target_node_id="set-2"),
        WorkflowConnection(source_node_id="set-2", target_node_id="log-1"),
        WorkflowConnection(source_node_id="log-1", target_node_id="set-3"),
        WorkflowConnection(source_node_id="set-3", target_node_id="log-2"),
    ]

    return workflow


class TestWorkflowExecution:
    """Integration tests for workflow execution."""

    @pytest.mark.asyncio
    async def test_simple_workflow_execution(
        self, storage: WorkflowStorage, executor: WorkflowExecutor, simple_workflow: Workflow
    ):
        """Test executing a simple workflow and verifying results."""
        # Save workflow
        storage.save_workflow(simple_workflow)

        # Execute workflow
        execution = await executor.execute(simple_workflow)

        # Verify execution completed successfully
        assert execution.status == "completed"
        assert execution.error is None
        assert execution.completed_at is not None
        assert execution.duration_ms > 0

        # Verify all nodes executed
        assert len(execution.node_results) == 3

        # Verify node execution order
        assert execution.node_results[0].node_id == "trigger-1"
        assert execution.node_results[1].node_id == "set-1"
        assert execution.node_results[2].node_id == "log-1"

        # Verify all nodes succeeded
        for result in execution.node_results:
            assert result.success is True
            assert result.error is None
            assert result.completed_at is not None

        # Save execution history
        storage.save_execution(execution)

        # Verify execution is in history
        history = storage.get_executions(workflow_id=simple_workflow.id)
        assert len(history) == 1
        assert history[0]["status"] == "completed"
        assert history[0]["workflow_id"] == simple_workflow.id

        # Clean up
        storage.delete_workflow(simple_workflow.id)

    @pytest.mark.asyncio
    async def test_execution_history_persistence(
        self, storage: WorkflowStorage, executor: WorkflowExecutor, simple_workflow: Workflow
    ):
        """Test that execution history is properly persisted."""
        # Save workflow
        storage.save_workflow(simple_workflow)

        # Execute workflow multiple times
        executions = []
        for i in range(3):
            execution = await executor.execute(
                simple_workflow,
                trigger_data={"run": i + 1},
            )
            storage.save_execution(execution)
            executions.append(execution)

        # Get execution history
        history = storage.get_executions(workflow_id=simple_workflow.id)

        # Verify count
        assert len(history) == 3

        # Verify they're sorted by started_at DESC (most recent first)
        assert history[0]["id"] == executions[2].id
        assert history[1]["id"] == executions[1].id
        assert history[2]["id"] == executions[0].id

        # Verify all required fields are present
        for exec_record in history:
            assert "id" in exec_record
            assert "workflow_id" in exec_record
            assert "workflow_name" in exec_record
            assert "status" in exec_record
            assert "trigger_type" in exec_record
            assert "started_at" in exec_record
            assert "completed_at" in exec_record
            assert "duration_ms" in exec_record
            assert exec_record["workflow_name"] == "Simple Execution Test"

        # Get all executions (not filtered by workflow)
        all_history = storage.get_executions()
        assert len(all_history) >= 3

        # Clean up
        storage.delete_workflow(simple_workflow.id)

    @pytest.mark.asyncio
    async def test_complex_workflow_execution(
        self, storage: WorkflowStorage, executor: WorkflowExecutor, complex_workflow: Workflow
    ):
        """Test executing a complex multi-node workflow with multiple variables and steps."""
        # Save workflow
        storage.save_workflow(complex_workflow)

        # Execute workflow
        execution = await executor.execute(complex_workflow)

        # Verify execution completed successfully
        assert execution.status == "completed"
        assert execution.error is None

        # Verify all nodes executed in order (6 nodes total)
        assert len(execution.node_results) == 6

        # Verify node execution order
        node_ids_executed = [r.node_id for r in execution.node_results]
        assert node_ids_executed[0] == "trigger-1"
        assert node_ids_executed[1] == "set-1"
        assert node_ids_executed[2] == "set-2"
        assert node_ids_executed[3] == "log-1"
        assert node_ids_executed[4] == "set-3"
        assert node_ids_executed[5] == "log-2"

        # Verify all nodes succeeded
        for result in execution.node_results:
            assert result.success is True
            assert result.error is None

        # Save execution
        storage.save_execution(execution)

        # Execute again with different trigger data
        execution2 = await executor.execute(
            complex_workflow,
            trigger_data={"user_id": 456},
        )

        # Verify second execution also completed
        assert execution2.status == "completed"
        storage.save_execution(execution2)

        # Verify both executions are in history
        history = storage.get_executions(workflow_id=complex_workflow.id)
        assert len(history) == 2

        # Clean up
        storage.delete_workflow(complex_workflow.id)


class TestWorkflowExecutionEdgeCases:
    """Integration tests for workflow execution edge cases."""

    @pytest.mark.asyncio
    async def test_empty_workflow_execution(
        self, storage: WorkflowStorage, executor: WorkflowExecutor
    ):
        """Test executing a workflow with no nodes."""
        workflow = Workflow(
            name="Empty Workflow",
            description="A workflow with no nodes",
        )

        # Save workflow
        storage.save_workflow(workflow)

        # Execute workflow
        execution = await executor.execute(workflow)

        # Verify execution completed (nothing to do)
        assert execution.status == "completed"
        assert len(execution.node_results) == 0

        # Clean up
        storage.delete_workflow(workflow.id)

    @pytest.mark.asyncio
    async def test_disabled_node_skipped(
        self, storage: WorkflowStorage, executor: WorkflowExecutor
    ):
        """Test that disabled nodes are skipped during execution."""
        workflow = Workflow(
            name="Disabled Node Test",
            description="Tests that disabled nodes are skipped",
        )

        # Manual trigger
        trigger = WorkflowNode(
            id="trigger-1",
            type="manual_trigger",
            name="Start",
            position={"x": 100, "y": 100},
        )

        # Disabled set variable
        set_var = WorkflowNode(
            id="set-1",
            type="set_variable",
            name="Set Variable",
            position={"x": 300, "y": 100},
            config={"variable_name": "test", "value": "disabled"},
            enabled=False,  # Disabled
        )

        # Log debug
        log = WorkflowNode(
            id="log-1",
            type="log_debug",
            name="Log",
            position={"x": 500, "y": 100},
            config={"message": "Test"},
        )

        workflow.nodes = [trigger, set_var, log]
        workflow.connections = [
            WorkflowConnection(source_node_id="trigger-1", target_node_id="set-1"),
            WorkflowConnection(source_node_id="set-1", target_node_id="log-1"),
        ]

        # Save and execute
        storage.save_workflow(workflow)
        execution = await executor.execute(workflow)

        # Verify execution completed
        assert execution.status == "completed"

        # Verify disabled node was skipped
        node_ids_executed = [r.node_id for r in execution.node_results]
        assert "trigger-1" in node_ids_executed
        assert "set-1" not in node_ids_executed  # Skipped because disabled
        assert "log-1" in node_ids_executed

        # Clean up
        storage.delete_workflow(workflow.id)

    @pytest.mark.asyncio
    async def test_execution_with_trigger_data(
        self, storage: WorkflowStorage, executor: WorkflowExecutor
    ):
        """Test that trigger data is properly passed to workflow."""
        workflow = Workflow(
            name="Trigger Data Test",
            description="Tests trigger data passing",
        )

        # Manual trigger
        trigger = WorkflowNode(
            id="trigger-1",
            type="manual_trigger",
            name="Start",
            position={"x": 100, "y": 100},
        )

        # Log that references trigger data
        log = WorkflowNode(
            id="log-1",
            type="log_debug",
            name="Log Trigger Data",
            position={"x": 300, "y": 100},
            config={"message": "User: {{$trigger.username}}, Action: {{$trigger.action}}"},
        )

        workflow.nodes = [trigger, log]
        workflow.connections = [
            WorkflowConnection(source_node_id="trigger-1", target_node_id="log-1"),
        ]

        # Save and execute with custom trigger data
        storage.save_workflow(workflow)
        execution = await executor.execute(
            workflow,
            trigger_data={"username": "testuser", "action": "login"},
            trigger_type="manual",
        )

        # Verify execution completed
        assert execution.status == "completed"
        assert execution.trigger_type == "manual"
        assert execution.trigger_data["username"] == "testuser"
        assert execution.trigger_data["action"] == "login"

        # Save and verify in history
        storage.save_execution(execution)
        history = storage.get_executions(workflow_id=workflow.id)
        assert len(history) == 1
        assert history[0]["trigger_type"] == "manual"

        # Clean up
        storage.delete_workflow(workflow.id)
