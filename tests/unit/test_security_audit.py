"""
Security Audit Tests for API Key Handling

Tests to verify that API keys are securely stored and handled:
- Keys stored via keyring (not plaintext)
- Keys not logged
- Keys not exposed in exceptions
- Memory handling documented
"""

import gc
import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from src.ai.security import (
    SERVICE_NAME,
    delete_api_key,
    get_api_key,
    store_api_key,
)


class TestKeyringUsage:
    """Tests to verify API keys use keyring storage."""

    @patch("keyring.set_password")
    def test_api_key_uses_keyring_for_storage(self, mock_set):
        """API keys are stored via keyring, not plaintext files."""
        store_api_key("test_provider", "sk-test-key-12345")

        mock_set.assert_called_once()
        args = mock_set.call_args[0]
        assert args[0] == SERVICE_NAME  # Service name
        assert args[1] == "test_provider"  # Provider
        assert args[2] == "sk-test-key-12345"  # Key

    @patch("keyring.get_password")
    def test_api_key_retrieved_from_keyring(self, mock_get):
        """API keys are retrieved from keyring."""
        mock_get.return_value = "sk-retrieved-key"

        result = get_api_key("test_provider")

        assert result == "sk-retrieved-key"
        mock_get.assert_called_once_with(SERVICE_NAME, "test_provider")

    @patch("keyring.delete_password")
    def test_api_key_deleted_from_keyring(self, mock_delete):
        """API keys are deleted from keyring."""
        delete_api_key("test_provider")

        mock_delete.assert_called_once_with(SERVICE_NAME, "test_provider")


class TestNoLogging:
    """Tests to verify API keys are not logged."""

    @patch("keyring.set_password")
    def test_api_key_not_logged_on_store(self, mock_set, caplog):
        """API keys should never appear in logs during storage."""
        test_key = "sk-super-secret-key-12345-audit"

        with caplog.at_level(logging.DEBUG):
            store_api_key("test_provider", test_key)

        # Check no log entry contains the key
        for record in caplog.records:
            assert test_key not in record.message
            assert "sk-super-secret" not in record.message

    @patch("keyring.get_password")
    def test_api_key_not_logged_on_retrieve(self, mock_get, caplog):
        """API keys should never appear in logs during retrieval."""
        test_key = "sk-retrieved-secret-key-67890"
        mock_get.return_value = test_key

        with caplog.at_level(logging.DEBUG):
            result = get_api_key("test_provider")

        # The key was retrieved
        assert result == test_key

        # But not logged
        for record in caplog.records:
            assert test_key not in record.message

    @patch("keyring.delete_password")
    def test_api_key_not_logged_on_delete(self, mock_delete, caplog):
        """API keys should never appear in logs during deletion."""
        with caplog.at_level(logging.DEBUG):
            delete_api_key("test_provider")

        # Provider name may be logged, but no key values
        for record in caplog.records:
            assert "sk-" not in record.message


class TestExceptionHandling:
    """Tests to verify API keys are not exposed in exceptions."""

    @patch("keyring.get_password", side_effect=Exception("Keyring error"))
    def test_get_key_exception_returns_none(self, mock_get):
        """Exceptions during key retrieval should return None, not raise."""
        result = get_api_key("nonexistent_provider")

        assert result is None

    @patch("keyring.get_password", side_effect=RuntimeError("Access denied"))
    def test_get_key_runtime_error_handled(self, mock_get):
        """Runtime errors during retrieval are handled gracefully."""
        result = get_api_key("test_provider")

        assert result is None

    @patch("keyring.set_password", side_effect=Exception("Storage error"))
    def test_store_key_exception_does_not_expose_key(self, mock_set):
        """Storage exceptions should not expose the API key."""
        test_key = "sk-should-not-appear-in-exception"

        with pytest.raises(Exception) as exc_info:
            store_api_key("test_provider", test_key)

        # The key should not appear in the exception message
        assert test_key not in str(exc_info.value)


class TestMemoryHandling:
    """Tests documenting memory handling behavior.

    Note: Python string interning may keep small strings alive.
    These tests document the behavior rather than guaranteeing cleanup.
    """

    def test_api_key_variable_cleanup_pattern(self):
        """Document the pattern for cleaning up key variables.

        Note: Python strings are immutable and may be interned.
        This test documents the recommended pattern for clearing
        key references, acknowledging Python's limitations.

        For truly secure key handling in memory, consider:
        - Using bytearray instead of str (can be zeroed)
        - Using secure memory libraries like cryptography.hazmat
        - Minimizing key lifetime in memory
        """
        # Create a key-like string in a local scope
        def use_key():
            key = "sk-test-memory-key-for-gc-test"
            # Use the key...
            _ = len(key)
            # Key goes out of scope here
            return True

        result = use_key()
        gc.collect()

        # Verify the function completed
        assert result is True

        # Document: Python strings cannot be explicitly zeroed,
        # but proper scoping and gc.collect() is best practice

    def test_gc_collection_happens(self):
        """Verify garbage collection runs without errors."""
        collected = gc.collect()
        # Just verify GC runs
        assert collected >= 0


class TestEnvironmentSafety:
    """Tests to verify API keys are not stored in environment variables."""

    def test_no_api_keys_in_env_variables(self):
        """API keys should not be stored in environment variables."""
        suspicious_patterns = ["sk-", "key-", "secret-"]

        for key, value in os.environ.items():
            # Skip known test mode markers
            if key in ("SKYNETTE_TEST_MODE", "SKYNETTE_MOCK_AI", "SKYNETTE_DATA_DIR"):
                continue

            # Skip CI/CD environment variables
            if key in ("GITHUB_TOKEN", "CI", "PATH", "PYTHONPATH"):
                continue

            # Check for suspicious values that look like API keys
            if "API" in key.upper() or "KEY" in key.upper():
                # Allow if it's just a boolean or empty
                if value.lower() in ("true", "false", "1", "0", ""):
                    continue

                # Fail if it looks like an actual secret key
                for pattern in suspicious_patterns:
                    if value.startswith(pattern) and len(value) > 30:
                        pytest.fail(
                            f"Potential API key found in environment variable: {key}"
                        )

    def test_skynette_specific_env_vars_safe(self):
        """Skynette-specific env vars should not contain keys."""
        for key, value in os.environ.items():
            if key.startswith("SKYNETTE_"):
                # These are allowed
                if key in (
                    "SKYNETTE_TEST_MODE",
                    "SKYNETTE_MOCK_AI",
                    "SKYNETTE_DATA_DIR",
                ):
                    continue

                # Others should not be API keys
                assert not value.startswith(
                    "sk-"
                ), f"SKYNETTE env var contains API key: {key}"


class TestSecurityCodeReview:
    """Tests that verify security.py follows best practices."""

    def test_service_name_constant_defined(self):
        """Service name should be a constant."""
        assert SERVICE_NAME == "skynette-ai"

    def test_store_validates_provider(self):
        """store_api_key should validate provider name."""
        with pytest.raises(ValueError, match="Provider name cannot be empty"):
            store_api_key("", "sk-test")

        with pytest.raises(ValueError, match="Provider name cannot be empty"):
            store_api_key("   ", "sk-test")

    def test_store_validates_key(self):
        """store_api_key should validate API key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            store_api_key("test_provider", "")

        with pytest.raises(ValueError, match="API key cannot be empty"):
            store_api_key("test_provider", "   ")

    def test_get_validates_provider(self):
        """get_api_key should validate provider name."""
        with pytest.raises(ValueError, match="Provider name cannot be empty"):
            get_api_key("")

    def test_delete_validates_provider(self):
        """delete_api_key should validate provider name."""
        with pytest.raises(ValueError, match="Provider name cannot be empty"):
            delete_api_key("")


class TestSecurityModule:
    """Tests for security module integrity."""

    def test_security_module_imports(self):
        """Security module should import without errors."""
        from src.ai import security

        assert hasattr(security, "store_api_key")
        assert hasattr(security, "get_api_key")
        assert hasattr(security, "delete_api_key")
        assert hasattr(security, "has_api_key")
        assert hasattr(security, "list_stored_providers")

    def test_no_debug_statements_in_security_module(self):
        """Security module should not have print statements for keys."""
        import inspect
        from src.ai import security

        source = inspect.getsource(security)

        # Should not have print statements that might leak keys
        assert "print(api_key" not in source
        assert "print(key" not in source

        # Should not log the actual key value
        assert "logger.debug(api_key" not in source
        assert "logger.info(api_key" not in source
