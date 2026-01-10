"""Performance check script for Skynette."""

from src.data.storage import WorkflowStorage
from src.core.workflow.models import Workflow
import time

print("=== Performance Check ===\n")

storage = WorkflowStorage()

# Create 50 test workflows
print("Creating 50 test workflows...")
start_time = time.time()
workflow_ids = []
for i in range(50):
    wf = Workflow(name=f"Performance Test {i}", description=f"Test workflow {i}")
    storage.save_workflow(wf)
    workflow_ids.append(wf.id)
create_time = time.time() - start_time
print(f"  Created 50 workflows in {create_time:.2f}s")

# List workflows
print("\nListing workflows...")
start_time = time.time()
workflows = storage.list_workflows()
list_time = time.time() - start_time
print(f"  Listed {len(workflows)} workflows in {list_time:.2f}s")

# Check if under 1 second
if list_time < 1.0:
    print(f"  [PASS] Performance PASSED: {list_time:.3f}s < 1.0s")
else:
    print(f"  [WARN] Performance WARNING: {list_time:.3f}s >= 1.0s")

# Cleanup
print("\nCleaning up test workflows...")
for wf_id in workflow_ids:
    storage.delete_workflow(wf_id)
print("  Cleanup complete")

print("\n=== Performance Check Complete ===")
