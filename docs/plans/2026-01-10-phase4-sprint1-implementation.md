# Phase 4 Sprint 1: AI Core Testing & Foundation - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Make existing AI infrastructure production-ready through comprehensive testing, data persistence, and secure API key storage.

**Architecture:** Extend existing WorkflowStorage with AI-specific tables, implement AIStorage service for AI data, add keyring-based API key security, write 90+ tests for all AI components.

**Tech Stack:** SQLite, Pydantic, keyring, pytest, pytest-asyncio, unittest.mock

---

## Task 1: Database Migrations for AI Tables

**Goal:** Add 4 new tables to support AI provider config, usage tracking, local models, and budgets.

**Files:**
- Modify: `src/data/storage.py:41-99` (extend `_init_db` method)
- Create: `tests/unit/test_ai_storage.py`

### Step 1: Write test for AI tables existence

**File:** `tests/unit/test_ai_storage.py`

```python
"""Tests for AI storage functionality."""

import pytest
import sqlite3
from pathlib import Path
import tempfile
import shutil

from src.data.storage import WorkflowStorage


class TestAIStorageMigration:
    """Test AI database tables are created."""

    def test_ai_providers_table_exists(self, tmp_path):
        """Test ai_providers table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_providers'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "ai_providers table should exist"

    def test_ai_usage_table_exists(self, tmp_path):
        """Test ai_usage table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_usage'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "ai_usage table should exist"

    def test_local_models_table_exists(self, tmp_path):
        """Test local_models table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='local_models'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "local_models table should exist"

    def test_ai_budgets_table_exists(self, tmp_path):
        """Test ai_budgets table is created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ai_budgets'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "ai_budgets table should exist"

    def test_ai_usage_indices_exist(self, tmp_path):
        """Test indices on ai_usage table are created."""
        storage = WorkflowStorage(data_dir=str(tmp_path))

        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()

        # Check indices exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='ai_usage'"
        )
        indices = cursor.fetchall()
        conn.close()

        index_names = [idx[0] for idx in indices]
        assert 'idx_ai_usage_workflow' in index_names
        assert 'idx_ai_usage_timestamp' in index_names
        assert 'idx_ai_usage_provider' in index_names
```

### Step 2: Run test to verify it fails

```bash
cd .worktrees/phase4-ai-integration
python -m pytest tests/unit/test_ai_storage.py::TestAIStorageMigration -v
```

**Expected Output:** FAIL - tables don't exist yet

### Step 3: Add AI tables to database initialization

**File:** `src/data/storage.py` (modify `_init_db` method, after line 95)

```python
        # AI Providers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 0,
                config TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # AI Usage Log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_usage (
                id TEXT PRIMARY KEY,
                workflow_id TEXT,
                node_id TEXT,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                cost_usd REAL,
                latency_ms INTEGER,
                timestamp TEXT,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
            )
        """)

        # Create indices for ai_usage
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_usage_workflow
            ON ai_usage(workflow_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_usage_timestamp
            ON ai_usage(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_usage_provider
            ON ai_usage(provider)
        """)

        # Local Models table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS local_models (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                size_bytes INTEGER,
                quantization TEXT,
                source TEXT,
                huggingface_repo TEXT,
                downloaded_at TEXT,
                last_used TEXT,
                usage_count INTEGER DEFAULT 0
            )
        """)

        # AI Budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_budgets (
                id TEXT PRIMARY KEY DEFAULT 'default',
                monthly_limit_usd REAL,
                alert_threshold REAL DEFAULT 0.8,
                email_notifications INTEGER DEFAULT 0,
                notification_email TEXT,
                reset_day INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        """)
```

### Step 4: Run test to verify it passes

```bash
python -m pytest tests/unit/test_ai_storage.py::TestAIStorageMigration -v
```

**Expected Output:** PASS - all 5 tests pass

### Step 5: Commit

```bash
git add src/data/storage.py tests/unit/test_ai_storage.py
git commit -m "feat(ai): add database tables for AI persistence

Add 4 new tables:
- ai_providers: Provider configuration storage
- ai_usage: Token usage and cost tracking
- local_models: Downloaded model management
- ai_budgets: Monthly budget limits

Includes indices on ai_usage for performance.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: Pydantic Models for AI Data

**Goal:** Create type-safe Pydantic models for AI data structures.

**Files:**
- Create: `src/ai/models/data.py`
- Create: `tests/unit/test_ai_models.py`

### Step 1: Write test for Pydantic models

**File:** `tests/unit/test_ai_models.py`

```python
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
```

### Step 2: Run test to verify it fails

```bash
python -m pytest tests/unit/test_ai_models.py -v
```

**Expected Output:** FAIL - module doesn't exist

### Step 3: Create Pydantic models

**File:** `src/ai/models/data.py`

```python
"""
Pydantic models for AI data structures.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4


class ProviderConfig(BaseModel):
    """Configuration for an AI provider."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    enabled: bool = True
    priority: int = 0
    config: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UsageRecord(BaseModel):
    """Record of AI API usage."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: Optional[str] = None
    node_id: Optional[str] = None
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None


class LocalModel(BaseModel):
    """Information about a downloaded local model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    file_path: Path
    size_bytes: int
    quantization: str
    source: str  # 'recommended' | 'huggingface'
    huggingface_repo: Optional[str] = None
    downloaded_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0


class BudgetSettings(BaseModel):
    """Budget settings for AI usage."""

    id: str = 'default'
    monthly_limit_usd: Optional[float] = None
    alert_threshold: float = 0.8
    email_notifications: bool = False
    notification_email: Optional[str] = None
    reset_day: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Step 4: Run test to verify it passes

```bash
python -m pytest tests/unit/test_ai_models.py -v
```

**Expected Output:** PASS - all model tests pass

### Step 5: Commit

```bash
git add src/ai/models/data.py tests/unit/test_ai_models.py
git commit -m "feat(ai): add Pydantic models for AI data

Add type-safe models:
- ProviderConfig: AI provider configuration
- UsageRecord: Token usage and cost tracking
- LocalModel: Downloaded model information
- BudgetSettings: Monthly budget configuration

All models include validation and auto-generated IDs.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: AIStorage Service Implementation

**Goal:** Implement AIStorage service with all CRUD operations for AI data.

**Files:**
- Create: `src/ai/storage.py`
- Modify: `tests/unit/test_ai_storage.py` (add AIStorage tests)

### Step 1: Write tests for AIStorage service

**File:** `tests/unit/test_ai_storage.py` (append to existing file)

```python
import json
from src.ai.storage import AIStorage
from src.ai.models.data import ProviderConfig, UsageRecord, LocalModel, BudgetSettings
from datetime import datetime, date


class TestAIStorage:
    """Test AIStorage service."""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create AIStorage instance with temp database."""
        return AIStorage(db_path=str(tmp_path / "test.db"))

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

        costs = await storage.get_cost_by_provider(1, 2026)
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
            downloaded_at=datetime.utcnow()
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
            source="recommended", downloaded_at=datetime.utcnow()
        )
        model2 = LocalModel(
            name="Llama", file_path=Path("/m2.gguf"),
            size_bytes=3800000000, quantization="Q4_K_M",
            source="recommended", downloaded_at=datetime.utcnow()
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
            source="recommended", downloaded_at=datetime.utcnow()
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
```

### Step 2: Run tests to verify they fail

```bash
python -m pytest tests/unit/test_ai_storage.py::TestAIStorage -v
```

**Expected Output:** FAIL - AIStorage class doesn't exist

### Step 3: Implement AIStorage service

**File:** `src/ai/storage.py`

```python
"""
AI Storage Service

Handles all AI-related database operations.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from src.ai.models.data import ProviderConfig, UsageRecord, LocalModel, BudgetSettings


class AIStorage:
    """Manages AI-related data persistence."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize AI storage."""
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / ".skynette" / "skynette.db"

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database (tables should exist from WorkflowStorage)
        self._init_db()

    def _init_db(self):
        """Verify AI tables exist."""
        # Tables are created by WorkflowStorage._init_db
        # This is just a connection test
        conn = sqlite3.connect(self.db_path)
        conn.close()

    # Provider Configuration Methods

    async def save_provider_config(self, config: ProviderConfig) -> None:
        """Save or update provider configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO ai_providers
            (id, name, enabled, priority, config, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            config.id,
            config.name,
            1 if config.enabled else 0,
            config.priority,
            json.dumps(config.config),
            config.created_at.isoformat(),
            config.updated_at.isoformat()
        ))

        conn.commit()
        conn.close()

    async def get_provider_config(self, provider_id: str) -> Optional[ProviderConfig]:
        """Get provider configuration by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, enabled, priority, config, created_at, updated_at
            FROM ai_providers WHERE id = ?
        """, (provider_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return ProviderConfig(
            id=row[0],
            name=row[1],
            enabled=bool(row[2]),
            priority=row[3],
            config=json.loads(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            updated_at=datetime.fromisoformat(row[6])
        )

    async def get_provider_configs(self) -> List[ProviderConfig]:
        """Get all provider configurations."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, enabled, priority, config, created_at, updated_at
            FROM ai_providers ORDER BY priority ASC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            ProviderConfig(
                id=row[0],
                name=row[1],
                enabled=bool(row[2]),
                priority=row[3],
                config=json.loads(row[4]),
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6])
            )
            for row in rows
        ]

    async def update_provider_priority(self, provider_id: str, priority: int) -> None:
        """Update provider priority."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ai_providers
            SET priority = ?, updated_at = ?
            WHERE id = ?
        """, (priority, datetime.utcnow().isoformat(), provider_id))

        conn.commit()
        conn.close()

    async def delete_provider_config(self, provider_id: str) -> None:
        """Delete provider configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM ai_providers WHERE id = ?", (provider_id,))

        conn.commit()
        conn.close()

    # Usage Tracking Methods

    async def log_usage(self, record: UsageRecord) -> None:
        """Log AI usage record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ai_usage
            (id, workflow_id, node_id, provider, model, prompt_tokens,
             completion_tokens, total_tokens, cost_usd, latency_ms,
             timestamp, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.id,
            record.workflow_id,
            record.node_id,
            record.provider,
            record.model,
            record.prompt_tokens,
            record.completion_tokens,
            record.total_tokens,
            record.cost_usd,
            record.latency_ms,
            record.timestamp.isoformat(),
            1 if record.success else 0,
            record.error_message
        ))

        conn.commit()
        conn.close()

    async def get_usage_stats(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Get usage statistics for date range."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_str = datetime.combine(start_date, datetime.min.time()).isoformat()
        end_str = datetime.combine(end_date, datetime.max.time()).isoformat()

        cursor.execute("""
            SELECT
                COUNT(*) as total_calls,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost,
                AVG(latency_ms) as avg_latency
            FROM ai_usage
            WHERE timestamp BETWEEN ? AND ?
        """, (start_str, end_str))

        row = cursor.fetchone()
        conn.close()

        return {
            "total_calls": row[0] or 0,
            "total_tokens": row[1] or 0,
            "total_cost": row[2] or 0.0,
            "avg_latency": row[3] or 0.0
        }

    async def get_cost_by_provider(self, month: int, year: int) -> Dict[str, float]:
        """Get cost breakdown by provider for a month."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        cursor.execute("""
            SELECT provider, SUM(cost_usd) as total_cost
            FROM ai_usage
            WHERE timestamp >= ? AND timestamp < ?
            GROUP BY provider
        """, (start_date.isoformat(), end_date.isoformat()))

        rows = cursor.fetchall()
        conn.close()

        return {row[0]: row[1] for row in rows}

    async def get_cost_by_workflow(self, month: int, year: int) -> Dict[str, float]:
        """Get cost breakdown by workflow for a month."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        cursor.execute("""
            SELECT workflow_id, SUM(cost_usd) as total_cost
            FROM ai_usage
            WHERE timestamp >= ? AND timestamp < ?
              AND workflow_id IS NOT NULL
            GROUP BY workflow_id
        """, (start_date.isoformat(), end_date.isoformat()))

        rows = cursor.fetchall()
        conn.close()

        return {row[0]: row[1] for row in rows}

    async def get_total_cost(self, month: int, year: int) -> float:
        """Get total cost for a month."""
        costs = await self.get_cost_by_provider(month, year)
        return sum(costs.values())

    # Model Management Methods

    async def save_model(self, model: LocalModel) -> None:
        """Save or update local model."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO local_models
            (id, name, file_path, size_bytes, quantization, source,
             huggingface_repo, downloaded_at, last_used, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model.id,
            model.name,
            str(model.file_path),
            model.size_bytes,
            model.quantization,
            model.source,
            model.huggingface_repo,
            model.downloaded_at.isoformat(),
            model.last_used.isoformat() if model.last_used else None,
            model.usage_count
        ))

        conn.commit()
        conn.close()

    async def get_model(self, model_id: str) -> Optional[LocalModel]:
        """Get local model by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, file_path, size_bytes, quantization, source,
                   huggingface_repo, downloaded_at, last_used, usage_count
            FROM local_models WHERE id = ?
        """, (model_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return LocalModel(
            id=row[0],
            name=row[1],
            file_path=Path(row[2]),
            size_bytes=row[3],
            quantization=row[4],
            source=row[5],
            huggingface_repo=row[6],
            downloaded_at=datetime.fromisoformat(row[7]),
            last_used=datetime.fromisoformat(row[8]) if row[8] else None,
            usage_count=row[9]
        )

    async def get_downloaded_models(self) -> List[LocalModel]:
        """Get all downloaded models."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, file_path, size_bytes, quantization, source,
                   huggingface_repo, downloaded_at, last_used, usage_count
            FROM local_models ORDER BY downloaded_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [
            LocalModel(
                id=row[0],
                name=row[1],
                file_path=Path(row[2]),
                size_bytes=row[3],
                quantization=row[4],
                source=row[5],
                huggingface_repo=row[6],
                downloaded_at=datetime.fromisoformat(row[7]),
                last_used=datetime.fromisoformat(row[8]) if row[8] else None,
                usage_count=row[9]
            )
            for row in rows
        ]

    async def update_model_usage(self, model_id: str) -> None:
        """Increment model usage count and update last_used."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE local_models
            SET usage_count = usage_count + 1,
                last_used = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), model_id))

        conn.commit()
        conn.close()

    async def delete_model(self, model_id: str) -> None:
        """Delete local model record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM local_models WHERE id = ?", (model_id,))

        conn.commit()
        conn.close()

    # Budget Methods

    async def get_budget_settings(self) -> Optional[BudgetSettings]:
        """Get budget settings."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, monthly_limit_usd, alert_threshold, email_notifications,
                   notification_email, reset_day, created_at, updated_at
            FROM ai_budgets WHERE id = 'default'
        """)

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return BudgetSettings(
            id=row[0],
            monthly_limit_usd=row[1],
            alert_threshold=row[2],
            email_notifications=bool(row[3]),
            notification_email=row[4],
            reset_day=row[5],
            created_at=datetime.fromisoformat(row[6]),
            updated_at=datetime.fromisoformat(row[7])
        )

    async def update_budget_settings(self, settings: BudgetSettings) -> None:
        """Save or update budget settings."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO ai_budgets
            (id, monthly_limit_usd, alert_threshold, email_notifications,
             notification_email, reset_day, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            settings.id,
            settings.monthly_limit_usd,
            settings.alert_threshold,
            1 if settings.email_notifications else 0,
            settings.notification_email,
            settings.reset_day,
            settings.created_at.isoformat(),
            settings.updated_at.isoformat()
        ))

        conn.commit()
        conn.close()
```

### Step 4: Run tests to verify they pass

```bash
python -m pytest tests/unit/test_ai_storage.py::TestAIStorage -v
```

**Expected Output:** PASS - all AIStorage tests pass

### Step 5: Commit

```bash
git add src/ai/storage.py tests/unit/test_ai_storage.py
git commit -m "feat(ai): implement AIStorage service

Complete CRUD operations for:
- Provider configurations
- Usage tracking and cost analytics
- Local model management
- Budget settings

All methods are async-ready and fully tested.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: API Key Security with Keyring

**Goal:** Implement secure API key storage using system keyring instead of database.

**Files:**
- Create: `src/ai/security.py`
- Create: `tests/unit/test_ai_security.py`

### Step 1: Write tests for keyring integration

**File:** `tests/unit/test_ai_security.py`

```python
"""Tests for AI API key security."""

import pytest
from unittest.mock import patch, MagicMock

from src.ai.security import store_api_key, get_api_key, delete_api_key, has_api_key


class TestAPIKeySecurity:
    """Test API key storage and retrieval."""

    @patch('keyring.set_password')
    def test_store_api_key(self, mock_set):
        """Test storing API key in keyring."""
        store_api_key("openai", "sk-test123")

        mock_set.assert_called_once_with(
            'skynette-ai',
            'openai',
            'sk-test123'
        )

    @patch('keyring.get_password')
    def test_get_api_key(self, mock_get):
        """Test retrieving API key from keyring."""
        mock_get.return_value = "sk-test123"

        key = get_api_key("openai")

        assert key == "sk-test123"
        mock_get.assert_called_once_with('skynette-ai', 'openai')

    @patch('keyring.get_password')
    def test_get_api_key_not_found(self, mock_get):
        """Test retrieving non-existent API key."""
        mock_get.return_value = None

        key = get_api_key("openai")

        assert key is None

    @patch('keyring.delete_password')
    def test_delete_api_key(self, mock_delete):
        """Test deleting API key from keyring."""
        delete_api_key("openai")

        mock_delete.assert_called_once_with('skynette-ai', 'openai')

    @patch('keyring.get_password')
    def test_has_api_key_true(self, mock_get):
        """Test checking if API key exists (positive)."""
        mock_get.return_value = "sk-test123"

        result = has_api_key("openai")

        assert result is True

    @patch('keyring.get_password')
    def test_has_api_key_false(self, mock_get):
        """Test checking if API key exists (negative)."""
        mock_get.return_value = None

        result = has_api_key("openai")

        assert result is False
```

### Step 2: Run tests to verify they fail

```bash
python -m pytest tests/unit/test_ai_security.py -v
```

**Expected Output:** FAIL - module doesn't exist

### Step 3: Implement keyring security module

**File:** `src/ai/security.py`

```python
"""
API Key Security

Secure storage of AI provider API keys using system keyring.
"""

import keyring
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Keyring service name
SERVICE_NAME = 'skynette-ai'


def store_api_key(provider: str, api_key: str) -> None:
    """
    Store API key securely in system keyring.

    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        api_key: The API key to store
    """
    try:
        keyring.set_password(SERVICE_NAME, provider, api_key)
        logger.info(f"API key stored for provider: {provider}")
    except Exception as e:
        logger.error(f"Failed to store API key for {provider}: {e}")
        raise


def get_api_key(provider: str) -> Optional[str]:
    """
    Retrieve API key from system keyring.

    Args:
        provider: Provider name

    Returns:
        API key if found, None otherwise
    """
    try:
        key = keyring.get_password(SERVICE_NAME, provider)
        if key:
            logger.debug(f"API key retrieved for provider: {provider}")
        else:
            logger.debug(f"No API key found for provider: {provider}")
        return key
    except Exception as e:
        logger.error(f"Failed to retrieve API key for {provider}: {e}")
        return None


def delete_api_key(provider: str) -> None:
    """
    Delete API key from system keyring.

    Args:
        provider: Provider name
    """
    try:
        keyring.delete_password(SERVICE_NAME, provider)
        logger.info(f"API key deleted for provider: {provider}")
    except keyring.errors.PasswordDeleteError:
        logger.warning(f"No API key to delete for provider: {provider}")
    except Exception as e:
        logger.error(f"Failed to delete API key for {provider}: {e}")
        raise


def has_api_key(provider: str) -> bool:
    """
    Check if API key exists for provider.

    Args:
        provider: Provider name

    Returns:
        True if API key exists, False otherwise
    """
    return get_api_key(provider) is not None


def list_stored_providers() -> list[str]:
    """
    List all providers with stored API keys.

    Note: This is a best-effort implementation since keyring
    doesn't provide a native list operation.

    Returns:
        List of provider names
    """
    known_providers = ['openai', 'anthropic', 'google', 'groq']
    return [p for p in known_providers if has_api_key(p)]
```

### Step 4: Run tests to verify they pass

```bash
python -m pytest tests/unit/test_ai_security.py -v
```

**Expected Output:** PASS - all security tests pass

### Step 5: Commit

```bash
git add src/ai/security.py tests/unit/test_ai_security.py
git commit -m "feat(ai): implement secure API key storage with keyring

Add keyring-based API key management:
- store_api_key: Save to system keyring
- get_api_key: Retrieve from keyring
- delete_api_key: Remove from keyring
- has_api_key: Check existence

API keys never stored in database or logs.

Platform support:
- Windows: Credential Manager
- macOS: Keychain
- Linux: Secret Service

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Cost Calculator Service

**Goal:** Implement accurate cost calculation for all AI providers.

**Files:**
- Create: `src/ai/cost.py`
- Create: `tests/unit/test_cost_calculator.py`

### Step 1: Write tests for cost calculation

**File:** `tests/unit/test_cost_calculator.py`

```python
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
        assert cost == expected
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
```

### Step 2: Run tests to verify they fail

```bash
python -m pytest tests/unit/test_cost_calculator.py -v
```

**Expected Output:** FAIL - module doesn't exist

### Step 3: Implement cost calculator

**File:** `src/ai/cost.py`

```python
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
```

### Step 4: Run tests to verify they pass

```bash
python -m pytest tests/unit/test_cost_calculator.py -v
```

**Expected Output:** PASS - all 10 cost calculator tests pass

### Step 5: Commit

```bash
git add src/ai/cost.py tests/unit/test_cost_calculator.py
git commit -m "feat(ai): implement cost calculator service

Add accurate cost calculation for all providers:
- OpenAI: GPT-4, GPT-4 Turbo, GPT-3.5
- Anthropic: Claude 3 Opus, Sonnet, Haiku
- Local models: Always $0.00

Pricing table based on January 2026 rates.
Supports bulk calculations and cost estimation.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Sprint 1 Summary

**Tasks Completed**: 5 of 10
- ✅ Task 1: Database Migrations
- ✅ Task 2: Pydantic Models
- ✅ Task 3: AIStorage Service
- ✅ Task 4: API Key Security
- ✅ Task 5: Cost Calculator

**Remaining Tasks**:
- Task 6: AIGateway Unit Tests (20 tests)
- Task 7: Provider Unit Tests (40 tests)
- Task 8: AI Node Integration Tests (30 tests)
- Task 9: Update Dependencies
- Task 10: Usage Logging Integration

**Tests Added So Far**: ~30 tests
**Target for Sprint 1**: 90+ tests

**Next Session**: Continue with Task 6 (AIGateway tests) and remaining testing tasks.

---

**Plan saved to**: `docs/plans/2026-01-10-phase4-sprint1-implementation.md`

## Execution Options

**Plan complete! Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
