"""
Unit tests for the visual canvas editor implementation.

Tests the _build_canvas, _build_canvas_node, _calculate_node_positions,
and _select_canvas_node methods added in Sprint 2 Task 1.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.core.workflow.models import Workflow, WorkflowNode
from src.core.nodes.registry import NodeRegistry
from src.core.nodes.base import NodeDefinition


class MockPage:
    """Mock Flet Page object for testing."""
    def __init__(self):
        self.overlay = []
        self.snack_bar = None

    def update(self):
        pass

    def run_task(self, coro):
        pass


class TestCanvasEditor:
    """Tests for canvas editor functionality."""

    @pytest.fixture
    def mock_page(self):
        """Create a mock page."""
        return MockPage()

    @pytest.fixture
    def node_registry(self):
        """Create a node registry with test nodes loaded."""
        registry = NodeRegistry()
        # Use the auto-loaded nodes from the registry
        return registry

    @pytest.fixture
    def test_workflow(self):
        """Create a test workflow with nodes."""
        workflow = Workflow(
            name="Test Workflow",
            description="Test workflow for canvas editor",
        )

        # Add some nodes
        node1 = WorkflowNode(
            type="manual_trigger",
            name="Start",
            position={"x": 100, "y": 100}
        )
        node2 = WorkflowNode(
            type="http_request",
            name="Fetch Data",
            position={"x": 250, "y": 100}
        )
        node3 = WorkflowNode(
            type="http_request",
            name="Process",
            position={"x": 400, "y": 100}
        )

        workflow.nodes = [node1, node2, node3]
        return workflow

    def test_calculate_node_positions(self, mock_page, node_registry):
        """Test grid positioning calculation."""
        from src.ui.app import SkynetteApp

        # Create app instance
        app = SkynetteApp(mock_page)
        app.node_registry = node_registry

        # Create workflow with 6 nodes
        workflow = Workflow(name="Test", description="Test")
        for i in range(6):
            workflow.nodes.append(
                WorkflowNode(
                    type="manual_trigger",
                    name=f"Node {i}",
                    position={"x": 0, "y": 0}
                )
            )

        app.current_workflow = workflow

        # Calculate positions
        positions = app._calculate_node_positions()

        # Verify we got positions for all nodes
        assert len(positions) == 6

        # Verify grid layout (4 nodes per row)
        # Row 0: nodes 0-3
        # Row 1: nodes 4-5
        node_ids = [node.id for node in workflow.nodes]

        # First row
        assert positions[node_ids[0]]["y"] == 50  # Same Y for row 0
        assert positions[node_ids[1]]["y"] == 50
        assert positions[node_ids[2]]["y"] == 50
        assert positions[node_ids[3]]["y"] == 50

        # Second row
        assert positions[node_ids[4]]["y"] == 170  # 50 + 120 (y_spacing)
        assert positions[node_ids[5]]["y"] == 170

        # Verify X spacing
        assert positions[node_ids[0]]["x"] == 50  # First column
        assert positions[node_ids[1]]["x"] == 200  # 50 + 150 (x_spacing)
        assert positions[node_ids[2]]["x"] == 350  # 50 + 2*150
        assert positions[node_ids[3]]["x"] == 500  # 50 + 3*150

    def test_calculate_node_positions_empty_workflow(self, mock_page, node_registry):
        """Test positioning with empty workflow."""
        from src.ui.app import SkynetteApp

        app = SkynetteApp(mock_page)
        app.node_registry = node_registry
        app.current_workflow = Workflow(name="Empty", description="Empty")

        positions = app._calculate_node_positions()
        assert positions == {}

    def test_calculate_node_positions_no_workflow(self, mock_page, node_registry):
        """Test positioning with no workflow."""
        from src.ui.app import SkynetteApp

        app = SkynetteApp(mock_page)
        app.node_registry = node_registry
        app.current_workflow = None

        positions = app._calculate_node_positions()
        assert positions == {}

    def test_select_canvas_node(self, mock_page, node_registry, test_workflow):
        """Test node selection."""
        from src.ui.app import SkynetteApp

        app = SkynetteApp(mock_page)
        app.node_registry = node_registry
        app.current_workflow = test_workflow

        # Select a node
        node_id = test_workflow.nodes[0].id
        app._select_canvas_node(node_id)

        # Verify selection
        assert app.selected_node_id == node_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
