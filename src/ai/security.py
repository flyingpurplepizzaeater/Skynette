"""
API Key Security

Secure storage of AI provider API keys using system keyring.
"""

import logging

import keyring

logger = logging.getLogger(__name__)

# Keyring service name
SERVICE_NAME = "skynette-ai"


def store_api_key(provider: str, api_key: str) -> None:
    """
    Store API key securely in system keyring.

    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        api_key: The API key to store
    """
    if not provider or not provider.strip():
        raise ValueError("Provider name cannot be empty")
    if not api_key or not api_key.strip():
        raise ValueError("API key cannot be empty")
    try:
        keyring.set_password(SERVICE_NAME, provider, api_key)
        logger.info(f"API key stored for provider: {provider}")
    except Exception as e:
        logger.error(f"Failed to store API key for {provider}: {type(e).__name__}")
        raise


def get_api_key(provider: str) -> str | None:
    """
    Retrieve API key from system keyring.

    Args:
        provider: Provider name

    Returns:
        API key if found, None otherwise
    """
    if not provider or not provider.strip():
        raise ValueError("Provider name cannot be empty")
    try:
        key = keyring.get_password(SERVICE_NAME, provider)
        if key:
            logger.debug(f"API key retrieved for provider: {provider}")
        else:
            logger.debug(f"No API key found for provider: {provider}")
        return key
    except Exception as e:
        logger.error(f"Failed to retrieve API key for {provider}: {type(e).__name__}")
        return None


def delete_api_key(provider: str) -> None:
    """
    Delete API key from system keyring.

    Args:
        provider: Provider name
    """
    if not provider or not provider.strip():
        raise ValueError("Provider name cannot be empty")
    try:
        keyring.delete_password(SERVICE_NAME, provider)
        logger.info(f"API key deleted for provider: {provider}")
    except keyring.errors.PasswordDeleteError:
        logger.warning(f"No API key to delete for provider: {provider}")
    except Exception as e:
        logger.error(f"Failed to delete API key for {provider}: {type(e).__name__}")
        raise


def has_api_key(provider: str) -> bool:
    """
    Check if API key exists for provider.

    Args:
        provider: Provider name

    Returns:
        True if API key exists, False otherwise
    """
    if not provider or not provider.strip():
        raise ValueError("Provider name cannot be empty")
    return get_api_key(provider) is not None


def list_stored_providers() -> list[str]:
    """
    List all providers with stored API keys.

    Note: This is a best-effort implementation since keyring
    doesn't provide a native list operation.

    Returns:
        List of provider names
    """
    known_providers = ["openai", "anthropic", "google", "groq"]
    return [p for p in known_providers if has_api_key(p)]
