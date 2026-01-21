"""
Model Router

Intelligent model selection based on task classification and cost awareness.
"""

import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from src.ai.cost import CostCalculator
from src.agent.routing.routing_rules import RoutingRules, RoutingRule, DEFAULT_RULES


class TaskCategory(str, Enum):
    """Categories of tasks for routing decisions."""

    SIMPLE_QUERY = "simple_query"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    RESEARCH = "research"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    GENERAL = "general"


class ModelRecommendation(BaseModel):
    """A model recommendation with cost estimate and alternatives."""

    provider: str
    model: str
    reason: str
    estimated_cost_usd: float
    capabilities: List[str] = Field(default_factory=lambda: ["chat"])
    alternatives: List["ModelRecommendation"] = Field(default_factory=list)


# Keyword patterns for task classification
TASK_KEYWORDS = {
    TaskCategory.CODE_GENERATION: [
        r"\bwrite\s+code\b",
        r"\bcreate\s+(a\s+)?function\b",
        r"\bimplement\b",
        r"\bbuild\b",
        r"\bwrite\s+(a\s+)?(python|javascript|typescript|java|go|rust)\b",
        r"\bcode\s+(to|that|for)\b",
        r"\bscript\b",
        r"\bprogram\b",
    ],
    TaskCategory.CODE_REVIEW: [
        r"\breview\b",
        r"\banalyze\s+code\b",
        r"\bfind\s+bugs\b",
        r"\brefactor\b",
        r"\bdebug\b",
        r"\bcode\s+quality\b",
    ],
    TaskCategory.RESEARCH: [
        r"\bresearch\b",
        r"\bfind\s+out\b",
        r"\binvestigate\b",
        r"\bexplore\b",
        r"\blearn\s+about\b",
        r"\bwhat\s+are\s+the\s+options\b",
    ],
    TaskCategory.SIMPLE_QUERY: [
        r"^what\s+is\b",
        r"^how\s+do\b",
        r"^when\s+",
        r"^where\s+",
        r"^who\s+",
        r"^can\s+you\s+tell\s+me\b",
        r"\bdefine\b",
        r"\bexplain\b",
    ],
    TaskCategory.CREATIVE: [
        r"\bwrite\s+(a\s+)?(story|poem|article|essay)\b",
        r"\bbrainstorm\b",
        r"\bdesign\b",
        r"\bcreative\b",
        r"\bimagine\b",
        r"\bgenerate\s+ideas\b",
    ],
    TaskCategory.ANALYSIS: [
        r"\banalyze\b",
        r"\bcompare\b",
        r"\bevaluate\b",
        r"\bassess\b",
        r"\bbreak\s+down\b",
        r"\bpros\s+and\s+cons\b",
    ],
}


class ModelRouter:
    """
    Route tasks to appropriate models based on classification and cost.

    Provides intelligent model selection with cost-aware recommendations
    and alternatives for user consideration.
    """

    def __init__(self, custom_rules: Optional[RoutingRules] = None):
        """
        Initialize the model router.

        Args:
            custom_rules: Optional custom routing rules to override defaults
        """
        self.rules = custom_rules or RoutingRules()
        self.cost_calc = CostCalculator()

    def classify_task(self, task: str) -> TaskCategory:
        """
        Classify a task into a category using keyword matching.

        Args:
            task: The user's task description

        Returns:
            TaskCategory for the task
        """
        task_lower = task.lower()

        # Check each category's keywords
        for category, patterns in TASK_KEYWORDS.items():
            for pattern in patterns:
                if re.search(pattern, task_lower, re.IGNORECASE):
                    return category

        # Default to general if no match
        return TaskCategory.GENERAL

    def recommend(
        self, task: str, estimated_tokens: int = 4000
    ) -> ModelRecommendation:
        """
        Get a model recommendation for a task.

        Args:
            task: The user's task description
            estimated_tokens: Estimated token usage for cost calculation

        Returns:
            ModelRecommendation with primary model and alternatives
        """
        # Classify the task
        category = self.classify_task(task)

        # Get routing rule for this category
        rule = self.rules.get_rule(category.value)

        # Calculate estimated cost
        estimated_cost = self.cost_calc.estimate_cost(
            provider=rule.provider,
            model=rule.model,
            estimated_tokens=estimated_tokens,
        )

        # Get capabilities based on model
        capabilities = self._get_capabilities(rule.provider, rule.model)

        # Get alternatives
        alternatives = self._get_alternatives(category, estimated_tokens)

        return ModelRecommendation(
            provider=rule.provider,
            model=rule.model,
            reason=rule.reason,
            estimated_cost_usd=estimated_cost,
            capabilities=capabilities,
            alternatives=alternatives,
        )

    def _get_capabilities(self, provider: str, model: str) -> List[str]:
        """Get capabilities for a model."""
        capabilities = ["chat"]

        # Add model-specific capabilities
        if "opus" in model.lower():
            capabilities.extend(["complex_reasoning", "long_context"])
        if "sonnet" in model.lower():
            capabilities.extend(["code_generation", "analysis"])
        if "haiku" in model.lower():
            capabilities.extend(["fast_response"])
        if "gpt-4" in model.lower():
            capabilities.extend(["complex_reasoning", "code_generation"])

        return capabilities

    def _get_alternatives(
        self, category: TaskCategory, estimated_tokens: int
    ) -> List[ModelRecommendation]:
        """
        Get alternative model recommendations.

        Always includes a cheaper option and a more capable option
        if not already the primary recommendation.
        """
        alternatives = []

        # Get the primary rule for comparison
        primary_rule = self.rules.get_rule(category.value)

        # Cheaper alternative (haiku)
        if primary_rule.model != "claude-3-haiku":
            haiku_cost = self.cost_calc.estimate_cost(
                "anthropic", "claude-3-haiku", estimated_tokens
            )
            alternatives.append(
                ModelRecommendation(
                    provider="anthropic",
                    model="claude-3-haiku",
                    reason="Fastest and most cost-effective option",
                    estimated_cost_usd=haiku_cost,
                    capabilities=["chat", "fast_response"],
                )
            )

        # More capable alternative (opus)
        if primary_rule.model != "claude-3-opus":
            opus_cost = self.cost_calc.estimate_cost(
                "anthropic", "claude-3-opus", estimated_tokens
            )
            alternatives.append(
                ModelRecommendation(
                    provider="anthropic",
                    model="claude-3-opus",
                    reason="Most capable for complex tasks",
                    estimated_cost_usd=opus_cost,
                    capabilities=["chat", "complex_reasoning", "long_context"],
                )
            )

        # Balanced alternative (sonnet) if not already primary
        if primary_rule.model != "claude-3-sonnet":
            sonnet_cost = self.cost_calc.estimate_cost(
                "anthropic", "claude-3-sonnet", estimated_tokens
            )
            alternatives.append(
                ModelRecommendation(
                    provider="anthropic",
                    model="claude-3-sonnet",
                    reason="Good balance of capability and cost",
                    estimated_cost_usd=sonnet_cost,
                    capabilities=["chat", "code_generation", "analysis"],
                )
            )

        return alternatives
