"""
AI Cost Calculator

Calculate costs for AI API usage across different providers.
"""

from typing import Dict, Any, List

# Pricing per 1M tokens (January 2026)
PRICING = {
    "openai": {
        "gpt-4": {
            "input": 30.0,  # $30 per 1M tokens
            "output": 60.0   # $60 per 1M tokens
        },
        "gpt-4-turbo": {
            "input": 10.0,
            "output": 30.0
        },
        "gpt-3.5-turbo": {
            "input": 1.5,
            "output": 2.0
        },
        "gpt-4o": {
            "input": 5.0,
            "output": 15.0
        },
        "gpt-4o-mini": {
            "input": 0.15,
            "output": 0.6
        }
    },
    "anthropic": {
        "claude-3-opus": {
            "input": 15.0,
            "output": 75.0
        },
        "claude-3-opus-20240229": {
            "input": 15.0,
            "output": 75.0
        },
        "claude-3-sonnet": {
            "input": 3.0,
            "output": 15.0
        },
        "claude-3-sonnet-20240229": {
            "input": 3.0,
            "output": 15.0
        },
        "claude-3-haiku": {
            "input": 0.25,
            "output": 1.25
        },
        "claude-3-haiku-20240307": {
            "input": 0.25,
            "output": 1.25
        }
    },
    "local": {
        "*": {  # All local models are free
            "input": 0.0,
            "output": 0.0
        }
    },
    "demo": {
        "*": {  # Demo provider is free
            "input": 0.0,
            "output": 0.0
        }
    }
}


class CostCalculator:
    """Calculate AI API costs."""

    def __init__(self, pricing: Dict[str, Any] = None):
        """
        Initialize cost calculator.

        Args:
            pricing: Optional custom pricing table
        """
        self.pricing = pricing or PRICING

    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for AI API call.

        Args:
            provider: Provider name (e.g., 'openai')
            model: Model name (e.g., 'gpt-4')
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # Get provider pricing
        if provider not in self.pricing:
            return 0.0

        provider_pricing = self.pricing[provider]

        # Get model pricing
        if model in provider_pricing:
            model_pricing = provider_pricing[model]
        elif "*" in provider_pricing:
            # Use wildcard pricing for unknown models
            model_pricing = provider_pricing["*"]
        else:
            # Fallback to first model in provider (usually most expensive)
            model_pricing = list(provider_pricing.values())[0]

        # Calculate cost per 1M tokens
        input_cost = (prompt_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * model_pricing["output"]

        total_cost = input_cost + output_cost

        # Round to 6 decimal places (nearest $0.000001)
        return round(total_cost, 6)

    def bulk_calculate_cost(self, requests: List[Dict[str, Any]]) -> float:
        """
        Calculate total cost for multiple requests.

        Args:
            requests: List of dicts with provider, model, prompt_tokens, completion_tokens

        Returns:
            Total cost in USD
        """
        total = 0.0
        for req in requests:
            total += self.calculate_cost(
                req["provider"],
                req["model"],
                req["prompt_tokens"],
                req["completion_tokens"]
            )
        return round(total, 6)

    def estimate_cost(
        self,
        provider: str,
        model: str,
        estimated_tokens: int
    ) -> float:
        """
        Estimate cost for a request.

        Assumes 70% input, 30% output token distribution.

        Args:
            provider: Provider name
            model: Model name
            estimated_tokens: Total estimated tokens

        Returns:
            Estimated cost in USD
        """
        prompt_tokens = int(estimated_tokens * 0.7)
        completion_tokens = int(estimated_tokens * 0.3)

        return self.calculate_cost(
            provider,
            model,
            prompt_tokens,
            completion_tokens
        )

    def get_model_pricing(self, provider: str, model: str) -> Dict[str, float]:
        """
        Get pricing info for a specific model.

        Args:
            provider: Provider name
            model: Model name

        Returns:
            Dict with 'input' and 'output' costs per 1M tokens
        """
        if provider not in self.pricing:
            return {"input": 0.0, "output": 0.0}

        provider_pricing = self.pricing[provider]

        if model in provider_pricing:
            return provider_pricing[model]
        elif "*" in provider_pricing:
            return provider_pricing["*"]
        else:
            return {"input": 0.0, "output": 0.0}
