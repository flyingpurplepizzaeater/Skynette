"""
Tests for Webhook Manager.

Tests webhook configuration, storage, authentication, and request handling.
"""

import base64
import hashlib
import hmac
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


class TestAuthMethod:
    """Tests for AuthMethod enum."""

    def test_auth_method_values(self):
        """Test authentication method enum values."""
        from src.core.webhooks.manager import AuthMethod

        assert AuthMethod.NONE.value == "none"
        assert AuthMethod.BASIC.value == "basic"
        assert AuthMethod.BEARER.value == "bearer"
        assert AuthMethod.API_KEY.value == "api_key"
        assert AuthMethod.HMAC_SHA256.value == "hmac_sha256"


class TestWebhookConfig:
    """Tests for WebhookConfig dataclass."""

    def test_create_minimal(self):
        """Test creating webhook config with minimal data."""
        from src.core.webhooks.manager import WebhookConfig, AuthMethod

        config = WebhookConfig(
            id="test-123",
            path="/webhook/test",
            workflow_id="workflow-456",
        )

        assert config.id == "test-123"
        assert config.path == "/webhook/test"
        assert config.workflow_id == "workflow-456"
        assert config.auth_method == AuthMethod.NONE
        assert config.enabled is True
        assert config.allowed_methods == ["POST"]

    def test_to_dict(self):
        """Test converting config to dictionary."""
        from src.core.webhooks.manager import WebhookConfig, AuthMethod

        config = WebhookConfig(
            id="test-123",
            path="/webhook/test",
            workflow_id="workflow-456",
            name="Test Webhook",
            description="A test webhook",
            auth_method=AuthMethod.BEARER,
            auth_value="secret-token",
            allowed_methods=["POST", "PUT"],
            trigger_count=5,
        )

        data = config.to_dict()

        assert data["id"] == "test-123"
        assert data["path"] == "/webhook/test"
        assert data["workflow_id"] == "workflow-456"
        assert data["name"] == "Test Webhook"
        assert data["auth_method"] == "bearer"
        assert data["allowed_methods"] == ["POST", "PUT"]
        assert data["trigger_count"] == 5

    def test_from_dict_minimal(self):
        """Test creating config from minimal dictionary."""
        from src.core.webhooks.manager import WebhookConfig, AuthMethod

        data = {
            "id": "from-dict-123",
            "path": "/webhook/from-dict",
            "workflow_id": "workflow-789",
        }

        config = WebhookConfig.from_dict(data)

        assert config.id == "from-dict-123"
        assert config.path == "/webhook/from-dict"
        assert config.workflow_id == "workflow-789"
        assert config.auth_method == AuthMethod.NONE
        assert config.enabled is True

    def test_from_dict_full(self):
        """Test creating config from full dictionary."""
        from src.core.webhooks.manager import WebhookConfig, AuthMethod

        data = {
            "id": "full-123",
            "path": "/webhook/full",
            "workflow_id": "workflow-full",
            "name": "Full Webhook",
            "description": "Full description",
            "auth_method": "hmac_sha256",
            "auth_value": "hmac-secret",
            "allowed_methods": ["POST", "GET"],
            "enabled": False,
            "created_at": "2024-01-01T00:00:00Z",
            "last_triggered": "2024-01-02T12:00:00Z",
            "trigger_count": 100,
        }

        config = WebhookConfig.from_dict(data)

        assert config.id == "full-123"
        assert config.auth_method == AuthMethod.HMAC_SHA256
        assert config.enabled is False
        assert config.trigger_count == 100

    def test_roundtrip(self):
        """Test config roundtrip (to_dict -> from_dict)."""
        from src.core.webhooks.manager import WebhookConfig, AuthMethod

        original = WebhookConfig(
            id="roundtrip-123",
            path="/webhook/roundtrip",
            workflow_id="workflow-rt",
            name="Roundtrip Test",
            auth_method=AuthMethod.API_KEY,
            auth_value="api-key-value",
            trigger_count=42,
        )

        data = original.to_dict()
        restored = WebhookConfig.from_dict(data)

        assert restored.id == original.id
        assert restored.path == original.path
        assert restored.auth_method == original.auth_method
        assert restored.trigger_count == original.trigger_count


class TestWebhookRequest:
    """Tests for WebhookRequest dataclass."""

    def test_json_property_valid(self):
        """Test JSON parsing of valid body."""
        from src.core.webhooks.manager import WebhookRequest

        request = WebhookRequest(
            method="POST",
            path="/webhook/test",
            headers={},
            query_params={},
            body=b'{"key": "value", "number": 42}',
        )

        assert request.json == {"key": "value", "number": 42}

    def test_json_property_invalid(self):
        """Test JSON parsing of invalid body."""
        from src.core.webhooks.manager import WebhookRequest

        request = WebhookRequest(
            method="POST",
            path="/webhook/test",
            headers={},
            query_params={},
            body=b"not valid json",
        )

        assert request.json is None

    def test_text_property(self):
        """Test text decoding of body."""
        from src.core.webhooks.manager import WebhookRequest

        request = WebhookRequest(
            method="POST",
            path="/webhook/test",
            headers={},
            query_params={},
            body=b"Hello, World!",
        )

        assert request.text == "Hello, World!"

    def test_to_trigger_data(self):
        """Test conversion to trigger data."""
        from src.core.webhooks.manager import WebhookRequest

        request = WebhookRequest(
            method="POST",
            path="/webhook/test",
            headers={"content-type": "application/json"},
            query_params={"param1": ["value1"], "param2": ["a", "b"]},
            body=b'{"event": "test"}',
            client_ip="192.168.1.1",
            timestamp="2024-01-01T00:00:00Z",
        )

        data = request.to_trigger_data()

        assert data["method"] == "POST"
        assert data["path"] == "/webhook/test"
        assert data["headers"]["content-type"] == "application/json"
        assert data["query"]["param1"] == "value1"  # Single value extracted
        assert data["query"]["param2"] == ["a", "b"]  # Multiple values kept as list
        assert data["body"]["event"] == "test"
        assert data["client_ip"] == "192.168.1.1"


class TestWebhookResponse:
    """Tests for WebhookResponse dataclass."""

    def test_to_bytes_none(self):
        """Test serialization of None body."""
        from src.core.webhooks.manager import WebhookResponse

        response = WebhookResponse(status=204, body=None)
        assert response.to_bytes() == b""

    def test_to_bytes_string(self):
        """Test serialization of string body."""
        from src.core.webhooks.manager import WebhookResponse

        response = WebhookResponse(status=200, body="Hello")
        assert response.to_bytes() == b"Hello"

    def test_to_bytes_bytes(self):
        """Test serialization of bytes body."""
        from src.core.webhooks.manager import WebhookResponse

        response = WebhookResponse(status=200, body=b"Binary data")
        assert response.to_bytes() == b"Binary data"

    def test_to_bytes_dict(self):
        """Test serialization of dict body."""
        from src.core.webhooks.manager import WebhookResponse

        response = WebhookResponse(status=200, body={"key": "value"})
        assert response.to_bytes() == b'{"key": "value"}'


class TestWebhookStore:
    """Tests for WebhookStore class."""

    @pytest.fixture
    def webhook_store(self, tmp_path):
        """Create a WebhookStore with temporary database."""
        from src.core.webhooks.manager import WebhookStore

        db_path = tmp_path / "webhooks.db"
        return WebhookStore(db_path=db_path)

    @pytest.fixture
    def sample_webhook(self):
        """Create a sample webhook config."""
        from src.core.webhooks.manager import WebhookConfig, AuthMethod

        return WebhookConfig(
            id="store-test-123",
            path="/webhook/store-test",
            workflow_id="workflow-store",
            name="Store Test",
            auth_method=AuthMethod.BEARER,
            auth_value="test-token",
            created_at="2024-01-01T00:00:00Z",
        )

    def test_save_and_get_by_id(self, webhook_store, sample_webhook):
        """Test saving and retrieving by ID."""
        webhook_store.save(sample_webhook)
        retrieved = webhook_store.get_by_id(sample_webhook.id)

        assert retrieved is not None
        assert retrieved.id == sample_webhook.id
        assert retrieved.path == sample_webhook.path
        assert retrieved.auth_value == sample_webhook.auth_value

    def test_get_by_id_not_found(self, webhook_store):
        """Test getting non-existent webhook."""
        result = webhook_store.get_by_id("non-existent")
        assert result is None

    def test_get_by_path(self, webhook_store, sample_webhook):
        """Test retrieving by path."""
        webhook_store.save(sample_webhook)
        retrieved = webhook_store.get_by_path(sample_webhook.path)

        assert retrieved is not None
        assert retrieved.id == sample_webhook.id

    def test_get_by_path_not_found(self, webhook_store):
        """Test getting by non-existent path."""
        result = webhook_store.get_by_path("/non/existent/path")
        assert result is None

    def test_get_by_workflow(self, webhook_store):
        """Test retrieving webhooks by workflow ID."""
        from src.core.webhooks.manager import WebhookConfig

        # Create multiple webhooks for same workflow
        for i in range(3):
            webhook = WebhookConfig(
                id=f"wf-test-{i}",
                path=f"/webhook/wf-test-{i}",
                workflow_id="shared-workflow",
                created_at="2024-01-01T00:00:00Z",
            )
            webhook_store.save(webhook)

        # Create webhook for different workflow
        other = WebhookConfig(
            id="other-wf",
            path="/webhook/other",
            workflow_id="other-workflow",
            created_at="2024-01-01T00:00:00Z",
        )
        webhook_store.save(other)

        # Retrieve by workflow
        webhooks = webhook_store.get_by_workflow("shared-workflow")
        assert len(webhooks) == 3

        other_webhooks = webhook_store.get_by_workflow("other-workflow")
        assert len(other_webhooks) == 1

    def test_list_all(self, webhook_store):
        """Test listing all webhooks."""
        from src.core.webhooks.manager import WebhookConfig

        # Create multiple webhooks
        for i in range(5):
            webhook = WebhookConfig(
                id=f"list-test-{i}",
                path=f"/webhook/list-{i}",
                workflow_id=f"workflow-{i}",
                created_at="2024-01-01T00:00:00Z",
            )
            webhook_store.save(webhook)

        all_webhooks = webhook_store.list_all()
        assert len(all_webhooks) == 5

    def test_delete(self, webhook_store, sample_webhook):
        """Test deleting a webhook."""
        webhook_store.save(sample_webhook)
        assert webhook_store.get_by_id(sample_webhook.id) is not None

        deleted = webhook_store.delete(sample_webhook.id)
        assert deleted is True
        assert webhook_store.get_by_id(sample_webhook.id) is None

    def test_delete_not_found(self, webhook_store):
        """Test deleting non-existent webhook."""
        deleted = webhook_store.delete("non-existent")
        assert deleted is False

    def test_update_trigger_stats(self, webhook_store, sample_webhook):
        """Test updating trigger statistics."""
        sample_webhook.trigger_count = 0
        webhook_store.save(sample_webhook)

        webhook_store.update_trigger_stats(sample_webhook.id)
        webhook_store.update_trigger_stats(sample_webhook.id)

        updated = webhook_store.get_by_id(sample_webhook.id)
        assert updated.trigger_count == 2
        assert updated.last_triggered is not None


class TestWebhookManager:
    """Tests for WebhookManager class."""

    @pytest.fixture
    def webhook_manager(self, tmp_path):
        """Create a WebhookManager with temporary storage."""
        from src.core.webhooks.manager import WebhookManager, WebhookStore

        store = WebhookStore(db_path=tmp_path / "webhooks.db")
        return WebhookManager(store=store, base_url="http://localhost:5678")

    def test_register_webhook_auto_path(self, webhook_manager):
        """Test registering webhook with auto-generated path."""
        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            name="Auto Path Test",
        )

        assert webhook.id is not None
        assert webhook.path.startswith("/webhook/")
        assert webhook.workflow_id == "test-workflow"
        assert webhook.enabled is True

    def test_register_webhook_custom_path(self, webhook_manager):
        """Test registering webhook with custom path."""
        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/custom/path",
            name="Custom Path Test",
        )

        assert webhook.path == "/custom/path"

    def test_register_webhook_normalizes_path(self, webhook_manager):
        """Test that paths without leading slash are normalized."""
        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="no/leading/slash",
        )

        assert webhook.path == "/no/leading/slash"

    def test_register_duplicate_path_fails(self, webhook_manager):
        """Test that duplicate paths raise error."""
        webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/duplicate/path",
        )

        with pytest.raises(ValueError, match="already exists"):
            webhook_manager.register_webhook(
                workflow_id="other-workflow",
                path="/duplicate/path",
            )

    def test_register_with_auth_generates_secret(self, webhook_manager):
        """Test that auth methods auto-generate secrets."""
        from src.core.webhooks.manager import AuthMethod

        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            auth_method=AuthMethod.BEARER,
        )

        assert webhook.auth_value != ""
        assert len(webhook.auth_value) > 20  # Token should be reasonably long

    def test_unregister_webhook(self, webhook_manager):
        """Test unregistering a webhook."""
        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/to/unregister",
        )

        result = webhook_manager.unregister_webhook(webhook.id)
        assert result is True

        assert webhook_manager.get_webhook(webhook.id) is None

    def test_unregister_nonexistent(self, webhook_manager):
        """Test unregistering non-existent webhook."""
        result = webhook_manager.unregister_webhook("non-existent-id")
        assert result is False

    def test_get_webhook_url(self, webhook_manager):
        """Test getting full webhook URL."""
        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/test/url",
        )

        url = webhook_manager.get_webhook_url(webhook)
        assert url == "http://localhost:5678/test/url"

    def test_list_webhooks_all(self, webhook_manager):
        """Test listing all webhooks."""
        for i in range(3):
            webhook_manager.register_webhook(
                workflow_id=f"workflow-{i}",
                path=f"/list/test/{i}",
            )

        webhooks = webhook_manager.list_webhooks()
        assert len(webhooks) == 3

    def test_list_webhooks_by_workflow(self, webhook_manager):
        """Test listing webhooks filtered by workflow."""
        for i in range(2):
            webhook_manager.register_webhook(
                workflow_id="target-workflow",
                path=f"/target/{i}",
            )

        webhook_manager.register_webhook(
            workflow_id="other-workflow",
            path="/other/webhook",
        )

        target_webhooks = webhook_manager.list_webhooks(workflow_id="target-workflow")
        assert len(target_webhooks) == 2

    def test_enable_disable_webhook(self, webhook_manager):
        """Test enabling and disabling webhooks."""
        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/enable/disable/test",
        )

        # Initially enabled
        assert webhook_manager.get_webhook(webhook.id).enabled is True

        # Disable
        result = webhook_manager.disable_webhook(webhook.id)
        assert result is True
        assert webhook_manager.get_webhook(webhook.id).enabled is False

        # Enable
        result = webhook_manager.enable_webhook(webhook.id)
        assert result is True
        assert webhook_manager.get_webhook(webhook.id).enabled is True

    def test_enable_nonexistent(self, webhook_manager):
        """Test enabling non-existent webhook."""
        result = webhook_manager.enable_webhook("non-existent")
        assert result is False

    def test_disable_nonexistent(self, webhook_manager):
        """Test disabling non-existent webhook."""
        result = webhook_manager.disable_webhook("non-existent")
        assert result is False


class TestWebhookAuthentication:
    """Tests for webhook authentication methods."""

    @pytest.fixture
    def webhook_manager(self, tmp_path):
        """Create a WebhookManager with temporary storage."""
        from src.core.webhooks.manager import WebhookManager, WebhookStore

        store = WebhookStore(db_path=tmp_path / "webhooks.db")
        return WebhookManager(store=store)

    def create_request(self, path, headers=None, body=b"", method="POST", query_params=None):
        """Helper to create WebhookRequest."""
        from src.core.webhooks.manager import WebhookRequest

        return WebhookRequest(
            method=method,
            path=path,
            headers=headers or {},
            query_params=query_params or {},
            body=body,
        )

    @pytest.mark.asyncio
    async def test_auth_none(self, webhook_manager):
        """Test request with no authentication required."""
        from src.core.webhooks.manager import AuthMethod

        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/auth/none",
            auth_method=AuthMethod.NONE,
        )

        request = self.create_request("/auth/none")
        response = await webhook_manager.handle_request(request)

        assert response.status == 200

    @pytest.mark.asyncio
    async def test_auth_basic_success(self, webhook_manager):
        """Test successful Basic authentication."""
        from src.core.webhooks.manager import AuthMethod

        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/auth/basic",
            auth_method=AuthMethod.BASIC,
            auth_value="user:password",
        )

        credentials = base64.b64encode(b"user:password").decode()
        request = self.create_request(
            "/auth/basic",
            headers={"authorization": f"Basic {credentials}"},
        )
        response = await webhook_manager.handle_request(request)

        assert response.status == 200

    @pytest.mark.asyncio
    async def test_auth_basic_failure(self, webhook_manager):
        """Test failed Basic authentication."""
        from src.core.webhooks.manager import AuthMethod

        webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/auth/basic/fail",
            auth_method=AuthMethod.BASIC,
            auth_value="user:correct",
        )

        credentials = base64.b64encode(b"user:wrong").decode()
        request = self.create_request(
            "/auth/basic/fail",
            headers={"authorization": f"Basic {credentials}"},
        )
        response = await webhook_manager.handle_request(request)

        assert response.status == 401

    @pytest.mark.asyncio
    async def test_auth_bearer_success(self, webhook_manager):
        """Test successful Bearer token authentication."""
        from src.core.webhooks.manager import AuthMethod

        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/auth/bearer",
            auth_method=AuthMethod.BEARER,
            auth_value="my-secret-token",
        )

        request = self.create_request(
            "/auth/bearer",
            headers={"authorization": "Bearer my-secret-token"},
        )
        response = await webhook_manager.handle_request(request)

        assert response.status == 200

    @pytest.mark.asyncio
    async def test_auth_bearer_failure(self, webhook_manager):
        """Test failed Bearer token authentication."""
        from src.core.webhooks.manager import AuthMethod

        webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/auth/bearer/fail",
            auth_method=AuthMethod.BEARER,
            auth_value="correct-token",
        )

        request = self.create_request(
            "/auth/bearer/fail",
            headers={"authorization": "Bearer wrong-token"},
        )
        response = await webhook_manager.handle_request(request)

        assert response.status == 401

    @pytest.mark.asyncio
    async def test_auth_api_key_header_success(self, webhook_manager):
        """Test successful API key authentication via header."""
        from src.core.webhooks.manager import AuthMethod

        webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/auth/apikey/header",
            auth_method=AuthMethod.API_KEY,
            auth_value="my-api-key",
        )

        request = self.create_request(
            "/auth/apikey/header",
            headers={"x-api-key": "my-api-key"},
        )
        response = await webhook_manager.handle_request(request)

        assert response.status == 200

    @pytest.mark.asyncio
    async def test_auth_api_key_query_success(self, webhook_manager):
        """Test successful API key authentication via query param."""
        from src.core.webhooks.manager import AuthMethod

        webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/auth/apikey/query",
            auth_method=AuthMethod.API_KEY,
            auth_value="query-api-key",
        )

        request = self.create_request(
            "/auth/apikey/query",
            query_params={"api_key": ["query-api-key"]},
        )
        response = await webhook_manager.handle_request(request)

        assert response.status == 200

    @pytest.mark.asyncio
    async def test_auth_hmac_sha256_success(self, webhook_manager):
        """Test successful HMAC-SHA256 signature verification."""
        from src.core.webhooks.manager import AuthMethod

        secret = "hmac-secret-key"
        webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/auth/hmac",
            auth_method=AuthMethod.HMAC_SHA256,
            auth_value=secret,
        )

        body = b'{"event": "test"}'
        signature = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        request = self.create_request(
            "/auth/hmac",
            headers={"x-signature-256": f"sha256={signature}"},
            body=body,
        )
        response = await webhook_manager.handle_request(request)

        assert response.status == 200

    @pytest.mark.asyncio
    async def test_auth_hmac_github_style(self, webhook_manager):
        """Test HMAC verification with GitHub-style header."""
        from src.core.webhooks.manager import AuthMethod

        secret = "github-secret"
        webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/auth/hmac/github",
            auth_method=AuthMethod.HMAC_SHA256,
            auth_value=secret,
        )

        body = b'{"action": "push"}'
        signature = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        request = self.create_request(
            "/auth/hmac/github",
            headers={"x-hub-signature-256": f"sha256={signature}"},
            body=body,
        )
        response = await webhook_manager.handle_request(request)

        assert response.status == 200


class TestWebhookRequestHandling:
    """Tests for webhook request handling."""

    @pytest.fixture
    def webhook_manager(self, tmp_path):
        """Create a WebhookManager with temporary storage."""
        from src.core.webhooks.manager import WebhookManager, WebhookStore

        store = WebhookStore(db_path=tmp_path / "webhooks.db")
        return WebhookManager(store=store)

    def create_request(self, path, headers=None, body=b"", method="POST"):
        """Helper to create WebhookRequest."""
        from src.core.webhooks.manager import WebhookRequest

        return WebhookRequest(
            method=method,
            path=path,
            headers=headers or {},
            query_params={},
            body=body,
        )

    @pytest.mark.asyncio
    async def test_not_found(self, webhook_manager):
        """Test request to non-existent webhook."""
        request = self.create_request("/not/found")
        response = await webhook_manager.handle_request(request)

        assert response.status == 404
        assert "not found" in response.body["error"].lower()

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, webhook_manager):
        """Test request with disallowed HTTP method."""
        webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/post/only",
            allowed_methods=["POST"],
        )

        request = self.create_request("/post/only", method="GET")
        response = await webhook_manager.handle_request(request)

        assert response.status == 405
        assert "not allowed" in response.body["error"].lower()

    @pytest.mark.asyncio
    async def test_disabled_webhook(self, webhook_manager):
        """Test request to disabled webhook."""
        webhook = webhook_manager.register_webhook(
            workflow_id="test-workflow",
            path="/disabled/webhook",
        )
        webhook_manager.disable_webhook(webhook.id)

        request = self.create_request("/disabled/webhook")
        response = await webhook_manager.handle_request(request)

        assert response.status == 404

    @pytest.mark.asyncio
    async def test_trigger_callback_success(self, webhook_manager):
        """Test successful workflow trigger callback."""
        webhook_manager.register_webhook(
            workflow_id="trigger-test",
            path="/trigger/success",
        )

        trigger_called = False
        trigger_data_received = None

        async def mock_trigger(workflow_id, trigger_data):
            nonlocal trigger_called, trigger_data_received
            trigger_called = True
            trigger_data_received = trigger_data
            return {"execution_id": "exec-123"}

        webhook_manager.set_trigger_callback(mock_trigger)

        request = self.create_request(
            "/trigger/success",
            body=b'{"event": "test"}',
        )
        response = await webhook_manager.handle_request(request)

        assert response.status == 200
        assert trigger_called is True
        assert trigger_data_received["body"]["event"] == "test"
        assert response.body["execution"]["execution_id"] == "exec-123"

    @pytest.mark.asyncio
    async def test_trigger_callback_error(self, webhook_manager):
        """Test workflow trigger callback error handling."""
        webhook_manager.register_webhook(
            workflow_id="trigger-error",
            path="/trigger/error",
        )

        async def mock_trigger_error(workflow_id, trigger_data):
            raise Exception("Trigger failed")

        webhook_manager.set_trigger_callback(mock_trigger_error)

        request = self.create_request("/trigger/error")
        response = await webhook_manager.handle_request(request)

        assert response.status == 500
        assert "Trigger failed" in response.body["error"]

    @pytest.mark.asyncio
    async def test_no_trigger_callback(self, webhook_manager):
        """Test request when no trigger callback is configured."""
        webhook_manager.register_webhook(
            workflow_id="no-trigger",
            path="/no/trigger",
        )
        # Don't set trigger callback

        request = self.create_request("/no/trigger")
        response = await webhook_manager.handle_request(request)

        assert response.status == 200
        assert "no trigger configured" in response.body["message"].lower()

    @pytest.mark.asyncio
    async def test_updates_trigger_stats(self, webhook_manager):
        """Test that successful requests update trigger statistics."""
        webhook = webhook_manager.register_webhook(
            workflow_id="stats-test",
            path="/stats/test",
        )

        assert webhook.trigger_count == 0

        request = self.create_request("/stats/test")
        await webhook_manager.handle_request(request)
        await webhook_manager.handle_request(request)

        updated = webhook_manager.get_webhook(webhook.id)
        assert updated.trigger_count == 2
        assert updated.last_triggered is not None
