"""Tests for AI storage functionality."""

import pytest
import sqlite3
import json
from pathlib import Path
from datetime import datetime, date, timezone

from src.data.storage import WorkflowStorage
from src.ai.storage import AIStorage
from src.ai.models.data import ProviderConfig, UsageRecord, LocalModel, BudgetSettings


class TestAIStorageMigration:
    """Test AI database tables are created."""

    def test_ai_providers_table_exists(self, tmp_path):
        """Test ai_providers table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.cursor()

            # Check table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_providers'"
            )
            result = cursor.fetchone()

        assert result is not None, "ai_providers table should exist"

    def test_ai_usage_table_exists(self, tmp_path):
        """Test ai_usage table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_usage'"
            )
            result = cursor.fetchone()

        assert result is not None, "ai_usage table should exist"

    def test_local_models_table_exists(self, tmp_path):
        """Test local_models table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='local_models'"
            )
            result = cursor.fetchone()

        assert result is not None, "local_models table should exist"

    def test_ai_budgets_table_exists(self, tmp_path):
        """Test ai_budgets table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_budgets'"
            )
            result = cursor.fetchone()

        assert result is not None, "ai_budgets table should exist"

    def test_ai_usage_indices_exist(self, tmp_path):
        """Test indices on ai_usage table are created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        with sqlite3.connect(storage.db_path) as conn:
            cursor = conn.cursor()

            # Check indices exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ai_usage'"
            )
            indices = cursor.fetchall()

        index_names = [idx[0] for idx in indices]
        assert 'idx_ai_usage_workflow' in index_names
        assert 'idx_ai_usage_timestamp' in index_names
        assert 'idx_ai_usage_provider' in index_names


class TestAIStorage:
    """Test AIStorage service."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create AIStorage instance with temp database."""
        # Initialize WorkflowStorage first to create tables
        WorkflowStorage(data_dir=str(tmp_path))
        return AIStorage(db_path=str(tmp_path / "skynette.db"))

    # Provider Config Tests
    async def test_save_provider_config(self, storage):
        """Test saving provider config."""
        config = ProviderConfig(
            name="openai",
            config={"api_key_stored": True, "model": "gpt-4"}
        )

        await storage.save_provider_config(config)

        loaded = await storage.get_provider_config(config.id)
        assert loaded is not None
        assert loaded.name == "openai"
        assert loaded.config["model"] == "gpt-4"

    async def test_get_all_provider_configs(self, storage):
        """Test getting all provider configs."""
        config1 = ProviderConfig(name="openai", config={})
        config2 = ProviderConfig(name="anthropic", config={})

        await storage.save_provider_config(config1)
        await storage.save_provider_config(config2)

        configs = await storage.get_provider_configs()
        assert len(configs) == 2

    async def test_update_provider_priority(self, storage):
        """Test updating provider priority."""
        config = ProviderConfig(name="openai", priority=0, config={})
        await storage.save_provider_config(config)

        await storage.update_provider_priority(config.id, 5)

        updated = await storage.get_provider_config(config.id)
        assert updated.priority == 5

    async def test_delete_provider_config(self, storage):
        """Test deleting provider config."""
        config = ProviderConfig(name="openai", config={})
        await storage.save_provider_config(config)

        await storage.delete_provider_config(config.id)

        loaded = await storage.get_provider_config(config.id)
        assert loaded is None

    # Usage Tracking Tests
    async def test_log_usage(self, storage):
        """Test logging usage record."""
        record = UsageRecord(
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.0045,
            latency_ms=1200
        )

        await storage.log_usage(record)

        # Verify it was saved (we'll implement get methods)
        stats = await storage.get_usage_stats(date.today(), date.today())
        assert stats["total_calls"] >= 1

    async def test_get_cost_by_provider(self, storage):
        """Test getting cost breakdown by provider."""
        from datetime import datetime
        
        # Get current month and year for the test
        now = datetime.now()
        month = now.month
        year = now.year
        
        record1 = UsageRecord(
            provider="openai", model="gpt-4",
            prompt_tokens=100, completion_tokens=50, total_tokens=150,
            cost_usd=0.50, latency_ms=1000
        )
        record2 = UsageRecord(
            provider="anthropic", model="claude-3",
            prompt_tokens=200, completion_tokens=100, total_tokens=300,
            cost_usd=0.30, latency_ms=800
        )

        await storage.log_usage(record1)
        await storage.log_usage(record2)

        costs = await storage.get_cost_by_provider(month, year)
        assert costs["openai"] == 0.50
        assert costs["anthropic"] == 0.30

    # Model Management Tests
    async def test_save_model(self, storage):
        """Test saving local model."""
        model = LocalModel(
            name="Mistral 7B",
            file_path=Path("/models/mistral.gguf"),
            size_bytes=4000000000,
            quantization="Q4_K_M",
            source="recommended",
            downloaded_at=datetime.now(timezone.utc)
        )

        await storage.save_model(model)

        loaded = await storage.get_model(model.id)
        assert loaded is not None
        assert loaded.name == "Mistral 7B"

    async def test_get_downloaded_models(self, storage):
        """Test getting all downloaded models."""
        model1 = LocalModel(
            name="Mistral", file_path=Path("/m1.gguf"),
            size_bytes=4000000000, quantization="Q4_K_M",
            source="recommended", downloaded_at=datetime.now(timezone.utc)
        )
        model2 = LocalModel(
            name="Llama", file_path=Path("/m2.gguf"),
            size_bytes=3800000000, quantization="Q4_K_M",
            source="recommended", downloaded_at=datetime.now(timezone.utc)
        )

        await storage.save_model(model1)
        await storage.save_model(model2)

        models = await storage.get_downloaded_models()
        assert len(models) == 2

    async def test_update_model_usage(self, storage):
        """Test incrementing model usage count."""
        model = LocalModel(
            name="Mistral", file_path=Path("/m.gguf"),
            size_bytes=4000000000, quantization="Q4_K_M",
            source="recommended", downloaded_at=datetime.now(timezone.utc)
        )
        await storage.save_model(model)

        await storage.update_model_usage(model.id)

        updated = await storage.get_model(model.id)
        assert updated.usage_count == 1
        assert updated.last_used is not None

    # Budget Tests
    async def test_save_budget_settings(self, storage):
        """Test saving budget settings."""
        budget = BudgetSettings(
            monthly_limit_usd=10.0,
            alert_threshold=0.8
        )

        await storage.update_budget_settings(budget)

        loaded = await storage.get_budget_settings()
        assert loaded is not None
        assert loaded.monthly_limit_usd == 10.0


@pytest.mark.asyncio
class TestBudgetAlerts:
    """Tests for budget alert system."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create AIStorage instance with temp database."""
        # Initialize WorkflowStorage first to create tables
        WorkflowStorage(data_dir=str(tmp_path))
        return AIStorage(db_path=str(tmp_path / "skynette.db"))

    async def test_check_budget_alert_below_threshold(self, storage):
        """Should return no alert when below threshold."""
        from src.ai.models.data import BudgetSettings

        # Set budget: $100 limit, 80% threshold
        budget = BudgetSettings(monthly_limit_usd=100.0, alert_threshold=0.8, reset_day=1)
        await storage.update_budget_settings(budget)

        # Check with $50 spent (50%)
        alert = await storage.check_budget_alert(50.0)

        assert alert is None  # No alert yet

    async def test_check_budget_alert_at_threshold(self, storage):
        """Should return threshold alert at 80%."""
        from src.ai.models.data import BudgetSettings

        # Set budget: $100 limit, 80% threshold
        budget = BudgetSettings(monthly_limit_usd=100.0, alert_threshold=0.8, reset_day=1)
        await storage.update_budget_settings(budget)

        # Check with $80 spent (80%)
        alert = await storage.check_budget_alert(80.0)

        assert alert is not None
        assert alert["type"] == "threshold"
        assert alert["percentage"] >= 0.8

    async def test_check_budget_alert_exceeded(self, storage):
        """Should return exceeded alert at 100%."""
        from src.ai.models.data import BudgetSettings

        # Set budget: $100 limit, 80% threshold
        budget = BudgetSettings(monthly_limit_usd=100.0, alert_threshold=0.8, reset_day=1)
        await storage.update_budget_settings(budget)

        # Check with $105 spent (105%)
        alert = await storage.check_budget_alert(105.0)

        assert alert is not None
        assert alert["type"] == "exceeded"
        assert alert["percentage"] >= 1.0
