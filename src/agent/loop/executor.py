"""
Agent Executor

Executes agent plans with tool invocation, retry logic, and budget enforcement.
"""

import asyncio
import logging
import time
from typing import AsyncIterator, Optional

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
from src.agent.models.cancel import (
    CancelMode,
    CancellationRequest,
    CancellationResult,
    ResultMode,
)
from src.agent.budget import TokenBudget
from src.agent.events import AgentEventEmitter
from src.agent.registry import get_tool_registry, AgentContext
from src.agent.loop.planner import AgentPlanner
from src.agent.safety import (
    ActionClassifier,
    get_kill_switch,
    get_approval_manager,
    get_audit_store,
    AuditEntry,
)
from src.agent.safety.autonomy import get_autonomy_service

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

    def __init__(self, session: AgentSession, project_path: str | None = None):
        self.session = session
        self.planner = AgentPlanner()
        self.registry = get_tool_registry()
        self.emitter = AgentEventEmitter()
        self.budget = TokenBudget(max_tokens=session.token_budget)
        self._cancel_request: Optional[CancellationRequest] = None
        self._current_step: Optional[PlanStep] = None
        self._completed_steps: list[str] = []

        # Project path for autonomy level lookup
        self._project_path = project_path
        self._level_downgraded: bool = False

        # Safety system components
        self.classifier = ActionClassifier()
        self.kill_switch = get_kill_switch()
        self.approval_manager = get_approval_manager()
        self.audit_store = get_audit_store()

    def cancel(self):
        """
        Request immediate cancellation of execution.

        Backward-compatible method that creates an IMMEDIATE cancellation request.
        For more control, use request_cancel() instead.
        """
        self.request_cancel(CancellationRequest(
            cancel_mode=CancelMode.IMMEDIATE,
            result_mode=ResultMode.KEEP,
            reason="Legacy cancel() called"
        ))

    def request_cancel(self, request: CancellationRequest):
        """
        Request cancellation with specific mode and result handling.

        Args:
            request: CancellationRequest specifying cancel mode and result mode
        """
        self._cancel_request = request
        # Try to emit cancellation_requested event if event loop is running
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emitter.emit(AgentEvent(
                type="cancelled",  # Use existing event type for request notification
                data={
                    "status": "requested",
                    "cancel_mode": request.cancel_mode.value,
                    "result_mode": request.result_mode.value,
                    "reason": request.reason,
                },
                session_id=self.session.id
            )))
        except RuntimeError:
            # No running event loop - event will be emitted when run() checks cancellation
            pass

    def _should_cancel(self) -> bool:
        """
        Check if execution should be cancelled based on current state.

        Returns:
            True if cancellation should proceed now, False otherwise
        """
        if self._cancel_request is None:
            return False

        if self._cancel_request.cancel_mode == CancelMode.IMMEDIATE:
            return True

        # AFTER_CURRENT mode: cancel only if no step is running
        if self._cancel_request.cancel_mode == CancelMode.AFTER_CURRENT:
            return self._current_step is None

        return False

    def _create_cancellation_result(self) -> CancellationResult:
        """Create a CancellationResult from current state."""
        cancelled_step = None
        if self._current_step is not None:
            cancelled_step = self._current_step.description

        return CancellationResult(
            completed_steps=self._completed_steps.copy(),
            cancelled_step=cancelled_step,
            cancel_mode=self._cancel_request.cancel_mode if self._cancel_request else CancelMode.IMMEDIATE,
            result_mode=self._cancel_request.result_mode if self._cancel_request else ResultMode.KEEP,
        )

    def _check_kill_switch(self) -> bool:
        """Check if kill switch has been triggered."""
        return self.kill_switch.is_triggered()

    def _on_autonomy_downgrade(
        self,
        project_path: str,
        old_level: str,
        new_level: str,
        downgrade: bool,
    ) -> None:
        """
        Handle autonomy level downgrade during execution.

        On downgrade, set flag to re-evaluate pending actions.

        Args:
            project_path: Project that changed
            old_level: Previous level
            new_level: New level
            downgrade: Whether this is a downgrade (more restrictive)
        """
        if downgrade and project_path == self._project_path:
            self._level_downgraded = True
            logger.info(
                f"Autonomy downgrade: {old_level} -> {new_level}, "
                "remaining actions will be re-evaluated"
            )

    async def run(self, task: str) -> AsyncIterator[AgentEvent]:
        """
        Execute a task, yielding events as execution progresses.

        Args:
            task: The user's task

        Yields:
            AgentEvent objects for each state change, step, etc.
        """
        # Initialize safety systems for this execution
        self.kill_switch.reset()
        self.approval_manager.start_session(self.session.id)

        # Register for autonomy level changes
        autonomy_service = get_autonomy_service()
        autonomy_service.on_level_changed(self._on_autonomy_downgrade)

        try:
            async for event in self._run_with_safety(task):
                yield event
        finally:
            # Cleanup safety systems
            self.approval_manager.end_session()
            self.kill_switch.reset()
            # Note: Don't remove callback - service manages its own lifecycle

    async def _run_with_safety(self, task: str) -> AsyncIterator[AgentEvent]:
        """Internal run method with safety systems initialized."""
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
            # Check kill switch first (highest priority)
            if self._check_kill_switch():
                self.session.state = AgentState.CANCELLED
                yield AgentEvent.kill_switch_triggered(
                    self.kill_switch.trigger_reason or "Kill switch activated",
                    self.session.id
                )
                return

            # Check cancellation with mode-aware logic
            if self._should_cancel():
                self.session.state = AgentState.CANCELLED
                result = self._create_cancellation_result()
                yield AgentEvent(
                    type="cancelled",
                    data={
                        "status": "cancelled",
                        "completed_steps": result.completed_steps,
                        "cancelled_step": result.cancelled_step,
                        "cancel_mode": result.cancel_mode.value,
                        "result_mode": result.result_mode.value,
                        "options": result.options,
                    },
                    session_id=self.session.id
                )
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

            # Check if autonomy was downgraded mid-task
            if self._level_downgraded:
                self._level_downgraded = False
                # Re-evaluation happens automatically because classify() is called
                # fresh for each step with current autonomy settings
                logger.debug("Re-evaluating step under new autonomy level")

            # Execute step
            self._current_step = step
            yield AgentEvent(
                type="step_started",
                data={"step_id": step.id, "description": step.description},
                session_id=self.session.id
            )

            step.status = StepStatus.RUNNING
            async for event in self._execute_step(step):
                yield event

            # Track completed step
            if step.status == StepStatus.COMPLETED:
                self._completed_steps.append(step.description)
            self._current_step = None
            self.session.steps_completed += 1

            # Check kill switch after step completes (step boundary)
            if self._check_kill_switch():
                self.session.state = AgentState.CANCELLED
                yield AgentEvent.kill_switch_triggered(
                    self.kill_switch.trigger_reason or "Kill switch activated",
                    self.session.id
                )
                return

            # Check for AFTER_CURRENT cancellation after step completes
            if self._should_cancel():
                self.session.state = AgentState.CANCELLED
                result = self._create_cancellation_result()
                yield AgentEvent(
                    type="cancelled",
                    data={
                        "status": "cancelled",
                        "completed_steps": result.completed_steps,
                        "cancelled_step": result.cancelled_step,
                        "cancel_mode": result.cancel_mode.value,
                        "result_mode": result.result_mode.value,
                        "options": result.options,
                    },
                    session_id=self.session.id
                )
                return

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
                # Tool invocation with safety (classification, approval, audit)
                result, events, auto_executed = await self._execute_tool_with_safety(
                    step.tool_name,
                    step.tool_params,
                    step.id
                )
                # Emit safety events (classification, approval)
                for event in events:
                    yield event

                if result.success:
                    step.status = StepStatus.COMPLETED
                    step.result = result.data
                    yield AgentEvent(
                        type="step_completed",
                        data={
                            "step_id": step.id,
                            "result": result.data,
                            "auto_executed": auto_executed,
                        },
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
                    data={
                        "step_id": step.id,
                        "result": step.result,
                        "auto_executed": False,
                    },
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

    async def _execute_tool_with_safety(
        self,
        tool_name: str,
        params: dict,
        step_id: str = "",
    ) -> tuple[ToolResult, list[AgentEvent], bool]:
        """
        Execute a tool with classification, approval (if needed), retry, and audit.

        Returns:
            Tuple of (ToolResult, list of events to emit, auto_executed flag)
        """
        events: list[AgentEvent] = []
        start_time = time.time()

        # 1. Classify the action with project-specific autonomy level
        classification = self.classifier.classify(tool_name, params, self._project_path)

        # Determine if this action is "auto-executing" (would need approval at lower level)
        # An action auto-executes at current level if:
        # - It doesn't require approval at current level
        # - But would require approval at a lower level (L1 requires all, so any non-approval is auto)
        auto_executed = not classification.requires_approval and classification.risk_level != "safe"

        # Emit classification event
        events.append(AgentEvent.action_classified(
            tool_name=tool_name,
            risk_level=classification.risk_level,
            reason=classification.reason,
            requires_approval=classification.requires_approval,
            session_id=self.session.id,
            auto_executed=auto_executed,
        ))

        # 2. Request approval if needed
        approval_decision = "auto"
        approval_time_ms = None

        if classification.requires_approval:
            self.session.state = AgentState.AWAITING_APPROVAL

            # Request approval (ApprovalManager checks similarity cache first)
            approval_start = time.time()
            approval_result = await self.approval_manager.request_approval(
                classification=classification,
                step_id=step_id,
                timeout=60.0,  # 60s default per CONTEXT.md
            )
            approval_time_ms = (time.time() - approval_start) * 1000

            # Emit approval events
            events.append(AgentEvent.approval_requested(
                request_id="",  # Request already submitted
                tool_name=tool_name,
                risk_level=classification.risk_level,
                reason=classification.reason,
                parameters=params,
                session_id=self.session.id,
            ))
            events.append(AgentEvent.approval_received(
                request_id="",
                decision=approval_result.decision,
                approve_similar=approval_result.approve_similar,
                session_id=self.session.id,
            ))

            approval_decision = approval_result.decision

            if approval_result.decision == "rejected":
                # Log rejection to audit
                self._log_audit(
                    step_id=step_id,
                    tool_name=tool_name,
                    params=params,
                    result=None,
                    error="Action rejected by user",
                    duration_ms=(time.time() - start_time) * 1000,
                    classification=classification,
                    approval_decision=approval_decision,
                    approval_time_ms=approval_time_ms,
                    success=False,
                )
                return ToolResult.failure_result(
                    tool_call_id="rejected",
                    error="Action rejected by user",
                ), events, False

            elif approval_result.decision == "timeout":
                # Per CONTEXT.md: pause (skip action) on timeout
                self._log_audit(
                    step_id=step_id,
                    tool_name=tool_name,
                    params=params,
                    result=None,
                    error="Approval timeout - action skipped",
                    duration_ms=(time.time() - start_time) * 1000,
                    classification=classification,
                    approval_decision=approval_decision,
                    approval_time_ms=approval_time_ms,
                    success=False,
                )
                return ToolResult.failure_result(
                    tool_call_id="timeout",
                    error="Approval timeout - action skipped",
                ), events, False

            self.session.state = AgentState.EXECUTING

        # 3. Execute the tool
        result = await self._execute_tool_with_retry(tool_name, params)

        # 4. Audit the action
        duration_ms = (time.time() - start_time) * 1000
        self._log_audit(
            step_id=step_id,
            tool_name=tool_name,
            params=params,
            result={"data": result.data} if result.success else None,
            error=result.error,
            duration_ms=duration_ms,
            classification=classification,
            approval_decision=approval_decision,
            approval_time_ms=approval_time_ms,
            success=result.success,
        )

        return result, events, auto_executed

    def _log_audit(
        self,
        step_id: str,
        tool_name: str,
        params: dict,
        result: Optional[dict],
        error: Optional[str],
        duration_ms: float,
        classification,
        approval_decision: str,
        approval_time_ms: Optional[float],
        success: bool,
    ):
        """Log an action to the audit store."""
        entry = AuditEntry(
            session_id=self.session.id,
            step_id=step_id,
            tool_name=tool_name,
            parameters=params,
            result=result,
            error=error,
            duration_ms=duration_ms,
            risk_level=classification.risk_level,
            approval_required=classification.requires_approval,
            approval_decision=approval_decision,
            approved_by="user" if approval_decision == "approved" else None,
            approval_time_ms=approval_time_ms,
            success=success,
        )
        self.audit_store.log(entry)

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
