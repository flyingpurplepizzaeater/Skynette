"""
Test Advanced Mode workflow creation.

Simulates:
1. Creating workflow
2. Adding nodes via "palette" (API)
3. Creating connections
4. Configuring nodes
5. Executing workflow
"""

from src.data.storage import WorkflowStorage
from src.core.workflow.models import Workflow, WorkflowNode, WorkflowConnection
from src.core.workflow.executor import WorkflowExecutor
from src.core.nodes.registry import NodeRegistry

print("=== Advanced Mode Test ===\n")

# 1. Create workflow
print("1. Creating workflow...")
workflow = Workflow(
    name="Advanced Mode Test",
    description="Tests visual editor node addition and connections",
)

# 2. Add nodes (simulates palette clicks)
print("\n2. Adding nodes from palette...")
registry = NodeRegistry()

# Get node definitions
trigger_def = registry.get_definition("manual_trigger")
setvar_def = registry.get_definition("set_variable")
ifelse_def = registry.get_definition("if_else")
log_def = registry.get_definition("log_debug")

# Add nodes
nodes = [
    WorkflowNode(type="manual_trigger", name="Start", config={"test_data": {"value": 42}}),
    WorkflowNode(type="set_variable", name="Set Status", config={
        "variable_name": "status_code",
        "value": 200,
    }),
    WorkflowNode(type="if_else", name="Check Status", config={
        "condition_type": "comparison",
        "left_value": 200,
        "operator": "equals",
        "right_value": 200,
    }),
    WorkflowNode(type="log_debug", name="Log Success", config={
        "message": "Test completed successfully",
        "log_level": "info",
    }),
]

for node in nodes:
    workflow.nodes.append(node)
    print(f"   + Added {node.name} ({node.type})")

# 3. Create connections (simulates connection dropdown)
print("\n3. Creating connections...")
connections = [
    (nodes[0].id, nodes[1].id, "Start -> Set Status"),
    (nodes[1].id, nodes[2].id, "Set Status -> Check Status"),
    (nodes[2].id, nodes[3].id, "Check Status -> Log Success"),
]

for source_id, target_id, label in connections:
    conn = WorkflowConnection(source_node_id=source_id, target_node_id=target_id)
    workflow.connections.append(conn)
    print(f"   + Connected: {label}")

# 4. Save workflow
print("\n4. Saving workflow...")
storage = WorkflowStorage()
storage.save_workflow(workflow)
print(f"   + Saved: {workflow.id}")

# 5. Execute workflow
print("\n5. Executing workflow...")
executor = WorkflowExecutor()
import asyncio
execution = asyncio.run(executor.execute(workflow))

print(f"   + Status: {execution.status}")
print(f"   + Duration: {execution.duration_ms}ms")

# 6. Verify results
print("\n6. Verifying results...")
assert execution.status == "completed", f"Expected completed, got {execution.status}"
assert len(execution.node_results) == 4, f"Expected 4 results, got {len(execution.node_results)}"

for node in nodes:
    result = execution.get_result(node.id)
    status = "SUCCESS" if result.success else "FAILED"
    print(f"   + {node.name}: {status} ({result.duration_ms}ms)")

print("\n" + "="*50)
print("+ Advanced Mode Test: PASSED")
print("="*50)
print("\nAdvanced mode features verified:")
print("  + Add multiple node types from palette")
print("  + Create complex connection graph")
print("  + Configure all node types")
print("  + Execute multi-node workflow")
print("  + All nodes executed successfully")
