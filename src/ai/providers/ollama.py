"""
Ollama Provider - Local LLM integration via Ollama API.

Connects to Ollama running locally on port 11434.
"""

from typing import AsyncIterator, Optional

import httpx

from src.ai.gateway import (
    AICapability,
    AIMessage,
    AIResponse,
    AIStreamChunk,
    GenerationConfig,
)
from src.ai.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    """
    Ollama provider for local model inference.

    Connects to local Ollama instance via native API.
    Default URL: http://localhost:11434
    """

    name = "ollama"
    display_name = "Ollama (Local)"
    capabilities = {
        AICapability.TEXT_GENERATION,
        AICapability.CHAT,
        AICapability.EMBEDDINGS,
        AICapability.CODE_GENERATION,
    }

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: Optional[str] = None,
    ):
        super().__init__()
        self.base_url = base_url
        self.model = default_model  # Will auto-detect if not specified
        self._available_models: list[dict] = []

    async def initialize(self) -> bool:
        """Initialize the Ollama provider."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()

            self._available_models = data.get("models", [])

            # Auto-select first model if none specified
            if not self.model and self._available_models:
                self.model = self._available_models[0].get("name")

            self._is_initialized = True
            self._is_available = bool(self._available_models)
            return self._is_available

        except Exception as e:
            print(f"Failed to initialize Ollama provider: {e}")
            self._is_available = False
            return False

    async def get_models(self) -> list[dict]:
        """Get available models from Ollama."""
        if not self._is_initialized:
            await self.initialize()

        models = []
        for model in self._available_models:
            name = model.get("name", "")
            details = model.get("details", {})
            size = model.get("size", 0)

            models.append({
                "id": name,
                "name": name.split(":")[0].replace("-", " ").title(),
                "size": size,
                "quantization": details.get("quantization_level", ""),
                "family": details.get("family", ""),
                "parameter_size": details.get("parameter_size", ""),
            })

        return models

    async def chat(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AIResponse:
        """Send a chat completion request."""
        if not self._is_initialized:
            await self.initialize()

        model = config.model or self.model

        if not model:
            raise ValueError("No model available. Please pull a model first.")

        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k or 40,
            },
        }

        if config.max_tokens:
            payload["options"]["num_predict"] = config.max_tokens

        if config.stop_sequences:
            payload["options"]["stop"] = config.stop_sequences

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            message = data.get("message", {})
            content = message.get("content", "")

            # Token counts from eval_count
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            return AIResponse(
                content=content,
                model=model,
                provider=self.name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                finish_reason="stop",
            )

        except httpx.TimeoutException:
            raise TimeoutError("Ollama request timed out")
        except Exception as e:
            raise RuntimeError(f"Ollama chat failed: {e}")

    async def chat_stream(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AsyncIterator[AIStreamChunk]:
        """Stream a chat completion request."""
        if not self._is_initialized:
            await self.initialize()

        model = config.model or self.model

        if not model:
            raise ValueError("No model available. Please pull a model first.")

        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k or 40,
            },
        }

        if config.max_tokens:
            payload["options"]["num_predict"] = config.max_tokens

        if config.stop_sequences:
            payload["options"]["stop"] = config.stop_sequences

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        try:
                            data = httpx.loads(line)
                        except Exception:
                            continue

                        message = data.get("message", {})
                        content = message.get("content", "")
                        done = data.get("done", False)

                        yield AIStreamChunk(
                            content=content,
                            model=model,
                            provider=self.name,
                            finish_reason="stop" if done else None,
                        )

        except Exception as e:
            raise RuntimeError(f"Ollama stream failed: {e}")

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate text from a prompt (non-chat mode)."""
        if not self._is_initialized:
            await self.initialize()

        model = config.model or self.model

        if not model:
            raise ValueError("No model available. Please pull a model first.")

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k or 40,
            },
        }

        if config.max_tokens:
            payload["options"]["num_predict"] = config.max_tokens

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            content = data.get("response", "")
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            return AIResponse(
                content=content,
                model=model,
                provider=self.name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                finish_reason="stop",
            )

        except Exception as e:
            raise RuntimeError(f"Ollama generate failed: {e}")

    async def embeddings(
        self,
        text: str | list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """Generate embeddings for text."""
        if not self._is_initialized:
            await self.initialize()

        model = model or "nomic-embed-text"  # Default embedding model

        texts = [text] if isinstance(text, str) else text
        embeddings = []

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                for t in texts:
                    response = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": model, "prompt": t},
                    )
                    response.raise_for_status()
                    data = response.json()
                    embeddings.append(data.get("embedding", []))

            return embeddings

        except Exception as e:
            raise RuntimeError(f"Ollama embeddings failed: {e}")

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self._is_available and bool(self._available_models)
