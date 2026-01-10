"""
Shared pytest fixtures for Skynette tests.

This module contains fixtures that are shared across all test types
(unit, integration, and e2e tests).
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def src_dir(project_root: Path) -> Path:
    """Return the src directory."""
    return project_root / "src"


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "skynette_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def test_env_vars(temp_data_dir: Path) -> dict:
    """Environment variables for test mode."""
    return {
        "SKYNETTE_TEST_MODE": "true",
        "SKYNETTE_MOCK_AI": "true",
        "SKYNETTE_DATA_DIR": str(temp_data_dir),
    }


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    yield
    # Clean up any singleton instances after each test
    # This prevents state leaking between tests


@pytest.fixture
def sample_workflow_data() -> dict:
    """Sample workflow data for testing."""
    return {
        "id": "test-workflow-1",
        "name": "Test Workflow",
        "description": "A test workflow for automated testing",
        "nodes": [
            {
                "id": "node-1",
                "type": "manual_trigger",
                "name": "Manual Trigger",
                "position": {"x": 100, "y": 100},
                "config": {},
            },
            {
                "id": "node-2",
                "type": "ai_chat",
                "name": "AI Chat",
                "position": {"x": 300, "y": 100},
                "config": {
                    "prompt": "Hello, world!",
                },
            },
        ],
        "connections": [
            {
                "source_node_id": "node-1",
                "target_node_id": "node-2",
                "source_port": "output",
                "target_port": "input",
            }
        ],
    }


@pytest.fixture
def multiple_workflows_data() -> list:
    """Multiple sample workflows for testing list views."""
    return [
        {
            "id": f"workflow-{i}",
            "name": f"Test Workflow {i}",
            "description": f"Description for workflow {i}",
            "nodes": [],
            "connections": [],
        }
        for i in range(1, 4)
    ]
