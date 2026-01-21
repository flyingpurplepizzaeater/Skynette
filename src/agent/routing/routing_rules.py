"""
Routing Rules Configuration

User-configurable rules for model routing decisions.
"""

from typing import Dict, Optional

from pydantic import BaseModel


class RoutingRule(BaseModel):
    """A single routing rule mapping task category to model."""

    provider: str
    model: str
    reason: str


# Default routing rules by task category
DEFAULT_RULES: Dict[str, Dict[str, str]] = {
    "simple_query": {
        "provider": "anthropic",
        "model": "claude-3-haiku",
        "reason": "Fast and cost-effective for simple queries",
    },
    "code_generation": {
        "provider": "anthropic",
        "model": "claude-3-sonnet",
        "reason": "Strong code generation with good cost balance",
    },
    "code_review": {
        "provider": "anthropic",
        "model": "claude-3-sonnet",
        "reason": "Effective for code analysis",
    },
    "research": {
        "provider": "anthropic",
        "model": "claude-3-opus",
        "reason": "Best reasoning for complex multi-step research",
    },
    "creative": {
        "provider": "anthropic",
        "model": "claude-3-sonnet",
        "reason": "Good creative writing capabilities",
    },
    "analysis": {
        "provider": "anthropic",
        "model": "claude-3-opus",
        "reason": "Deep analytical reasoning",
    },
    "general": {
        "provider": "anthropic",
        "model": "claude-3-sonnet",
        "reason": "Good all-around performance",
    },
}


class RoutingRules(BaseModel):
    """
    Collection of routing rules with custom override support.

    Custom rules take precedence over defaults.
    """

    rules: Dict[str, RoutingRule] = {}

    def get_rule(self, category: str) -> RoutingRule:
        """
        Get the routing rule for a category.

        Custom rules override defaults.

        Args:
            category: Task category name

        Returns:
            RoutingRule for the category
        """
        # Check custom rules first
        if category in self.rules:
            return self.rules[category]

        # Fall back to defaults
        if category in DEFAULT_RULES:
            return RoutingRule(**DEFAULT_RULES[category])

        # Ultimate fallback to general
        return RoutingRule(**DEFAULT_RULES["general"])

    def set_rule(self, category: str, rule: RoutingRule) -> None:
        """
        Set a custom routing rule for a category.

        Args:
            category: Task category name
            rule: Custom routing rule
        """
        self.rules[category] = rule

    def reset_to_defaults(self) -> None:
        """Clear all custom rules, reverting to defaults."""
        self.rules = {}
