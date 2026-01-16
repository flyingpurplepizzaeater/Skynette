"""
Local file import source.

Allows importing GGUF files from local filesystem.
"""

import json
import re
import shutil
import struct
from pathlib import Path
from typing import Callable, Optional

from ..hub import ModelInfo, DownloadProgress
from . import ModelSource, SearchResult


# GGUF magic number
GGUF_MAGIC = 0x46554747  # "GGUF" in little-endian


class LocalFileSource(ModelSource):
    """Model source for importing local GGUF files."""

    # Quantization patterns for detection
    QUANT_PATTERNS = [
        "Q2_K", "Q3_K_S", "Q3_K_M", "Q3_K_L",
        "Q4_0", "Q4_K_S", "Q4_K_M",
        "Q5_0", "Q5_K_S", "Q5_K_M",
        "Q6_K", "Q8_0", "F16", "F32",
        "IQ1_S", "IQ2_XXS", "IQ2_XS", "IQ3_XXS",
    ]

    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path.home() / "skynette" / "models"

    @property
    def name(self) -> str:
        return "Local Import"

    @property
    def source_id(self) -> str:
        return "local"

    async def list_available(self) -> list[ModelInfo]:
        """List locally imported models (not from other sources)."""
        models = []

        if not self.models_dir.exists():
            return models

        for model_path in self.models_dir.glob("*.gguf"):
            # Skip cache files
            if ".cache" in str(model_path):
                continue

            meta = self._load_metadata(model_path)
            if meta.get("source") == "local":
                models.append(self._create_model_info(model_path, meta))

        return models

    async def search(self, query: str, limit: int = 20) -> SearchResult:
        """Search is not applicable for local import."""
        return SearchResult(models=[], total_count=0, has_more=False)

    async def download(
        self,
        model: ModelInfo,
        dest_dir: Path,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> Path:
        """
        Import a local file (copy or move).

        The model.source_url should contain the source file path.
        """
        source_path = Path(model.source_url)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{model.id}.gguf"

        progress = DownloadProgress(
            model_id=model.id,
            downloaded_bytes=0,
            total_bytes=source_path.stat().st_size,
            status="downloading",
        )

        if progress_callback:
            progress_callback(progress)

        try:
            # Copy file with progress
            chunk_size = 1024 * 1024 * 10  # 10MB chunks

            with open(source_path, "rb") as src, open(dest_path, "wb") as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break

                    dst.write(chunk)
                    progress.downloaded_bytes += len(chunk)

                    if progress_callback:
                        progress_callback(progress)

            # Save metadata
            meta_path = dest_path.with_suffix(".json")
            with open(meta_path, "w") as f:
                json.dump({
                    "id": model.id,
                    "name": model.name,
                    "description": model.description,
                    "quantization": model.quantization,
                    "source": "local",
                    "source_url": str(source_path),
                    "original_filename": source_path.name,
                    "metadata": model.metadata,
                }, f, indent=2)

            progress.status = "complete"
            if progress_callback:
                progress_callback(progress)

            return dest_path

        except Exception as e:
            progress.status = "failed"
            progress.error = str(e)
            if progress_callback:
                progress_callback(progress)

            # Cleanup on failure
            if dest_path.exists():
                dest_path.unlink()

            raise

    async def validate_file(self, file_path: Path) -> Optional[ModelInfo]:
        """
        Validate a local GGUF file and extract info.

        Args:
            file_path: Path to GGUF file

        Returns:
            ModelInfo if valid GGUF, None otherwise
        """
        if not file_path.exists():
            return None

        if not file_path.suffix.lower() == ".gguf":
            return None

        # Check GGUF magic number
        if not self._is_valid_gguf(file_path):
            return None

        # Extract info from filename
        stem = file_path.stem
        size_bytes = file_path.stat().st_size
        quantization = self._detect_quantization(stem)
        name = self._clean_model_name(stem)

        return ModelInfo(
            id=self._generate_id(stem),
            name=name,
            description=f"Imported from {file_path.name}",
            size_bytes=size_bytes,
            quantization=quantization,
            source="local",
            source_url=str(file_path),
            metadata={
                "original_filename": file_path.name,
                "original_path": str(file_path),
            },
        )

    def _is_valid_gguf(self, file_path: Path) -> bool:
        """Check if file has valid GGUF magic number."""
        try:
            with open(file_path, "rb") as f:
                magic = struct.unpack("<I", f.read(4))[0]
                return magic == GGUF_MAGIC
        except Exception:
            return False

    def _detect_quantization(self, filename: str) -> str:
        """Detect quantization from filename."""
        upper = filename.upper()
        for q in self.QUANT_PATTERNS:
            if q in upper:
                return q
        return "unknown"

    def _clean_model_name(self, stem: str) -> str:
        """Clean up filename to human-readable name."""
        # Remove quantization patterns
        name = stem
        for q in self.QUANT_PATTERNS:
            name = re.sub(rf"[-_\.]{q}[-_\.]?", " ", name, flags=re.IGNORECASE)
            name = re.sub(rf"{q}[-_\.]?", " ", name, flags=re.IGNORECASE)

        # Remove common suffixes
        name = re.sub(r"[-_\.]gguf$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"[-_\.]instruct$", " Instruct", name, flags=re.IGNORECASE)
        name = re.sub(r"[-_\.]chat$", " Chat", name, flags=re.IGNORECASE)

        # Clean up separators
        name = re.sub(r"[-_\.]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip()

        # Title case
        return name.title() if name else stem

    def _generate_id(self, stem: str) -> str:
        """Generate a clean ID from filename."""
        # Remove special chars, lowercase
        clean = re.sub(r"[^a-zA-Z0-9]+", "-", stem.lower())
        clean = re.sub(r"-+", "-", clean).strip("-")
        return clean or "imported-model"

    def _load_metadata(self, model_path: Path) -> dict:
        """Load metadata from JSON sidecar if exists."""
        meta_path = model_path.with_suffix(".json")
        if meta_path.exists():
            try:
                with open(meta_path) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _create_model_info(self, model_path: Path, metadata: dict) -> ModelInfo:
        """Create ModelInfo from path and metadata."""
        return ModelInfo(
            id=metadata.get("id", model_path.stem),
            name=metadata.get("name", model_path.stem),
            description=metadata.get("description", ""),
            size_bytes=model_path.stat().st_size,
            quantization=metadata.get("quantization", self._detect_quantization(model_path.stem)),
            source="local",
            source_url=str(model_path),
            local_path=model_path,
            is_downloaded=True,
            metadata=metadata.get("metadata", {}),
        )

    @staticmethod
    def estimate_ram_requirement(size_bytes: int) -> str:
        """Estimate RAM requirement for a model."""
        # Rule of thumb: model needs ~1.2x its size in RAM
        ram_bytes = size_bytes * 1.2
        ram_gb = ram_bytes / (1024 ** 3)

        if ram_gb < 4:
            return f"{ram_gb:.1f} GB (should work on most systems)"
        elif ram_gb < 8:
            return f"{ram_gb:.1f} GB (requires 8GB+ RAM)"
        elif ram_gb < 16:
            return f"{ram_gb:.1f} GB (requires 16GB+ RAM)"
        else:
            return f"{ram_gb:.1f} GB (requires 32GB+ RAM or GPU offloading)"
