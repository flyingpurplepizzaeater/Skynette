"""
Local Provider - llama.cpp based local model inference.

Supports running GGUF models locally for free, private AI.
"""

import asyncio
from pathlib import Path
from typing import AsyncIterator, Optional
import json

from src.ai.gateway import (
    AICapability,
    AIMessage,
    AIResponse,
    AIStreamChunk,
    GenerationConfig,
)
from src.ai.providers.base import BaseProvider


class LocalProvider(BaseProvider):
    """
    Local AI provider using llama-cpp-python.

    Runs GGUF models locally for free, private inference.
    Supports CPU and GPU acceleration.
    """

    name = "local"
    display_name = "Local (llama.cpp)"
    capabilities = {
        AICapability.TEXT_GENERATION,
        AICapability.CHAT,
        AICapability.EMBEDDINGS,
        AICapability.CODE_GENERATION,
    }

    def __init__(
        self,
        models_dir: Optional[Path] = None,
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,  # -1 = auto, 0 = CPU only
        n_threads: Optional[int] = None,
    ):
        super().__init__()
        self.models_dir = models_dir or Path.home() / "skynette" / "models"
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads

        self._llm = None
        self._current_model: Optional[str] = None
        self._available_models: list[dict] = []

    async def initialize(self) -> bool:
        """Initialize the local provider."""
        try:
            # Ensure models directory exists
            self.models_dir.mkdir(parents=True, exist_ok=True)

            # Scan for available models
            self._scan_models()

            self._is_initialized = True
            self._is_available = True
            return True
        except Exception as e:
            print(f"Failed to initialize local provider: {e}")
            self._is_available = False
            return False

    def is_available(self) -> bool:
        """Check if local provider is available."""
        return self._is_available and self._is_initialized

    def _scan_models(self):
        """Scan models directory for GGUF files."""
        self._available_models = []

        if not self.models_dir.exists():
            return

        for model_path in self.models_dir.glob("**/*.gguf"):
            size_gb = model_path.stat().st_size / (1024 ** 3)
            self._available_models.append({
                "id": model_path.stem,
                "name": model_path.stem.replace("-", " ").replace("_", " ").title(),
                "path": str(model_path),
                "size_gb": round(size_gb, 2),
                "type": "gguf",
            })

    def get_models(self) -> list[dict]:
        """Get available local models."""
        return self._available_models

    async def load_model(self, model_id: str) -> bool:
        """
        Load a specific model.

        Args:
            model_id: ID of the model to load

        Returns:
            True if loaded successfully
        """
        # Find model
        model_info = None
        for m in self._available_models:
            if m["id"] == model_id:
                model_info = m
                break

        if not model_info:
            raise ValueError(f"Model '{model_id}' not found")

        # Unload current model if different
        if self._current_model == model_id and self._llm is not None:
            return True

        if self._llm is not None:
            del self._llm
            self._llm = None

        # Load new model
        try:
            from llama_cpp import Llama

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            self._llm = await loop.run_in_executor(
                None,
                lambda: Llama(
                    model_path=model_info["path"],
                    n_ctx=self.n_ctx,
                    n_gpu_layers=self.n_gpu_layers,
                    n_threads=self.n_threads,
                    verbose=False,
                )
            )
            self._current_model = model_id
            return True
        except ImportError:
            raise RuntimeError(
                "llama-cpp-python not installed. "
                "Install with: pip install llama-cpp-python"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    async def _ensure_model_loaded(self):
        """Ensure a model is loaded, loading default if needed."""
        if self._llm is not None:
            return

        models = self.get_models()
        if not models:
            raise RuntimeError(
                "No models available. Download a GGUF model to "
                f"{self.models_dir}"
            )

        await self.load_model(models[0]["id"])

    async def generate(
        self,
        prompt: str,
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate text from a prompt."""
        await self._ensure_model_loaded()

        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            None,
            lambda: self._llm(
                prompt,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                stop=config.stop_sequences or None,
            )
        )

        return AIResponse(
            content=result["choices"][0]["text"],
            provider=self.name,
            model=self._current_model or "unknown",
            usage={
                "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": result.get("usage", {}).get("total_tokens", 0),
            },
            finish_reason=result["choices"][0].get("finish_reason"),
            raw_response=result,
        )

    async def chat(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AIResponse:
        """Generate a chat response."""
        await self._ensure_model_loaded()

        loop = asyncio.get_event_loop()

        # Convert messages to dict format
        msg_dicts = [m.to_dict() for m in messages]

        result = await loop.run_in_executor(
            None,
            lambda: self._llm.create_chat_completion(
                messages=msg_dicts,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                stop=config.stop_sequences or None,
            )
        )

        return AIResponse(
            content=result["choices"][0]["message"]["content"],
            provider=self.name,
            model=self._current_model or "unknown",
            usage={
                "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": result.get("usage", {}).get("total_tokens", 0),
            },
            finish_reason=result["choices"][0].get("finish_reason"),
            raw_response=result,
        )

    async def chat_stream(
        self,
        messages: list[AIMessage],
        config: GenerationConfig,
    ) -> AsyncIterator[AIStreamChunk]:
        """Stream a chat response."""
        await self._ensure_model_loaded()

        msg_dicts = [m.to_dict() for m in messages]

        # Create streaming generator
        stream = self._llm.create_chat_completion(
            messages=msg_dicts,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            stop=config.stop_sequences or None,
            stream=True,
        )

        for chunk in stream:
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            finish_reason = chunk["choices"][0].get("finish_reason")

            if content or finish_reason:
                yield AIStreamChunk(
                    content=content,
                    is_final=finish_reason is not None,
                    usage=chunk.get("usage"),
                )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        await self._ensure_model_loaded()

        loop = asyncio.get_event_loop()

        embeddings = []
        for text in texts:
            result = await loop.run_in_executor(
                None,
                lambda t=text: self._llm.embed(t)
            )
            embeddings.append(result)

        return embeddings

    def unload_model(self):
        """Unload the current model to free memory."""
        if self._llm is not None:
            del self._llm
            self._llm = None
            self._current_model = None
