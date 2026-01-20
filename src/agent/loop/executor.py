"""
Agent Executor

Executes agent plans with tool invocation, retry logic, and budget enforcement.
"""

import asyncio
import logging
import time
from typing import AsyncIterator

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log,
)

from src.agent.models.state import AgentState, AgentSession
from src.agent.models.plan import AgentPlan, PlanStep, StepStatus
from src.agent.models.event import AgentEvent
from src.agent.models.tool import ToolResult
from src.agent.budget import TokenBudget
from src.agent.events import AgentEventEmitter
from src.agent.registry import get_tool_registry, AgentContext
from src.agent.loop.planner import AgentPlanner

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    pass


class AgentExecutor:
    """
    Execute agent plans with tool invocation, retry logic, and budget enforcement.
    """

    MAX_ITERATIONS = 20
    TIMEOUT_SECONDS = 300  # 5 minutes

    def __init__(self, session: AgentSession):
        self.session = session
        self.planner = AgentPlanner()
        self.registry = get_tool_registry()
        self.emitter = AgentEventEmitter()
        self.budget = TokenBudget(max_tokens=session.token_budget)
        self._cancelled = False

    def cancel(self):
        """Request cancellation of execution."""
        self._cancelled = True

    async def run(self, task: str) -> AsyncIterator[AgentEvent]:
        """
        Execute a task, yielding events as execution progresses.

        Args:
            task: The user's task

        Yields:
            AgentEvent objects for each state change, step, etc.
        """
        self.session.task = task
        self.session.state = AgentState.PLANNING
        yield AgentEvent.state_change("planning", self.session.id)

        # Phase 1: Generate plan
        try:
            plan = await self.planner.create_plan(task)
            yield AgentEvent.plan_created(plan.model_dump(), self.session.id)
        except Exception as e:
            self.session.state = AgentState.FAILED
            yield AgentEvent.error(f"Planning failed: {e}", self.session.id)
            return

        # Phase 2: Execute steps
        self.session.state = AgentState.EXECUTING
        yield AgentEvent.state_change("executing", self.session.id)

        iteration = 0
        start_time = time.time()

        while not plan.is_complete() and not plan.has_failed():
            # Check cancellation
            if self._cancelled:
                self.session.state = AgentState.CANCELLED
                yield AgentEvent(type="cancelled", data={}, session_id=self.session.id)
                return

            # Check iteration limit
            iteration += 1
            if iteration > self.MAX_ITERATIONS:
                yield AgentEvent(
                    type="iteration_limit",
                    data={"max": self.MAX_ITERATIONS},
                    session_id=self.session.id
                )
                break

            # Check timeout
            if time.time() - start_time > self.TIMEOUT_SECONDS:
                yield AgentEvent(
                    type="error",
                    data={"message": "Execution timeout"},
                    session_id=self.session.id
                )
                break

            # Check budget
            if not self.budget.can_proceed():
                yield AgentEvent(
                    type="budget_exceeded",
                    data=self.budget.to_dict(),
                    session_id=self.session.id
                )
                break

            if self.budget.is_warning():
                yield AgentEvent(
                    type="budget_warning",
                    data=self.budget.to_dict(),
                    session_id=self.session.id
                )

            # Get next step
            step = plan.get_next_step()
            if step is None:
                # No step ready (dependencies not met or all done)
                await asyncio.sleep(0.1)
                continue

            # Execute step
            yield AgentEvent(
                type="step_started",
                data={"step_id": step.id, "description": step.description},
                session_id=self.session.id
            )

            step.status = StepStatus.RUNNING
            async for event in self._execute_step(step):
                yield event

            self.session.steps_completed += 1

        # Determine final state
        if plan.has_failed():
            self.session.state = AgentState.FAILED
            yield AgentEvent.error("Plan execution failed", self.session.id)
        elif plan.is_complete():
            self.session.state = AgentState.COMPLETED
            yield AgentEvent(
                type="completed",
                data=self._get_summary(plan),
                session_id=self.session.id
            )
        else:
            self.session.state = AgentState.FAILED
            yield AgentEvent.error("Plan did not complete", self.session.id)

    async def _execute_step(self, step: PlanStep) -> AsyncIterator[AgentEvent]:
        """Execute a single plan step."""
        try:
            if step.tool_name:
                # Tool invocation
                result = await self._execute_tool_with_retry(
                    step.tool_name,
                    step.tool_params
                )

                if result.success:
                    step.status = StepStatus.COMPLETED
                    step.result = result.data
                    yield AgentEvent(
                        type="step_completed",
                        data={"step_id": step.id, "result": result.data},
                        session_id=self.session.id
                    )
                else:
                    step.status = StepStatus.FAILED
                    step.error = result.error
                    yield AgentEvent(
                        type="error",
                        data={"step_id": step.id, "error": result.error},
                        session_id=self.session.id
                    )
            else:
                # No tool - step is informational/reasoning
                step.status = StepStatus.COMPLETED
                step.result = {"note": "Reasoning step completed"}
                yield AgentEvent(
                    type="step_completed",
                    data={"step_id": step.id, "result": step.result},
                    session_id=self.session.id
                )

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            yield AgentEvent(
                type="error",
                data={"step_id": step.id, "error": str(e)},
                session_id=self.session.id
            )

    async def _execute_tool_with_retry(
        self,
        tool_name: str,
        params: dict
    ) -> ToolResult:
        """
        Execute a tool with automatic retry on transient failures.
        Retries up to 3 times with exponential backoff.
        """
        tool = self.registry.get_tool(tool_name)
        if tool is None:
            return ToolResult.failure_result(
                tool_call_id="unknown",
                error=f"Tool not found: {tool_name}"
            )

        # Validate parameters
        valid, error = tool.validate_params(params)
        if not valid:
            return ToolResult.failure_result(
                tool_call_id="validation",
                error=f"Parameter validation failed: {error}"
            )

        # Create context
        context = AgentContext(
            session_id=self.session.id,
            variables=self.session.variables
        )

        # Execute with retry
        return await self._retry_tool_execution(tool, params, context)

    async def _retry_tool_execution(self, tool, params: dict, context: AgentContext) -> ToolResult:
        """Internal method that applies retry logic."""

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential_jitter(initial=1, max=30, exp_base=2),
            retry=retry_if_exception_type(ToolExecutionError),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        async def _execute():
            start = time.time()
            try:
                result = await tool.execute(params, context)
                result.duration_ms = (time.time() - start) * 1000
                return result
            except Exception as e:
                # Wrap in ToolExecutionError for retry
                raise ToolExecutionError(f"Tool {tool.name} failed: {e}") from e

        try:
            return await _execute()
        except ToolExecutionError as e:
            return ToolResult.failure_result(
                tool_call_id="retry_exhausted",
                error=str(e)
            )

    def _get_summary(self, plan: AgentPlan) -> dict:
        """Get execution summary."""
        completed = sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in plan.steps if s.status == StepStatus.FAILED)
        return {
            "task": self.session.task,
            "overview": plan.overview,
            "steps_total": len(plan.steps),
            "steps_completed": completed,
            "steps_failed": failed,
            "tokens_used": self.budget.used_total,
        }
