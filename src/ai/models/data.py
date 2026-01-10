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
