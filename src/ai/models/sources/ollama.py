"""
Ollama model source.

Connects to a local Ollama instance for model management.
"""

import asyncio
from pathlib import Path
from typing import Callable, Optional

import httpx

from ..hub import ModelInfo, DownloadProgress
from . import ModelSource, SearchResult


# Popular Ollama models with metadata
OLLAMA_LIBRARY = [
    {
        "name": "llama3.2",
        "description": "Meta's latest Llama model, great for general tasks",
        "sizes": ["1b", "3b"],
        "tags": ["chat", "general"],
    },
    {
        "name": "llama3.1",
        "description": "Powerful Llama model with 8B to 405B parameters",
        "sizes": ["8b", "70b", "405b"],
        "tags": ["chat", "reasoning"],
    },
    {
        "name": "mistral",
        "description": "Mistral 7B - excellent reasoning and instruction following",
        "sizes": ["7b"],
        "tags": ["chat", "reasoning"],
    },
    {
        "name": "mixtral",
        "description": "Mistral's Mixture of Experts model",
        "sizes": ["8x7b", "8x22b"],
        "tags": ["chat", "reasoning", "code"],
    },
    {
        "name": "codellama",
        "description": "Meta's code-specialized Llama model",
        "sizes": ["7b", "13b", "34b", "70b"],
        "tags": ["code", "programming"],
    },
    {
        "name": "deepseek-coder",
        "description": "Code generation and understanding specialist",
        "sizes": ["1.3b", "6.7b", "33b"],
        "tags": ["code", "programming"],
    },
    {
        "name": "phi3",
        "description": "Microsoft's efficient small language model",
        "sizes": ["mini", "small", "medium"],
        "tags": ["efficiency", "general"],
    },
    {
        "name": "qwen2",
        "description": "Alibaba's Qwen model with strong multilingual support",
        "sizes": ["0.5b", "1.5b", "7b", "72b"],
        "tags": ["multilingual", "chat"],
    },
    {
        "name": "gemma2",
        "description": "Google's open model, efficient and capable",
        "sizes": ["2b", "9b", "27b"],
        "tags": ["chat", "general"],
    },
    {
        "name": "nomic-embed-text",
        "description": "Text embedding model for semantic search",
        "sizes": ["v1.5"],
        "tags": ["embeddings"],
    },
]


class OllamaSource(ModelSource):
    """Model source for local Ollama instance."""

    DEFAULT_HOST = "http://localhost:11434"

    def __init__(self, host: Optional[str] = None):
        self.host = host or self.DEFAULT_HOST

    @property
    def name(self) -> str:
        return "Ollama"

    @property
    def source_id(self) -> str:
        return "ollama"

    async def is_running(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def get_installed_models(self) -> list[ModelInfo]:
        """Get models currently installed in Ollama."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                response.raise_for_status()
                data = response.json()

            models = []
            for item in data.get("models", []):
                name = item.get("name", "")
                size = item.get("size", 0)
                details = item.get("details", {})

                models.append(ModelInfo(
                    id=f"ollama-{name.replace(':', '-')}",
                    name=name,
                    description=f"Ollama model: {name}",
                    size_bytes=size,
                    quantization=details.get("quantization_level", ""),
                    source="ollama",
                    source_url=name,
                    is_downloaded=True,
                    metadata={
                        "family": details.get("family", ""),
                        "parameter_size": details.get("parameter_size", ""),
                        "modified_at": item.get("modified_at", ""),
                    },
                ))

            return models

        except Exception:
            return []

    async def list_available(self) -> list[ModelInfo]:
        """List available models from Ollama library."""
        models = []
        installed = await self.get_installed_models()
        installed_names = {m.source_url for m in installed}

        for item in OLLAMA_LIBRARY:
            name = item["name"]
            # Default to smallest size
            default_size = item["sizes"][0] if item["sizes"] else ""
            full_name = f"{name}:{default_size}" if default_size and default_size != name else name

            models.append(ModelInfo(
                id=f"ollama-{name}",
                name=item["name"],
                description=item["description"],
                size_bytes=0,  # Unknown until pulled
                quantization="",
                source="ollama",
                source_url=full_name,
                is_downloaded=full_name in installed_names or name in installed_names,
                metadata={
                    "sizes": item["sizes"],
                    "tags": item["tags"],
                },
            ))

        return models

    async def search(self, query: str, limit: int = 20) -> SearchResult:
        """Search available Ollama models."""
        query_lower = query.lower()
        all_models = await self.list_available()

        # Filter by name or tags
        matching = []
        for model in all_models:
            if query_lower in model.name.lower():
                matching.append(model)
            elif any(query_lower in tag for tag in model.metadata.get("tags", [])):
                matching.append(model)

        return SearchResult(
            models=matching[:limit],
            total_count=len(matching),
            has_more=len(matching) > limit,
        )

    async def download(
        self,
        model: ModelInfo,
        dest_dir: Path,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """
        Pull a model from Ollama library.

        Note: Ollama manages its own model storage, so dest_dir is not used.
        Returns a virtual path indicating the model is available in Ollama.
        """
        model_name = model.source_url

        progress = DownloadProgress(
            model_id=model.id,
            downloaded_bytes=0,
            total_bytes=0,
            status="downloading",
        )

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                # Stream the pull response
                async with client.stream(
                    "POST",
                    f"{self.host}/api/pull",
                    json={"name": model_name},
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        try:
                            data = httpx.loads(line)
                        except Exception:
                            continue

                        status = data.get("status", "")

                        if "total" in data and "completed" in data:
                            progress.total_bytes = data["total"]
                            progress.downloaded_bytes = data["completed"]

                        if "error" in data:
                            raise Exception(data["error"])

                        if status == "success":
                            progress.status = "complete"
                            progress.downloaded_bytes = progress.total_bytes
                        elif "pulling" in status.lower() or "downloading" in status.lower():
                            progress.status = "downloading"
                        elif "verifying" in status.lower():
                            progress.status = "verifying"

                        if progress_callback:
                            progress_callback(progress)

            # Return a virtual path (Ollama manages storage)
            return Path(f"ollama://{model_name}")

        except Exception as e:
            progress.status = "failed"
            progress.error = str(e)
            if progress_callback:
                progress_callback(progress)
            raise

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.host}/api/delete",
                    json={"name": model_name},
                )
                return response.status_code == 200
        except Exception:
            return False

    async def get_model_info(self, model_name: str) -> Optional[dict]:
        """Get detailed info about a model."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.host}/api/show",
                    json={"name": model_name},
                )
                response.raise_for_status()
                return response.json()
        except Exception:
            return None
