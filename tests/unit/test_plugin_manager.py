"""
Tests for Plugin Manager.

Tests plugin discovery, loading, enabling/disabling, and marketplace integration.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


class TestPluginManifest:
    """Tests for PluginManifest dataclass."""

    def test_from_dict_minimal(self):
        """Test creating manifest with minimal data."""
        from src.plugins.manager import PluginManifest

        data = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
        }

        manifest = PluginManifest.from_dict(data)

        assert manifest.id == "test-plugin"
        assert manifest.name == "Test Plugin"
        assert manifest.version == "1.0.0"
        assert manifest.description == ""
        assert manifest.author == "Unknown"
        assert manifest.license == "MIT"

    def test_from_dict_full(self):
        """Test creating manifest with all fields."""
        from src.plugins.manager import PluginManifest

        data = {
            "id": "full-plugin",
            "name": "Full Plugin",
            "version": "2.0.0",
            "description": "A full plugin",
            "author": "Test Author",
            "author_url": "https://example.com",
            "homepage": "https://plugin.example.com",
            "repository": "https://github.com/test/plugin",
            "license": "Apache-2.0",
            "min_skynette_version": "0.5.0",
            "keywords": ["test", "example"],
            "nodes": ["CustomNode", "AnotherNode"],
            "dependencies": {"requests": ">=2.28.0"},
        }

        manifest = PluginManifest.from_dict(data)

        assert manifest.id == "full-plugin"
        assert manifest.description == "A full plugin"
        assert manifest.author == "Test Author"
        assert manifest.license == "Apache-2.0"
        assert "test" in manifest.keywords
        assert "CustomNode" in manifest.nodes
        assert manifest.dependencies.get("requests") == ">=2.28.0"

    def test_to_dict(self):
        """Test converting manifest to dictionary."""
        from src.plugins.manager import PluginManifest

        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test description",
            author="Author",
        )

        data = manifest.to_dict()

        assert data["id"] == "test-plugin"
        assert data["name"] == "Test Plugin"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Test description"
        assert isinstance(data["keywords"], list)
        assert isinstance(data["nodes"], list)

    def test_roundtrip(self):
        """Test manifest roundtrip (to_dict -> from_dict)."""
        from src.plugins.manager import PluginManifest

        original = PluginManifest(
            id="roundtrip",
            name="Roundtrip Test",
            version="3.0.0",
            keywords=["a", "b", "c"],
        )

        data = original.to_dict()
        restored = PluginManifest.from_dict(data)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.version == original.version
        assert restored.keywords == original.keywords


class TestInstalledPlugin:
    """Tests for InstalledPlugin dataclass."""

    def test_properties(self, tmp_path):
        """Test InstalledPlugin property accessors."""
        from src.plugins.manager import PluginManifest, InstalledPlugin

        manifest = PluginManifest(
            id="prop-test",
            name="Property Test",
            version="1.2.3",
            description="Testing properties",
            author="Test Author",
        )

        plugin = InstalledPlugin(
            manifest=manifest,
            path=tmp_path / "prop-test",
            enabled=True,
        )

        assert plugin.id == "prop-test"
        assert plugin.name == "Property Test"
        assert plugin.version == "1.2.3"
        assert plugin.description == "Testing properties"
        assert plugin.author == "Test Author"

    def test_enabled_default(self, tmp_path):
        """Test that plugins are enabled by default."""
        from src.plugins.manager import PluginManifest, InstalledPlugin

        manifest = PluginManifest(id="test", name="Test", version="1.0.0")
        plugin = InstalledPlugin(manifest=manifest, path=tmp_path)

        assert plugin.enabled is True


class TestPluginSource:
    """Tests for PluginSource enum."""

    def test_source_values(self):
        """Test plugin source enum values."""
        from src.plugins.manager import PluginSource

        assert PluginSource.GITHUB.value == "github"
        assert PluginSource.NPM.value == "npm"
        assert PluginSource.OFFICIAL.value == "official"
        assert PluginSource.URL.value == "url"


class TestMarketplacePlugin:
    """Tests for MarketplacePlugin dataclass."""

    def test_marketplace_plugin_creation(self):
        """Test creating a marketplace plugin."""
        from src.plugins.manager import MarketplacePlugin, PluginSource

        plugin = MarketplacePlugin(
            id="marketplace-test",
            name="Marketplace Test",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            downloads=100,
            rating=4.5,
            stars=50,
            source=PluginSource.GITHUB,
        )

        assert plugin.id == "marketplace-test"
        assert plugin.downloads == 100
        assert plugin.rating == 4.5
        assert plugin.stars == 50
        assert plugin.source == PluginSource.GITHUB


class TestPluginManager:
    """Tests for PluginManager class."""

    @pytest.fixture
    def plugin_manager(self, tmp_path):
        """Create a PluginManager with temporary directories."""
        from src.plugins.manager import PluginManager

        plugins_dir = tmp_path / "plugins"
        config_dir = tmp_path / "config"

        return PluginManager(plugins_dir=plugins_dir, config_dir=config_dir)

    def test_init_creates_directories(self, tmp_path):
        """Test that PluginManager creates necessary directories."""
        from src.plugins.manager import PluginManager

        plugins_dir = tmp_path / "new_plugins"
        config_dir = tmp_path / "new_config"

        assert not plugins_dir.exists()
        assert not config_dir.exists()

        manager = PluginManager(plugins_dir=plugins_dir, config_dir=config_dir)

        assert plugins_dir.exists()
        assert config_dir.exists()

    def test_get_installed_plugins_empty(self, plugin_manager):
        """Test getting installed plugins when none exist."""
        plugins = plugin_manager.get_installed_plugins()
        assert plugins == []

    def test_discover_plugins(self, plugin_manager):
        """Test discovering installed plugins."""
        # Create a mock plugin directory
        plugin_dir = plugin_manager.plugins_dir / "test-plugin"
        plugin_dir.mkdir()

        manifest = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
        }

        with open(plugin_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        # Discover plugins
        plugins = plugin_manager.discover_plugins()

        assert len(plugins) == 1
        assert plugins[0].id == "test-plugin"
        assert plugins[0].name == "Test Plugin"

    def test_discover_plugins_skips_invalid(self, plugin_manager):
        """Test that discovery skips invalid plugin directories."""
        # Create directory without manifest
        invalid_dir = plugin_manager.plugins_dir / "invalid-plugin"
        invalid_dir.mkdir()

        # Create file instead of directory
        (plugin_manager.plugins_dir / "not-a-dir.txt").touch()

        plugins = plugin_manager.discover_plugins()
        assert len(plugins) == 0

    def test_get_plugin(self, plugin_manager):
        """Test getting a specific plugin by ID."""
        # Create plugin
        plugin_dir = plugin_manager.plugins_dir / "my-plugin"
        plugin_dir.mkdir()

        with open(plugin_dir / "manifest.json", "w") as f:
            json.dump({"id": "my-plugin", "name": "My Plugin", "version": "1.0.0"}, f)

        plugin_manager.discover_plugins()

        # Get existing plugin
        plugin = plugin_manager.get_plugin("my-plugin")
        assert plugin is not None
        assert plugin.id == "my-plugin"

        # Get non-existing plugin
        not_found = plugin_manager.get_plugin("non-existent")
        assert not_found is None

    def test_enable_plugin(self, plugin_manager):
        """Test enabling a plugin."""
        # Create plugin
        plugin_dir = plugin_manager.plugins_dir / "enable-test"
        plugin_dir.mkdir()

        with open(plugin_dir / "manifest.json", "w") as f:
            json.dump({"id": "enable-test", "name": "Enable Test", "version": "1.0.0"}, f)

        plugin_manager.discover_plugins()

        # Disable first
        plugin_manager.disable_plugin("enable-test")
        assert plugin_manager.get_plugin("enable-test").enabled is False

        # Enable
        result = plugin_manager.enable_plugin("enable-test")
        assert result is True
        assert plugin_manager.get_plugin("enable-test").enabled is True

    def test_enable_nonexistent_plugin(self, plugin_manager):
        """Test enabling a plugin that doesn't exist."""
        result = plugin_manager.enable_plugin("nonexistent")
        assert result is False

    def test_disable_plugin(self, plugin_manager):
        """Test disabling a plugin."""
        # Create plugin
        plugin_dir = plugin_manager.plugins_dir / "disable-test"
        plugin_dir.mkdir()

        with open(plugin_dir / "manifest.json", "w") as f:
            json.dump({"id": "disable-test", "name": "Disable Test", "version": "1.0.0"}, f)

        plugin_manager.discover_plugins()

        # Plugin should be enabled by default
        assert plugin_manager.get_plugin("disable-test").enabled is True

        # Disable
        result = plugin_manager.disable_plugin("disable-test")
        assert result is True
        assert plugin_manager.get_plugin("disable-test").enabled is False

    def test_disable_nonexistent_plugin(self, plugin_manager):
        """Test disabling a plugin that doesn't exist."""
        result = plugin_manager.disable_plugin("nonexistent")
        assert result is False

    def test_config_persistence(self, tmp_path):
        """Test that plugin configuration persists."""
        from src.plugins.manager import PluginManager

        plugins_dir = tmp_path / "plugins"
        config_dir = tmp_path / "config"

        # Create plugin
        plugins_dir.mkdir(parents=True)
        plugin_dir = plugins_dir / "persist-test"
        plugin_dir.mkdir()

        with open(plugin_dir / "manifest.json", "w") as f:
            json.dump({"id": "persist-test", "name": "Persist Test", "version": "1.0.0"}, f)

        # First manager instance - disable plugin
        manager1 = PluginManager(plugins_dir=plugins_dir, config_dir=config_dir)
        manager1.disable_plugin("persist-test")

        # Second manager instance - check persistence
        manager2 = PluginManager(plugins_dir=plugins_dir, config_dir=config_dir)
        plugin = manager2.get_plugin("persist-test")

        assert plugin is not None
        assert plugin.enabled is False


class TestGitHubMarketplace:
    """Tests for GitHubMarketplace class."""

    @pytest.fixture
    def github_marketplace(self):
        """Create a GitHubMarketplace instance."""
        from src.plugins.manager import GitHubMarketplace
        return GitHubMarketplace()

    @pytest.mark.asyncio
    async def test_search_success(self, github_marketplace):
        """Test successful GitHub search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "full_name": "owner/plugin",
                    "name": "plugin",
                    "description": "A test plugin",
                    "owner": {"login": "owner", "avatar_url": "https://example.com/avatar"},
                    "stargazers_count": 100,
                    "forks_count": 20,
                    "topics": ["skynette-plugin"],
                    "html_url": "https://github.com/owner/plugin",
                    "default_branch": "main",
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            results = await github_marketplace.search("test")

        assert len(results) == 1
        assert results[0].name == "plugin"
        assert results[0].stars == 100

    @pytest.mark.asyncio
    async def test_search_error_handling(self, github_marketplace):
        """Test GitHub search handles errors gracefully."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = Exception("Network error")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            results = await github_marketplace.search("test")

        assert results == []


class TestNpmMarketplace:
    """Tests for NpmMarketplace class."""

    @pytest.fixture
    def npm_marketplace(self):
        """Create an NpmMarketplace instance."""
        from src.plugins.manager import NpmMarketplace
        return NpmMarketplace()

    @pytest.mark.asyncio
    async def test_search_success(self, npm_marketplace):
        """Test successful npm search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "objects": [
                {
                    "package": {
                        "name": "skynette-plugin-test",
                        "version": "1.0.0",
                        "description": "A test plugin",
                        "author": {"name": "Test Author"},
                        "links": {"npm": "https://npmjs.com/package/test"},
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            results = await npm_marketplace.search("test")

        assert len(results) == 1
        assert results[0].version == "1.0.0"


class TestPluginMarketplace:
    """Tests for PluginMarketplace class."""

    @pytest.fixture
    def marketplace(self):
        """Create a PluginMarketplace instance."""
        from src.plugins.manager import PluginMarketplace
        return PluginMarketplace()

    @pytest.mark.asyncio
    async def test_search_multiple_sources(self, marketplace):
        """Test searching across multiple sources."""
        from src.plugins.manager import PluginSource, MarketplacePlugin

        # Mock both sources
        mock_github_results = [
            MarketplacePlugin(
                id="github-plugin",
                name="GitHub Plugin",
                version="1.0.0",
                description="From GitHub",
                author="Author",
                stars=100,
            )
        ]

        mock_npm_results = [
            MarketplacePlugin(
                id="npm-plugin",
                name="npm Plugin",
                version="1.0.0",
                description="From npm",
                author="Author",
                downloads=50,
            )
        ]

        with patch.object(marketplace.sources[PluginSource.GITHUB], "search", return_value=mock_github_results):
            with patch.object(marketplace.sources[PluginSource.NPM], "search", return_value=mock_npm_results):
                results = await marketplace.search("test")

        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_search_single_source(self, marketplace):
        """Test searching a single source."""
        from src.plugins.manager import PluginSource, MarketplacePlugin

        mock_results = [
            MarketplacePlugin(
                id="github-only",
                name="GitHub Only",
                version="1.0.0",
                description="From GitHub",
                author="Author",
                stars=50,
            )
        ]

        with patch.object(marketplace.sources[PluginSource.GITHUB], "search", return_value=mock_results):
            results = await marketplace.search_github("test")

        assert len(results) == 1
        assert results[0].id == "github-only"

    @pytest.mark.asyncio
    async def test_caching(self, marketplace):
        """Test that popular plugins are cached."""
        from src.plugins.manager import PluginSource, MarketplacePlugin

        mock_results = [
            MarketplacePlugin(
                id="cached",
                name="Cached Plugin",
                version="1.0.0",
                description="Should be cached",
                author="Author",
            )
        ]

        call_count = 0

        async def mock_search(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return mock_results

        with patch.object(marketplace.sources[PluginSource.GITHUB], "search", side_effect=mock_search):
            with patch.object(marketplace.sources[PluginSource.NPM], "search", return_value=[]):
                # First call
                await marketplace.get_popular()
                # Second call (should use cache)
                await marketplace.get_popular()

        # Should only call search once due to caching
        assert call_count == 1
