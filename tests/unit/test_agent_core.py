"""
Unit tests for Agent Core Components

Tests for TokenBudget, AgentEventEmitter, AgentPlanner, AgentExecutor,
ModelRouter, and Cancellation components.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.budget import TokenBudget
from src.agent.events import AgentEventEmitter, EventSubscription
from src.agent.loop.executor import AgentExecutor
from src.agent.loop.planner import AgentPlanner
from src.agent.models.cancel import (
    CancelMode,
    CancellationRequest,
    CancellationResult,
    ResultMode,
)
from src.agent.models.event import AgentEvent
from src.agent.models.state import AgentSession, AgentState
from src.agent.routing import ModelRouter, ModelRecommendation, TaskCategory
from src.agent.routing.routing_rules import RoutingRules, RoutingRule


class TestTokenBudget:
    """Test TokenBudget token tracking and limits."""

    def test_initial_state(self):
        """Budget starts with 0 used, full remaining."""
        budget = TokenBudget(max_tokens=10000)
        assert budget.used_input_tokens == 0
        assert budget.used_output_tokens == 0
        assert budget.used_total == 0
        assert budget.remaining == 10000

    def test_consume_tokens(self):
        """consume() updates counts correctly."""
        budget = TokenBudget(max_tokens=10000)
        result = budget.consume(input_tokens=100, output_tokens=50)
        assert result is True  # Still within budget
        assert budget.used_input_tokens == 100
        assert budget.used_output_tokens == 50
        assert budget.used_total == 150
        assert budget.remaining == 9850

    def test_can_proceed_under_budget(self):
        """can_proceed() returns True when tokens available."""
        budget = TokenBudget(max_tokens=10000)
        budget.consume(5000, 0)
        assert budget.can_proceed() is True
        assert budget.can_proceed(estimated_tokens=4000) is True

    def test_can_proceed_over_budget(self):
        """can_proceed() returns False when budget exceeded."""
        budget = TokenBudget(max_tokens=10000)
        budget.consume(10000, 0)
        assert budget.can_proceed() is True  # At limit, still can proceed
        budget.consume(1, 0)
        assert budget.can_proceed() is False  # Over limit

    def test_can_proceed_with_estimate(self):
        """can_proceed() considers estimated future tokens."""
        budget = TokenBudget(max_tokens=10000)
        budget.consume(8000, 0)
        assert budget.can_proceed(estimated_tokens=3000) is False
        assert budget.can_proceed(estimated_tokens=2000) is True

    def test_is_warning_at_threshold(self):
        """is_warning() returns True at 80%+."""
        budget = TokenBudget(max_tokens=10000, warning_threshold=0.8)
        budget.consume(7999, 0)
        assert budget.is_warning() is False  # 79.99%
        budget.consume(1, 0)
        assert budget.is_warning() is True  # 80%
        budget.consume(1000, 0)
        assert budget.is_warning() is True  # 90%

    def test_to_dict_serialization(self):
        """to_dict() returns correct structure."""
        budget = TokenBudget(max_tokens=10000)
        budget.consume(1000, 500)
        d = budget.to_dict()
        assert d["max_tokens"] == 10000
        assert d["used_input"] == 1000
        assert d["used_output"] == 500
        assert d["used_total"] == 1500
        assert d["remaining"] == 8500
        assert d["percentage"] == 15.0


class TestAgentEventEmitter:
    """Test AgentEventEmitter subscription and broadcasting."""

    def test_subscribe_creates_subscription(self):
        """subscribe() returns EventSubscription."""
        emitter = AgentEventEmitter()
        subscription = emitter.subscribe()
        assert isinstance(subscription, EventSubscription)
        assert len(emitter._subscribers) == 1

    @pytest.mark.asyncio
    async def test_emit_reaches_subscriber(self):
        """Emitted event received by subscriber."""
        emitter = AgentEventEmitter()
        subscription = emitter.subscribe()

        # Use a valid event type (message is a valid AgentEventType)
        event = AgentEvent(type="message", data={"key": "value"}, session_id="s1")
        await emitter.emit(event)

        # Get event from queue with timeout
        received = await asyncio.wait_for(
            subscription._queue.get(), timeout=1.0
        )
        assert received.type == "message"
        assert received.data["key"] == "value"

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        """Multiple subscribers each receive events."""
        emitter = AgentEventEmitter()
        sub1 = emitter.subscribe()
        sub2 = emitter.subscribe()

        # Use a valid event type
        event = AgentEvent(type="message", data={"broadcast": True}, session_id="s1")
        await emitter.emit(event)

        received1 = await asyncio.wait_for(sub1._queue.get(), timeout=1.0)
        received2 = await asyncio.wait_for(sub2._queue.get(), timeout=1.0)

        assert received1.type == "message"
        assert received2.type == "message"

    @pytest.mark.asyncio
    async def test_bounded_queue_drops_events(self):
        """Slow subscriber doesn't block, events dropped."""
        emitter = AgentEventEmitter()
        # Create subscription with very small queue
        subscription = emitter.subscribe(maxsize=2)

        # Emit more events than queue can hold - use valid event types
        valid_types = ["message", "step_started", "step_completed", "error", "completed"]
        for i in range(5):
            event = AgentEvent(type=valid_types[i], data={"idx": i}, session_id="s1")
            await emitter.emit(event)

        # Queue should have at most maxsize events
        assert subscription._queue.qsize() <= 2

    def test_unsubscribe_removes_subscriber(self):
        """close() removes subscriber from list."""
        emitter = AgentEventEmitter()
        subscription = emitter.subscribe()
        assert len(emitter._subscribers) == 1

        subscription.close()
        assert len(emitter._subscribers) == 0


class TestAgentPlanner:
    """Test AgentPlanner plan generation."""

    def test_planner_has_system_prompt(self):
        """System prompt includes tool descriptions."""
        planner = AgentPlanner()
        assert "Available tools:" in planner.SYSTEM_PROMPT
        assert "steps" in planner.SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_fallback_plan_on_failure(self):
        """Returns single-step plan when AI fails."""
        planner = AgentPlanner()

        # Mock gateway to raise exception
        with patch.object(planner, 'gateway') as mock_gateway:
            mock_gateway.chat = AsyncMock(side_effect=Exception("API Error"))

            plan = await planner.create_plan("Test task")

            # Should return fallback plan
            assert plan.task == "Test task"
            assert "Fallback" in plan.overview or "fallback" in plan.overview.lower()
            assert len(plan.steps) == 1


class TestAgentExecutor:
    """Test AgentExecutor lifecycle and cancellation."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        return AgentSession(task="Test task", token_budget=10000)

    def test_executor_initial_state(self, mock_session):
        """Executor created with session."""
        executor = AgentExecutor(mock_session)
        assert executor.session == mock_session
        assert executor._cancel_request is None

    def test_cancel_sets_flag(self, mock_session):
        """cancel() sets cancelled state via request."""
        executor = AgentExecutor(mock_session)
        executor.cancel()
        assert executor._cancel_request is not None
        assert executor._cancel_request.cancel_mode == CancelMode.IMMEDIATE

    def test_cancel_request_stores_request(self, mock_session):
        """request_cancel() stores CancellationRequest."""
        executor = AgentExecutor(mock_session)
        req = CancellationRequest(
            cancel_mode=CancelMode.AFTER_CURRENT,
            result_mode=ResultMode.KEEP,
            reason="Test cancel"
        )
        executor.request_cancel(req)

        assert executor._cancel_request is not None
        assert executor._cancel_request.cancel_mode == CancelMode.AFTER_CURRENT
        assert executor._cancel_request.result_mode == ResultMode.KEEP

    def test_should_cancel_immediate(self, mock_session):
        """IMMEDIATE mode cancels regardless of step state."""
        executor = AgentExecutor(mock_session)
        req = CancellationRequest(
            cancel_mode=CancelMode.IMMEDIATE,
            result_mode=ResultMode.KEEP
        )
        executor.request_cancel(req)

        # Should cancel immediately
        assert executor._should_cancel() is True

    def test_should_cancel_after_current_no_step(self, mock_session):
        """AFTER_CURRENT cancels when no step is running."""
        executor = AgentExecutor(mock_session)
        req = CancellationRequest(
            cancel_mode=CancelMode.AFTER_CURRENT,
            result_mode=ResultMode.KEEP
        )
        executor.request_cancel(req)
        executor._current_step = None

        assert executor._should_cancel() is True


class TestModelRouter:
    """Test ModelRouter task classification and recommendations."""

    def test_classify_code_generation(self):
        """'write code' -> CODE_GENERATION."""
        router = ModelRouter()
        category = router.classify_task("Write code to parse JSON")
        assert category == TaskCategory.CODE_GENERATION

    def test_classify_simple_query(self):
        """'what is' -> SIMPLE_QUERY."""
        router = ModelRouter()
        category = router.classify_task("What is the capital of France?")
        assert category == TaskCategory.SIMPLE_QUERY

    def test_classify_research(self):
        """'research' -> RESEARCH."""
        router = ModelRouter()
        category = router.classify_task("Research the history of AI")
        assert category == TaskCategory.RESEARCH

    def test_classify_code_review(self):
        """'review' -> CODE_REVIEW."""
        router = ModelRouter()
        # Use a phrase that matches code review but not code generation
        category = router.classify_task("Please review my pull request")
        assert category == TaskCategory.CODE_REVIEW

    def test_classify_creative(self):
        """'write a story' -> CREATIVE."""
        router = ModelRouter()
        category = router.classify_task("Write a story about a robot")
        assert category == TaskCategory.CREATIVE

    def test_classify_analysis(self):
        """'analyze' -> ANALYSIS."""
        router = ModelRouter()
        category = router.classify_task("Analyze this market data")
        assert category == TaskCategory.ANALYSIS

    def test_classify_defaults_to_general(self):
        """Unrecognized -> GENERAL."""
        router = ModelRouter()
        category = router.classify_task("Do something random for me")
        assert category == TaskCategory.GENERAL

    def test_recommend_returns_valid_model(self):
        """Recommendation has provider, model, cost."""
        router = ModelRouter()
        rec = router.recommend("Write some Python code")

        assert rec.provider is not None
        assert rec.model is not None
        assert rec.estimated_cost_usd >= 0
        assert rec.reason is not None

    def test_recommend_includes_alternatives(self):
        """Alternatives list not empty."""
        router = ModelRouter()
        rec = router.recommend("Help with a task")

        assert len(rec.alternatives) > 0
        for alt in rec.alternatives:
            assert isinstance(alt, ModelRecommendation)
            assert alt.estimated_cost_usd >= 0

    def test_custom_rules_override_defaults(self):
        """Custom rules take precedence."""
        custom_rules = RoutingRules()
        custom_rules.set_rule("simple_query", RoutingRule(
            provider="local",
            model="mistral-7b",
            reason="Use local model"
        ))

        router = ModelRouter(custom_rules=custom_rules)
        rec = router.recommend("What is 2+2?")

        assert rec.provider == "local"
        assert rec.model == "mistral-7b"

    def test_routing_rules_get_rule_default(self):
        """get_rule returns default when no custom rule."""
        rules = RoutingRules()
        rule = rules.get_rule("code_generation")

        assert rule.provider == "anthropic"
        assert rule.model == "claude-3-sonnet"

    def test_routing_rules_reset_to_defaults(self):
        """reset_to_defaults clears custom rules."""
        rules = RoutingRules()
        rules.set_rule("test", RoutingRule(
            provider="custom",
            model="custom-model",
            reason="Custom"
        ))

        assert "test" in rules.rules
        rules.reset_to_defaults()
        assert len(rules.rules) == 0


class TestCancellation:
    """Test cancellation models and enums."""

    def test_cancellation_request_modes(self):
        """CancelMode and ResultMode enums work."""
        assert CancelMode.IMMEDIATE.value == "immediate"
        assert CancelMode.AFTER_CURRENT.value == "after_current"
        assert ResultMode.KEEP.value == "keep"
        assert ResultMode.ROLLBACK.value == "rollback"

    def test_cancellation_request_creation(self):
        """CancellationRequest creates with all fields."""
        req = CancellationRequest(
            cancel_mode=CancelMode.AFTER_CURRENT,
            result_mode=ResultMode.KEEP,
            reason="User requested"
        )

        assert req.cancel_mode == CancelMode.AFTER_CURRENT
        assert req.result_mode == ResultMode.KEEP
        assert req.reason == "User requested"
        assert isinstance(req.requested_at, datetime)

    def test_cancellation_result_structure(self):
        """CancellationResult includes required fields."""
        result = CancellationResult(
            completed_steps=["Step 1", "Step 2"],
            cancelled_step="Step 3",
            cancel_mode=CancelMode.IMMEDIATE,
            result_mode=ResultMode.KEEP
        )

        assert len(result.completed_steps) == 2
        assert result.cancelled_step == "Step 3"
        assert result.cancel_mode == CancelMode.IMMEDIATE
        assert "resume" in result.options
        assert "restart" in result.options
        assert "abandon" in result.options
