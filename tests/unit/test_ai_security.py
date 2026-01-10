"""Tests for AI API key security."""

import pytest
from unittest.mock import patch, MagicMock

from src.ai.security import store_api_key, get_api_key, delete_api_key, has_api_key


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
