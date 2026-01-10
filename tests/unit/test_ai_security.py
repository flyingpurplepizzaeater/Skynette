"""Tests for AI API key security."""

import pytest
from unittest.mock import patch, MagicMock

from src.ai.security import store_api_key, get_api_key, delete_api_key, has_api_key, list_stored_providers


class TestAPIKeySecurity:
    """Test API key storage and retrieval."""

    @patch('keyring.set_password')
    def test_store_api_key(self, mock_set):
        """Test storing API key in keyring."""
        store_api_key("openai", "sk-test123")

        mock_set.assert_called_once_with(
            'skynette-ai',
            'openai',
            'sk-test123'
        )

    @patch('keyring.get_password')
    def test_get_api_key(self, mock_get):
        """Test retrieving API key from keyring."""
        mock_get.return_value = "sk-test123"

        key = get_api_key("openai")

        assert key == "sk-test123"
        mock_get.assert_called_once_with('skynette-ai', 'openai')

    @patch('keyring.get_password')
    def test_get_api_key_not_found(self, mock_get):
        """Test retrieving non-existent API key."""
        mock_get.return_value = None

        key = get_api_key("openai")

        assert key is None

    @patch('keyring.delete_password')
    def test_delete_api_key(self, mock_delete):
        """Test deleting API key from keyring."""
        delete_api_key("openai")

        mock_delete.assert_called_once_with('skynette-ai', 'openai')

    @patch('keyring.get_password')
    def test_has_api_key_true(self, mock_get):
        """Test checking if API key exists (positive)."""
        mock_get.return_value = "sk-test123"

        result = has_api_key("openai")

        assert result is True

    @patch('keyring.get_password')
    def test_has_api_key_false(self, mock_get):
        """Test checking if API key exists (negative)."""
        mock_get.return_value = None

        result = has_api_key("openai")

        assert result is False

    @patch('keyring.set_password', side_effect=Exception("Keyring error"))
    def test_store_api_key_error(self, mock_set):
        """Test error handling when storing API key fails."""
        with pytest.raises(Exception):
            store_api_key("openai", "sk-test123")

    @patch('keyring.get_password', side_effect=Exception("Keyring error"))
    def test_get_api_key_error(self, mock_get):
        """Test error handling when retrieving API key fails."""
        key = get_api_key("openai")
        assert key is None

    @patch('keyring.delete_password', side_effect=Exception("Keyring error"))
    def test_delete_api_key_error(self, mock_delete):
        """Test error handling when deleting API key fails."""
        with pytest.raises(Exception):
            delete_api_key("openai")

    @patch('src.ai.security.get_api_key')
    def test_list_stored_providers(self, mock_get):
        """Test listing stored providers."""
        def side_effect(provider):
            return "sk-key" if provider in ["openai", "anthropic"] else None

        mock_get.side_effect = side_effect

        providers = list_stored_providers()

        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" not in providers
        assert "groq" not in providers

    def test_store_api_key_empty_provider(self):
        """Test that empty provider name is rejected."""
        with pytest.raises(ValueError, match="Provider name cannot be empty"):
            store_api_key("", "sk-test123")

    def test_store_api_key_whitespace_provider(self):
        """Test that whitespace-only provider name is rejected."""
        with pytest.raises(ValueError, match="Provider name cannot be empty"):
            store_api_key("   ", "sk-test123")

    def test_store_api_key_empty_key(self):
        """Test that empty API key is rejected."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            store_api_key("openai", "")

    def test_get_api_key_empty_provider(self):
        """Test that empty provider name is rejected."""
        with pytest.raises(ValueError, match="Provider name cannot be empty"):
            get_api_key("")

    def test_delete_api_key_empty_provider(self):
        """Test that empty provider name is rejected."""
        with pytest.raises(ValueError, match="Provider name cannot be empty"):
            delete_api_key("")

    def test_has_api_key_empty_provider(self):
        """Test that empty provider name is rejected."""
        with pytest.raises(ValueError, match="Provider name cannot be empty"):
            has_api_key("")
