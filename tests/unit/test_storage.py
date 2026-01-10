"""
Unit Tests for Storage Layer

Tests for WorkflowStorage class.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.data.storage import WorkflowStorage
from src.core.workflow.models import (
    Workflow,
    WorkflowNode,
    WorkflowExecution,
    ExecutionResult,
)


@pytest.fixture
def temp_storage():
    """Create a temporary storage instance for testing."""
    temp_dir = tempfile.mkdtemp()
    storage = WorkflowStorage(data_dir=temp_dir)
    yield storage
    # Cleanup
    shutil.rmtree(temp_dir)


class TestWorkflowStorage:
    """Tests for workflow storage operations."""

    def test_storage_initialization(self, temp_storage):
        """Test that storage initializes correctly."""
        assert temp_storage.data_dir.exists()
        assert temp_storage.workflows_dir.exists()
        assert temp_storage.db_path.exists()

    def test_save_workflow(self, temp_storage):
        """Test saving a workflow."""
        workflow = Workflow(
            name="Test Workflow",
            description="A test",
            nodes=[
                WorkflowNode(type="manual_trigger", name="Start"),
                WorkflowNode(type="http_request", name="API"),
            ],
            tags=["test", "automation"],
        )

        file_path = temp_storage.save_workflow(workflow)

        assert Path(file_path).exists()
        assert workflow.name.replace(" ", "_") in file_path

    def test_load_workflow(self, temp_storage):
        """Test loading a saved workflow."""
        # Create and save
        original = Workflow(
            name="Load Test",
            description="Test loading",
            nodes=[WorkflowNode(type="manual_trigger", name="Start")],
            variables={"api_key": "secret"},
        )

        temp_storage.save_workflow(original)

        # Load
        loaded = temp_storage.load_workflow(original.id)

        assert loaded is not None
        assert loaded.id == original.id
        assert loaded.name == original.name
        assert loaded.description == original.description
        assert len(loaded.nodes) == 1
        assert loaded.variables["api_key"] == "secret"

    def test_load_nonexistent_workflow(self, temp_storage):
        """Test loading a workflow that doesn't exist."""
        result = temp_storage.load_workflow("nonexistent_id")
        assert result is None

    def test_delete_workflow(self, temp_storage):
        """Test deleting a workflow."""
        workflow = Workflow(name="Delete Me")
        temp_storage.save_workflow(workflow)

        # Verify it exists
        loaded = temp_storage.load_workflow(workflow.id)
        assert loaded is not None

        # Delete
        result = temp_storage.delete_workflow(workflow.id)
        assert result is True

        # Verify it's gone
        loaded_after = temp_storage.load_workflow(workflow.id)
        assert loaded_after is None

    def test_delete_nonexistent_workflow(self, temp_storage):
        """Test deleting a workflow that doesn't exist."""
        result = temp_storage.delete_workflow("nonexistent_id")
        assert result is False

    def test_list_workflows(self, temp_storage):
        """Test listing all workflows."""
        # Create multiple workflows
        workflow1 = Workflow(name="First", description="First workflow")
        workflow2 = Workflow(name="Second", description="Second workflow", tags=["tag1"])
        workflow3 = Workflow(name="Third", tags=["tag2"])

        temp_storage.save_workflow(workflow1)
        temp_storage.save_workflow(workflow2)
        temp_storage.save_workflow(workflow3)

        # List all
        workflows = temp_storage.list_workflows()

        assert len(workflows) == 3
        names = [w["name"] for w in workflows]
        assert "First" in names
        assert "Second" in names
        assert "Third" in names

    def test_list_workflows_ordered_by_update(self, temp_storage):
        """Test that workflows are ordered by update time."""
        import time

        workflow1 = Workflow(name="Oldest")
        temp_storage.save_workflow(workflow1)

        time.sleep(0.1)

        workflow2 = Workflow(name="Newest")
        temp_storage.save_workflow(workflow2)

        workflows = temp_storage.list_workflows()

        # Should be ordered with newest first
        assert workflows[0]["name"] == "Newest"
        assert workflows[1]["name"] == "Oldest"

    def test_search_workflows(self, temp_storage):
        """Test searching workflows."""
        workflow1 = Workflow(name="API Integration", description="Connects to external API")
        workflow2 = Workflow(name="Data Processing", description="Processes CSV files")
        workflow3 = Workflow(name="Email API", description="Sends emails via API")

        temp_storage.save_workflow(workflow1)
        temp_storage.save_workflow(workflow2)
        temp_storage.save_workflow(workflow3)

        # Search for "API"
        results = temp_storage.search_workflows("API")

        assert len(results) == 2
        names = [r["name"] for r in results]
        assert "API Integration" in names
        assert "Email API" in names
        assert "Data Processing" not in names

    def test_workflow_metadata_includes_timestamps(self, temp_storage):
        """Test that workflow metadata includes timestamps."""
        workflow = Workflow(name="Timestamped")
        temp_storage.save_workflow(workflow)

        workflows = temp_storage.list_workflows()
        assert len(workflows) == 1

        metadata = workflows[0]
        assert "created_at" in metadata
        assert "updated_at" in metadata
        assert metadata["created_at"] is not None
        assert metadata["updated_at"] is not None


class TestExecutionHistory:
    """Tests for execution history storage."""

    def test_save_execution(self, temp_storage):
        """Test saving an execution record."""
        execution = WorkflowExecution(
            workflow_id="workflow123",
            status="completed",
            trigger_type="manual",
            trigger_data={"user": "admin"},
        )

        result1 = ExecutionResult(
            node_id="node1",
            success=True,
            data={"output": "success"},
            duration_ms=150,
        )
        execution.add_result(result1)

        execution_id = temp_storage.save_execution(execution)

        assert execution_id == execution.id

    def test_get_executions_all(self, temp_storage):
        """Test getting all executions."""
        # Save workflow first
        workflow = Workflow(name="Test Workflow")
        temp_storage.save_workflow(workflow)

        # Create executions
        exec1 = WorkflowExecution(workflow_id=workflow.id, status="completed")
        exec2 = WorkflowExecution(workflow_id=workflow.id, status="failed")

        temp_storage.save_execution(exec1)
        temp_storage.save_execution(exec2)

        # Get all
        executions = temp_storage.get_executions()

        assert len(executions) >= 2
        statuses = [e["status"] for e in executions]
        assert "completed" in statuses
        assert "failed" in statuses

    def test_get_executions_by_workflow(self, temp_storage):
        """Test getting executions filtered by workflow."""
        workflow1 = Workflow(name="Workflow 1")
        workflow2 = Workflow(name="Workflow 2")
        temp_storage.save_workflow(workflow1)
        temp_storage.save_workflow(workflow2)

        exec1 = WorkflowExecution(workflow_id=workflow1.id, status="completed")
        exec2 = WorkflowExecution(workflow_id=workflow1.id, status="completed")
        exec3 = WorkflowExecution(workflow_id=workflow2.id, status="completed")

        temp_storage.save_execution(exec1)
        temp_storage.save_execution(exec2)
        temp_storage.save_execution(exec3)

        # Get executions for workflow1
        executions = temp_storage.get_executions(workflow_id=workflow1.id)

        assert len(executions) == 2
        assert all(e["workflow_id"] == workflow1.id for e in executions)

    def test_get_executions_with_limit(self, temp_storage):
        """Test execution limit parameter."""
        workflow = Workflow(name="Test")
        temp_storage.save_workflow(workflow)

        # Create 10 executions
        for i in range(10):
            exec_i = WorkflowExecution(workflow_id=workflow.id, status="completed")
            temp_storage.save_execution(exec_i)

        # Get only 5
        executions = temp_storage.get_executions(limit=5)

        assert len(executions) == 5

    def test_execution_includes_workflow_name(self, temp_storage):
        """Test that execution records include workflow name."""
        workflow = Workflow(name="Named Workflow")
        temp_storage.save_workflow(workflow)

        execution = WorkflowExecution(workflow_id=workflow.id, status="completed")
        temp_storage.save_execution(execution)

        executions = temp_storage.get_executions(workflow_id=workflow.id)

        assert len(executions) == 1
        assert executions[0]["workflow_name"] == "Named Workflow"


class TestSettings:
    """Tests for settings storage."""

    def test_set_and_get_setting(self, temp_storage):
        """Test setting and getting a setting."""
        temp_storage.set_setting("theme", "dark")

        value = temp_storage.get_setting("theme")

        assert value == "dark"

    def test_get_nonexistent_setting(self, temp_storage):
        """Test getting a setting that doesn't exist."""
        value = temp_storage.get_setting("nonexistent")

        assert value is None

    def test_get_setting_with_default(self, temp_storage):
        """Test getting a setting with default value."""
        value = temp_storage.get_setting("nonexistent", default="default_value")

        assert value == "default_value"

    def test_update_setting(self, temp_storage):
        """Test updating an existing setting."""
        temp_storage.set_setting("language", "en")
        assert temp_storage.get_setting("language") == "en"

        temp_storage.set_setting("language", "es")
        assert temp_storage.get_setting("language") == "es"

    def test_multiple_settings(self, temp_storage):
        """Test storing multiple settings."""
        temp_storage.set_setting("theme", "dark")
        temp_storage.set_setting("language", "en")
        temp_storage.set_setting("auto_save", "true")

        assert temp_storage.get_setting("theme") == "dark"
        assert temp_storage.get_setting("language") == "en"
        assert temp_storage.get_setting("auto_save") == "true"
