"""
Token Budget Tracking

Tracks token usage against a budget for agent sessions.
"""

from dataclasses import dataclass


@dataclass
class TokenBudget:
    """Track token usage against a budget."""

    max_tokens: int = 50000  # Default 50K tokens per task
    used_input_tokens: int = 0
    used_output_tokens: int = 0
    warning_threshold: float = 0.8  # Warn at 80%

    @property
    def used_total(self) -> int:
        """Total tokens consumed."""
        return self.used_input_tokens + self.used_output_tokens

    @property
    def remaining(self) -> int:
        """Tokens remaining in budget."""
        return max(0, self.max_tokens - self.used_total)

    @property
    def usage_percentage(self) -> float:
        """Usage as percentage (0.0 to 1.0)."""
        if self.max_tokens == 0:
            return 1.0
        return self.used_total / self.max_tokens

    def can_proceed(self, estimated_tokens: int = 0) -> bool:
        """Check if we can proceed with estimated additional usage."""
        return (self.used_total + estimated_tokens) <= self.max_tokens

    def consume(self, input_tokens: int, output_tokens: int) -> bool:
        """
        Record token consumption.
        Returns True if within budget, False if exceeded.
        """
        self.used_input_tokens += input_tokens
        self.used_output_tokens += output_tokens
        return self.used_total <= self.max_tokens

    def is_warning(self) -> bool:
        """True if approaching budget limit."""
        return self.usage_percentage >= self.warning_threshold

    def to_dict(self) -> dict:
        """Convert to dict for event data."""
        return {
            "max_tokens": self.max_tokens,
            "used_input": self.used_input_tokens,
            "used_output": self.used_output_tokens,
            "used_total": self.used_total,
            "remaining": self.remaining,
            "percentage": round(self.usage_percentage * 100, 1),
        }
