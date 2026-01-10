"""Tests for AI cost calculation."""

import pytest
from src.ai.cost import CostCalculator, PRICING


class TestCostCalculator:
    """Test cost calculation for various providers and models."""

    def setup_method(self):
        """Set up test."""
        self.calc = CostCalculator()

    def test_openai_gpt4_cost(self):
        """Test GPT-4 cost calculation."""
        cost = self.calc.calculate_cost(
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # GPT-4: $0.03/1K input, $0.06/1K output
        expected = (1000 * 0.03 / 1000) + (500 * 0.06 / 1000)
        assert cost == expected
        assert cost == 0.06  # 0.03 + 0.03

    def test_openai_gpt4_turbo_cost(self):
        """Test GPT-4 Turbo cost calculation."""
        cost = self.calc.calculate_cost(
            provider="openai",
            model="gpt-4-turbo",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # GPT-4 Turbo: $0.01/1K input, $0.03/1K output
        expected = (1000 * 0.01 / 1000) + (500 * 0.03 / 1000)
        assert cost == expected
        assert cost == 0.025  # 0.01 + 0.015

    def test_openai_gpt35_cost(self):
        """Test GPT-3.5 Turbo cost calculation."""
        cost = self.calc.calculate_cost(
            provider="openai",
            model="gpt-3.5-turbo",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # GPT-3.5 Turbo: $0.0015/1K input, $0.002/1K output
        expected = (1000 * 0.0015 / 1000) + (500 * 0.002 / 1000)
        assert cost == expected
        assert cost == 0.0025  # 0.0015 + 0.001

    def test_anthropic_opus_cost(self):
        """Test Claude 3 Opus cost calculation."""
        cost = self.calc.calculate_cost(
            provider="anthropic",
            model="claude-3-opus",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # Opus: $0.015/1K input, $0.075/1K output
        expected = (1000 * 0.015 / 1000) + (500 * 0.075 / 1000)
        assert cost == expected
        assert cost == 0.0525  # 0.015 + 0.0375

    def test_anthropic_sonnet_cost(self):
        """Test Claude 3 Sonnet cost calculation."""
        cost = self.calc.calculate_cost(
            provider="anthropic",
            model="claude-3-sonnet",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # Sonnet: $0.003/1K input, $0.015/1K output
        expected = (1000 * 0.003 / 1000) + (500 * 0.015 / 1000)
        assert cost == pytest.approx(expected, rel=1e-6)
        assert cost == 0.0105  # 0.003 + 0.0075

    def test_anthropic_haiku_cost(self):
        """Test Claude 3 Haiku cost calculation."""
        cost = self.calc.calculate_cost(
            provider="anthropic",
            model="claude-3-haiku",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # Haiku: $0.00025/1K input, $0.00125/1K output
        expected = (1000 * 0.00025 / 1000) + (500 * 0.00125 / 1000)
        assert cost == expected
        assert cost == 0.000875  # 0.00025 + 0.000625

    def test_local_model_cost_is_zero(self):
        """Test local models have zero cost."""
        cost = self.calc.calculate_cost(
            provider="local",
            model="mistral-7b",
            prompt_tokens=1000,
            completion_tokens=500
        )

        assert cost == 0.0

    def test_unknown_model_fallback(self):
        """Test unknown model uses provider default pricing."""
        cost = self.calc.calculate_cost(
            provider="openai",
            model="unknown-model",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # Should use GPT-4 pricing as fallback
        expected = (1000 * 0.03 / 1000) + (500 * 0.06 / 1000)
        assert cost == expected

    def test_cost_rounding(self):
        """Test cost is rounded to appropriate precision."""
        cost = self.calc.calculate_cost(
            provider="openai",
            model="gpt-4",
            prompt_tokens=1,
            completion_tokens=1
        )

        # Very small cost, should still be accurate
        expected = (1 * 0.03 / 1000) + (1 * 0.06 / 1000)
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_bulk_cost_calculation(self):
        """Test calculating cost for multiple requests."""
        requests = [
            {"provider": "openai", "model": "gpt-4", "prompt_tokens": 100, "completion_tokens": 50},
            {"provider": "anthropic", "model": "claude-3-sonnet", "prompt_tokens": 200, "completion_tokens": 100},
            {"provider": "local", "model": "mistral", "prompt_tokens": 300, "completion_tokens": 150},
        ]

        total_cost = self.calc.bulk_calculate_cost(requests)

        # Calculate expected
        expected = 0.0
        expected += self.calc.calculate_cost("openai", "gpt-4", 100, 50)
        expected += self.calc.calculate_cost("anthropic", "claude-3-sonnet", 200, 100)
        expected += 0.0  # local is free

        assert total_cost == expected

    def test_estimate_cost(self):
        """Test cost estimation with 70/30 split."""
        cost = self.calc.estimate_cost(
            provider="openai",
            model="gpt-4",
            estimated_tokens=1000
        )

        # Should split 1000 tokens into 700 input + 300 output
        expected = self.calc.calculate_cost("openai", "gpt-4", 700, 300)
        assert cost == expected

    def test_get_model_pricing_existing_model(self):
        """Test getting pricing for existing model."""
        pricing = self.calc.get_model_pricing("openai", "gpt-4")

        assert pricing["input"] == 30.0
        assert pricing["output"] == 60.0

    def test_get_model_pricing_wildcard(self):
        """Test getting pricing for wildcard provider."""
        pricing = self.calc.get_model_pricing("local", "any-model")

        assert pricing["input"] == 0.0
        assert pricing["output"] == 0.0

    def test_get_model_pricing_unknown_provider(self):
        """Test getting pricing for unknown provider."""
        pricing = self.calc.get_model_pricing("unknown", "model")

        assert pricing["input"] == 0.0
        assert pricing["output"] == 0.0

    def test_negative_tokens_raises_error(self):
        """Test that negative tokens are rejected."""
        with pytest.raises(ValueError, match="Token counts cannot be negative"):
            self.calc.calculate_cost("openai", "gpt-4", -100, 50)

        with pytest.raises(ValueError, match="Token counts cannot be negative"):
            self.calc.calculate_cost("openai", "gpt-4", 100, -50)

    def test_invalid_token_type_raises_error(self):
        """Test that non-integer tokens are rejected."""
        with pytest.raises(TypeError, match="Token counts must be integers"):
            self.calc.calculate_cost("openai", "gpt-4", "100", 50)

        with pytest.raises(TypeError, match="Token counts must be integers"):
            self.calc.calculate_cost("openai", "gpt-4", 100.5, 50)

    def test_unknown_provider(self):
        """Test unknown provider returns zero cost."""
        cost = self.calc.calculate_cost("unknown-provider", "model", 1000, 500)
        assert cost == 0.0

    def test_versioned_model_name(self):
        """Test versioned model names work correctly."""
        cost = self.calc.calculate_cost(
            provider="anthropic",
            model="claude-3-opus-20240229",
            prompt_tokens=1000,
            completion_tokens=500
        )

        # Should use same pricing as claude-3-opus
        expected = (1000 * 0.015 / 1000) + (500 * 0.075 / 1000)
        assert cost == expected

    def test_zero_tokens(self):
        """Test zero tokens results in zero cost."""
        cost = self.calc.calculate_cost("openai", "gpt-4", 0, 0)
        assert cost == 0.0
