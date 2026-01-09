"""
Workflow Executor

Handles the execution of workflows.
"""

import asyncio
from datetime import datetime
from typing import Any, Optional
import logging

from src.core.workflow.models import (
    Workflow,
    WorkflowExecution,
    ExecutionResult,
    WorkflowNode,
)
from src.core.nodes.registry import NodeRegistry
from src.core.expressions import resolve_expressions

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executes workflows by running nodes in order."""

    def __init__(self):
        self.node_registry = NodeRegistry()
        self.current_execution: Optional[WorkflowExecution] = None

    async def execute(
        self,
        workflow: Workflow,
        trigger_data: dict = None,
        trigger_type: str = "manual",
        resume_from: Optional[str] = None,
        previous_context: Optional[dict] = None,
    ) -> WorkflowExecution:
        """
        Execute a workflow and return the execution result.

        Args:
            workflow: The workflow to execute
            trigger_data: Data passed from the trigger
            trigger_type: Type of trigger (manual, schedule, webhook, etc.)
            resume_from: Optional node ID to resume execution from (skips prior nodes)
            previous_context: Context from previous execution (for resume)

        Returns:
            WorkflowExecution with results
        """
        trigger_data = trigger_data or {}

        # Create execution record
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            status="running",
            trigger_type=trigger_type if not resume_from else "resume",
            trigger_data=trigger_data,
        )
        self.current_execution = execution

        try:
            # Get execution order
            node_order = workflow.get_execution_order()
            logger.info(f"Executing workflow {workflow.name} with {len(node_order)} nodes")

            # Context for passing data between nodes
            if previous_context:
                # Resume with previous context
                context = previous_context.copy()
                context["$trigger"] = trigger_data or context.get("$trigger", {})
                logger.info(f"Resuming with context from previous execution")
            else:
                context = {
                    "$trigger": trigger_data,
                    "$vars": workflow.variables.copy(),
                    "$nodes": {},
                }

            # Handle resume - skip nodes until we reach resume_from
            skip_until_resume = resume_from is not None
            skipped_nodes = []

            # Execute nodes in order
            for node_id in node_order:
                node = workflow.get_node(node_id)
                if not node or not node.enabled:
                    continue

                # Handle resume - skip nodes until we reach the resume point
                if skip_until_resume:
                    if node_id == resume_from:
                        skip_until_resume = False
                        logger.info(f"Resuming execution from node '{node.name}'")
                    else:
                        skipped_nodes.append(node_id)
                        logger.debug(f"Skipping node '{node.name}' (before resume point)")
                        continue

                result = await self._execute_node(node, context)
                execution.add_result(result)

                if result.success:
                    # Store result in context for downstream nodes
                    context["$nodes"][node_id] = result.data
                    context["$prev"] = result.data
                else:
                    # Handle error based on node configuration
                    error_strategy = node.config.get("on_error", "stop")
                    if error_strategy == "stop":
                        execution.status = "failed"
                        execution.error = result.error
                        break
                    elif error_strategy == "continue":
                        context["$nodes"][node_id] = None
                        context["$prev"] = None
                    # Other strategies: retry, fallback, etc.

            # Mark execution as complete
            if execution.status == "running":
                execution.status = "completed"

            execution.completed_at = datetime.utcnow()
            execution.duration_ms = (
                execution.completed_at - execution.started_at
            ).total_seconds() * 1000

            logger.info(
                f"Workflow {workflow.name} execution {execution.status} "
                f"in {execution.duration_ms:.2f}ms"
            )

        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            logger.exception(f"Workflow execution failed: {e}")

        finally:
            self.current_execution = None

        return execution

    async def _execute_node(
        self, node: WorkflowNode, context: dict
    ) -> ExecutionResult:
        """Execute a single node."""
        start_time = datetime.utcnow()

        try:
            # Get node handler from registry
            handler = self.node_registry.get_handler(node.type)
            if not handler:
                raise ValueError(f"Unknown node type: {node.type}")

            # Resolve expressions in node config
            resolved_config = self._resolve_expressions(node.config, context)

            # Execute the node
            logger.debug(f"Executing node {node.name} ({node.type})")
            output = await handler.execute(resolved_config, context)

            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            return ExecutionResult(
                node_id=node.id,
                success=True,
                data=output,
                duration_ms=duration_ms,
                started_at=start_time,
                completed_at=end_time,
            )

        except Exception as e:
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            logger.error(f"Node {node.name} execution failed: {e}")

            return ExecutionResult(
                node_id=node.id,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                started_at=start_time,
                completed_at=end_time,
            )

    def _resolve_expressions(self, config: dict, context: dict) -> dict:
        """Resolve {{expressions}} in configuration values using the expression parser."""
        return resolve_expressions(config, context)


class DebugExecutor(WorkflowExecutor):
    """Executor with debugging capabilities."""

    def __init__(self):
        super().__init__()
        self.breakpoints: set[str] = set()
        self.paused = False
        self.step_mode = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused by default

    def set_breakpoint(self, node_id: str):
        """Set a breakpoint on a node."""
        self.breakpoints.add(node_id)

    def remove_breakpoint(self, node_id: str):
        """Remove a breakpoint from a node."""
        self.breakpoints.discard(node_id)

    def resume(self):
        """Resume execution."""
        self.paused = False
        self._pause_event.set()

    def step(self):
        """Execute one step."""
        self.step_mode = True
        self._pause_event.set()

    async def _execute_node(
        self, node: WorkflowNode, context: dict
    ) -> ExecutionResult:
        """Execute a node with debug support."""
        # Check for breakpoint
        if node.id in self.breakpoints or self.step_mode:
            self.paused = True
            self._pause_event.clear()
            logger.info(f"Paused at node {node.name}")

            # Wait for resume/step
            await self._pause_event.wait()

            if self.step_mode:
                self._pause_event.clear()

        return await super()._execute_node(node, context)
