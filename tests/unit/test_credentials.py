"""
Tests for Credential Vault and OAuth2 Manager.

Tests secure credential storage, encryption, and OAuth2 token management.
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta, UTC
from unittest.mock import patch, MagicMock


class TestCredentialVault:
    """Tests for CredentialVault class."""

    @pytest.fixture
    def vault(self, tmp_path):
        """Create a vault with temporary database."""
        from src.data.credentials import CredentialVault
        db_path = tmp_path / "test_credentials.db"
        return CredentialVault(db_path=db_path)

    def test_save_and_get_credential(self, vault):
        """Test saving and retrieving a credential."""
        cred_id = vault.save_credential(
            name="Test API Key",
            service="test_service",
            data={"api_key": "sk-test-123"}
        )

        assert cred_id is not None

        retrieved = vault.get_credential(cred_id)
        assert retrieved is not None
        assert retrieved["name"] == "Test API Key"
        assert retrieved["service"] == "test_service"
        assert retrieved["data"]["api_key"] == "sk-test-123"

    def test_get_credential_by_service(self, vault):
        """Test retrieving credential by service name."""
        vault.save_credential(
            name="OpenAI Key",
            service="openai",
            data={"api_key": "sk-openai-123"}
        )

        cred = vault.get_credential_by_service("openai")
        assert cred is not None
        assert cred["data"]["api_key"] == "sk-openai-123"

    def test_get_nonexistent_credential(self, vault):
        """Test getting a credential that doesn't exist."""
        result = vault.get_credential("nonexistent-id")
        assert result is None

    def test_list_credentials(self, vault):
        """Test listing all credentials."""
        vault.save_credential("Key 1", "service_a", {"key": "1"})
        vault.save_credential("Key 2", "service_b", {"key": "2"})
        vault.save_credential("Key 3", "service_a", {"key": "3"})

        creds = vault.list_credentials()
        assert len(creds) == 3

        # Should not include decrypted data
        for cred in creds:
            assert "data" not in cred

    def test_list_credentials_by_service(self, vault):
        """Test listing credentials for a specific service."""
        vault.save_credential("Key 1", "slack", {"key": "1"})
        vault.save_credential("Key 2", "slack", {"key": "2"})
        vault.save_credential("Key 3", "github", {"key": "3"})

        slack_creds = vault.list_credentials_by_service("slack")
        assert len(slack_creds) == 2

    def test_update_credential(self, vault):
        """Test updating a credential."""
        cred_id = vault.save_credential(
            name="Original Name",
            service="test",
            data={"key": "original"}
        )

        # Update name only
        vault.update_credential(cred_id, name="New Name")
        cred = vault.get_credential(cred_id)
        assert cred["name"] == "New Name"
        assert cred["data"]["key"] == "original"

        # Update data only
        vault.update_credential(cred_id, data={"key": "updated"})
        cred = vault.get_credential(cred_id)
        assert cred["data"]["key"] == "updated"

    def test_delete_credential(self, vault):
        """Test deleting a credential."""
        cred_id = vault.save_credential(
            name="To Delete",
            service="test",
            data={"key": "value"}
        )

        assert vault.get_credential(cred_id) is not None

        deleted = vault.delete_credential(cred_id)
        assert deleted is True
        assert vault.get_credential(cred_id) is None

    def test_delete_nonexistent_credential(self, vault):
        """Test deleting a credential that doesn't exist."""
        deleted = vault.delete_credential("nonexistent")
        assert deleted is False

    def test_encryption_actually_encrypts(self, vault):
        """Verify data is actually encrypted in the database."""
        import sqlite3

        secret_value = "super-secret-api-key"
        vault.save_credential(
            name="Secret",
            service="test",
            data={"api_key": secret_value}
        )

        # Read raw data from database
        conn = sqlite3.connect(vault.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM credentials")
        row = cursor.fetchone()
        conn.close()

        # Raw data should NOT contain the secret (it's encrypted)
        assert secret_value not in row[0]

    def test_export_credentials_without_data(self, vault, tmp_path):
        """Test exporting credentials metadata only."""
        vault.save_credential("Key 1", "service_a", {"key": "secret1"})
        vault.save_credential("Key 2", "service_b", {"key": "secret2"})

        export_path = tmp_path / "export.json"
        vault.export_credentials(export_path, include_data=False)

        import json
        with open(export_path) as f:
            exported = json.load(f)

        assert len(exported) == 2
        for cred in exported:
            assert "data" not in cred

    def test_export_credentials_with_data(self, vault, tmp_path):
        """Test exporting credentials with decrypted data."""
        vault.save_credential("Key 1", "service_a", {"key": "secret1"})

        export_path = tmp_path / "export.json"
        vault.export_credentials(export_path, include_data=True)

        import json
        with open(export_path) as f:
            exported = json.load(f)

        assert exported[0]["data"]["key"] == "secret1"

    def test_import_credentials(self, vault, tmp_path):
        """Test importing credentials from JSON."""
        import json

        export_data = [
            {
                "id": "import-1",
                "name": "Imported Key",
                "service": "imported_service",
                "data": {"api_key": "imported-secret"},
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
        ]

        import_path = tmp_path / "import.json"
        with open(import_path, "w") as f:
            json.dump(export_data, f)

        vault.import_credentials(import_path)

        cred = vault.get_credential("import-1")
        assert cred is not None
        assert cred["name"] == "Imported Key"
        assert cred["data"]["api_key"] == "imported-secret"


class TestCredentialHelpers:
    """Tests for credential helper functions."""

    def test_store_api_key(self, tmp_path):
        """Test storing an API key."""
        from src.data.credentials import store_api_key, get_api_key, CredentialVault

        vault = CredentialVault(db_path=tmp_path / "test.db")

        cred_id = vault.save_credential(
            name="OpenAI API Key",
            service="openai",
            data={"api_key": "sk-test-123", "type": "api_key"}
        )

        cred = vault.get_credential_by_service("openai")
        assert cred["data"]["api_key"] == "sk-test-123"

    def test_store_basic_auth(self, tmp_path):
        """Test storing basic auth credentials."""
        from src.data.credentials import CredentialVault, CredentialType

        vault = CredentialVault(db_path=tmp_path / "test.db")

        vault.save_credential(
            name="Email Login",
            service="email",
            data={
                "type": CredentialType.BASIC_AUTH.value,
                "username": "user@example.com",
                "password": "secret123"
            }
        )

        cred = vault.get_credential_by_service("email")
        assert cred["data"]["username"] == "user@example.com"
        assert cred["data"]["password"] == "secret123"


class TestOAuth2Manager:
    """Tests for OAuth2Manager class."""

    @pytest.fixture
    def oauth_manager(self, tmp_path):
        """Create OAuth2Manager with temporary vault."""
        from src.data.credentials import OAuth2Manager, CredentialVault

        vault = CredentialVault(db_path=tmp_path / "oauth_test.db")
        return OAuth2Manager(vault=vault)

    def test_store_oauth_tokens(self, oauth_manager):
        """Test storing OAuth2 tokens."""
        cred_id = oauth_manager.store_oauth_tokens(
            service="google",
            access_token="ya29.test-access-token",
            refresh_token="1//test-refresh-token",
            expires_at="2024-12-31T23:59:59+00:00",
            scopes=["https://www.googleapis.com/auth/drive"],
        )

        assert cred_id is not None

        tokens = oauth_manager.get_oauth_tokens("google")
        assert tokens is not None
        assert tokens["access_token"] == "ya29.test-access-token"
        assert tokens["refresh_token"] == "1//test-refresh-token"

    def test_get_access_token(self, oauth_manager):
        """Test getting just the access token."""
        oauth_manager.store_oauth_tokens(
            service="microsoft",
            access_token="eyJ0eXAi.test-token",
        )

        token = oauth_manager.get_access_token("microsoft")
        assert token == "eyJ0eXAi.test-token"

    def test_get_nonexistent_tokens(self, oauth_manager):
        """Test getting tokens for service without credentials."""
        tokens = oauth_manager.get_oauth_tokens("nonexistent")
        assert tokens is None

    def test_is_token_expired_no_expiry(self, oauth_manager):
        """Test token expiry check when no expiry set."""
        oauth_manager.store_oauth_tokens(
            service="test",
            access_token="token",
            expires_at=None,
        )

        # Should be considered expired if no expiry set
        assert oauth_manager.is_token_expired("test") is True

    def test_is_token_expired_future(self, oauth_manager):
        """Test token expiry check for future expiry."""
        future_time = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

        oauth_manager.store_oauth_tokens(
            service="test",
            access_token="token",
            expires_at=future_time,
        )

        assert oauth_manager.is_token_expired("test") is False

    def test_is_token_expired_past(self, oauth_manager):
        """Test token expiry check for past expiry."""
        past_time = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

        oauth_manager.store_oauth_tokens(
            service="test",
            access_token="token",
            expires_at=past_time,
        )

        assert oauth_manager.is_token_expired("test") is True

    def test_is_token_expired_within_buffer(self, oauth_manager):
        """Test token expiry check within 5-minute buffer."""
        # Token expires in 3 minutes (within 5-minute buffer)
        near_expiry = (datetime.now(UTC) + timedelta(minutes=3)).isoformat()

        oauth_manager.store_oauth_tokens(
            service="test",
            access_token="token",
            expires_at=near_expiry,
        )

        # Should be considered expired (within buffer)
        assert oauth_manager.is_token_expired("test") is True

    def test_needs_refresh(self, oauth_manager):
        """Test needs_refresh check."""
        past_time = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

        oauth_manager.store_oauth_tokens(
            service="test",
            access_token="token",
            refresh_token="refresh",
            expires_at=past_time,
        )

        assert oauth_manager.needs_refresh("test") is True

    def test_needs_refresh_no_refresh_token(self, oauth_manager):
        """Test needs_refresh when no refresh token."""
        past_time = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

        oauth_manager.store_oauth_tokens(
            service="test",
            access_token="token",
            refresh_token=None,
            expires_at=past_time,
        )

        # Can't refresh without refresh token
        assert oauth_manager.needs_refresh("test") is False

    def test_update_tokens(self, oauth_manager):
        """Test updating tokens after refresh."""
        oauth_manager.store_oauth_tokens(
            service="test",
            access_token="old-token",
            refresh_token="refresh",
        )

        new_expiry = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

        updated = oauth_manager.update_tokens(
            service="test",
            access_token="new-token",
            expires_at=new_expiry,
        )

        assert updated is True

        tokens = oauth_manager.get_oauth_tokens("test")
        assert tokens["access_token"] == "new-token"
        assert tokens["expires_at"] == new_expiry

    def test_delete_oauth(self, oauth_manager):
        """Test deleting OAuth credentials."""
        oauth_manager.store_oauth_tokens(
            service="test",
            access_token="token",
        )

        assert oauth_manager.get_oauth_tokens("test") is not None

        deleted = oauth_manager.delete_oauth("test")
        assert deleted is True
        assert oauth_manager.get_oauth_tokens("test") is None

    def test_list_oauth_credentials(self, oauth_manager):
        """Test listing OAuth credentials."""
        oauth_manager.store_oauth_tokens("google", "token1")
        oauth_manager.store_oauth_tokens("microsoft", "token2")

        # Add a non-OAuth credential
        oauth_manager.vault.save_credential("API Key", "openai", {"api_key": "sk-123"})

        oauth_creds = oauth_manager.list_oauth_credentials()

        assert len(oauth_creds) == 2
        services = [c["service"] for c in oauth_creds]
        assert "google_oauth" in services
        assert "microsoft_oauth" in services
        assert "openai" not in services


class TestOAuth2ProviderConfig:
    """Tests for OAuth2 provider configuration."""

    def test_get_provider_config_google(self):
        """Test getting Google OAuth config."""
        from src.data.credentials import OAuth2Manager

        config = OAuth2Manager.get_provider_config("google")
        assert config is not None
        assert "auth_url" in config
        assert "token_url" in config
        assert "scopes" in config
        assert "drive" in config["scopes"]

    def test_get_provider_config_microsoft(self):
        """Test getting Microsoft OAuth config."""
        from src.data.credentials import OAuth2Manager

        config = OAuth2Manager.get_provider_config("microsoft")
        assert config is not None
        assert "teams" in config["scopes"]

    def test_get_provider_config_unknown(self):
        """Test getting config for unknown provider."""
        from src.data.credentials import OAuth2Manager

        config = OAuth2Manager.get_provider_config("unknown_provider")
        assert config is None

    def test_get_auth_url_google(self):
        """Test building Google auth URL."""
        from src.data.credentials import OAuth2Manager

        url = OAuth2Manager.get_auth_url(
            provider="google",
            client_id="test-client-id",
            redirect_uri="http://localhost:8080/callback",
            scope_set="drive",
            state="random-state",
        )

        assert url is not None
        assert "accounts.google.com" in url
        assert "test-client-id" in url
        assert "redirect_uri=" in url
        assert "state=random-state" in url
        assert "access_type=offline" in url  # Google-specific

    def test_get_auth_url_unknown_provider(self):
        """Test auth URL for unknown provider."""
        from src.data.credentials import OAuth2Manager

        url = OAuth2Manager.get_auth_url(
            provider="unknown",
            client_id="test",
            redirect_uri="http://localhost/callback",
        )

        assert url is None


class TestCredentialType:
    """Tests for CredentialType enum."""

    def test_credential_types_exist(self):
        """Test all credential types are defined."""
        from src.data.credentials import CredentialType

        assert CredentialType.API_KEY.value == "api_key"
        assert CredentialType.OAUTH2.value == "oauth2"
        assert CredentialType.BASIC_AUTH.value == "basic_auth"
        assert CredentialType.CUSTOM.value == "custom"

    def test_credential_type_is_string(self):
        """Test credential types can be used as strings."""
        from src.data.credentials import CredentialType

        # Should be usable in JSON/dict contexts
        data = {"type": CredentialType.OAUTH2}
        assert data["type"] == "oauth2"
