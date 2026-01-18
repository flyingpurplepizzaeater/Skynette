# src/ai/completions/__init__.py
"""AI completions utilities.

Provides TokenCounter for estimating context token usage,
and CompletionService for fetching inline code completions.
"""

from .completion_service import CompletionRequest, CompletionService
from .token_counter import TokenCounter

__all__ = ["CompletionRequest", "CompletionService", "TokenCounter"]
