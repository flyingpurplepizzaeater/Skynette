"""
Integration tests for workflow editing in code editor.

Tests the WorkflowBridge integration allowing workflows to be
edited as code (YAML, JSON, Python DSL) in the code editor.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.core.workflow.models import Workflow, WorkflowNode, WorkflowConnection
from src.ui.views.code_editor.workflow_bridge import WorkflowBridge, WorkflowFormat


class TestWorkflowLoadAsCode:
    """Tests for loading workflows as editable code."""

    @pytest.fixture
    def sample_workflow(self):
        """Create a sample workflow for testing."""
        return Workflow(
            id="test-workflow-id",
            name="Test Workflow",
            description="For testing code editor integration",
            nodes=[
                WorkflowNode(
                    id="node-1",
                    type="manual_trigger",
                    name="Start",
                ),
                WorkflowNode(
                    id="node-2",
                    type="http_request",
                    name="API Call",
                    config={"url": "https://api.example.com"},
                ),
            ],
            connections=[
                WorkflowConnection(
                    source_node_id="node-1",
                    target_node_id="node-2",
                ),
            ],
        )

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_workflow_load_as_yaml(self, mock_get_storage, sample_workflow):
        """Workflow can be loaded as YAML for editing."""
        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = sample_workflow
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        yaml_code = bridge.load_as_code(sample_workflow.id, WorkflowFormat.YAML)

        assert yaml_code is not None
        assert "name: Test Workflow" in yaml_code
        assert "manual_trigger" in yaml_code
        assert "http_request" in yaml_code

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_workflow_load_as_json(self, mock_get_storage, sample_workflow):
        """Workflow can be loaded as JSON for editing."""
        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = sample_workflow
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        json_code = bridge.load_as_code(sample_workflow.id, WorkflowFormat.JSON)

        assert json_code is not None
        assert '"name": "Test Workflow"' in json_code
        assert '"type": "manual_trigger"' in json_code

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_workflow_load_as_python_dsl(self, mock_get_storage, sample_workflow):
        """Workflow can be loaded as Python DSL for editing."""
        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = sample_workflow
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        python_code = bridge.load_as_code(sample_workflow.id, WorkflowFormat.PYTHON_DSL)

        assert python_code is not None
        assert 'Workflow(name="Test Workflow")' in python_code
        assert 'add_node("manual_trigger"' in python_code


class TestWorkflowRoundtrip:
    """Tests for workflow roundtrip (load, modify, save)."""

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_yaml_roundtrip(self, mock_get_storage):
        """Workflow survives YAML roundtrip (load -> edit -> save)."""
        # Create original workflow
        original = Workflow(
            id="roundtrip-test",
            name="Original Name",
            description="Original description",
            nodes=[
                WorkflowNode(id="n1", type="manual_trigger", name="Start"),
            ],
        )

        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = original
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()

        # Load as YAML
        yaml_code = bridge.load_as_code(original.id, WorkflowFormat.YAML)
        assert yaml_code is not None

        # Modify YAML
        yaml_code = yaml_code.replace("Original Name", "Modified Name")

        # Save back
        success, error = bridge.save_from_code(original.id, yaml_code, WorkflowFormat.YAML)
        assert success, f"Save failed: {error}"

        # Verify save was called
        mock_storage.save_workflow.assert_called_once()

        # Check saved workflow has modified name
        saved_workflow = mock_storage.save_workflow.call_args[0][0]
        assert saved_workflow.name == "Modified Name"
        assert saved_workflow.id == original.id  # ID preserved

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_json_roundtrip(self, mock_get_storage):
        """Workflow survives JSON roundtrip."""
        original = Workflow(
            id="json-roundtrip",
            name="JSON Workflow",
            nodes=[],
        )

        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = original
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()

        # Load as JSON
        json_code = bridge.load_as_code(original.id, WorkflowFormat.JSON)

        # Modify JSON
        json_code = json_code.replace("JSON Workflow", "Modified JSON Workflow")

        # Save back
        success, error = bridge.save_from_code(original.id, json_code, WorkflowFormat.JSON)
        assert success, f"Save failed: {error}"

        saved_workflow = mock_storage.save_workflow.call_args[0][0]
        assert saved_workflow.name == "Modified JSON Workflow"


class TestWorkflowValidation:
    """Tests for workflow code validation."""

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    @patch("src.ui.views.code_editor.workflow_bridge.NodeRegistry")
    def test_validate_valid_workflow(self, mock_registry_class, mock_get_storage):
        """Valid workflow code passes validation."""
        mock_registry = MagicMock()
        mock_registry.node_types = ["manual_trigger"]
        mock_registry_class.return_value = mock_registry
        mock_get_storage.return_value = MagicMock()

        bridge = WorkflowBridge()
        yaml_code = """
name: Valid Workflow
version: "1.0.0"
nodes:
  - id: n1
    type: manual_trigger
    name: Start
    position: {x: 0, y: 0}
    config: {}
    enabled: true
connections: []
variables: {}
settings: {}
tags: []
"""
        errors = bridge.validate_code(yaml_code, WorkflowFormat.YAML)
        assert len(errors) == 0

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_validate_invalid_yaml(self, mock_get_storage):
        """Invalid YAML returns syntax error."""
        mock_get_storage.return_value = MagicMock()

        bridge = WorkflowBridge()
        errors = bridge.validate_code("invalid: yaml: :", WorkflowFormat.YAML)

        assert len(errors) > 0
        assert any("error" in e.lower() for e in errors)

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_validate_empty_workflow(self, mock_get_storage):
        """Empty YAML returns error."""
        mock_get_storage.return_value = MagicMock()

        bridge = WorkflowBridge()
        errors = bridge.validate_code("", WorkflowFormat.YAML)

        assert len(errors) > 0


class TestWorkflowChangeNotification:
    """Tests for workflow change notification."""

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_listener_notified_on_save(self, mock_get_storage):
        """Listeners are notified when workflow is saved."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        notifications = []
        bridge.add_listener(lambda wid: notifications.append(wid))

        yaml_code = """
name: Notify Test
version: "1.0.0"
nodes: []
connections: []
variables: {}
settings: {}
tags: []
"""
        bridge.save_from_code("workflow-123", yaml_code, WorkflowFormat.YAML)

        assert len(notifications) == 1
        assert notifications[0] == "workflow-123"

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_listener_not_notified_after_removal(self, mock_get_storage):
        """Removed listeners are not notified."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        notifications = []
        listener = lambda wid: notifications.append(wid)

        bridge.add_listener(listener)
        bridge.remove_listener(listener)

        yaml_code = """
name: No Notify
version: "1.0.0"
nodes: []
connections: []
variables: {}
settings: {}
tags: []
"""
        bridge.save_from_code("workflow-456", yaml_code, WorkflowFormat.YAML)

        assert len(notifications) == 0


class TestWorkflowFormatConversion:
    """Tests for converting between workflow formats."""

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_convert_yaml_to_json(self, mock_get_storage):
        """Can convert YAML to JSON."""
        mock_get_storage.return_value = MagicMock()

        bridge = WorkflowBridge()
        yaml_code = """
name: Convert Test
description: Testing conversion
version: "1.0.0"
nodes: []
connections: []
variables: {}
settings: {}
tags: []
"""
        result, error = bridge.convert_format(
            yaml_code, WorkflowFormat.YAML, WorkflowFormat.JSON
        )

        assert error == ""
        assert '"name": "Convert Test"' in result

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_convert_json_to_yaml(self, mock_get_storage):
        """Can convert JSON to YAML."""
        mock_get_storage.return_value = MagicMock()

        bridge = WorkflowBridge()
        json_code = """{
            "name": "JSON Source",
            "description": "",
            "version": "1.0.0",
            "nodes": [],
            "connections": [],
            "variables": {},
            "settings": {},
            "tags": []
        }"""
        result, error = bridge.convert_format(
            json_code, WorkflowFormat.JSON, WorkflowFormat.YAML
        )

        assert error == ""
        assert "name: JSON Source" in result


class TestCodeEditorWorkflowIntegration:
    """Integration tests for code editor workflow features."""

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_workflow_name_lookup(self, mock_get_storage):
        """Can look up workflow name for display."""
        workflow = Workflow(id="lookup-test", name="My Workflow")
        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = workflow
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        name = bridge.get_workflow_name("lookup-test")

        assert name == "My Workflow"

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_nonexistent_workflow_returns_none(self, mock_get_storage):
        """Nonexistent workflow returns None for name."""
        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = None
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        name = bridge.get_workflow_name("nonexistent")

        assert name is None
