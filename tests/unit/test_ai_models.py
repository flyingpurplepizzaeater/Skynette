"""Tests for AI Pydantic models."""

import pytest
from datetime import datetime
from pathlib import Path

from src.ai.models.data import ProviderConfig, UsageRecord, LocalModel, BudgetSettings


class TestProviderConfig:
    """Test ProviderConfig model."""

    def test_create_provider_config(self):
        """Test creating a provider config."""
        config = ProviderConfig(
            name="openai",
            enabled=True,
            priority=0,
            config={"api_key_stored": True, "model": "gpt-4"}
        )

        assert config.name == "openai"
        assert config.enabled is True
        assert config.priority == 0
        assert config.config["model"] == "gpt-4"
        assert config.id is not None  # Auto-generated
        assert isinstance(config.created_at, datetime)

    def test_provider_config_defaults(self):
        """Test default values."""
        config = ProviderConfig(
            name="anthropic",
            config={}
        )

        assert config.enabled is True
        assert config.priority == 0


class TestUsageRecord:
    """Test UsageRecord model."""

    def test_create_usage_record(self):
        """Test creating a usage record."""
        record = UsageRecord(
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.0045,
            latency_ms=1200
        )

        assert record.provider == "openai"
        assert record.total_tokens == 150
        assert record.cost_usd == 0.0045
        assert record.success is True
        assert record.error_message is None

    def test_usage_record_with_workflow(self):
        """Test usage record with workflow ID."""
        record = UsageRecord(
            workflow_id="wf_123",
            node_id="node_456",
            provider="anthropic",
            model="claude-3-opus",
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
            cost_usd=0.0045,
            latency_ms=800
        )

        assert record.workflow_id == "wf_123"
        assert record.node_id == "node_456"

    def test_usage_record_with_error(self):
        """Test usage record with error."""
        record = UsageRecord(
            provider="openai",
            model="gpt-4",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            cost_usd=0.0,
            latency_ms=500,
            success=False,
            error_message="API key invalid"
        )

        assert record.success is False
        assert record.error_message == "API key invalid"


class TestLocalModel:
    """Test LocalModel model."""

    def test_create_local_model(self):
        """Test creating a local model."""
        model = LocalModel(
            name="Mistral 7B Instruct",
            file_path=Path("~/.skynette/models/mistral-7b.gguf"),
            size_bytes=4100000000,
            quantization="Q4_K_M",
            source="recommended",
            downloaded_at=datetime.utcnow()
        )

        assert model.name == "Mistral 7B Instruct"
        assert model.size_bytes == 4100000000
        assert model.usage_count == 0

    def test_local_model_with_huggingface(self):
        """Test local model from Hugging Face."""
        model = LocalModel(
            name="Mistral 7B",
            file_path=Path("/models/mistral.gguf"),
            size_bytes=4000000000,
            quantization="Q4_K_M",
            source="huggingface",
            huggingface_repo="TheBloke/Mistral-7B-GGUF",
            downloaded_at=datetime.utcnow()
        )

        assert model.source == "huggingface"
        assert model.huggingface_repo is not None


class TestBudgetSettings:
    """Test BudgetSettings model."""

    def test_create_budget_settings(self):
        """Test creating budget settings."""
        budget = BudgetSettings(
            monthly_limit_usd=10.0,
            alert_threshold=0.8,
            email_notifications=True,
            notification_email="user@example.com"
        )

        assert budget.monthly_limit_usd == 10.0
        assert budget.alert_threshold == 0.8
        assert budget.reset_day == 1

    def test_budget_defaults(self):
        """Test budget default values."""
        budget = BudgetSettings()

        assert budget.monthly_limit_usd is None
        assert budget.alert_threshold == 0.8
        assert budget.email_notifications is False
        assert budget.reset_day == 1
