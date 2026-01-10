"""
Mock storage for testing.

Provides an in-memory implementation of WorkflowStorage that
doesn't require filesystem or database access.
"""

from datetime import datetime
from typing import Optional
import json
import uuid

from src.core.workflow.models import Workflow, WorkflowExecution


class MockWorkflowStorage:
    """
    In-memory mock storage for testing.

    Provides the same interface as WorkflowStorage but stores
    everything in memory, making tests fast and isolated.
    """

    def __init__(self):
        """Initialize empty storage."""
        self.workflows: dict[str, Workflow] = {}
        self.workflow_metadata: dict[str, dict] = {}
        self.executions: list[WorkflowExecution] = []
        self.settings: dict[str, str] = {}
        self.credentials: dict[str, dict] = {}

    def reset(self):
        """Reset storage to empty state for test isolation."""
        self.workflows.clear()
        self.workflow_metadata.clear()
        self.executions.clear()
        self.settings.clear()
        self.credentials.clear()

    # ==================== Workflow Operations ====================

    def save_workflow(self, workflow: Workflow) -> str:
        """Save a workflow to memory."""
        # Update timestamp
        workflow.updated_at = datetime.utcnow()

        # Store workflow
        self.workflows[workflow.id] = workflow

        # Store metadata
        self.workflow_metadata[workflow.id] = {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "tags": workflow.tags,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
        }

        return workflow.id

    def load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Load a workflow by ID."""
        return self.workflows.get(workflow_id)

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            del self.workflow_metadata[workflow_id]
            # Remove related executions
            self.executions = [
                e for e in self.executions
                if e.workflow_id != workflow_id
            ]
            return True
        return False

    def list_workflows(self) -> list[dict]:
        """List all workflows with metadata."""
        workflows = list(self.workflow_metadata.values())
        # Sort by updated_at descending
        workflows.sort(key=lambda w: w["updated_at"], reverse=True)
        return workflows

    def search_workflows(self, query: str) -> list[dict]:
        """Search workflows by name or description."""
        query_lower = query.lower()
        results = [
            w for w in self.workflow_metadata.values()
            if query_lower in w["name"].lower()
            or (w["description"] and query_lower in w["description"].lower())
        ]
        results.sort(key=lambda w: w["updated_at"], reverse=True)
        return results

    # ==================== Execution History ====================

    def save_execution(self, execution: WorkflowExecution) -> str:
        """Save an execution record."""
        self.executions.append(execution)
        return execution.id

    def get_executions(
        self, workflow_id: Optional[str] = None, limit: int = 100
    ) -> list[dict]:
        """Get execution history, optionally filtered by workflow."""
        results = self.executions

        if workflow_id:
            results = [e for e in results if e.workflow_id == workflow_id]

        # Sort by started_at descending
        results = sorted(results, key=lambda e: e.started_at, reverse=True)

        # Convert to dict format
        execution_dicts = []
        for e in results[:limit]:
            workflow_name = None
            if e.workflow_id in self.workflow_metadata:
                workflow_name = self.workflow_metadata[e.workflow_id]["name"]

            execution_dicts.append({
                "id": e.id,
                "workflow_id": e.workflow_id,
                "workflow_name": workflow_name,
                "status": e.status,
                "trigger_type": e.trigger_type,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "error": e.error,
                "duration_ms": e.duration_ms,
            })

        return execution_dicts

    def clear_executions(self, workflow_id: Optional[str] = None):
        """Clear execution history."""
        if workflow_id:
            self.executions = [
                e for e in self.executions
                if e.workflow_id != workflow_id
            ]
        else:
            self.executions.clear()

    # ==================== Settings ====================

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value."""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: str):
        """Set a setting value."""
        self.settings[key] = value

    # ==================== Credentials (if needed) ====================

    def save_credential(self, credential: dict) -> str:
        """Save a credential."""
        cred_id = credential.get("id") or str(uuid.uuid4())
        credential["id"] = cred_id
        credential["created_at"] = credential.get("created_at") or datetime.utcnow().isoformat()
        credential["updated_at"] = datetime.utcnow().isoformat()
        self.credentials[cred_id] = credential
        return cred_id

    def get_credential(self, cred_id: str) -> Optional[dict]:
        """Get a credential by ID."""
        return self.credentials.get(cred_id)

    def delete_credential(self, cred_id: str) -> bool:
        """Delete a credential."""
        if cred_id in self.credentials:
            del self.credentials[cred_id]
            return True
        return False

    def list_credentials(self) -> list[dict]:
        """List all credentials."""
        return list(self.credentials.values())


# Global mock storage instance for tests
_mock_storage: Optional[MockWorkflowStorage] = None


def get_mock_storage() -> MockWorkflowStorage:
    """Get the global mock storage instance."""
    global _mock_storage
    if _mock_storage is None:
        _mock_storage = MockWorkflowStorage()
    return _mock_storage


def reset_mock_storage():
    """Reset the mock storage to empty state."""
    global _mock_storage
    if _mock_storage:
        _mock_storage.reset()
