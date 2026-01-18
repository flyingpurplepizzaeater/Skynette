# src/ai/completions/__init__.py
"""AI completions utilities.

Provides TokenCounter for estimating context token usage.
"""

from .token_counter import TokenCounter

__all__ = ["TokenCounter"]
