from src.data.storage import WorkflowStorage
from src.core.workflow.models import Workflow, WorkflowNode

storage = WorkflowStorage()

workflow = Workflow(
    name="Test Workflow",
    description="Test workflow for UI integration",
    nodes=[
        WorkflowNode(type="manual_trigger", name="Start"),
        WorkflowNode(type="log_debug", name="Log"),
    ]
)

storage.save_workflow(workflow)
print(f"Created workflow: {workflow.id}")
