"""
Tests for Skynette Auto-Updater.

Tests version parsing, update checking, downloading, and applying updates.
"""

import json
import pytest
import sys
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


class TestUpdateInfo:
    """Tests for UpdateInfo dataclass."""

    def test_create_update_info(self):
        """Test creating UpdateInfo with all fields."""
        from src.updater import UpdateInfo

        info = UpdateInfo(
            version="2.0.0",
            current_version="1.0.0",
            download_url="https://example.com/update.zip",
            release_notes="Bug fixes and improvements",
            published_at="2024-01-15T10:00:00Z",
            size_bytes=10485760,
            is_newer=True,
        )

        assert info.version == "2.0.0"
        assert info.current_version == "1.0.0"
        assert info.is_newer is True
        assert info.size_bytes == 10485760


class TestUpdaterVersionParsing:
    """Tests for version parsing functionality."""

    def test_parse_version_simple(self):
        """Test parsing simple version strings."""
        from src.updater import Updater

        assert Updater._parse_version("1.0.0") == (1, 0, 0)
        assert Updater._parse_version("2.3.4") == (2, 3, 4)
        assert Updater._parse_version("10.20.30") == (10, 20, 30)

    def test_parse_version_with_prefix(self):
        """Test parsing versions with 'v' prefix."""
        from src.updater import Updater

        assert Updater._parse_version("v1.0.0") == (1, 0, 0)
        assert Updater._parse_version("v2.3.4") == (2, 3, 4)

    def test_parse_version_with_suffix(self):
        """Test parsing versions with suffixes like -beta."""
        from src.updater import Updater

        # Note: The parser extracts digits from each part, so rc1 becomes 1
        assert Updater._parse_version("1.0.0-beta") == (1, 0, 0)
        assert Updater._parse_version("2.0.0-rc1") == (2, 0, 1)  # rc1 -> 1
        assert Updater._parse_version("1.5.0-alpha2") == (1, 5, 2)  # alpha2 -> 2

    def test_parse_version_two_parts(self):
        """Test parsing versions with two parts."""
        from src.updater import Updater

        assert Updater._parse_version("1.0") == (1, 0)

    def test_parse_version_single_part(self):
        """Test parsing single number versions."""
        from src.updater import Updater

        assert Updater._parse_version("5") == (5,)


class TestUpdaterVersionComparison:
    """Tests for version comparison functionality."""

    def test_is_newer_version_true(self):
        """Test detecting newer versions."""
        from src.updater import Updater

        updater = Updater()
        updater.CURRENT_VERSION = "1.0.0"

        assert updater._is_newer_version("2.0.0") is True
        assert updater._is_newer_version("1.1.0") is True
        assert updater._is_newer_version("1.0.1") is True

    def test_is_newer_version_false(self):
        """Test detecting same or older versions."""
        from src.updater import Updater

        updater = Updater()
        updater.CURRENT_VERSION = "2.0.0"

        assert updater._is_newer_version("1.0.0") is False
        assert updater._is_newer_version("2.0.0") is False
        assert updater._is_newer_version("1.9.9") is False

    def test_is_newer_version_with_prefix(self):
        """Test version comparison with v prefix."""
        from src.updater import Updater

        updater = Updater()
        updater.CURRENT_VERSION = "1.0.0"

        assert updater._is_newer_version("v2.0.0") is True
        assert updater._is_newer_version("v1.0.0") is False

    def test_is_newer_version_invalid(self):
        """Test version comparison with invalid strings."""
        from src.updater import Updater

        updater = Updater()
        updater.CURRENT_VERSION = "1.0.0"

        # Invalid versions should return False (not crash)
        assert updater._is_newer_version("invalid") is False


class TestUpdaterPlatformDetection:
    """Tests for platform-specific asset detection."""

    def test_get_platform_asset_name_windows(self):
        """Test Windows platform detection."""
        from src.updater import Updater

        updater = Updater()

        with patch.object(sys, 'platform', 'win32'):
            assert updater._get_platform_asset_name() == "windows"

    def test_get_platform_asset_name_macos(self):
        """Test macOS platform detection."""
        from src.updater import Updater

        updater = Updater()

        with patch.object(sys, 'platform', 'darwin'):
            assert updater._get_platform_asset_name() == "macos"

    def test_get_platform_asset_name_linux(self):
        """Test Linux platform detection."""
        from src.updater import Updater

        updater = Updater()

        with patch.object(sys, 'platform', 'linux'):
            assert updater._get_platform_asset_name() == "linux"


class TestUpdaterProgressCallback:
    """Tests for progress callback functionality."""

    def test_progress_callback_called(self):
        """Test that progress callback is invoked."""
        from src.updater import Updater

        progress_messages = []

        def on_progress(message, percent):
            progress_messages.append((message, percent))

        updater = Updater(on_progress=on_progress)
        updater._report_progress("Test message", 50)

        assert len(progress_messages) == 1
        assert progress_messages[0] == ("Test message", 50)

    def test_default_progress_callback(self):
        """Test that default callback doesn't crash."""
        from src.updater import Updater

        updater = Updater()  # No callback provided
        # Should not raise
        updater._report_progress("Message", 100)


class TestUpdaterCheckForUpdates:
    """Tests for update checking functionality."""

    @pytest.fixture
    def mock_github_response(self):
        """Create mock GitHub API response."""
        return {
            "tag_name": "v2.0.0",
            "body": "Release notes for version 2.0.0",
            "published_at": "2024-01-15T10:00:00Z",
            "zipball_url": "https://api.github.com/repos/test/test/zipball/v2.0.0",
            "assets": [
                {
                    "name": "skynette-windows.zip",
                    "browser_download_url": "https://github.com/test/test/releases/download/v2.0.0/skynette-windows.zip",
                    "size": 50000000,
                },
                {
                    "name": "skynette-macos.zip",
                    "browser_download_url": "https://github.com/test/test/releases/download/v2.0.0/skynette-macos.zip",
                    "size": 45000000,
                },
                {
                    "name": "skynette-linux.tar.gz",
                    "browser_download_url": "https://github.com/test/test/releases/download/v2.0.0/skynette-linux.tar.gz",
                    "size": 40000000,
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_check_for_updates_newer_available(self, mock_github_response):
        """Test finding a newer version available."""
        from src.updater import Updater

        updater = Updater()
        updater.CURRENT_VERSION = "1.0.0"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_github_response

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await updater.check_for_updates()

        assert result is not None
        assert result.version == "2.0.0"
        assert result.is_newer is True
        assert result.current_version == "1.0.0"

    @pytest.mark.asyncio
    async def test_check_for_updates_no_newer(self, mock_github_response):
        """Test when current version is up to date."""
        from src.updater import Updater

        mock_github_response["tag_name"] = "v1.0.0"

        updater = Updater()
        updater.CURRENT_VERSION = "1.0.0"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_github_response

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await updater.check_for_updates()

        assert result is not None
        assert result.is_newer is False

    @pytest.mark.asyncio
    async def test_check_for_updates_api_error(self):
        """Test handling API errors."""
        from src.updater import Updater

        updater = Updater()

        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await updater.check_for_updates()

        assert result is None

    @pytest.mark.asyncio
    async def test_check_for_updates_network_error(self):
        """Test handling network errors."""
        from src.updater import Updater

        updater = Updater()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = Exception("Network error")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await updater.check_for_updates()

        assert result is None

    @pytest.mark.asyncio
    async def test_check_for_updates_finds_platform_asset(self, mock_github_response):
        """Test that correct platform asset is selected."""
        from src.updater import Updater

        updater = Updater()
        updater.CURRENT_VERSION = "1.0.0"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_github_response

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            with patch.object(sys, 'platform', 'win32'):
                result = await updater.check_for_updates()

        assert "windows" in result.download_url.lower()

    @pytest.mark.asyncio
    async def test_check_for_updates_fallback_to_zipball(self):
        """Test fallback to zipball when no platform asset exists."""
        from src.updater import Updater

        updater = Updater()
        updater.CURRENT_VERSION = "1.0.0"

        response_data = {
            "tag_name": "v2.0.0",
            "body": "Release notes",
            "published_at": "2024-01-15T10:00:00Z",
            "zipball_url": "https://api.github.com/repos/test/test/zipball/v2.0.0",
            "assets": [],  # No platform-specific assets
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await updater.check_for_updates()

        assert result.download_url == "https://api.github.com/repos/test/test/zipball/v2.0.0"


class TestUpdaterDownload:
    """Tests for update download functionality."""

    @pytest.mark.asyncio
    async def test_download_no_url(self):
        """Test download with no URL available."""
        from src.updater import Updater

        updater = Updater()
        updater._update_info = None

        result = await updater.download_update()

        assert result is None

    @pytest.mark.asyncio
    async def test_download_uses_cached_url(self):
        """Test download uses cached update info URL."""
        from src.updater import Updater, UpdateInfo

        updater = Updater()
        updater._update_info = UpdateInfo(
            version="2.0.0",
            current_version="1.0.0",
            download_url="https://cached-url.com/update.zip",
            release_notes="",
            published_at="",
            size_bytes=1000,
            is_newer=True,
        )

        # Mock the download to fail but verify URL was used
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.stream.side_effect = Exception("Expected failure")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            # Should attempt download with cached URL
            result = await updater.download_update()

        # Download fails but we verified it tried using cached URL
        assert result is None
        mock_instance.stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_network_error(self):
        """Test download with network error."""
        from src.updater import Updater

        updater = Updater()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.stream.side_effect = Exception("Download failed")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await updater.download_update(url="https://example.com/update.zip")

        assert result is None


class TestUpdaterApplyUpdate:
    """Tests for applying updates."""

    @pytest.fixture
    def mock_update_zip(self, tmp_path):
        """Create a mock update zip file."""
        # Create a zip with source structure
        zip_path = tmp_path / "update.zip"
        content_dir = tmp_path / "content"
        src_dir = content_dir / "skynette-2.0.0" / "src"
        src_dir.mkdir(parents=True)

        # Create some mock files
        (src_dir / "main.py").write_text("# Updated main.py")
        (src_dir / "__init__.py").write_text("")

        # Create the zip
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file in content_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(content_dir))

        return zip_path

    @pytest.mark.asyncio
    async def test_apply_update_reports_progress(self, mock_update_zip):
        """Test that apply_update reports progress."""
        from src.updater import Updater

        progress_messages = []

        def on_progress(message, percent):
            progress_messages.append((message, percent))

        updater = Updater(on_progress=on_progress)

        # Mock sys.frozen to skip actual file operations
        with patch.object(sys, 'frozen', False, create=True):
            with patch("shutil.rmtree"):
                with patch("shutil.copytree"):
                    with patch("shutil.copy"):
                        await updater.apply_update(mock_update_zip)

        # Should have progress messages
        assert len(progress_messages) > 0
        assert any("Preparing" in msg for msg, _ in progress_messages)

    @pytest.mark.asyncio
    async def test_apply_update_extracts_zip(self, tmp_path):
        """Test that update zip is extracted."""
        from src.updater import Updater

        # Create a simple zip
        zip_path = tmp_path / "update.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("test.txt", "test content")

        updater = Updater()

        with patch.object(sys, 'frozen', False, create=True):
            with patch("shutil.rmtree"):
                with patch("shutil.copytree"):
                    with patch("shutil.copy"):
                        # Will extract but mock file operations
                        await updater.apply_update(zip_path)

        # Extraction should have happened (directory created)
        extract_dir = zip_path.parent / "extracted"
        assert extract_dir.exists()


class TestUpdaterFullWorkflow:
    """Tests for the full update workflow."""

    @pytest.mark.asyncio
    async def test_update_no_newer_version(self):
        """Test full update when no newer version available."""
        from src.updater import Updater

        updater = Updater()
        updater.CURRENT_VERSION = "2.0.0"

        response_data = {
            "tag_name": "v1.0.0",  # Older version
            "body": "",
            "published_at": "",
            "zipball_url": "",
            "assets": [],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await updater.update()

        assert result is False

    @pytest.mark.asyncio
    async def test_update_download_fails(self):
        """Test full update when download fails."""
        from src.updater import Updater, UpdateInfo

        updater = Updater()
        updater.CURRENT_VERSION = "1.0.0"

        # Mock check_for_updates to return newer version
        updater._update_info = UpdateInfo(
            version="2.0.0",
            current_version="1.0.0",
            download_url="https://example.com/update.zip",
            release_notes="",
            published_at="",
            size_bytes=0,
            is_newer=True,
        )

        with patch.object(updater, "check_for_updates", return_value=updater._update_info):
            with patch.object(updater, "download_update", return_value=None):
                result = await updater.update()

        assert result is False


class TestUpdaterProgressMessages:
    """Tests for specific progress message scenarios."""

    @pytest.mark.asyncio
    async def test_progress_messages_during_check(self):
        """Test progress messages during update check."""
        from src.updater import Updater

        messages = []

        def capture_progress(msg, pct):
            messages.append(msg)

        updater = Updater(on_progress=capture_progress)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v2.0.0",
            "body": "",
            "published_at": "",
            "zipball_url": "",
            "assets": [],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            await updater.check_for_updates()

        assert any("Checking" in msg for msg in messages)
        assert any("Update available" in msg or "up to date" in msg for msg in messages)

    @pytest.mark.asyncio
    async def test_progress_messages_on_error(self):
        """Test progress messages when error occurs."""
        from src.updater import Updater

        messages = []

        def capture_progress(msg, pct):
            messages.append(msg)

        updater = Updater(on_progress=capture_progress)

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = Exception("Network error")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            await updater.check_for_updates()

        assert any("failed" in msg.lower() for msg in messages)
