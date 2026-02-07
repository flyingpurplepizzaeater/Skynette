"""
Model Sources - Abstraction for different model providers.

Supports:
- Hugging Face (browse, URL paste, recommended models)
- Ollama (local Ollama instance)
- Local file import
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..hub import DownloadProgress, ModelInfo


@dataclass
class SearchResult:
    """Result from searching a model source."""

    models: list[ModelInfo]
    total_count: int
    has_more: bool = False
    next_cursor: str | None = None


class ModelSource(ABC):
    """
    Abstract base class for model sources.

    Each source provides methods to:
    - List available/recommended models
    - Search for models
    - Download models
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this source."""
        pass

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Unique identifier for this source (e.g., 'huggingface', 'ollama')."""
        pass

    @abstractmethod
    async def list_available(self) -> list[ModelInfo]:
        """
        List available/recommended models from this source.

        Returns:
            List of ModelInfo for available models
        """
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> SearchResult:
        """
        Search for models matching a query.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            SearchResult with matching models
        """
        pass

    @abstractmethod
    async def download(
        self,
        model: ModelInfo,
        dest_dir: Path,
        progress_callback: Callable[[DownloadProgress], None] | None = None,
    ) -> Path:
        """
        Download a model to the destination directory.

        Args:
            model: Model to download
            dest_dir: Directory to download to
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the downloaded model file
        """
        pass

    async def get_model_files(self, model_id: str) -> list[dict]:
        """
        Get available files for a model (e.g., different quantizations).

        Args:
            model_id: Model identifier

        Returns:
            List of file info dicts with 'filename', 'size', 'quantization'
        """
        return []

    async def validate_url(self, url: str) -> ModelInfo | None:
        """
        Validate a URL and return model info if valid for this source.

        Args:
            url: URL to validate

        Returns:
            ModelInfo if valid, None otherwise
        """
        return None


# Import concrete implementations for convenience
from .huggingface import HuggingFaceSource
from .local import LocalFileSource
from .ollama import OllamaSource

__all__ = [
    "ModelSource",
    "SearchResult",
    "HuggingFaceSource",
    "OllamaSource",
    "LocalFileSource",
]
