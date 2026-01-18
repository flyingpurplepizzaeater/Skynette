"""
Gemini Provider - Google Gemini API integration.

Supports Gemini 2.5 Flash, 2.0 Pro, and 1.5 models with long context.
Uses the official google-genai SDK (not deprecated google-generativeai).
"""

import os
from collections.abc import AsyncIterator

from src.ai.gateway import (
    AICapability,
    AIMessage,
    AIResponse,
    AIStreamChunk,
    GenerationConfig,
)
from src.ai.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    """
    Google Gemini API provider.

    Supports Gemini models with very long context windows (1M+ tokens).
    Requires GOOGLE_API_KEY environment variable or explicit key.
    """

    name = "gemini"
    display_name = "Google Gemini"
    capabilities = {
        AICapability.TEXT_GENERATION,
        AICapability.CHAT,
        AICapability.IMAGE_ANALYSIS,
        AICapability.CODE_GENERATION,
    }

    MODELS = [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "context": 1048576},
        {"id": "gemini-2.0-pro", "name": "Gemini 2.0 Pro", "context": 2097152},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "context": 2097152},
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "context": 1048576},
    ]

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
    ):
        super().__init__()
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.model = model
        self._client = None
        self._aclient = None

    async def initialize(self) -> bool:
        """Initialize the Gemini provider."""
        if not self.api_key:
            self._is_available = False
            return False

        try:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
            self._aclient = self._client.aio
            self._is_initialized = True
            self._is_available = True
            return True
        except ImportError:
            print("google-genai package not installed. Install with: pip install google-genai")
            self._is_available = False
            return False
        except Exception as e:
            print(f"Failed to initialize Gemini provider: {e}")
            self._is_available = False
            return False

    def is_available(self) -> bool:
        """Check if Gemini provider is available."""
        return self._is_available and self.api_key is not None

    def get_models(self) -> list[dict]:
        """Get available Gemini models."""
        return self.MODELS

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.model

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate text from a prompt using messages API."""
        messages = [AIMessage(role="user", content=prompt)]
        return await self.chat(messages, config)

    async def chat(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate a chat response."""
        if not self._aclient:
            await self.initialize()

        if not self._aclient:
            return AIResponse(
                content="Gemini provider not initialized. Check GOOGLE_API_KEY.",
                provider=self.name,
                model=self.model,
                usage={},
                finish_reason="error",
            )

        try:
            from google.genai import types

            # Extract system instruction and build contents
            system_instruction = None
            contents = []

            for msg in messages:
                if msg.role == "system":
                    system_instruction = msg.content
                else:
                    # Map role to Gemini format (user/model)
                    role = "model" if msg.role == "assistant" else "user"
                    contents.append(types.Content(
                        role=role,
                        parts=[types.Part(text=msg.content)]
                    ))

            # Build generation config
            gen_config = types.GenerateContentConfig(
                max_output_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                stop_sequences=config.stop_sequences or None,
                system_instruction=system_instruction,
            )

            response = await self._aclient.models.generate_content(
                model=self.model,
                contents=contents,
                config=gen_config,
            )

            # Extract text content
            content = response.text if response.text else ""

            # Extract usage if available
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count or 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count or 0,
                    "total_tokens": response.usage_metadata.total_token_count or 0,
                }

            return AIResponse(
                content=content,
                provider=self.name,
                model=self.model,
                usage=usage,
                finish_reason="stop",
            )

        except Exception as e:
            error_msg = str(e)
            # Check for common API errors
            if "API key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                error_msg = "Invalid or missing GOOGLE_API_KEY"
            return AIResponse(
                content=f"Error: {error_msg}",
                provider=self.name,
                model=self.model,
                usage={},
                finish_reason="error",
            )

    async def chat_stream(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AsyncIterator[AIStreamChunk]:
        """Stream a chat response."""
        if not self._aclient:
            await self.initialize()

        if not self._aclient:
            yield AIStreamChunk(
                content="Gemini provider not initialized. Check GOOGLE_API_KEY.",
                is_final=True,
            )
            return

        try:
            from google.genai import types

            # Extract system instruction and build contents
            system_instruction = None
            contents = []

            for msg in messages:
                if msg.role == "system":
                    system_instruction = msg.content
                else:
                    role = "model" if msg.role == "assistant" else "user"
                    contents.append(types.Content(
                        role=role,
                        parts=[types.Part(text=msg.content)]
                    ))

            # Build generation config
            gen_config = types.GenerateContentConfig(
                max_output_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                stop_sequences=config.stop_sequences or None,
                system_instruction=system_instruction,
            )

            # Stream the response
            async for chunk in await self._aclient.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=gen_config,
            ):
                if chunk.text:
                    yield AIStreamChunk(
                        content=chunk.text,
                        is_final=False,
                    )

            # Final chunk
            yield AIStreamChunk(
                content="",
                is_final=True,
            )

        except Exception as e:
            error_msg = str(e)
            if "API key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                error_msg = "Invalid or missing GOOGLE_API_KEY"
            yield AIStreamChunk(
                content=f"\n\n[Error: {error_msg}]",
                is_final=True,
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._aclient:
            try:
                await self._aclient.aclose()
            except Exception:
                pass
            self._aclient = None
            self._client = None
