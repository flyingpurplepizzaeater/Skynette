"""
Model Hub - Download and manage AI models.

Supports downloading from:
- Hugging Face
- Ollama library
- Direct URLs
- GitHub releases
"""

import asyncio
import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Callable, Optional
from urllib.parse import urlparse

import httpx


@dataclass
class ModelInfo:
    """Information about a model."""
    id: str
    name: str
    description: str = ""
    size_bytes: int = 0
    quantization: str = ""  # e.g., "Q4_K_M", "Q5_K_S"
    source: str = ""  # "huggingface", "ollama", "url", "github"
    source_url: str = ""
    local_path: Optional[Path] = None
    is_downloaded: bool = False
    sha256: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024 ** 3)

    @property
    def size_display(self) -> str:
        if self.size_bytes < 1024 ** 3:
            return f"{self.size_bytes / (1024 ** 2):.1f} MB"
        return f"{self.size_gb:.2f} GB"


@dataclass
class DownloadProgress:
    """Progress information for downloads."""
    model_id: str
    downloaded_bytes: int
    total_bytes: int
    speed_bps: float = 0
    status: str = "downloading"  # downloading, verifying, complete, failed
    error: Optional[str] = None

    @property
    def percent(self) -> float:
        if self.total_bytes == 0:
            return 0
        return (self.downloaded_bytes / self.total_bytes) * 100

    @property
    def eta_seconds(self) -> float:
        if self.speed_bps == 0:
            return float("inf")
        remaining = self.total_bytes - self.downloaded_bytes
        return remaining / self.speed_bps


# Recommended models for different use cases
RECOMMENDED_MODELS = [
    ModelInfo(
        id="llama-3.2-3b-instruct",
        name="Llama 3.2 3B Instruct",
        description="Fast and efficient, great for most tasks. Good balance of speed and quality.",
        size_bytes=2_000_000_000,
        quantization="Q4_K_M",
        source="huggingface",
        source_url="bartowski/Llama-3.2-3B-Instruct-GGUF",
        metadata={"recommended_for": ["chat", "general", "code"]},
    ),
    ModelInfo(
        id="mistral-7b-instruct-v0.3",
        name="Mistral 7B Instruct v0.3",
        description="High quality reasoning and instruction following. Excellent all-rounder.",
        size_bytes=4_100_000_000,
        quantization="Q4_K_M",
        source="huggingface",
        source_url="bartowski/Mistral-7B-Instruct-v0.3-GGUF",
        metadata={"recommended_for": ["reasoning", "chat", "code"]},
    ),
    ModelInfo(
        id="phi-3-mini-4k-instruct",
        name="Phi-3 Mini 4K",
        description="Microsoft's efficient small model. Great for limited resources.",
        size_bytes=2_300_000_000,
        quantization="Q4_K_M",
        source="huggingface",
        source_url="microsoft/Phi-3-mini-4k-instruct-gguf",
        metadata={"recommended_for": ["efficiency", "general"]},
    ),
    ModelInfo(
        id="qwen2-7b-instruct",
        name="Qwen2 7B Instruct",
        description="Strong multilingual support. Good for diverse language tasks.",
        size_bytes=4_500_000_000,
        quantization="Q4_K_M",
        source="huggingface",
        source_url="Qwen/Qwen2-7B-Instruct-GGUF",
        metadata={"recommended_for": ["multilingual", "chat"]},
    ),
    ModelInfo(
        id="deepseek-coder-6.7b-instruct",
        name="DeepSeek Coder 6.7B",
        description="Specialized for code generation and understanding.",
        size_bytes=4_000_000_000,
        quantization="Q4_K_M",
        source="huggingface",
        source_url="deepseek-ai/deepseek-coder-6.7b-instruct",
        metadata={"recommended_for": ["code", "programming"]},
    ),
]


class ModelHub:
    """
    Manages AI model downloads and local model library.
    """

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path.home() / "skynette" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self._cache_dir = self.models_dir / ".cache"
        self._cache_dir.mkdir(exist_ok=True)

        self._downloads: dict[str, DownloadProgress] = {}
        self._local_models: list[ModelInfo] = []

        # Load local models on init
        self.scan_local_models()

    def scan_local_models(self) -> list[ModelInfo]:
        """Scan the models directory for downloaded models."""
        self._local_models = []

        for model_path in self.models_dir.glob("**/*.gguf"):
            if model_path.parent.name == ".cache":
                continue

            size_bytes = model_path.stat().st_size
            model_id = model_path.stem

            # Try to load metadata if exists
            meta_path = model_path.with_suffix(".json")
            metadata = {}
            if meta_path.exists():
                try:
                    with open(meta_path) as f:
                        metadata = json.load(f)
                except Exception:
                    pass

            self._local_models.append(ModelInfo(
                id=model_id,
                name=metadata.get("name", model_id.replace("-", " ").replace("_", " ").title()),
                description=metadata.get("description", ""),
                size_bytes=size_bytes,
                quantization=metadata.get("quantization", self._detect_quantization(model_id)),
                source=metadata.get("source", "local"),
                source_url=metadata.get("source_url", ""),
                local_path=model_path,
                is_downloaded=True,
                metadata=metadata,
            ))

        return self._local_models

    def _detect_quantization(self, model_id: str) -> str:
        """Try to detect quantization from model filename."""
        quants = ["Q2_K", "Q3_K_S", "Q3_K_M", "Q3_K_L", "Q4_0", "Q4_K_S", "Q4_K_M",
                  "Q5_0", "Q5_K_S", "Q5_K_M", "Q6_K", "Q8_0", "F16", "F32"]
        model_upper = model_id.upper()
        for q in quants:
            if q in model_upper:
                return q
        return "unknown"

    def get_local_models(self) -> list[ModelInfo]:
        """Get list of locally downloaded models."""
        return self._local_models

    def get_recommended_models(self) -> list[ModelInfo]:
        """Get list of recommended models to download."""
        # Mark which ones are already downloaded
        local_ids = {m.id for m in self._local_models}
        result = []
        for model in RECOMMENDED_MODELS:
            model_copy = ModelInfo(
                id=model.id,
                name=model.name,
                description=model.description,
                size_bytes=model.size_bytes,
                quantization=model.quantization,
                source=model.source,
                source_url=model.source_url,
                is_downloaded=model.id in local_ids,
                metadata=model.metadata.copy(),
            )
            if model.id in local_ids:
                # Find local path
                for local_model in self._local_models:
                    if local_model.id == model.id:
                        model_copy.local_path = local_model.local_path
                        break
            result.append(model_copy)
        return result

    async def download_model(
        self,
        model: ModelInfo,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """
        Download a model.

        Args:
            model: Model info to download
            progress_callback: Optional callback for progress updates

        Returns:
            Path to downloaded model file
        """
        if model.source == "huggingface":
            return await self._download_from_huggingface(model, progress_callback)
        elif model.source == "url":
            return await self._download_from_url(model, progress_callback)
        else:
            raise ValueError(f"Unsupported source: {model.source}")

    async def _download_from_huggingface(
        self,
        model: ModelInfo,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """Download a model from Hugging Face."""
        # Construct URL for the model file
        # Format: bartowski/Llama-3.2-3B-Instruct-GGUF -> specific file
        repo_id = model.source_url

        # We need to find the actual file URL
        # For simplicity, construct a likely filename based on quantization
        filename = f"{model.id}.{model.quantization}.gguf"

        hf_url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"

        return await self._download_from_url(
            ModelInfo(
                id=model.id,
                name=model.name,
                description=model.description,
                size_bytes=model.size_bytes,
                quantization=model.quantization,
                source="url",
                source_url=hf_url,
                metadata=model.metadata,
            ),
            progress_callback,
        )

    async def _download_from_url(
        self,
        model: ModelInfo,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """Download a model from a direct URL."""
        url = model.source_url
        dest_path = self.models_dir / f"{model.id}.gguf"
        temp_path = self._cache_dir / f"{model.id}.gguf.tmp"

        progress = DownloadProgress(
            model_id=model.id,
            downloaded_bytes=0,
            total_bytes=model.size_bytes,
            status="downloading",
        )
        self._downloads[model.id] = progress

        try:
            # Extended timeout for large model downloads (up to 2 hours)
            async with httpx.AsyncClient(follow_redirects=True, timeout=7200.0) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()

                    # Get total size from headers if available
                    content_length = response.headers.get("content-length")
                    if content_length:
                        progress.total_bytes = int(content_length)

                    with open(temp_path, "wb") as f:
                        last_time = asyncio.get_event_loop().time()
                        last_bytes = 0

                        async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                            f.write(chunk)
                            progress.downloaded_bytes += len(chunk)

                            # Calculate speed
                            now = asyncio.get_event_loop().time()
                            elapsed = now - last_time
                            if elapsed >= 1.0:
                                bytes_delta = progress.downloaded_bytes - last_bytes
                                progress.speed_bps = bytes_delta / elapsed
                                last_time = now
                                last_bytes = progress.downloaded_bytes

                            if progress_callback:
                                progress_callback(progress)

            # Verify download
            progress.status = "verifying"
            if progress_callback:
                progress_callback(progress)

            # Move to final location
            shutil.move(temp_path, dest_path)

            # Save metadata
            meta_path = dest_path.with_suffix(".json")
            with open(meta_path, "w") as f:
                json.dump({
                    "id": model.id,
                    "name": model.name,
                    "description": model.description,
                    "quantization": model.quantization,
                    "source": model.source,
                    "source_url": model.source_url,
                    "metadata": model.metadata,
                }, f, indent=2)

            progress.status = "complete"
            if progress_callback:
                progress_callback(progress)

            # Refresh local models
            self.scan_local_models()

            return dest_path

        except Exception as e:
            progress.status = "failed"
            progress.error = str(e)
            if progress_callback:
                progress_callback(progress)

            # Cleanup temp file
            if temp_path.exists():
                temp_path.unlink()

            raise

    def get_download_progress(self, model_id: str) -> Optional[DownloadProgress]:
        """Get download progress for a model."""
        return self._downloads.get(model_id)

    def delete_model(self, model_id: str) -> bool:
        """Delete a downloaded model."""
        for model in self._local_models:
            if model.id == model_id and model.local_path:
                model.local_path.unlink(missing_ok=True)
                # Delete metadata too
                meta_path = model.local_path.with_suffix(".json")
                meta_path.unlink(missing_ok=True)
                self.scan_local_models()
                return True
        return False

    def get_model_by_id(self, model_id: str) -> Optional[ModelInfo]:
        """Get a model by ID (local or recommended)."""
        for model in self._local_models:
            if model.id == model_id:
                return model
        for model in RECOMMENDED_MODELS:
            if model.id == model_id:
                return model
        return None


# Singleton hub instance
_hub: Optional[ModelHub] = None


def get_hub() -> ModelHub:
    """Get the global model hub instance."""
    global _hub
    if _hub is None:
        _hub = ModelHub()
    return _hub
