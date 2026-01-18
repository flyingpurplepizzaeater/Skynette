# src/ai/completions/token_counter.py
"""Token counting for AI context estimation.

Uses tiktoken for accurate token counts with OpenAI models,
and provides fallback approximations for other providers.
"""

import tiktoken


class TokenCounter:
    """Estimate token counts for different AI providers.

    Uses tiktoken encodings for accurate counts with OpenAI models,
    and provides fallback approximations for other providers.

    Example:
        counter = TokenCounter()
        tokens = counter.count_tokens("Hello, world!")
        print(f"Token count: {tokens}")  # ~3 tokens

        if counter.is_within_limit(code, limit=4000, provider="openai"):
            # Safe to send to API
            pass
    """

    def __init__(self):
        """Initialize encodings for token counting."""
        # cl100k_base for GPT-4/GPT-3.5-turbo
        self._openai_enc = tiktoken.get_encoding("cl100k_base")
        # p50k_base as fallback approximation for other providers
        self._fallback_enc = tiktoken.get_encoding("p50k_base")

    def count_tokens(self, text: str, provider: str = "openai") -> int:
        """Count tokens for the given text and provider.

        Args:
            text: Text to count tokens for.
            provider: Provider name (openai, anthropic, gemini, grok, ollama).

        Returns:
            Estimated token count.
        """
        if provider in ("openai", "gpt-4", "gpt-3.5"):
            return len(self._openai_enc.encode(text))
        # Other providers use fallback (approximation)
        return len(self._fallback_enc.encode(text))

    def estimate_heuristic(self, text: str) -> int:
        """Quick heuristic estimate: ~4 chars per token average.

        Useful when speed is more important than accuracy.

        Args:
            text: Text to estimate tokens for.

        Returns:
            Estimated token count using character-based heuristic.
        """
        return len(text) // 4

    def is_within_limit(self, text: str, limit: int, provider: str = "openai") -> bool:
        """Check if text is within token limit.

        Args:
            text: Text to check.
            limit: Maximum token count allowed.
            provider: Provider name for accurate counting.

        Returns:
            True if text is within the limit.
        """
        return self.count_tokens(text, provider) <= limit

    def count_messages(
        self, messages: list[dict], provider: str = "openai"
    ) -> int:
        """Count tokens for a list of chat messages.

        Accounts for message formatting overhead.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            provider: Provider name for accurate counting.

        Returns:
            Estimated total token count including overhead.
        """
        total = 0
        for msg in messages:
            # ~4 tokens overhead per message for formatting
            total += 4
            if "role" in msg:
                total += self.count_tokens(msg["role"], provider)
            if "content" in msg:
                total += self.count_tokens(msg["content"], provider)
        # ~2 tokens for conversation structure
        total += 2
        return total
