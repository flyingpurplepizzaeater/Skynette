"""Unit tests for Ollama status checking functionality.

Tests verify the check_status() method returns proper tuples with
connection status, model lists, and user-friendly error messages.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.ai.providers.ollama import OllamaProvider


def create_mock_response(models_data):
    """Create a mock httpx response for successful requests."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = models_data
    mock_response.raise_for_status = MagicMock()
    return mock_response


class TestOllamaStatusCheckReturnType:
    """Test check_status return type and structure."""

    @pytest.mark.asyncio
    async def test_check_status_returns_tuple(self):
        """Test check_status returns a tuple."""
        provider = OllamaProvider()
        mock_response = create_mock_response({"models": []})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await provider.check_status()

            assert isinstance(result, tuple)

    @pytest.mark.asyncio
    async def test_check_status_returns_three_elements(self):
        """Test check_status returns tuple with 3 elements."""
        provider = OllamaProvider()
        mock_response = create_mock_response({"models": []})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await provider.check_status()

            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_check_status_first_element_is_bool(self):
        """Test first element (connected) is boolean."""
        provider = OllamaProvider()
        mock_response = create_mock_response({"models": []})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            connected, _, _ = await provider.check_status()

            assert isinstance(connected, bool)

    @pytest.mark.asyncio
    async def test_check_status_second_element_is_list(self):
        """Test second element (models) is list."""
        provider = OllamaProvider()
        mock_response = create_mock_response({"models": []})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            _, models, _ = await provider.check_status()

            assert isinstance(models, list)


class TestOllamaStatusCheckConnected:
    """Test check_status when Ollama is running."""

    @pytest.mark.asyncio
    async def test_connected_returns_true(self):
        """Test connected is True when Ollama responds."""
        provider = OllamaProvider()
        mock_response = create_mock_response({
            "models": [{"name": "llama3:latest"}]
        })

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            connected, _, _ = await provider.check_status()

            assert connected is True

    @pytest.mark.asyncio
    async def test_connected_returns_model_names(self):
        """Test model names are returned when connected."""
        provider = OllamaProvider()
        mock_response = create_mock_response({
            "models": [
                {"name": "llama3:latest"},
                {"name": "codellama:latest"},
            ]
        })

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            _, models, _ = await provider.check_status()

            assert "llama3:latest" in models
            assert "codellama:latest" in models

    @pytest.mark.asyncio
    async def test_connected_returns_no_error(self):
        """Test error is None when connected."""
        provider = OllamaProvider()
        mock_response = create_mock_response({"models": [{"name": "llama3:latest"}]})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            _, _, error = await provider.check_status()

            assert error is None


class TestOllamaStatusCheckNotRunning:
    """Test check_status when Ollama is not running."""

    @pytest.mark.asyncio
    async def test_not_running_returns_false(self):
        """Test connected is False when connection refused."""
        provider = OllamaProvider()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            connected, _, _ = await provider.check_status()

            assert connected is False

    @pytest.mark.asyncio
    async def test_not_running_returns_empty_models(self):
        """Test models list is empty when not running."""
        provider = OllamaProvider()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            _, models, _ = await provider.check_status()

            assert models == []

    @pytest.mark.asyncio
    async def test_not_running_error_is_user_friendly(self):
        """Test error message is user-friendly when not running."""
        provider = OllamaProvider()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            _, _, error = await provider.check_status()

            assert error is not None
            # Should mention "not running" or similar
            assert "not running" in error.lower() or "ollama" in error.lower()


class TestOllamaStatusCheckTimeout:
    """Test check_status when Ollama times out."""

    @pytest.mark.asyncio
    async def test_timeout_returns_false(self):
        """Test connected is False on timeout."""
        provider = OllamaProvider()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            connected, _, _ = await provider.check_status()

            assert connected is False

    @pytest.mark.asyncio
    async def test_timeout_returns_empty_models(self):
        """Test models list is empty on timeout."""
        provider = OllamaProvider()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            _, models, _ = await provider.check_status()

            assert models == []

    @pytest.mark.asyncio
    async def test_timeout_error_is_user_friendly(self):
        """Test error message is user-friendly on timeout."""
        provider = OllamaProvider()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            _, _, error = await provider.check_status()

            assert error is not None
            # Should mention slow response or timeout
            assert "slow" in error.lower() or "loading" in error.lower()


class TestOllamaStatusCheckGenericError:
    """Test check_status with generic errors."""

    @pytest.mark.asyncio
    async def test_generic_error_returns_false(self):
        """Test connected is False on generic error."""
        provider = OllamaProvider()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Something went wrong"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            connected, _, _ = await provider.check_status()

            assert connected is False

    @pytest.mark.asyncio
    async def test_generic_error_returns_empty_models(self):
        """Test models list is empty on generic error."""
        provider = OllamaProvider()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Something went wrong"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            _, models, _ = await provider.check_status()

            assert models == []

    @pytest.mark.asyncio
    async def test_generic_error_includes_details(self):
        """Test error includes details about the issue."""
        provider = OllamaProvider()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Something went wrong"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            _, _, error = await provider.check_status()

            assert error is not None
            assert "ollama" in error.lower() or "connect" in error.lower()


class TestOllamaRefreshModels:
    """Test refresh_models method."""

    @pytest.mark.asyncio
    async def test_refresh_models_returns_list(self):
        """Test refresh_models returns list of model names."""
        provider = OllamaProvider()
        mock_response = create_mock_response({
            "models": [{"name": "llama3:latest"}]
        })

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            models = await provider.refresh_models()

            assert isinstance(models, list)

    @pytest.mark.asyncio
    async def test_refresh_models_auto_selects_first(self):
        """Test refresh_models auto-selects first model if none set."""
        provider = OllamaProvider()
        assert provider.model is None

        mock_response = create_mock_response({
            "models": [{"name": "llama3:latest"}]
        })

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            await provider.refresh_models()

            assert provider.model == "llama3:latest"
