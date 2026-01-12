"""
AI Storage Service

Handles all AI-related database operations.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, date, timezone
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
        with sqlite3.connect(self.db_path) as conn:
            pass

    # Provider Configuration Methods

    async def save_provider_config(self, config: ProviderConfig) -> None:
        """Save or update provider configuration."""
        with sqlite3.connect(self.db_path) as conn:
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

    async def get_provider_config(self, provider_id: str) -> Optional[ProviderConfig]:
        """Get provider configuration by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, enabled, priority, config, created_at, updated_at
                FROM ai_providers WHERE id = ?
            """, (provider_id,))

            row = cursor.fetchone()

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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, enabled, priority, config, created_at, updated_at
                FROM ai_providers ORDER BY priority ASC
            """)

            rows = cursor.fetchall()

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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE ai_providers
                SET priority = ?, updated_at = ?
                WHERE id = ?
            """, (priority, datetime.now(timezone.utc).isoformat(), provider_id))

            conn.commit()

    async def delete_provider_config(self, provider_id: str) -> None:
        """Delete provider configuration."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM ai_providers WHERE id = ?", (provider_id,))

            conn.commit()

    # Usage Tracking Methods

    async def log_usage(self, record: UsageRecord) -> None:
        """Log AI usage record."""
        with sqlite3.connect(self.db_path) as conn:
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

    async def get_usage_stats(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Get usage statistics for date range."""
        if end_date < start_date:
            raise ValueError("end_date must be >= start_date")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            start_str = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc).isoformat()
            end_str = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc).isoformat()

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

        return {
            "total_calls": row[0] or 0,
            "total_tokens": row[1] or 0,
            "total_cost": row[2] or 0.0,
            "avg_latency": row[3] or 0.0
        }

    async def get_cost_by_provider(self, month: int, year: int) -> Dict[str, float]:
        """Get cost breakdown by provider for a month."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            start_date = datetime(year, month, 1, tzinfo=timezone.utc)
            if month == 12:
                end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)

            cursor.execute("""
                SELECT provider, SUM(cost_usd) as total_cost
                FROM ai_usage
                WHERE timestamp >= ? AND timestamp < ?
                GROUP BY provider
            """, (start_date.isoformat(), end_date.isoformat()))

            rows = cursor.fetchall()

        return {row[0]: row[1] for row in rows}

    async def get_cost_by_workflow(self, month: int, year: int) -> Dict[str, float]:
        """Get cost breakdown by workflow for a month."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            start_date = datetime(year, month, 1, tzinfo=timezone.utc)
            if month == 12:
                end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)

            cursor.execute("""
                SELECT workflow_id, SUM(cost_usd) as total_cost
                FROM ai_usage
                WHERE timestamp >= ? AND timestamp < ?
                  AND workflow_id IS NOT NULL
                GROUP BY workflow_id
            """, (start_date.isoformat(), end_date.isoformat()))

            rows = cursor.fetchall()

        return {row[0]: row[1] for row in rows}

    async def get_total_cost(self, month: int, year: int) -> float:
        """Get total cost for a month."""
        costs = await self.get_cost_by_provider(month, year)
        return sum(costs.values())

    # Model Management Methods

    async def save_model(self, model: LocalModel) -> None:
        """Save or update local model."""
        with sqlite3.connect(self.db_path) as conn:
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

    async def get_model(self, model_id: str) -> Optional[LocalModel]:
        """Get local model by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, file_path, size_bytes, quantization, source,
                       huggingface_repo, downloaded_at, last_used, usage_count
                FROM local_models WHERE id = ?
            """, (model_id,))

            row = cursor.fetchone()

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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, file_path, size_bytes, quantization, source,
                       huggingface_repo, downloaded_at, last_used, usage_count
                FROM local_models ORDER BY downloaded_at DESC
            """)

            rows = cursor.fetchall()

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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE local_models
                SET usage_count = usage_count + 1,
                    last_used = ?
                WHERE id = ?
            """, (datetime.now(timezone.utc).isoformat(), model_id))

            conn.commit()

    async def delete_model(self, model_id: str) -> None:
        """Delete local model record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("DELETE FROM local_models WHERE id = ?", (model_id,))

            conn.commit()

    # Budget Methods

    async def get_budget_settings(self) -> Optional[BudgetSettings]:
        """Get budget settings."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, monthly_limit_usd, alert_threshold, email_notifications,
                       notification_email, reset_day, created_at, updated_at
                FROM ai_budgets WHERE id = 'default'
            """)

            row = cursor.fetchone()

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

    async def check_budget_alert(self, current_cost: float) -> Optional[Dict[str, Any]]:
        """
        Check if current cost triggers budget alert.

        Returns:
            None if no alert, or dict with alert details:
            {"type": "threshold|exceeded", "percentage": float, "limit": float, "current": float}
        """
        budget = await self.get_budget_settings()
        if not budget or budget.monthly_limit_usd <= 0:
            return None

        percentage = current_cost / budget.monthly_limit_usd

        if percentage >= 1.0:
            return {
                "type": "exceeded",
                "percentage": percentage,
                "limit": budget.monthly_limit_usd,
                "current": current_cost,
            }
        elif percentage >= budget.alert_threshold:
            return {
                "type": "threshold",
                "percentage": percentage,
                "limit": budget.monthly_limit_usd,
                "current": current_cost,
            }

        return None

    async def update_budget_settings(self, settings: BudgetSettings) -> None:
        """Save or update budget settings."""
        with sqlite3.connect(self.db_path) as conn:
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


# Singleton instance
_ai_storage_instance: Optional[AIStorage] = None


def get_ai_storage() -> AIStorage:
    """Get or create the global AIStorage instance."""
    global _ai_storage_instance
    if _ai_storage_instance is None:
        _ai_storage_instance = AIStorage()
    return _ai_storage_instance
