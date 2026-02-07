"""
Pydantic models for AI data structures.
"""

# Standard library
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

# Third-party
from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Configuration for an AI provider."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    enabled: bool = True
    priority: int = 0
    config: dict
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UsageRecord(BaseModel):
    """Record of AI API usage."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str | None = None
    node_id: str | None = None
    provider: str
    model: str
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0.0)
    latency_ms: int = Field(ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    success: bool = True
    error_message: str | None = None


class LocalModel(BaseModel):
    """Information about a downloaded local model."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    file_path: Path
    size_bytes: int
    quantization: str
    source: str  # 'recommended' | 'huggingface'
    huggingface_repo: str | None = None
    downloaded_at: datetime
    last_used: datetime | None = None
    usage_count: int = 0


class BudgetSettings(BaseModel):
    """Budget settings for AI usage."""

    id: str = "default"
    monthly_limit_usd: float | None = None
    alert_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    email_notifications: bool = False
    notification_email: str | None = None
    reset_day: int = Field(default=1, ge=1, le=31)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
