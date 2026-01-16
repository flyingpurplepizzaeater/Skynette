"""
Hugging Face model source.

Supports:
- Recommended models (curated list)
- Custom URL paste
- Browse/search Hugging Face API
"""

import asyncio
import json
import re
import shutil
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

import httpx

from ..hub import ModelInfo, DownloadProgress, RECOMMENDED_MODELS
from . import ModelSource, SearchResult


class HuggingFaceSource(ModelSource):
    """Model source for Hugging Face."""

    HF_API_BASE = "https://huggingface.co/api"
    HF_DOWNLOAD_BASE = "https://huggingface.co"

    # Common quantization patterns
    QUANT_PATTERNS = [
        "Q2_K", "Q3_K_S", "Q3_K_M", "Q3_K_L",
        "Q4_0", "Q4_K_S", "Q4_K_M",
        "Q5_0", "Q5_K_S", "Q5_K_M",
        "Q6_K", "Q8_0", "F16", "F32",
    ]

    @property
    def name(self) -> str:
        return "Hugging Face"

    @property
    def source_id(self) -> str:
        return "huggingface"

    async def list_available(self) -> list[ModelInfo]:
        """Return recommended models from Hugging Face."""
        return [m for m in RECOMMENDED_MODELS if m.source == "huggingface"]

    async def search(self, query: str, limit: int = 20) -> SearchResult:
        """
        Search Hugging Face for GGUF models.

        Args:
            query: Search query
            limit: Max results

        Returns:
            SearchResult with matching models
        """
        url = f"{self.HF_API_BASE}/models"
        params = {
            "search": query,
            "filter": "gguf",
            "sort": "downloads",
            "direction": "-1",
            "limit": limit,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            models = []
            for item in data:
                model_id = item.get("modelId", "")
                downloads = item.get("downloads", 0)

                models.append(ModelInfo(
                    id=model_id.replace("/", "--"),
                    name=model_id.split("/")[-1],
                    description=item.get("description", "")[:200] if item.get("description") else "",
                    size_bytes=0,  # Will be filled when selecting specific file
                    quantization="",
                    source="huggingface",
                    source_url=model_id,
                    metadata={
                        "downloads": downloads,
                        "likes": item.get("likes", 0),
                        "tags": item.get("tags", []),
                    },
                ))

            return SearchResult(
                models=models,
                total_count=len(models),
                has_more=len(models) == limit,
            )

        except Exception as e:
            return SearchResult(
                models=[],
                total_count=0,
                has_more=False,
            )

    async def get_model_files(self, repo_id: str) -> list[dict]:
        """
        Get available GGUF files for a repository.

        Args:
            repo_id: Hugging Face repo ID (e.g., "TheBloke/Llama-2-7B-GGUF")

        Returns:
            List of file info with filename, size, quantization
        """
        url = f"{self.HF_API_BASE}/models/{repo_id}/tree/main"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

            files = []
            for item in data:
                if item.get("type") != "file":
                    continue

                path = item.get("path", "")
                if not path.lower().endswith(".gguf"):
                    continue

                size = item.get("size", 0)
                filename = path.split("/")[-1]
                quant = self._detect_quantization(filename)

                files.append({
                    "filename": filename,
                    "path": path,
                    "size": size,
                    "quantization": quant,
                    "size_display": self._format_size(size),
                })

            # Sort by quantization quality (Q4_K_M is common default)
            quant_order = {q: i for i, q in enumerate(self.QUANT_PATTERNS)}
            files.sort(key=lambda f: quant_order.get(f["quantization"], 999))

            return files

        except Exception as e:
            return []

    async def validate_url(self, url: str) -> Optional[ModelInfo]:
        """
        Validate a Hugging Face URL and extract model info.

        Supports formats:
        - https://huggingface.co/TheBloke/Llama-2-7B-GGUF
        - TheBloke/Llama-2-7B-GGUF

        Returns:
            ModelInfo if valid HF URL, None otherwise
        """
        repo_id = self._extract_repo_id(url)
        if not repo_id:
            return None

        # Verify repo exists by fetching files
        files = await self.get_model_files(repo_id)
        if not files:
            return None

        # Get repo info
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.HF_API_BASE}/models/{repo_id}")
                response.raise_for_status()
                data = response.json()

            return ModelInfo(
                id=repo_id.replace("/", "--"),
                name=repo_id.split("/")[-1],
                description=data.get("description", "")[:200] if data.get("description") else "",
                size_bytes=files[0]["size"] if files else 0,
                quantization=files[0]["quantization"] if files else "",
                source="huggingface",
                source_url=repo_id,
                metadata={
                    "downloads": data.get("downloads", 0),
                    "available_files": files,
                },
            )

        except Exception:
            return None

    def _extract_repo_id(self, url: str) -> Optional[str]:
        """Extract repo ID from URL or direct input."""
        # Direct repo ID format: "TheBloke/Llama-2-7B-GGUF"
        if "/" in url and not url.startswith("http"):
            parts = url.strip().split("/")
            if len(parts) == 2:
                return url.strip()

        # URL format: https://huggingface.co/TheBloke/Llama-2-7B-GGUF
        try:
            parsed = urlparse(url)
            if "huggingface.co" in parsed.netloc:
                path_parts = [p for p in parsed.path.split("/") if p]
                if len(path_parts) >= 2:
                    return f"{path_parts[0]}/{path_parts[1]}"
        except Exception:
            pass

        return None

    async def download(
        self,
        model: ModelInfo,
        dest_dir: Path,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        filename: Optional[str] = None,
    ) -> Path:
        """
        Download a model from Hugging Face.

        Args:
            model: Model info with source_url as repo ID
            dest_dir: Destination directory
            progress_callback: Progress callback
            filename: Specific file to download (optional)

        Returns:
            Path to downloaded file
        """
        repo_id = model.source_url
        cache_dir = dest_dir / ".cache"
        cache_dir.mkdir(exist_ok=True)

        # Get available files if no filename specified
        if not filename:
            files = await self.get_model_files(repo_id)
            if not files:
                raise ValueError(f"No GGUF files found in {repo_id}")
            # Default to first file (usually best quantization)
            filename = files[0]["filename"]

        # Construct download URL
        download_url = f"{self.HF_DOWNLOAD_BASE}/{repo_id}/resolve/main/{filename}"

        # Determine local filename
        local_filename = f"{model.id}.gguf"
        dest_path = dest_dir / local_filename
        temp_path = cache_dir / f"{local_filename}.tmp"

        progress = DownloadProgress(
            model_id=model.id,
            downloaded_bytes=0,
            total_bytes=model.size_bytes,
            status="downloading",
        )

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=7200.0) as client:
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()

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

            # Verify and move
            progress.status = "verifying"
            if progress_callback:
                progress_callback(progress)

            shutil.move(str(temp_path), str(dest_path))

            # Save metadata
            meta_path = dest_path.with_suffix(".json")
            with open(meta_path, "w") as f:
                json.dump({
                    "id": model.id,
                    "name": model.name,
                    "description": model.description,
                    "quantization": model.quantization,
                    "source": "huggingface",
                    "source_url": repo_id,
                    "filename": filename,
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

            if temp_path.exists():
                temp_path.unlink()

            raise

    def _detect_quantization(self, filename: str) -> str:
        """Detect quantization from filename."""
        upper = filename.upper()
        for q in self.QUANT_PATTERNS:
            if q in upper:
                return q
        return "unknown"

    def _format_size(self, size_bytes: int) -> str:
        """Format size in human readable format."""
        if size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        return f"{size_bytes / (1024 ** 3):.2f} GB"
