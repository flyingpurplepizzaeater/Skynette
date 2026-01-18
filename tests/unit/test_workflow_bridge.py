# tests/unit/test_workflow_bridge.py
"""Unit tests for WorkflowBridge service."""

import pytest
from unittest.mock import MagicMock, patch

from src.core.workflow.models import Workflow, WorkflowNode, WorkflowConnection
from src.ui.views.code_editor.workflow_bridge import WorkflowBridge, WorkflowFormat


class TestWorkflowBridge:
    """Tests for WorkflowBridge service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.workflow = Workflow(
            id="test-workflow-123",
            name="Test Workflow",
            description="A test workflow",
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
            variables={"api_key": "secret"},
            tags=["test", "automation"],
        )

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_load_as_yaml(self, mock_get_storage):
        """Loading workflow as YAML returns valid YAML."""
        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = self.workflow
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        code = bridge.load_as_code("test-workflow-123", WorkflowFormat.YAML)

        assert code is not None
        assert "Test Workflow" in code
        assert "manual_trigger" in code
        assert "http_request" in code
        mock_storage.load_workflow.assert_called_once_with("test-workflow-123")

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_load_as_json(self, mock_get_storage):
        """Loading workflow as JSON returns valid JSON."""
        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = self.workflow
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        code = bridge.load_as_code("test-workflow-123", WorkflowFormat.JSON)

        assert code is not None
        assert '"name": "Test Workflow"' in code
        assert '"type": "manual_trigger"' in code

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_load_as_python_dsl(self, mock_get_storage):
        """Loading workflow as Python DSL returns valid DSL."""
        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = self.workflow
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        code = bridge.load_as_code("test-workflow-123", WorkflowFormat.PYTHON_DSL)

        assert code is not None
        assert 'Workflow(name="Test Workflow")' in code
        assert 'add_node("manual_trigger"' in code
        assert "workflow.connect(" in code

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_load_nonexistent_workflow(self, mock_get_storage):
        """Loading nonexistent workflow returns None."""
        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = None
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        code = bridge.load_as_code("nonexistent", WorkflowFormat.YAML)

        assert code is None

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_save_from_yaml(self, mock_get_storage):
        """Saving from YAML code updates workflow."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        yaml_code = """
name: Updated Workflow
description: Updated description
nodes:
  - id: node-1
    type: manual_trigger
    name: Start
    position:
      x: 0
      y: 0
    config: {}
    enabled: true
connections: []
variables: {}
settings: {}
tags: []
version: "1.0.0"
"""
        success, error = bridge.save_from_code(
            "workflow-id", yaml_code, WorkflowFormat.YAML
        )

        assert success is True
        assert error == ""
        mock_storage.save_workflow.assert_called_once()
        saved_workflow = mock_storage.save_workflow.call_args[0][0]
        assert saved_workflow.id == "workflow-id"  # ID preserved
        assert saved_workflow.name == "Updated Workflow"

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_save_from_json(self, mock_get_storage):
        """Saving from JSON code updates workflow."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        json_code = """{
            "name": "JSON Workflow",
            "description": "",
            "version": "1.0.0",
            "nodes": [],
            "connections": [],
            "variables": {},
            "settings": {},
            "tags": []
        }"""
        success, error = bridge.save_from_code(
            "workflow-id", json_code, WorkflowFormat.JSON
        )

        assert success is True
        assert error == ""
        saved_workflow = mock_storage.save_workflow.call_args[0][0]
        assert saved_workflow.name == "JSON Workflow"

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_save_invalid_yaml(self, mock_get_storage):
        """Saving invalid YAML returns error without throwing."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        invalid_yaml = """
name: "Unclosed string
nodes: [[[
"""
        success, error = bridge.save_from_code(
            "workflow-id", invalid_yaml, WorkflowFormat.YAML
        )

        assert success is False
        assert "Invalid YAML" in error or "YAML" in error.upper()
        mock_storage.save_workflow.assert_not_called()

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_save_invalid_json(self, mock_get_storage):
        """Saving invalid JSON returns error without throwing."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        invalid_json = '{"name": "Test", invalid}'
        success, error = bridge.save_from_code(
            "workflow-id", invalid_json, WorkflowFormat.JSON
        )

        assert success is False
        assert "Invalid JSON" in error or "JSON" in error.upper()
        mock_storage.save_workflow.assert_not_called()

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_save_empty_yaml(self, mock_get_storage):
        """Saving empty YAML returns error."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        success, error = bridge.save_from_code("workflow-id", "", WorkflowFormat.YAML)

        assert success is False
        assert "Empty" in error or "empty" in error
        mock_storage.save_workflow.assert_not_called()

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_convert_yaml_to_json(self, mock_get_storage):
        """Converting YAML to JSON works correctly."""
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
    def test_listener_notified_on_save(self, mock_get_storage):
        """Listeners are notified when workflow is saved."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        listener_calls = []
        bridge.add_listener(lambda wid: listener_calls.append(wid))

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

        assert len(listener_calls) == 1
        assert listener_calls[0] == "workflow-123"

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_remove_listener(self, mock_get_storage):
        """Removed listeners are not notified."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        listener_calls = []
        listener = lambda wid: listener_calls.append(wid)
        bridge.add_listener(listener)
        bridge.remove_listener(listener)

        yaml_code = """
name: No Notify Test
version: "1.0.0"
nodes: []
connections: []
variables: {}
settings: {}
tags: []
"""
        bridge.save_from_code("workflow-123", yaml_code, WorkflowFormat.YAML)

        assert len(listener_calls) == 0

    @patch("src.ui.views.code_editor.workflow_bridge.get_storage")
    def test_get_workflow_name(self, mock_get_storage):
        """Getting workflow name returns correct name."""
        mock_storage = MagicMock()
        mock_storage.load_workflow.return_value = self.workflow
        mock_get_storage.return_value = mock_storage

        bridge = WorkflowBridge()
        name = bridge.get_workflow_name("test-workflow-123")

        assert name == "Test Workflow"


class TestWorkflowPythonDSL:
    """Tests for Workflow Python DSL methods."""

    def test_to_python_dsl_basic(self):
        """Basic workflow converts to Python DSL."""
        workflow = Workflow(
            name="Simple Workflow",
            description="A simple test",
            nodes=[
                WorkflowNode(id="n1", type="manual_trigger", name="Start"),
            ],
        )

        dsl = workflow.to_python_dsl()

        assert 'Workflow(name="Simple Workflow")' in dsl
        assert 'workflow.description = "A simple test"' in dsl
        assert 'add_node("manual_trigger"' in dsl

    def test_to_python_dsl_with_connections(self):
        """Workflow with connections includes connect calls."""
        workflow = Workflow(
            name="Connected",
            nodes=[
                WorkflowNode(id="n1", type="manual_trigger", name="Start"),
                WorkflowNode(id="n2", type="http_request", name="API"),
            ],
            connections=[
                WorkflowConnection(source_node_id="n1", target_node_id="n2"),
            ],
        )

        dsl = workflow.to_python_dsl()

        assert 'workflow.connect("n1", "n2")' in dsl

    def test_to_python_dsl_with_variables(self):
        """Workflow with variables includes variable assignments."""
        workflow = Workflow(
            name="Variables Test",
            variables={"key": "value", "count": 5},
        )

        dsl = workflow.to_python_dsl()

        assert 'workflow.variables["key"] = "value"' in dsl
        assert 'workflow.variables["count"] = 5' in dsl

    def test_to_python_dsl_with_tags(self):
        """Workflow with tags includes tags list."""
        workflow = Workflow(
            name="Tagged",
            tags=["test", "automation"],
        )

        dsl = workflow.to_python_dsl()

        assert "workflow.tags = " in dsl

    def test_from_python_dsl_basic(self):
        """Basic Python DSL parses to workflow."""
        dsl = '''
workflow = Workflow(name="From DSL")
workflow.description = "Created from DSL"
'''
        workflow = Workflow.from_python_dsl(dsl)

        assert workflow.name == "From DSL"
        assert workflow.description == "Created from DSL"

    def test_from_python_dsl_with_nodes(self):
        """Python DSL with nodes creates workflow with nodes."""
        dsl = '''
workflow = Workflow(name="With Nodes")
workflow.add_node("manual_trigger", name="Start", id="n1")
workflow.add_node("http_request", name="API", id="n2")
'''
        workflow = Workflow.from_python_dsl(dsl)

        assert len(workflow.nodes) == 2
        assert workflow.nodes[0].type == "manual_trigger"
        assert workflow.nodes[0].name == "Start"
        assert workflow.nodes[1].type == "http_request"

    def test_from_python_dsl_with_connections(self):
        """Python DSL with connections creates workflow with connections."""
        dsl = '''
workflow = Workflow(name="Connected")
workflow.add_node("manual_trigger", name="Start", id="n1")
workflow.add_node("http_request", name="API", id="n2")
workflow.connect("n1", "n2")
'''
        workflow = Workflow.from_python_dsl(dsl)

        assert len(workflow.connections) == 1
        assert workflow.connections[0].source_node_id == "n1"
        assert workflow.connections[0].target_node_id == "n2"

    def test_from_python_dsl_with_variables(self):
        """Python DSL with variables creates workflow with variables."""
        dsl = '''
workflow = Workflow(name="With Vars")
workflow.variables["api_key"] = "secret"
workflow.variables["count"] = 10
'''
        workflow = Workflow.from_python_dsl(dsl)

        assert workflow.variables["api_key"] == "secret"
        assert workflow.variables["count"] == 10

    def test_from_python_dsl_invalid(self):
        """Invalid Python DSL raises ValueError."""
        dsl = "This is not valid Python"

        with pytest.raises(ValueError) as exc:
            Workflow.from_python_dsl(dsl)

        assert "Invalid Python DSL" in str(exc.value)

    def test_from_python_dsl_restricted_exec(self):
        """Python DSL exec is restricted (no imports, etc)."""
        dsl = '''
import os
workflow = Workflow(name="Malicious")
'''
        with pytest.raises(ValueError):
            Workflow.from_python_dsl(dsl)

    def test_roundtrip_yaml(self):
        """Workflow survives YAML roundtrip."""
        original = Workflow(
            name="Roundtrip Test",
            description="Testing roundtrip",
            nodes=[
                WorkflowNode(id="n1", type="manual_trigger", name="Start"),
                WorkflowNode(id="n2", type="http_request", name="API"),
            ],
            connections=[
                WorkflowConnection(source_node_id="n1", target_node_id="n2"),
            ],
            tags=["test"],
        )

        yaml_code = original.to_yaml()
        restored = Workflow.from_yaml(yaml_code)

        assert restored.name == original.name
        assert restored.description == original.description
        assert len(restored.nodes) == len(original.nodes)
        assert len(restored.connections) == len(original.connections)
