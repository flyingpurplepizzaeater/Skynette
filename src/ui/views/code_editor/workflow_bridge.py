# src/ui/views/code_editor/workflow_bridge.py
"""Bridge between code editor and workflow storage.

Enables bidirectional sync between code representation and workflow models.
"""

from enum import Enum
from typing import Callable
import json
import logging
import yaml

from src.core.workflow.models import Workflow, WorkflowNode, WorkflowConnection
from src.data.storage import get_storage

logger = logging.getLogger(__name__)


class WorkflowFormat(Enum):
    """Supported workflow code formats."""

    YAML = "yaml"
    JSON = "json"
    PYTHON_DSL = "python"


class WorkflowBridge:
    """Bridge for loading/saving workflows as code.

    Provides bidirectional conversion between Workflow models and
    editable code formats (YAML, JSON, Python DSL).

    Example:
        bridge = WorkflowBridge()
        code = bridge.load_as_code("workflow-id", WorkflowFormat.YAML)
        success, error = bridge.save_from_code("workflow-id", code, WorkflowFormat.YAML)
    """

    def __init__(self):
        """Initialize workflow bridge."""
        self._storage = get_storage()
        self._listeners: list[Callable[[str], None]] = []

    def add_listener(self, callback: Callable[[str], None]) -> None:
        """Add listener for workflow changes.

        Args:
            callback: Function called with workflow_id when saved.
        """
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str], None]) -> None:
        """Remove change listener.

        Args:
            callback: Previously registered callback.
        """
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_change(self, workflow_id: str) -> None:
        """Notify listeners of workflow change.

        Args:
            workflow_id: ID of changed workflow.
        """
        for listener in self._listeners:
            try:
                listener(workflow_id)
            except Exception as e:
                logger.warning(f"Listener error: {e}")

    def load_as_code(
        self, workflow_id: str, format: WorkflowFormat = WorkflowFormat.YAML
    ) -> str | None:
        """Load workflow as editable code.

        Args:
            workflow_id: ID of workflow to load.
            format: Output format (YAML, JSON, or Python DSL).

        Returns:
            Code string or None if workflow not found.
        """
        workflow = self._storage.load_workflow(workflow_id)
        if workflow is None:
            return None

        if format == WorkflowFormat.YAML:
            return workflow.to_yaml()
        elif format == WorkflowFormat.JSON:
            return workflow.model_dump_json(indent=2)
        elif format == WorkflowFormat.PYTHON_DSL:
            return workflow.to_python_dsl()
        else:
            raise ValueError(f"Unknown format: {format}")

    def save_from_code(
        self, workflow_id: str, code: str, format: WorkflowFormat
    ) -> tuple[bool, str]:
        """Save workflow from code representation.

        Args:
            workflow_id: Original workflow ID to preserve.
            code: Code content to parse.
            format: Format of the code.

        Returns:
            Tuple of (success, error_message). On success error is empty.
        """
        try:
            # Parse code into workflow
            if format == WorkflowFormat.YAML:
                workflow = self._parse_yaml(code)
            elif format == WorkflowFormat.JSON:
                workflow = self._parse_json(code)
            elif format == WorkflowFormat.PYTHON_DSL:
                workflow = Workflow.from_python_dsl(code)
            else:
                return False, f"Unknown format: {format}"

            # Preserve original ID
            workflow.id = workflow_id

            # Save to storage
            self._storage.save_workflow(workflow)
            self._notify_change(workflow_id)

            logger.info(f"Saved workflow {workflow_id} from {format.value} code")
            return True, ""

        except yaml.YAMLError as e:
            return False, f"Invalid YAML: {e}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            return False, f"Save failed: {e}"

    def _parse_yaml(self, code: str) -> Workflow:
        """Parse YAML code into Workflow.

        Args:
            code: YAML content.

        Returns:
            Parsed Workflow.

        Raises:
            yaml.YAMLError: If YAML is invalid.
            ValueError: If data doesn't validate as Workflow.
        """
        # Use safe_load to prevent code execution attacks
        data = yaml.safe_load(code)
        if data is None:
            # Empty YAML
            raise ValueError("Empty workflow definition")
        return Workflow.model_validate(data)

    def _parse_json(self, code: str) -> Workflow:
        """Parse JSON code into Workflow.

        Args:
            code: JSON content.

        Returns:
            Parsed Workflow.

        Raises:
            json.JSONDecodeError: If JSON is invalid.
            ValueError: If data doesn't validate as Workflow.
        """
        return Workflow.model_validate_json(code)

    def convert_format(
        self, code: str, from_format: WorkflowFormat, to_format: WorkflowFormat
    ) -> tuple[str, str]:
        """Convert code between formats.

        Args:
            code: Source code.
            from_format: Current format.
            to_format: Target format.

        Returns:
            Tuple of (converted_code, error). Error is empty on success.
        """
        try:
            # Parse from source format
            if from_format == WorkflowFormat.YAML:
                workflow = self._parse_yaml(code)
            elif from_format == WorkflowFormat.JSON:
                workflow = self._parse_json(code)
            elif from_format == WorkflowFormat.PYTHON_DSL:
                workflow = Workflow.from_python_dsl(code)
            else:
                return "", f"Unknown source format: {from_format}"

            # Convert to target format
            if to_format == WorkflowFormat.YAML:
                return workflow.to_yaml(), ""
            elif to_format == WorkflowFormat.JSON:
                return workflow.model_dump_json(indent=2), ""
            elif to_format == WorkflowFormat.PYTHON_DSL:
                return workflow.to_python_dsl(), ""
            else:
                return "", f"Unknown target format: {to_format}"

        except Exception as e:
            return "", str(e)

    def get_workflow_name(self, workflow_id: str) -> str | None:
        """Get workflow name for display.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Workflow name or None if not found.
        """
        workflow = self._storage.load_workflow(workflow_id)
        return workflow.name if workflow else None
