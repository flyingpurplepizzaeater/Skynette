"""
Plugin Manager - Core plugin system for Skynette.

Handles plugin discovery, loading, enabling/disabling, and lifecycle management.
Supports multiple plugin sources: GitHub, npm, and custom registries.
"""

import asyncio
import importlib
import importlib.util
import json
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import httpx


@dataclass
class PluginManifest:
    """Plugin manifest information."""

    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    author_url: str = ""
    homepage: str = ""
    repository: str = ""
    license: str = "MIT"
    min_skynette_version: str = "1.0.0"
    keywords: list[str] = field(default_factory=list)
    nodes: list[str] = field(default_factory=list)  # Custom nodes provided
    dependencies: dict[str, str] = field(default_factory=dict)  # Python package dependencies

    @classmethod
    def from_dict(cls, data: dict) -> "PluginManifest":
        """Create manifest from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            author=data.get("author", "Unknown"),
            author_url=data.get("author_url", ""),
            homepage=data.get("homepage", ""),
            repository=data.get("repository", ""),
            license=data.get("license", "MIT"),
            min_skynette_version=data.get("min_skynette_version", "1.0.0"),
            keywords=data.get("keywords", []),
            nodes=data.get("nodes", []),
            dependencies=data.get("dependencies", {}),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "author_url": self.author_url,
            "homepage": self.homepage,
            "repository": self.repository,
            "license": self.license,
            "min_skynette_version": self.min_skynette_version,
            "keywords": self.keywords,
            "nodes": self.nodes,
            "dependencies": self.dependencies,
        }


@dataclass
class InstalledPlugin:
    """Information about an installed plugin."""

    manifest: PluginManifest
    path: Path
    enabled: bool = True
    installed_at: str = ""
    updated_at: str = ""
    module: Any | None = None  # Loaded Python module

    @property
    def id(self) -> str:
        return self.manifest.id

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def version(self) -> str:
        return self.manifest.version

    @property
    def description(self) -> str:
        return self.manifest.description

    @property
    def author(self) -> str:
        return self.manifest.author


class PluginSource(Enum):
    """Supported plugin sources."""

    GITHUB = "github"
    NPM = "npm"
    OFFICIAL = "official"
    URL = "url"


@dataclass
class MarketplacePlugin:
    """Information about a plugin in the marketplace."""

    id: str
    name: str
    version: str
    description: str
    author: str
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    categories: list[str] = field(default_factory=list)
    icon_url: str = ""
    download_url: str = ""
    is_verified: bool = False
    is_featured: bool = False
    created_at: str = ""
    updated_at: str = ""
    source: PluginSource = PluginSource.OFFICIAL
    source_url: str = ""  # Original source URL (e.g., GitHub repo URL)
    stars: int = 0  # GitHub stars
    forks: int = 0  # GitHub forks


@dataclass
class GitHubRepo:
    """Information about a GitHub repository."""

    full_name: str  # owner/repo
    name: str
    owner: str
    description: str
    stars: int
    forks: int
    topics: list[str]
    url: str
    default_branch: str
    updated_at: str


# API endpoints
GITHUB_API = "https://api.github.com"
NPM_REGISTRY = "https://registry.npmjs.org"


class MarketplaceSource:
    """Base class for marketplace sources."""

    async def search(self, query: str, limit: int = 20) -> list[MarketplacePlugin]:
        """Search for plugins."""
        raise NotImplementedError

    async def get_plugin_info(self, plugin_id: str) -> MarketplacePlugin | None:
        """Get detailed plugin information."""
        raise NotImplementedError

    async def get_download_url(self, plugin: MarketplacePlugin) -> str:
        """Get download URL for a plugin."""
        raise NotImplementedError


class GitHubMarketplace(MarketplaceSource):
    """Search for Skynette plugins on GitHub."""

    SEARCH_TOPICS = ["skynette-plugin", "skynette"]

    async def search(self, query: str = "", limit: int = 20) -> list[MarketplacePlugin]:
        """Search GitHub for Skynette plugins."""
        plugins = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Search for repos with skynette-plugin topic
                search_query = f"topic:skynette-plugin {query}".strip()

                response = await client.get(
                    f"{GITHUB_API}/search/repositories",
                    params={
                        "q": search_query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": limit,
                    },
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("items", []):
                    plugins.append(
                        MarketplacePlugin(
                            id=item["full_name"].replace("/", "-"),
                            name=item["name"],
                            version="latest",
                            description=item.get("description") or "",
                            author=item["owner"]["login"],
                            downloads=0,  # GitHub doesn't provide this
                            stars=item.get("stargazers_count", 0),
                            forks=item.get("forks_count", 0),
                            categories=item.get("topics", []),
                            icon_url=item["owner"]["avatar_url"],
                            download_url=f"https://github.com/{item['full_name']}/archive/refs/heads/{item.get('default_branch', 'main')}.zip",
                            source=PluginSource.GITHUB,
                            source_url=item["html_url"],
                            created_at=item.get("created_at", ""),
                            updated_at=item.get("updated_at", ""),
                        )
                    )

        except Exception as e:
            print(f"GitHub search error: {e}")

        return plugins

    async def get_popular(self, limit: int = 10) -> list[MarketplacePlugin]:
        """Get popular Skynette plugins from GitHub."""
        return await self.search("", limit=limit)

    async def get_plugin_releases(self, owner: str, repo: str) -> list[dict]:
        """Get releases for a GitHub repository."""
        releases = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{GITHUB_API}/repos/{owner}/{repo}/releases",
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                response.raise_for_status()
                releases = response.json()

        except Exception as e:
            print(f"GitHub releases error: {e}")

        return releases

    async def get_manifest_from_repo(self, owner: str, repo: str) -> PluginManifest | None:
        """Try to get plugin manifest from a GitHub repo."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Try to fetch manifest.json from the repo
                for branch in ["main", "master"]:
                    response = await client.get(
                        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/manifest.json",
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return PluginManifest.from_dict(data)

        except Exception as e:
            print(f"Error fetching manifest: {e}")

        return None


class NpmMarketplace(MarketplaceSource):
    """Search for Skynette plugins on npm."""

    PACKAGE_PREFIX = "skynette-plugin-"

    async def search(self, query: str = "", limit: int = 20) -> list[MarketplacePlugin]:
        """Search npm for Skynette plugins."""
        plugins = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Search for packages with skynette-plugin prefix
                search_query = f"keywords:skynette-plugin {query}".strip()

                response = await client.get(
                    f"{NPM_REGISTRY}/-/v1/search",
                    params={
                        "text": search_query,
                        "size": limit,
                    },
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("objects", []):
                    pkg = item.get("package", {})
                    plugins.append(
                        MarketplacePlugin(
                            id=pkg.get("name", ""),
                            name=pkg.get("name", "")
                            .replace(self.PACKAGE_PREFIX, "")
                            .replace("-", " ")
                            .title(),
                            version=pkg.get("version", "0.0.0"),
                            description=pkg.get("description", ""),
                            author=pkg.get("author", {}).get("name", "")
                            if isinstance(pkg.get("author"), dict)
                            else str(pkg.get("author", "")),
                            downloads=item.get("downloads", {}).get("all", 0)
                            if isinstance(item.get("downloads"), dict)
                            else 0,
                            categories=pkg.get("keywords", []),
                            download_url=f"https://registry.npmjs.org/{pkg.get('name', '')}/-/{pkg.get('name', '')}-{pkg.get('version', '')}.tgz",
                            source=PluginSource.NPM,
                            source_url=f"https://www.npmjs.com/package/{pkg.get('name', '')}",
                            created_at=pkg.get("date", ""),
                            updated_at=pkg.get("date", ""),
                        )
                    )

        except Exception as e:
            print(f"npm search error: {e}")

        return plugins


# Official Skynette Marketplace Registry URL
OFFICIAL_REGISTRY_URL = "https://raw.githubusercontent.com/flyingpurplepizzaeater/skynette-marketplace/main/registry.json"


class OfficialRegistrySource(MarketplaceSource):
    """Fetch plugins from the official Skynette marketplace registry."""

    def __init__(self, registry_url: str = OFFICIAL_REGISTRY_URL):
        self.registry_url = registry_url
        self._cache: dict = {}
        self._cache_time: datetime | None = None
        self._cache_ttl = 300  # 5 minutes

    async def _fetch_registry(self) -> dict:
        """Fetch and cache the registry."""
        # Check cache
        if self._cache and self._cache_time:
            if (datetime.now() - self._cache_time).seconds < self._cache_ttl:
                return self._cache

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.registry_url)
                response.raise_for_status()
                self._cache = response.json()
                self._cache_time = datetime.now()
                return self._cache
        except Exception as e:
            print(f"Failed to fetch official registry: {e}")
            return {"featured": [], "community": []}

    async def search(self, query: str = "", limit: int = 20) -> list[MarketplacePlugin]:
        """Search official registry for plugins."""
        registry = await self._fetch_registry()
        plugins = []

        # Combine featured and community plugins
        all_entries = registry.get("featured", []) + registry.get("community", [])

        for entry in all_entries:
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                if (
                    query_lower not in entry.get("name", "").lower()
                    and query_lower not in entry.get("description", "").lower()
                    and not any(query_lower in tag.lower() for tag in entry.get("tags", []))
                ):
                    continue

            is_featured = entry in registry.get("featured", [])

            plugins.append(
                MarketplacePlugin(
                    id=entry.get("id", ""),
                    name=entry.get("name", ""),
                    version=entry.get("version", "1.0.0"),
                    description=entry.get("description", ""),
                    author=entry.get("author", ""),
                    downloads=entry.get("downloads", 0),
                    categories=entry.get("tags", []),
                    download_url=f"https://github.com/{entry.get('repo', '')}/archive/refs/heads/main.zip",
                    source=PluginSource.OFFICIAL,
                    source_url=f"https://github.com/{entry.get('repo', '')}",
                    is_verified=entry.get("verified", False),
                    is_featured=is_featured,
                )
            )

        return plugins[:limit]

    async def get_featured(self) -> list[MarketplacePlugin]:
        """Get featured plugins from official registry."""
        registry = await self._fetch_registry()
        plugins = []

        for entry in registry.get("featured", []):
            plugins.append(
                MarketplacePlugin(
                    id=entry.get("id", ""),
                    name=entry.get("name", ""),
                    version=entry.get("version", "1.0.0"),
                    description=entry.get("description", ""),
                    author=entry.get("author", ""),
                    downloads=entry.get("downloads", 0),
                    categories=entry.get("tags", []),
                    download_url=f"https://github.com/{entry.get('repo', '')}/archive/refs/heads/main.zip",
                    source=PluginSource.OFFICIAL,
                    source_url=f"https://github.com/{entry.get('repo', '')}",
                    is_verified=entry.get("verified", False),
                    is_featured=True,
                )
            )

        return plugins


class PluginMarketplace:
    """Aggregates plugins from multiple sources."""

    def __init__(self):
        self._official = OfficialRegistrySource()
        self.sources = {
            PluginSource.OFFICIAL: self._official,
            PluginSource.GITHUB: GitHubMarketplace(),
            PluginSource.NPM: NpmMarketplace(),
        }
        self._cache: dict[str, list[MarketplacePlugin]] = {}
        self._cache_time: dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 minutes

    async def search(
        self,
        query: str = "",
        sources: list[PluginSource] = None,
        limit: int = 20,
    ) -> list[MarketplacePlugin]:
        """
        Search for plugins across all or specified sources.

        Args:
            query: Search query
            sources: List of sources to search (default: all)
            limit: Max results per source

        Returns:
            Combined list of plugins from all sources
        """
        if sources is None:
            sources = list(self.sources.keys())

        all_plugins = []

        # Search all sources concurrently
        tasks = []
        for source in sources:
            if source in self.sources:
                tasks.append(self.sources[source].search(query, limit))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_plugins.extend(result)
                elif isinstance(result, Exception):
                    print(f"Search error: {result}")

        # Sort by stars/downloads
        all_plugins.sort(key=lambda p: p.stars + p.downloads, reverse=True)

        return all_plugins[: limit * len(sources)]

    async def get_popular(self, limit: int = 10) -> list[MarketplacePlugin]:
        """Get popular plugins from all sources."""
        cache_key = f"popular_{limit}"

        # Check cache
        if cache_key in self._cache:
            cache_time = self._cache_time.get(cache_key)
            if cache_time and (datetime.now() - cache_time).seconds < self._cache_ttl:
                return self._cache[cache_key]

        plugins = await self.search("", limit=limit)

        # Update cache
        self._cache[cache_key] = plugins
        self._cache_time[cache_key] = datetime.now()

        return plugins

    async def search_github(self, query: str = "", limit: int = 20) -> list[MarketplacePlugin]:
        """Search only GitHub for plugins."""
        return await self.search(query, sources=[PluginSource.GITHUB], limit=limit)

    async def search_npm(self, query: str = "", limit: int = 20) -> list[MarketplacePlugin]:
        """Search only npm for plugins."""
        return await self.search(query, sources=[PluginSource.NPM], limit=limit)

    async def get_featured(self) -> list[MarketplacePlugin]:
        """Get featured plugins from the official registry."""
        return await self._official.get_featured()

    async def search_official(self, query: str = "", limit: int = 20) -> list[MarketplacePlugin]:
        """Search only the official registry for plugins."""
        return await self.search(query, sources=[PluginSource.OFFICIAL], limit=limit)


class PluginManager:
    """
    Manages plugin lifecycle including discovery, loading, and unloading.
    """

    def __init__(self, plugins_dir: Path | None = None, config_dir: Path | None = None):
        self.plugins_dir = plugins_dir or Path.home() / "skynette" / "plugins"
        self.config_dir = config_dir or Path.home() / "skynette" / "config"

        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self._installed: dict[str, InstalledPlugin] = {}
        self._config_file = self.config_dir / "plugins.json"

        # Multi-source marketplace
        self.marketplace = PluginMarketplace()

        # Load configuration
        self._load_config()

        # Discover installed plugins
        self.discover_plugins()

    def _load_config(self):
        """Load plugin configuration."""
        self._config = {
            "enabled_plugins": {},
            "settings": {},
        }

        if self._config_file.exists():
            try:
                with open(self._config_file) as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"Error loading plugin config: {e}")

    def _save_config(self):
        """Save plugin configuration."""
        try:
            with open(self._config_file, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving plugin config: {e}")

    def discover_plugins(self) -> list[InstalledPlugin]:
        """Discover all installed plugins."""
        self._installed = {}

        for plugin_path in self.plugins_dir.iterdir():
            if not plugin_path.is_dir():
                continue

            manifest_path = plugin_path / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path) as f:
                    manifest_data = json.load(f)

                manifest = PluginManifest.from_dict(manifest_data)

                # Check if enabled in config
                enabled = self._config.get("enabled_plugins", {}).get(manifest.id, True)

                plugin = InstalledPlugin(
                    manifest=manifest,
                    path=plugin_path,
                    enabled=enabled,
                    installed_at=manifest_data.get("installed_at", ""),
                    updated_at=manifest_data.get("updated_at", ""),
                )

                self._installed[manifest.id] = plugin

            except Exception as e:
                print(f"Error loading plugin from {plugin_path}: {e}")

        return list(self._installed.values())

    def get_installed_plugins(self) -> list[InstalledPlugin]:
        """Get list of installed plugins."""
        return list(self._installed.values())

    def get_plugin(self, plugin_id: str) -> InstalledPlugin | None:
        """Get a specific plugin by ID."""
        return self._installed.get(plugin_id)

    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin."""
        plugin = self._installed.get(plugin_id)
        if not plugin:
            return False

        plugin.enabled = True
        self._config.setdefault("enabled_plugins", {})[plugin_id] = True
        self._save_config()

        # Load the plugin module
        self._load_plugin(plugin)

        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin."""
        plugin = self._installed.get(plugin_id)
        if not plugin:
            return False

        plugin.enabled = False
        self._config.setdefault("enabled_plugins", {})[plugin_id] = False
        self._save_config()

        # Unload the plugin module
        self._unload_plugin(plugin)

        return True

    def _load_plugin(self, plugin: InstalledPlugin):
        """Load a plugin's Python module."""
        try:
            init_path = plugin.path / "__init__.py"
            if not init_path.exists():
                return

            spec = importlib.util.spec_from_file_location(f"skynette_plugin_{plugin.id}", init_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"skynette_plugin_{plugin.id}"] = module
                spec.loader.exec_module(module)
                plugin.module = module

                # Call plugin's on_load if exists
                if hasattr(module, "on_load"):
                    module.on_load()

        except Exception as e:
            print(f"Error loading plugin {plugin.id}: {e}")

    def _unload_plugin(self, plugin: InstalledPlugin):
        """Unload a plugin's Python module."""
        if plugin.module:
            # Call plugin's on_unload if exists
            if hasattr(plugin.module, "on_unload"):
                try:
                    plugin.module.on_unload()
                except Exception as e:
                    print(f"Error unloading plugin {plugin.id}: {e}")

            # Remove from sys.modules
            module_name = f"skynette_plugin_{plugin.id}"
            if module_name in sys.modules:
                del sys.modules[module_name]

            plugin.module = None

    def load_enabled_plugins(self):
        """Load all enabled plugins."""
        for plugin in self._installed.values():
            if plugin.enabled:
                self._load_plugin(plugin)

    async def install_from_marketplace(
        self,
        plugin_info: MarketplacePlugin,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> bool:
        """Install a plugin from the marketplace."""
        import httpx

        try:
            if progress_callback:
                progress_callback("Downloading...", 0)

            plugin_dir = self.plugins_dir / plugin_info.id
            temp_dir = self.plugins_dir / f".tmp_{plugin_info.id}"

            # Download the plugin archive
            async with httpx.AsyncClient() as client:
                response = await client.get(plugin_info.download_url)
                response.raise_for_status()

                if progress_callback:
                    progress_callback("Extracting...", 50)

                # Save and extract (assuming zip format)
                temp_zip = temp_dir / "plugin.zip"
                temp_dir.mkdir(parents=True, exist_ok=True)

                with open(temp_zip, "wb") as f:
                    f.write(response.content)

                # Extract
                import zipfile

                with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Find the manifest
                manifest_path = None
                for path in temp_dir.rglob("manifest.json"):
                    manifest_path = path
                    break

                if not manifest_path:
                    raise ValueError("Plugin missing manifest.json")

                # Move to final location
                src_dir = manifest_path.parent
                if plugin_dir.exists():
                    shutil.rmtree(plugin_dir)
                shutil.move(str(src_dir), str(plugin_dir))

                # Cleanup
                shutil.rmtree(temp_dir, ignore_errors=True)

                if progress_callback:
                    progress_callback("Finalizing...", 90)

                # Update manifest with install time
                with open(plugin_dir / "manifest.json", "r+") as f:
                    manifest_data = json.load(f)
                    manifest_data["installed_at"] = datetime.now().isoformat()
                    manifest_data["updated_at"] = datetime.now().isoformat()
                    f.seek(0)
                    json.dump(manifest_data, f, indent=2)
                    f.truncate()

                if progress_callback:
                    progress_callback("Complete!", 100)

                # Refresh plugin list
                self.discover_plugins()

                # Enable and load the new plugin
                self.enable_plugin(plugin_info.id)

                return True

        except Exception as e:
            print(f"Error installing plugin: {e}")
            # Cleanup on failure
            temp_dir = self.plugins_dir / f".tmp_{plugin_info.id}"
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            return False

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin."""
        plugin = self._installed.get(plugin_id)
        if not plugin:
            return False

        try:
            # Disable first
            self.disable_plugin(plugin_id)

            # Remove plugin directory
            if plugin.path.exists():
                shutil.rmtree(plugin.path)

            # Remove from installed
            del self._installed[plugin_id]

            # Remove from config
            if plugin_id in self._config.get("enabled_plugins", {}):
                del self._config["enabled_plugins"][plugin_id]
            self._save_config()

            return True

        except Exception as e:
            print(f"Error uninstalling plugin: {e}")
            return False

    def get_plugin_settings(self, plugin_id: str) -> dict:
        """Get settings for a plugin."""
        return self._config.get("settings", {}).get(plugin_id, {})

    def set_plugin_settings(self, plugin_id: str, settings: dict):
        """Set settings for a plugin."""
        self._config.setdefault("settings", {})[plugin_id] = settings
        self._save_config()


# Singleton instance
_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _manager
    if _manager is None:
        _manager = PluginManager()
    return _manager
