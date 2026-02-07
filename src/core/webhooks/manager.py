"""
Webhook Manager - HTTP webhook infrastructure for workflow triggers.

Provides a lightweight HTTP server for receiving webhooks that trigger workflows.
Supports multiple authentication methods and secure endpoint management.
"""

import hashlib
import hmac
import json
import logging
import secrets
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


class AuthMethod(str, Enum):
    """Webhook authentication methods."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    HMAC_SHA256 = "hmac_sha256"


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""

    id: str
    path: str
    workflow_id: str
    name: str = ""
    description: str = ""
    auth_method: AuthMethod = AuthMethod.NONE
    auth_value: str = ""  # The secret/password/api_key
    allowed_methods: list[str] = field(default_factory=lambda: ["POST"])
    enabled: bool = True
    created_at: str = ""
    last_triggered: str | None = None
    trigger_count: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "auth_method": self.auth_method.value,
            "auth_value": self.auth_value,
            "allowed_methods": self.allowed_methods,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "last_triggered": self.last_triggered,
            "trigger_count": self.trigger_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WebhookConfig":
        return cls(
            id=data["id"],
            path=data["path"],
            workflow_id=data["workflow_id"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            auth_method=AuthMethod(data.get("auth_method", "none")),
            auth_value=data.get("auth_value", ""),
            allowed_methods=data.get("allowed_methods", ["POST"]),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at", ""),
            last_triggered=data.get("last_triggered"),
            trigger_count=data.get("trigger_count", 0),
        )


@dataclass
class WebhookRequest:
    """Incoming webhook request data."""

    method: str
    path: str
    headers: dict[str, str]
    query_params: dict[str, list[str]]
    body: bytes
    client_ip: str = ""
    timestamp: str = ""

    @property
    def json(self) -> dict | None:
        """Parse body as JSON."""
        try:
            return json.loads(self.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    @property
    def text(self) -> str:
        """Get body as text."""
        try:
            return self.body.decode("utf-8")
        except UnicodeDecodeError:
            return self.body.decode("latin-1")

    def to_trigger_data(self) -> dict:
        """Convert to trigger data for workflow execution."""
        return {
            "method": self.method,
            "path": self.path,
            "headers": self.headers,
            "query": {k: v[0] if len(v) == 1 else v for k, v in self.query_params.items()},
            "body": self.json or self.text,
            "client_ip": self.client_ip,
            "timestamp": self.timestamp,
        }


@dataclass
class WebhookResponse:
    """Response to send back to webhook caller."""

    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None

    def to_bytes(self) -> bytes:
        """Serialize body to bytes."""
        if self.body is None:
            return b""
        if isinstance(self.body, bytes):
            return self.body
        if isinstance(self.body, str):
            return self.body.encode("utf-8")
        return json.dumps(self.body).encode("utf-8")


class WebhookStore:
    """Persistent storage for webhook configurations."""

    def __init__(self, db_path: Path | None = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / ".skynette" / "skynette.db"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize webhook table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                workflow_id TEXT NOT NULL,
                name TEXT,
                description TEXT,
                auth_method TEXT DEFAULT 'none',
                auth_value TEXT,
                allowed_methods TEXT DEFAULT '["POST"]',
                enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                last_triggered TEXT,
                trigger_count INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_webhooks_path
            ON webhooks(path)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_webhooks_workflow
            ON webhooks(workflow_id)
        """)

        conn.commit()
        conn.close()

    def save(self, webhook: WebhookConfig) -> None:
        """Save or update a webhook configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO webhooks
            (id, path, workflow_id, name, description, auth_method, auth_value,
             allowed_methods, enabled, created_at, last_triggered, trigger_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                webhook.id,
                webhook.path,
                webhook.workflow_id,
                webhook.name,
                webhook.description,
                webhook.auth_method.value,
                webhook.auth_value,
                json.dumps(webhook.allowed_methods),
                1 if webhook.enabled else 0,
                webhook.created_at,
                webhook.last_triggered,
                webhook.trigger_count,
            ),
        )

        conn.commit()
        conn.close()

    def get_by_id(self, webhook_id: str) -> WebhookConfig | None:
        """Get webhook by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM webhooks WHERE id = ?", (webhook_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_webhook(row)

    def get_by_path(self, path: str) -> WebhookConfig | None:
        """Get webhook by path."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM webhooks WHERE path = ?", (path,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_webhook(row)

    def get_by_workflow(self, workflow_id: str) -> list[WebhookConfig]:
        """Get all webhooks for a workflow."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM webhooks WHERE workflow_id = ? ORDER BY created_at DESC", (workflow_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_webhook(row) for row in rows]

    def list_all(self) -> list[WebhookConfig]:
        """List all webhooks."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM webhooks ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_webhook(row) for row in rows]

    def delete(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM webhooks WHERE id = ?", (webhook_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def update_trigger_stats(self, webhook_id: str) -> None:
        """Update trigger statistics for a webhook."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(UTC).isoformat()
        cursor.execute(
            """
            UPDATE webhooks
            SET last_triggered = ?, trigger_count = trigger_count + 1
            WHERE id = ?
        """,
            (now, webhook_id),
        )

        conn.commit()
        conn.close()

    def _row_to_webhook(self, row: sqlite3.Row) -> WebhookConfig:
        """Convert database row to WebhookConfig."""
        return WebhookConfig(
            id=row["id"],
            path=row["path"],
            workflow_id=row["workflow_id"],
            name=row["name"] or "",
            description=row["description"] or "",
            auth_method=AuthMethod(row["auth_method"]),
            auth_value=row["auth_value"] or "",
            allowed_methods=json.loads(row["allowed_methods"]),
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
            last_triggered=row["last_triggered"],
            trigger_count=row["trigger_count"],
        )


class WebhookManager:
    """
    Manages webhook endpoints for workflow triggers.

    Handles registration, authentication, and routing of incoming webhooks
    to their associated workflows.
    """

    def __init__(
        self,
        store: WebhookStore | None = None,
        base_url: str = "http://localhost:5678",
    ):
        """
        Initialize the webhook manager.

        Args:
            store: Webhook storage backend
            base_url: Base URL for generating webhook URLs
        """
        self.store = store or WebhookStore()
        self.base_url = base_url.rstrip("/")

        # Callback for triggering workflows
        self._trigger_callback: Callable | None = None

        # In-memory cache for fast path lookups
        self._path_cache: dict[str, WebhookConfig] = {}
        self._load_cache()

    def _load_cache(self):
        """Load webhooks into memory cache."""
        webhooks = self.store.list_all()
        self._path_cache = {w.path: w for w in webhooks if w.enabled}

    def set_trigger_callback(self, callback: Callable):
        """
        Set the callback function for triggering workflows.

        The callback should accept (workflow_id: str, trigger_data: dict)
        and return an execution result or None.
        """
        self._trigger_callback = callback

    def register_webhook(
        self,
        workflow_id: str,
        path: str | None = None,
        name: str = "",
        description: str = "",
        auth_method: AuthMethod = AuthMethod.NONE,
        auth_value: str | None = None,
        allowed_methods: list[str] = None,
    ) -> WebhookConfig:
        """
        Register a new webhook endpoint.

        Args:
            workflow_id: ID of the workflow to trigger
            path: Custom path (auto-generated if not provided)
            name: Human-readable name
            description: Description of the webhook
            auth_method: Authentication method
            auth_value: Auth secret (auto-generated for certain methods)
            allowed_methods: HTTP methods to accept (default: ["POST"])

        Returns:
            The created WebhookConfig
        """
        import uuid

        webhook_id = str(uuid.uuid4())

        # Generate path if not provided
        if not path:
            short_id = webhook_id[:8]
            path = f"/webhook/{short_id}"

        # Normalize path
        if not path.startswith("/"):
            path = "/" + path

        # Check if path already exists
        existing = self.store.get_by_path(path)
        if existing:
            raise ValueError(f"Webhook path '{path}' already exists")

        # Generate auth value if needed
        if auth_method in (AuthMethod.BEARER, AuthMethod.API_KEY, AuthMethod.HMAC_SHA256):
            if not auth_value:
                auth_value = secrets.token_urlsafe(32)

        webhook = WebhookConfig(
            id=webhook_id,
            path=path,
            workflow_id=workflow_id,
            name=name or f"Webhook for {workflow_id}",
            description=description,
            auth_method=auth_method,
            auth_value=auth_value or "",
            allowed_methods=allowed_methods or ["POST"],
            enabled=True,
            created_at=datetime.now(UTC).isoformat(),
        )

        self.store.save(webhook)
        self._path_cache[path] = webhook

        logger.info(f"Registered webhook '{webhook.name}' at {path}")
        return webhook

    def unregister_webhook(self, webhook_id: str) -> bool:
        """
        Unregister a webhook endpoint.

        Args:
            webhook_id: ID of the webhook to remove

        Returns:
            True if deleted, False if not found
        """
        webhook = self.store.get_by_id(webhook_id)
        if not webhook:
            return False

        # Remove from cache
        if webhook.path in self._path_cache:
            del self._path_cache[webhook.path]

        # Remove from store
        deleted = self.store.delete(webhook_id)

        if deleted:
            logger.info(f"Unregistered webhook {webhook_id}")

        return deleted

    def get_webhook(self, webhook_id: str) -> WebhookConfig | None:
        """Get webhook by ID."""
        return self.store.get_by_id(webhook_id)

    def get_webhook_url(self, webhook: WebhookConfig) -> str:
        """Get the full URL for a webhook."""
        return f"{self.base_url}{webhook.path}"

    def list_webhooks(self, workflow_id: str | None = None) -> list[WebhookConfig]:
        """
        List webhooks, optionally filtered by workflow.

        Args:
            workflow_id: Filter by workflow ID (optional)

        Returns:
            List of webhook configurations
        """
        if workflow_id:
            return self.store.get_by_workflow(workflow_id)
        return self.store.list_all()

    def enable_webhook(self, webhook_id: str) -> bool:
        """Enable a webhook."""
        webhook = self.store.get_by_id(webhook_id)
        if not webhook:
            return False

        webhook.enabled = True
        self.store.save(webhook)
        self._path_cache[webhook.path] = webhook

        return True

    def disable_webhook(self, webhook_id: str) -> bool:
        """Disable a webhook."""
        webhook = self.store.get_by_id(webhook_id)
        if not webhook:
            return False

        webhook.enabled = False
        self.store.save(webhook)

        # Remove from active cache
        if webhook.path in self._path_cache:
            del self._path_cache[webhook.path]

        return True

    async def handle_request(self, request: WebhookRequest) -> WebhookResponse:
        """
        Handle an incoming webhook request.

        Args:
            request: The incoming webhook request

        Returns:
            WebhookResponse to send back
        """
        # Find webhook by path
        webhook = self._path_cache.get(request.path)
        if not webhook:
            logger.warning(f"Webhook not found: {request.path}")
            return WebhookResponse(status=404, body={"error": "Webhook not found"})

        # Check if enabled
        if not webhook.enabled:
            return WebhookResponse(status=404, body={"error": "Webhook not found"})

        # Check HTTP method
        if request.method not in webhook.allowed_methods:
            return WebhookResponse(
                status=405, body={"error": f"Method {request.method} not allowed"}
            )

        # Authenticate request
        auth_result = self._authenticate(request, webhook)
        if not auth_result:
            logger.warning(f"Webhook auth failed: {request.path}")
            return WebhookResponse(
                status=401,
                headers={"WWW-Authenticate": self._get_auth_header(webhook)},
                body={"error": "Unauthorized"},
            )

        # Update trigger stats
        self.store.update_trigger_stats(webhook.id)

        # Trigger the workflow
        if self._trigger_callback:
            try:
                trigger_data = request.to_trigger_data()
                result = await self._trigger_callback(webhook.workflow_id, trigger_data)

                return WebhookResponse(
                    status=200,
                    body={
                        "success": True,
                        "workflow_id": webhook.workflow_id,
                        "execution": result,
                    },
                )
            except Exception as e:
                logger.exception(f"Webhook trigger failed: {e}")
                return WebhookResponse(status=500, body={"error": str(e)})
        else:
            logger.warning("No trigger callback configured")
            return WebhookResponse(
                status=200,
                body={
                    "success": True,
                    "message": "Webhook received (no trigger configured)",
                },
            )

    def _authenticate(self, request: WebhookRequest, webhook: WebhookConfig) -> bool:
        """
        Authenticate a webhook request.

        Returns True if authenticated, False otherwise.
        """
        if webhook.auth_method == AuthMethod.NONE:
            return True

        if webhook.auth_method == AuthMethod.BASIC:
            # Check Basic auth
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Basic "):
                return False

            import base64

            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                return decoded == webhook.auth_value
            except Exception:
                return False

        if webhook.auth_method == AuthMethod.BEARER:
            # Check Bearer token
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return False
            return auth_header[7:] == webhook.auth_value

        if webhook.auth_method == AuthMethod.API_KEY:
            # Check API key in header or query
            api_key = request.headers.get("x-api-key", "")
            if not api_key:
                api_key = request.query_params.get("api_key", [""])[0]
            return api_key == webhook.auth_value

        if webhook.auth_method == AuthMethod.HMAC_SHA256:
            # Verify HMAC signature
            signature_header = request.headers.get("x-signature-256", "")
            if not signature_header:
                signature_header = request.headers.get("x-hub-signature-256", "")

            if not signature_header:
                return False

            # Remove sha256= prefix if present
            if signature_header.startswith("sha256="):
                signature_header = signature_header[7:]

            expected = hmac.new(
                webhook.auth_value.encode("utf-8"), request.body, hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature_header, expected)

        return False

    def _get_auth_header(self, webhook: WebhookConfig) -> str:
        """Get WWW-Authenticate header value for auth method."""
        if webhook.auth_method == AuthMethod.BASIC:
            return 'Basic realm="Webhook"'
        if webhook.auth_method == AuthMethod.BEARER:
            return 'Bearer realm="Webhook"'
        return 'API-Key realm="Webhook"'


# =============================================================================
# HTTP SERVER INTEGRATION
# =============================================================================


class WebhookServer:
    """
    Lightweight HTTP server for receiving webhooks.

    Uses aiohttp for async HTTP handling.
    """

    def __init__(
        self,
        manager: WebhookManager,
        # Default 0.0.0.0 is intentional to receive external webhooks.
        # For production, configure firewall rules appropriately.
        host: str = "0.0.0.0",  # nosec B104 - intentional for webhook reception
        port: int = 5678,
    ):
        self.manager = manager
        self.host = host
        self.port = port
        self._app = None
        self._runner = None
        self._site = None

    async def start(self):
        """Start the webhook server."""
        try:
            from aiohttp import web
        except ImportError:
            logger.error("aiohttp required for webhook server: pip install aiohttp")
            return

        self._app = web.Application()
        self._app.router.add_route("*", "/{path:.*}", self._handle_request)

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()

        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()

        logger.info(f"Webhook server started at http://{self.host}:{self.port}")

    async def stop(self):
        """Stop the webhook server."""
        if self._runner:
            await self._runner.cleanup()
            logger.info("Webhook server stopped")

    async def _handle_request(self, aiohttp_request):
        """Handle incoming aiohttp request."""
        from aiohttp import web

        # Convert to WebhookRequest
        body = await aiohttp_request.read()
        path = "/" + aiohttp_request.match_info["path"]

        request = WebhookRequest(
            method=aiohttp_request.method,
            path=path,
            headers={k.lower(): v for k, v in aiohttp_request.headers.items()},
            query_params=parse_qs(aiohttp_request.query_string),
            body=body,
            client_ip=aiohttp_request.remote or "",
            timestamp=datetime.now(UTC).isoformat(),
        )

        # Process through manager
        response = await self.manager.handle_request(request)

        # Convert to aiohttp response
        content_type = "application/json" if isinstance(response.body, dict) else "text/plain"

        return web.Response(
            status=response.status,
            headers={**response.headers, "Content-Type": content_type},
            body=response.to_bytes(),
        )


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_manager: WebhookManager | None = None
_server: WebhookServer | None = None


def get_webhook_manager() -> WebhookManager:
    """Get the global webhook manager instance."""
    global _manager
    if _manager is None:
        _manager = WebhookManager()
    return _manager


def get_webhook_server() -> WebhookServer:
    """Get the global webhook server instance."""
    global _server, _manager
    if _server is None:
        if _manager is None:
            _manager = WebhookManager()
        _server = WebhookServer(_manager)
    return _server
