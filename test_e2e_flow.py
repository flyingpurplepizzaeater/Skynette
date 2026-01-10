"""
End-to-end integration test for Sprint 1 MVP.

Simulates complete user flow:
1. Create workflow
2. Add nodes
3. Save workflow
4. Execute workflow
5. Verify results
"""

from src.data.storage import WorkflowStorage
from src.core.workflow.models import Workflow, WorkflowNode, WorkflowConnection
from src.core.workflow.executor import WorkflowExecutor

print("=== E2E Integration Test ===\n")

# 1. Create workflow (simulates UI dialog)
print("1. Creating workflow...")
workflow = Workflow(
    name="E2E Test",
    description="End-to-end integration test",
)

# Add trigger node
trigger = WorkflowNode(type="manual_trigger", name="Start")
workflow.nodes.append(trigger)
print(f"   + Added trigger node: {trigger.id}")

# 2. Add action node (simulates Simple Mode "Add Step")
print("\n2. Adding Log Debug node...")
log_node = WorkflowNode(
    type="log_debug", 
    name="Log",
    config={"message": "E2E test successful", "log_level": "info"}
)
workflow.nodes.append(log_node)

# Auto-connect nodes
conn = WorkflowConnection(
    source_node_id=trigger.id,
    target_node_id=log_node.id
)
workflow.connections.append(conn)
print(f"   + Added log node: {log_node.id}")
print(f"   + Connected: {trigger.id} -> {log_node.id}")

# 3. Save workflow (simulates Save button)
print("\n3. Saving workflow...")
storage = WorkflowStorage()
storage.save_workflow(workflow)
print(f"   + Saved to storage: {workflow.id}")

# Verify saved
loaded = storage.load_workflow(workflow.id)
assert loaded is not None, "Failed to load saved workflow"
assert loaded.name == "E2E Test"
assert len(loaded.nodes) == 2
print("   + Verified: Workflow persisted correctly")

# 4. Execute workflow (simulates Run button)
print("\n4. Executing workflow...")
executor = WorkflowExecutor()
import asyncio
execution = asyncio.run(executor.execute(workflow))

print(f"   + Status: {execution.status}")
print(f"   + Duration: {execution.duration_ms}ms")
print(f"   + Node results: {len(execution.node_results)}")

# 5. Verify results
print("\n5. Verifying execution results...")
assert execution.status == "completed", f"Expected completed, got {execution.status}"
assert len(execution.node_results) == 2, f"Expected 2 results, got {len(execution.node_results)}"

trigger_result = execution.get_result(trigger.id)
assert trigger_result.success, "Trigger node failed"
print(f"   + Trigger: SUCCESS ({trigger_result.duration_ms}ms)")

log_result = execution.get_result(log_node.id)
assert log_result.success, "Log node failed"
print(f"   + Log Debug: SUCCESS ({log_result.duration_ms}ms)")

# 6. Verify execution saved to database
print("\n6. Verifying execution history...")
storage.save_execution(execution)
executions = storage.get_executions(workflow_id=workflow.id)
assert len(executions) >= 1, "Execution not saved to history"
print(f"   + Found {len(executions)} execution(s) in history")
print(f"   + Latest status: {executions[0]['status']}")

print("\n" + "="*40)
print("+ Sprint 1 MVP Success Criteria: PASSED")
print("="*40)
print("\nComplete workflow lifecycle verified:")
print("  + Create workflow via API (simulates UI dialog)")
print("  + Add nodes (simulates Simple Mode)")
print("  + Configure node properties")
print("  + Save workflow to storage")
print("  + Execute workflow successfully")
print("  + View execution results")
print("  + Execution history saved")
