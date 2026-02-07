# src/ai/completions/completion_service.py
"""Inline code completion service.

Fetches AI-powered inline completions based on code context,
with debouncing and caching for performance.
"""

import asyncio
from dataclasses import dataclass

from src.ai.completions.token_counter import TokenCounter
from src.ai.gateway import AIGateway, GenerationConfig


@dataclass
class CompletionRequest:
    """Request for code completion."""

    code_before: str  # Code before cursor
    code_after: str  # Code after cursor (for context)
    language: str
    max_tokens: int = 50
    provider: str | None = None


class CompletionService:
    """Service for fetching inline code completions.

    Uses AI Gateway to get completions based on code context.
    Implements debouncing and caching for performance.

    Example:
        service = CompletionService(gateway)
        suggestion = await service.get_completion(request)
    """

    # Debounce delay in seconds
    DEBOUNCE_DELAY = 0.5

    def __init__(self, gateway: AIGateway):
        """Initialize completion service.

        Args:
            gateway: AI Gateway for provider access.
        """
        self.gateway = gateway
        self.token_counter = TokenCounter()
        self._pending_task: asyncio.Task | None = None
        self._cache: dict[str, str] = {}  # Simple cache by code hash

    async def get_completion(self, request: CompletionRequest) -> str | None:
        """Get completion for the given context.

        Args:
            request: Completion request with code context.

        Returns:
            Suggested completion text, or None if no suggestion.
        """
        # Cancel any pending request
        if self._pending_task and not self._pending_task.done():
            self._pending_task.cancel()

        # Check cache
        cache_key = self._make_cache_key(request)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Debounce
        await asyncio.sleep(self.DEBOUNCE_DELAY)

        # Build prompt for completion
        prompt = self._build_completion_prompt(request)

        # Check token limit
        if not self.token_counter.is_within_limit(prompt, 4000, request.provider or "openai"):
            # Truncate context if too large
            prompt = self._truncate_prompt(prompt, 3000)

        try:
            config = GenerationConfig(
                max_tokens=request.max_tokens,
                temperature=0.2,  # Low temp for completions
                stop_sequences=["\n\n", "```"],  # Stop at natural boundaries
            )

            response = await self.gateway.generate(
                prompt,
                config=config,
                provider=request.provider,
            )

            suggestion = self._clean_suggestion(response.content)

            # Cache result
            self._cache[cache_key] = suggestion

            return suggestion if suggestion else None

        except Exception:
            # Silently fail - inline suggestions are optional
            return None

    def _build_completion_prompt(self, request: CompletionRequest) -> str:
        """Build prompt for completion request."""
        return f"""Complete the following {request.language} code. Only output the completion, no explanation.

```{request.language}
{request.code_before}
```

Continue from where the code ends. Output only the next few tokens/lines that would naturally follow."""

    def _clean_suggestion(self, text: str) -> str:
        """Clean up AI response to extract just the completion."""
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (``` markers)
            if len(lines) > 2:
                text = "\n".join(lines[1:-1])
            else:
                text = ""

        # Take only first meaningful chunk
        text = text.strip()
        return text

    def _make_cache_key(self, request: CompletionRequest) -> str:
        """Create cache key from request."""
        # Use last 100 chars of code_before for cache key
        context = (
            request.code_before[-100:] if len(request.code_before) > 100 else request.code_before
        )
        return f"{request.language}:{hash(context)}"

    def _truncate_prompt(self, prompt: str, max_tokens: int) -> str:
        """Truncate prompt to fit within token limit."""
        # Simple character-based truncation (4 chars per token)
        max_chars = max_tokens * 4
        if len(prompt) > max_chars:
            return prompt[-max_chars:]
        return prompt

    def clear_cache(self) -> None:
        """Clear the completion cache."""
        self._cache.clear()

    def cancel_pending(self) -> None:
        """Cancel any pending completion request."""
        if self._pending_task and not self._pending_task.done():
            self._pending_task.cancel()
