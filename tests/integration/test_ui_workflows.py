"""
Integration Tests for UI Workflow CRUD Operations

Tests the integration between UI layer and WorkflowStorage for workflow management.
"""

import pytest
from pathlib import Path

from src.core.workflow.models import Workflow, WorkflowNode, WorkflowConnection
from src.data.storage import WorkflowStorage


@pytest.fixture
def storage(temp_data_dir: Path) -> WorkflowStorage:
    """Create a WorkflowStorage instance with temp directory."""
    return WorkflowStorage(data_dir=str(temp_data_dir))


@pytest.fixture
def sample_workflow() -> Workflow:
    """Create a sample workflow for testing."""
    workflow = Workflow(
        name="Test Workflow",
        description="A test workflow for integration testing",
        tags=["test", "integration"],
    )

    # Add nodes
    trigger = WorkflowNode(
        id="trigger-1",
        type="manual_trigger",
        name="Manual Trigger",
        position={"x": 100, "y": 100},
        config={"test_data": {"message": "Hello"}},
    )

    log = WorkflowNode(
        id="log-1",
        type="log_debug",
        name="Log Message",
        position={"x": 300, "y": 100},
        config={"message": "Workflow triggered: {{$trigger.message}}"},
    )

    workflow.nodes = [trigger, log]

    # Add connection
    connection = WorkflowConnection(
        source_node_id="trigger-1",
        target_node_id="log-1",
    )
    workflow.connections = [connection]

    return workflow


class TestWorkflowCRUD:
    """Integration tests for workflow CRUD operations."""

    def test_create_and_save_workflow(self, storage: WorkflowStorage, sample_workflow: Workflow):
        """Test creating and saving a new workflow."""
        # Save workflow
        file_path = storage.save_workflow(sample_workflow)

        # Verify file was created
        assert Path(file_path).exists()

        # Verify workflow appears in list
        workflows = storage.list_workflows()
        assert len(workflows) == 1
        assert workflows[0]["name"] == "Test Workflow"
        assert workflows[0]["description"] == "A test workflow for integration testing"
        assert "test" in workflows[0]["tags"]
        assert "integration" in workflows[0]["tags"]

        # Clean up
        storage.delete_workflow(sample_workflow.id)

    def test_list_workflows(self, storage: WorkflowStorage):
        """Test listing multiple workflows."""
        # Create multiple workflows
        workflows_to_create = [
            Workflow(name="Workflow 1", description="First workflow", tags=["tag1"]),
            Workflow(name="Workflow 2", description="Second workflow", tags=["tag2"]),
            Workflow(name="Workflow 3", description="Third workflow", tags=["tag3"]),
        ]

        created_ids = []
        for workflow in workflows_to_create:
            storage.save_workflow(workflow)
            created_ids.append(workflow.id)

        # List workflows
        listed = storage.list_workflows()

        # Verify count
        assert len(listed) == 3

        # Verify they're sorted by updated_at DESC (most recent first)
        assert listed[0]["name"] == "Workflow 3"
        assert listed[1]["name"] == "Workflow 2"
        assert listed[2]["name"] == "Workflow 1"

        # Verify all fields are present
        for workflow in listed:
            assert "id" in workflow
            assert "name" in workflow
            assert "description" in workflow
            assert "version" in workflow
            assert "tags" in workflow
            assert "created_at" in workflow
            assert "updated_at" in workflow

        # Clean up
        for workflow_id in created_ids:
            storage.delete_workflow(workflow_id)

    def test_update_workflow(self, storage: WorkflowStorage, sample_workflow: Workflow):
        """Test updating an existing workflow."""
        # Save initial version
        storage.save_workflow(sample_workflow)
        original_updated_at = sample_workflow.updated_at

        # Load and verify
        loaded = storage.load_workflow(sample_workflow.id)
        assert loaded is not None
        assert loaded.name == "Test Workflow"
        assert len(loaded.nodes) == 2

        # Update workflow
        sample_workflow.name = "Updated Workflow"
        sample_workflow.description = "Updated description"
        sample_workflow.tags.append("updated")

        # Add a new node
        new_node = WorkflowNode(
            id="set-var-1",
            type="set_variable",
            name="Set Variable",
            position={"x": 500, "y": 100},
            config={"variable": "result", "value": "complete"},
        )
        sample_workflow.nodes.append(new_node)

        # Save updated version
        storage.save_workflow(sample_workflow)

        # Load and verify changes
        loaded = storage.load_workflow(sample_workflow.id)
        assert loaded is not None
        assert loaded.name == "Updated Workflow"
        assert loaded.description == "Updated description"
        assert "updated" in loaded.tags
        assert len(loaded.nodes) == 3
        assert loaded.updated_at > original_updated_at

        # Verify new node exists
        new_node_loaded = loaded.get_node("set-var-1")
        assert new_node_loaded is not None
        assert new_node_loaded.name == "Set Variable"

        # Clean up
        storage.delete_workflow(sample_workflow.id)

    def test_delete_workflow(self, storage: WorkflowStorage, sample_workflow: Workflow):
        """Test deleting a workflow."""
        # Save workflow
        file_path = storage.save_workflow(sample_workflow)

        # Verify it exists
        assert Path(file_path).exists()
        workflows = storage.list_workflows()
        assert len(workflows) == 1

        # Delete workflow
        deleted = storage.delete_workflow(sample_workflow.id)
        assert deleted is True

        # Verify it's gone
        assert not Path(file_path).exists()
        workflows = storage.list_workflows()
        assert len(workflows) == 0

        # Verify load returns None
        loaded = storage.load_workflow(sample_workflow.id)
        assert loaded is None

        # Verify deleting again returns False
        deleted = storage.delete_workflow(sample_workflow.id)
        assert deleted is False


class TestWorkflowSearch:
    """Integration tests for workflow search functionality."""

    def test_search_workflows_by_name(self, storage: WorkflowStorage):
        """Test searching workflows by name."""
        # Create test workflows
        workflows = [
            Workflow(name="Data Processing Pipeline", description="Processes data"),
            Workflow(name="Email Notification", description="Sends emails"),
            Workflow(name="Data Export", description="Exports data to CSV"),
        ]

        created_ids = []
        for workflow in workflows:
            storage.save_workflow(workflow)
            created_ids.append(workflow.id)

        # Search for "data"
        results = storage.search_workflows("data")
        assert len(results) == 2
        result_names = [r["name"] for r in results]
        assert "Data Processing Pipeline" in result_names
        assert "Data Export" in result_names

        # Search for "email"
        results = storage.search_workflows("email")
        assert len(results) == 1
        assert results[0]["name"] == "Email Notification"

        # Clean up
        for workflow_id in created_ids:
            storage.delete_workflow(workflow_id)

    def test_search_workflows_by_description(self, storage: WorkflowStorage):
        """Test searching workflows by description."""
        # Create test workflows
        workflows = [
            Workflow(name="Pipeline A", description="Processes customer data daily"),
            Workflow(name="Pipeline B", description="Generates reports"),
            Workflow(name="Pipeline C", description="Processes transaction data"),
        ]

        created_ids = []
        for workflow in workflows:
            storage.save_workflow(workflow)
            created_ids.append(workflow.id)

        # Search for "processes"
        results = storage.search_workflows("processes")
        assert len(results) == 2

        # Search for "reports"
        results = storage.search_workflows("reports")
        assert len(results) == 1
        assert results[0]["name"] == "Pipeline B"

        # Clean up
        for workflow_id in created_ids:
            storage.delete_workflow(workflow_id)


class TestWorkflowYAMLPersistence:
    """Integration tests for YAML workflow persistence."""

    def test_workflow_yaml_roundtrip(self, storage: WorkflowStorage, sample_workflow: Workflow):
        """Test that workflows can be saved and loaded without data loss."""
        # Save workflow
        storage.save_workflow(sample_workflow)

        # Load workflow
        loaded = storage.load_workflow(sample_workflow.id)

        # Verify all fields match
        assert loaded.id == sample_workflow.id
        assert loaded.name == sample_workflow.name
        assert loaded.description == sample_workflow.description
        assert loaded.version == sample_workflow.version
        assert loaded.tags == sample_workflow.tags
        assert loaded.variables == sample_workflow.variables

        # Verify nodes
        assert len(loaded.nodes) == len(sample_workflow.nodes)
        for i, node in enumerate(loaded.nodes):
            original_node = sample_workflow.nodes[i]
            assert node.id == original_node.id
            assert node.type == original_node.type
            assert node.name == original_node.name
            assert node.position == original_node.position
            assert node.config == original_node.config

        # Verify connections
        assert len(loaded.connections) == len(sample_workflow.connections)
        for i, conn in enumerate(loaded.connections):
            original_conn = sample_workflow.connections[i]
            assert conn.source_node_id == original_conn.source_node_id
            assert conn.target_node_id == original_conn.target_node_id

        # Clean up
        storage.delete_workflow(sample_workflow.id)

    def test_workflow_with_complex_config(self, storage: WorkflowStorage):
        """Test workflow with complex node configurations."""
        workflow = Workflow(
            name="Complex Workflow",
            description="Tests complex configurations",
        )

        # Add node with nested config
        http_node = WorkflowNode(
            id="http-1",
            type="http_request",
            name="API Request",
            position={"x": 100, "y": 100},
            config={
                "method": "POST",
                "url": "https://api.example.com/data",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {{$vars.api_token}}",
                },
                "body": {
                    "user_id": "{{$trigger.user_id}}",
                    "action": "process",
                    "options": {
                        "retry": True,
                        "timeout": 30,
                        "validation": ["email", "phone"],
                    },
                },
            },
        )
        workflow.nodes.append(http_node)

        # Save and load
        storage.save_workflow(workflow)
        loaded = storage.load_workflow(workflow.id)

        # Verify complex config preserved
        assert loaded is not None
        http_loaded = loaded.get_node("http-1")
        assert http_loaded is not None
        assert http_loaded.config["method"] == "POST"
        assert http_loaded.config["headers"]["Content-Type"] == "application/json"
        assert http_loaded.config["body"]["options"]["retry"] is True
        assert http_loaded.config["body"]["options"]["validation"] == ["email", "phone"]

        # Clean up
        storage.delete_workflow(workflow.id)
