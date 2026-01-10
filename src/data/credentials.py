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
from datetime import datetime
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
        now = datetime.utcnow().isoformat()

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
        now = datetime.utcnow().isoformat()

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
        data={'api_key': api_key}
    )
