"""
Credential Vault - Secure Credential Storage

Provides encrypted storage for API keys and sensitive credentials.
Uses Fernet symmetric encryption with a master key derived from the machine.
"""

import os
import json
import base64
import hashlib
import secrets
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, UTC
from typing import Optional, Any
import logging

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class CredentialVault:
    """
    Secure credential storage with encryption.

    Uses Fernet (AES-128-CBC) encryption with a key derived from:
    - Machine-specific identifier
    - Optional user passphrase
    - Salt stored alongside data

    Credentials are stored in SQLite with encrypted JSON payloads.
    """

    def __init__(self, db_path: Optional[Path] = None, passphrase: Optional[str] = None):
        """
        Initialize the credential vault.

        Args:
            db_path: Path to SQLite database (defaults to ~/.skynette/skynette.db)
            passphrase: Optional passphrase for additional security
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path.home() / ".skynette" / "skynette.db"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize encryption
        self._passphrase = passphrase
        self._fernet: Optional[Fernet] = None
        self._init_encryption()

        # Ensure table exists
        self._init_db()

    def _get_machine_id(self) -> bytes:
        """
        Get a machine-specific identifier for key derivation.

        Uses a combination of:
        - Machine hostname
        - User directory
        - Platform info

        This is NOT high security - for production use, consider:
        - Hardware-backed key storage (TPM, Secure Enclave)
        - OS keychain (keyring library)
        - Cloud KMS
        """
        import platform
        import getpass

        components = [
            platform.node(),  # Hostname
            str(Path.home()),  # User home directory
            getpass.getuser(),  # Username
            platform.system(),  # OS name
        ]

        machine_string = "|".join(components)
        return hashlib.sha256(machine_string.encode()).digest()

    def _init_encryption(self):
        """Initialize Fernet encryption with derived key."""
        # Get or create salt
        salt_file = self.db_path.parent / ".vault_salt"

        if salt_file.exists():
            with open(salt_file, 'rb') as f:
                salt = f.read()
        else:
            salt = secrets.token_bytes(16)
            with open(salt_file, 'wb') as f:
                f.write(salt)
            # Set restrictive permissions (Unix only)
            try:
                os.chmod(salt_file, 0o600)
            except (OSError, AttributeError):
                pass

        # Derive key from machine ID + passphrase
        key_material = self._get_machine_id()
        if self._passphrase:
            key_material += self._passphrase.encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP recommended minimum
        )

        key = base64.urlsafe_b64encode(kdf.derive(key_material))
        self._fernet = Fernet(key)

        logger.debug("Credential vault encryption initialized")

    def _init_db(self):
        """Ensure credentials table exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                service TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create index for service lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_credentials_service
            ON credentials(service)
        """)

        conn.commit()
        conn.close()

    def _encrypt(self, data: dict) -> str:
        """Encrypt data to base64 string."""
        json_bytes = json.dumps(data).encode('utf-8')
        encrypted = self._fernet.encrypt(json_bytes)
        return base64.b64encode(encrypted).decode('utf-8')

    def _decrypt(self, encrypted_str: str) -> dict:
        """Decrypt base64 string to data."""
        encrypted = base64.b64decode(encrypted_str.encode('utf-8'))
        json_bytes = self._fernet.decrypt(encrypted)
        return json.loads(json_bytes.decode('utf-8'))

    # ==================== Public API ====================

    def save_credential(
        self,
        name: str,
        service: str,
        data: dict,
        credential_id: Optional[str] = None
    ) -> str:
        """
        Save a credential to the vault.

        Args:
            name: Human-readable name for the credential
            service: Service type (e.g., 'openai', 'slack', 'github')
            data: Dictionary of credential fields (will be encrypted)
            credential_id: Optional ID (auto-generated if not provided)

        Returns:
            The credential ID
        """
        import uuid

        cred_id = credential_id or str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()

        # Encrypt the credential data
        encrypted_data = self._encrypt(data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO credentials
            (id, name, service, data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cred_id, name, service, encrypted_data, now, now))

        conn.commit()
        conn.close()

        logger.info(f"Saved credential '{name}' for service '{service}'")
        return cred_id

    def get_credential(self, credential_id: str) -> Optional[dict]:
        """
        Get a credential by ID.

        Returns:
            Dictionary with credential metadata and decrypted data,
            or None if not found.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, service, data, created_at, updated_at
            FROM credentials WHERE id = ?
        """, (credential_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        try:
            decrypted_data = self._decrypt(row['data'])
        except Exception as e:
            logger.error(f"Failed to decrypt credential {credential_id}: {e}")
            return None

        return {
            'id': row['id'],
            'name': row['name'],
            'service': row['service'],
            'data': decrypted_data,
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
        }

    def get_credential_by_service(self, service: str) -> Optional[dict]:
        """
        Get the first credential for a service.

        Args:
            service: Service type (e.g., 'openai')

        Returns:
            Credential dict or None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, service, data, created_at, updated_at
            FROM credentials WHERE service = ?
            ORDER BY updated_at DESC LIMIT 1
        """, (service,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        try:
            decrypted_data = self._decrypt(row['data'])
        except Exception as e:
            logger.error(f"Failed to decrypt credential for {service}: {e}")
            return None

        return {
            'id': row['id'],
            'name': row['name'],
            'service': row['service'],
            'data': decrypted_data,
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
        }

    def list_credentials(self) -> list[dict]:
        """
        List all credentials (metadata only, no decrypted data).

        Returns:
            List of credential metadata dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, service, created_at, updated_at
            FROM credentials ORDER BY updated_at DESC
        """)

        creds = []
        for row in cursor.fetchall():
            creds.append({
                'id': row['id'],
                'name': row['name'],
                'service': row['service'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
            })

        conn.close()
        return creds

    def list_credentials_by_service(self, service: str) -> list[dict]:
        """List all credentials for a specific service."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, service, created_at, updated_at
            FROM credentials WHERE service = ?
            ORDER BY updated_at DESC
        """, (service,))

        creds = []
        for row in cursor.fetchall():
            creds.append({
                'id': row['id'],
                'name': row['name'],
                'service': row['service'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
            })

        conn.close()
        return creds

    def delete_credential(self, credential_id: str) -> bool:
        """
        Delete a credential.

        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM credentials WHERE id = ?", (credential_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        if deleted:
            logger.info(f"Deleted credential {credential_id}")

        return deleted

    def update_credential(
        self,
        credential_id: str,
        name: Optional[str] = None,
        data: Optional[dict] = None
    ) -> bool:
        """
        Update a credential's name or data.

        Returns:
            True if updated, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get existing credential
        cursor.execute("SELECT name, data FROM credentials WHERE id = ?", (credential_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        # Update fields
        new_name = name or row[0]
        now = datetime.now(UTC).isoformat()

        if data is not None:
            new_data = self._encrypt(data)
        else:
            new_data = row[1]

        cursor.execute("""
            UPDATE credentials
            SET name = ?, data = ?, updated_at = ?
            WHERE id = ?
        """, (new_name, new_data, now, credential_id))

        conn.commit()
        conn.close()

        logger.info(f"Updated credential {credential_id}")
        return True

    def export_credentials(self, output_path: Path, include_data: bool = False):
        """
        Export credentials to a JSON file.

        Args:
            output_path: Path to output file
            include_data: If True, include decrypted data (SECURITY RISK!)
        """
        creds = []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM credentials ORDER BY service, name")

        for row in cursor.fetchall():
            cred = {
                'id': row['id'],
                'name': row['name'],
                'service': row['service'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
            }

            if include_data:
                try:
                    cred['data'] = self._decrypt(row['data'])
                except Exception:
                    cred['data'] = None

            creds.append(cred)

        conn.close()

        with open(output_path, 'w') as f:
            json.dump(creds, f, indent=2)

        logger.info(f"Exported {len(creds)} credentials to {output_path}")

    def import_credentials(self, input_path: Path, overwrite: bool = False):
        """
        Import credentials from a JSON file.

        Args:
            input_path: Path to input file
            overwrite: If True, overwrite existing credentials
        """
        with open(input_path, 'r') as f:
            creds = json.load(f)

        imported = 0
        skipped = 0

        for cred in creds:
            if 'data' not in cred:
                logger.warning(f"Skipping credential {cred.get('name')} - no data")
                skipped += 1
                continue

            # Check if exists
            existing = self.get_credential(cred['id'])
            if existing and not overwrite:
                logger.info(f"Skipping existing credential {cred['name']}")
                skipped += 1
                continue

            self.save_credential(
                name=cred['name'],
                service=cred['service'],
                data=cred['data'],
                credential_id=cred['id']
            )
            imported += 1

        logger.info(f"Imported {imported} credentials, skipped {skipped}")


# ==================== Credential Helper Functions ====================

def get_api_key(service: str, field: str = 'api_key') -> Optional[str]:
    """
    Quick helper to get an API key from the vault.

    Args:
        service: Service name (e.g., 'openai', 'anthropic')
        field: Field name in credential data (default: 'api_key')

    Returns:
        API key string or None
    """
    vault = CredentialVault()
    cred = vault.get_credential_by_service(service)

    if cred and cred.get('data'):
        return cred['data'].get(field)

    return None


def store_api_key(service: str, api_key: str, name: Optional[str] = None) -> str:
    """
    Quick helper to store an API key.

    Args:
        service: Service name
        api_key: The API key value
        name: Optional credential name

    Returns:
        Credential ID
    """
    vault = CredentialVault()
    return vault.save_credential(
        name=name or f"{service.title()} API Key",
        service=service,
        data={'api_key': api_key, 'type': 'api_key'}
    )


# ==================== OAuth2 Support ====================

from enum import Enum


class CredentialType(str, Enum):
    """Types of credentials supported."""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    CUSTOM = "custom"


class OAuth2Manager:
    """
    Manages OAuth2 credentials with token refresh support.

    Stores OAuth2 tokens encrypted and handles:
    - Access token storage
    - Refresh token storage
    - Token expiry tracking
    - Automatic refresh detection
    """

    # OAuth2 provider configurations
    PROVIDERS = {
        "google": {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "scopes": {
                "drive": ["https://www.googleapis.com/auth/drive"],
                "sheets": ["https://www.googleapis.com/auth/spreadsheets"],
                "gmail": ["https://www.googleapis.com/auth/gmail.modify"],
            }
        },
        "microsoft": {
            "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "scopes": {
                "teams": ["Chat.ReadWrite", "Channel.ReadBasic.All", "ChannelMessage.Send"],
                "onedrive": ["Files.ReadWrite.All"],
                "outlook": ["Mail.ReadWrite", "Mail.Send"],
            }
        },
        "github": {
            "auth_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "scopes": {
                "repo": ["repo"],
                "user": ["user"],
                "workflow": ["workflow"],
            }
        },
        "slack": {
            "auth_url": "https://slack.com/oauth/v2/authorize",
            "token_url": "https://slack.com/api/oauth.v2.access",
            "scopes": {
                "bot": ["chat:write", "channels:read", "users:read"],
            }
        },
        "notion": {
            "auth_url": "https://api.notion.com/v1/oauth/authorize",
            "token_url": "https://api.notion.com/v1/oauth/token",
            "scopes": {
                "default": [],  # Notion uses capability-based access
            }
        },
    }

    def __init__(self, vault: Optional[CredentialVault] = None):
        """Initialize with optional vault instance."""
        self.vault = vault or CredentialVault()

    def store_oauth_tokens(
        self,
        service: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        name: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> str:
        """
        Store OAuth2 tokens securely.

        Args:
            service: Service identifier (e.g., 'google', 'microsoft')
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token (for token refresh)
            expires_at: ISO timestamp when access token expires
            scopes: List of granted scopes
            name: Human-readable name
            extra_data: Additional service-specific data

        Returns:
            Credential ID
        """
        data = {
            'type': CredentialType.OAUTH2.value,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at,
            'scopes': scopes or [],
        }

        if extra_data:
            data.update(extra_data)

        return self.vault.save_credential(
            name=name or f"{service.title()} OAuth",
            service=f"{service}_oauth",
            data=data
        )

    def get_oauth_tokens(self, service: str) -> Optional[dict]:
        """
        Get OAuth2 tokens for a service.

        Returns dict with access_token, refresh_token, expires_at, etc.
        or None if not found.
        """
        cred = self.vault.get_credential_by_service(f"{service}_oauth")
        if cred:
            return cred.get('data')
        return None

    def get_access_token(self, service: str) -> Optional[str]:
        """Get just the access token for a service."""
        tokens = self.get_oauth_tokens(service)
        if tokens:
            return tokens.get('access_token')
        return None

    def is_token_expired(self, service: str) -> bool:
        """
        Check if the access token is expired or about to expire.

        Returns True if expired or expiring within 5 minutes.
        """
        tokens = self.get_oauth_tokens(service)
        if not tokens or not tokens.get('expires_at'):
            return True

        try:
            expires_at = datetime.fromisoformat(tokens['expires_at'].replace('Z', '+00:00'))
            # Consider expired if within 5 minutes of expiry
            buffer = 300  # 5 minutes
            return datetime.now(UTC) >= expires_at - timedelta(seconds=buffer)
        except (ValueError, TypeError):
            return True

    def needs_refresh(self, service: str) -> bool:
        """Check if tokens need to be refreshed."""
        tokens = self.get_oauth_tokens(service)
        if not tokens:
            return False

        # Has refresh token and access token is expired
        return bool(tokens.get('refresh_token')) and self.is_token_expired(service)

    def update_tokens(
        self,
        service: str,
        access_token: str,
        expires_at: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> bool:
        """
        Update tokens after a refresh.

        Args:
            service: Service identifier
            access_token: New access token
            expires_at: New expiry time
            refresh_token: New refresh token (if rotated)

        Returns:
            True if updated, False if credential not found
        """
        cred = self.vault.get_credential_by_service(f"{service}_oauth")
        if not cred:
            return False

        data = cred['data']
        data['access_token'] = access_token
        if expires_at:
            data['expires_at'] = expires_at
        if refresh_token:
            data['refresh_token'] = refresh_token

        return self.vault.update_credential(cred['id'], data=data)

    def delete_oauth(self, service: str) -> bool:
        """Delete OAuth credentials for a service."""
        cred = self.vault.get_credential_by_service(f"{service}_oauth")
        if cred:
            return self.vault.delete_credential(cred['id'])
        return False

    def list_oauth_credentials(self) -> list[dict]:
        """List all OAuth credentials (metadata only)."""
        all_creds = self.vault.list_credentials()
        return [c for c in all_creds if c['service'].endswith('_oauth')]

    @classmethod
    def get_provider_config(cls, provider: str) -> Optional[dict]:
        """Get OAuth2 configuration for a provider."""
        return cls.PROVIDERS.get(provider)

    @classmethod
    def get_auth_url(
        cls,
        provider: str,
        client_id: str,
        redirect_uri: str,
        scope_set: str = "default",
        state: Optional[str] = None,
    ) -> Optional[str]:
        """
        Build OAuth2 authorization URL.

        Args:
            provider: Provider name (google, microsoft, etc.)
            client_id: OAuth2 client ID
            redirect_uri: Callback URL
            scope_set: Named scope set from provider config
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL or None if provider not found
        """
        config = cls.get_provider_config(provider)
        if not config:
            return None

        from urllib.parse import urlencode

        scopes = config['scopes'].get(scope_set, [])

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(scopes),
        }

        if state:
            params['state'] = state

        # Provider-specific adjustments
        if provider == 'google':
            params['access_type'] = 'offline'
            params['prompt'] = 'consent'

        return f"{config['auth_url']}?{urlencode(params)}"

    async def exchange_code(
        self,
        provider: str,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> Optional[dict]:
        """
        Exchange authorization code for tokens.

        Args:
            provider: Provider name (google, microsoft, etc.)
            code: Authorization code from OAuth callback
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            redirect_uri: Callback URL (must match authorization request)

        Returns:
            Token response dict or None on failure
        """
        import httpx

        config = self.get_provider_config(provider)
        if not config:
            logger.error(f"Unknown OAuth provider: {provider}")
            return None

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
        }

        headers = {'Accept': 'application/json'}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    config['token_url'],
                    data=data,
                    headers=headers,
                )

                if response.status_code != 200:
                    logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                    return None

                token_data = response.json()

                # Calculate expiry time
                expires_at = None
                if 'expires_in' in token_data:
                    expires_at = (
                        datetime.now(UTC) + timedelta(seconds=int(token_data['expires_in']))
                    ).isoformat()

                # Store tokens
                self.store_oauth_tokens(
                    service=provider,
                    access_token=token_data.get('access_token'),
                    refresh_token=token_data.get('refresh_token'),
                    expires_at=expires_at,
                    scopes=token_data.get('scope', '').split() if token_data.get('scope') else [],
                )

                logger.info(f"Successfully exchanged code for {provider} tokens")
                return token_data

        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None

    async def refresh_access_token(
        self,
        provider: str,
        client_id: str,
        client_secret: str,
    ) -> Optional[str]:
        """
        Refresh the access token using stored refresh token.

        Args:
            provider: Provider name (google, microsoft, etc.)
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret

        Returns:
            New access token or None on failure
        """
        import httpx

        config = self.get_provider_config(provider)
        if not config:
            logger.error(f"Unknown OAuth provider: {provider}")
            return None

        tokens = self.get_oauth_tokens(provider)
        if not tokens or not tokens.get('refresh_token'):
            logger.error(f"No refresh token available for {provider}")
            return None

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': tokens['refresh_token'],
            'client_id': client_id,
            'client_secret': client_secret,
        }

        headers = {'Accept': 'application/json'}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    config['token_url'],
                    data=data,
                    headers=headers,
                )

                if response.status_code != 200:
                    logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                    return None

                token_data = response.json()

                # Calculate new expiry time
                expires_at = None
                if 'expires_in' in token_data:
                    expires_at = (
                        datetime.now(UTC) + timedelta(seconds=int(token_data['expires_in']))
                    ).isoformat()

                # Update stored tokens
                self.update_tokens(
                    service=provider,
                    access_token=token_data.get('access_token'),
                    expires_at=expires_at,
                    # Some providers rotate refresh tokens
                    refresh_token=token_data.get('refresh_token'),
                )

                logger.info(f"Successfully refreshed {provider} access token")
                return token_data.get('access_token')

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None

    async def get_valid_access_token(
        self,
        provider: str,
        client_id: str,
        client_secret: str,
    ) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.

        This is the main method to use when making API calls.

        Args:
            provider: Provider name
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret

        Returns:
            Valid access token or None if unavailable
        """
        if not self.is_token_expired(provider):
            return self.get_access_token(provider)

        if self.needs_refresh(provider):
            return await self.refresh_access_token(provider, client_id, client_secret)

        return None


# ==================== Basic Auth Support ====================

def store_basic_auth(
    service: str,
    username: str,
    password: str,
    name: Optional[str] = None
) -> str:
    """
    Store basic authentication credentials.

    Args:
        service: Service name
        username: Username/email
        password: Password
        name: Optional credential name

    Returns:
        Credential ID
    """
    vault = CredentialVault()
    return vault.save_credential(
        name=name or f"{service.title()} Login",
        service=service,
        data={
            'type': CredentialType.BASIC_AUTH.value,
            'username': username,
            'password': password,
        }
    )


def get_basic_auth(service: str) -> Optional[tuple[str, str]]:
    """
    Get basic auth credentials as (username, password) tuple.

    Returns:
        Tuple of (username, password) or None
    """
    vault = CredentialVault()
    cred = vault.get_credential_by_service(service)

    if cred and cred.get('data'):
        data = cred['data']
        username = data.get('username')
        password = data.get('password')
        if username and password:
            return (username, password)

    return None
