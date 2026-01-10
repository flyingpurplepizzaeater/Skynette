"""Custom exception classes for Skynette.

This module defines all custom exceptions used throughout the application,
providing structured error handling with user-friendly messages.
"""

from typing import Optional, Dict, Any


class SkynetteError(Exception):
    """Base exception for all Skynette errors.

    All custom exceptions should inherit from this class to allow
    for catch-all exception handling when needed.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        """Initialize the error.

        Args:
            message: Technical error message for logging
            details: Additional error context for debugging
            user_message: User-friendly message to display in UI
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.user_message = user_message or self._default_user_message()

    def _default_user_message(self) -> str:
        """Generate default user-friendly message."""
        return "An error occurred. Please try again or contact support."

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details
        }


# AI Provider Errors

class AIProviderError(SkynetteError):
    """Base class for AI provider errors."""

    def _default_user_message(self) -> str:
        return "AI service is currently unavailable. Please try again later."


class AIConnectionError(AIProviderError):
    """Failed to connect to AI provider."""

    def _default_user_message(self) -> str:
        return "Unable to connect to AI service. Please check your internet connection."


class AIAuthenticationError(AIProviderError):
    """AI provider authentication failed."""

    def _default_user_message(self) -> str:
        return "AI service authentication failed. Please check your API key in settings."


class AIRateLimitError(AIProviderError):
    """AI provider rate limit exceeded."""

    def _default_user_message(self) -> str:
        return "AI service rate limit exceeded. Please wait a moment and try again."


class AIModelNotFoundError(AIProviderError):
    """Requested AI model not found."""

    def _default_user_message(self) -> str:
        return "The requested AI model is not available. Please select a different model."


class AIGenerationError(AIProviderError):
    """AI generation/completion failed."""

    def _default_user_message(self) -> str:
        return "AI generation failed. Please try rephrasing your request."


# Workflow Errors

class WorkflowError(SkynetteError):
    """Base class for workflow-related errors."""

    def _default_user_message(self) -> str:
        return "Workflow execution failed. Please check your workflow configuration."


class WorkflowNotFoundError(WorkflowError):
    """Workflow not found in storage."""

    def _default_user_message(self) -> str:
        return "Workflow not found. It may have been deleted."


class WorkflowValidationError(WorkflowError):
    """Workflow validation failed."""

    def _default_user_message(self) -> str:
        return "Workflow configuration is invalid. Please check all node connections."


class WorkflowExecutionError(WorkflowError):
    """Workflow execution encountered an error."""

    def _default_user_message(self) -> str:
        return "Workflow execution failed. Check the error log for details."


class NodeExecutionError(WorkflowError):
    """Individual node execution failed."""

    def _default_user_message(self) -> str:
        return "A workflow step failed to execute. Check the node configuration."


# Storage Errors

class StorageError(SkynetteError):
    """Base class for storage/database errors."""

    def _default_user_message(self) -> str:
        return "Unable to save or load data. Please try again."


class DatabaseConnectionError(StorageError):
    """Failed to connect to database."""

    def _default_user_message(self) -> str:
        return "Database connection failed. Please restart the application."


class DataNotFoundError(StorageError):
    """Requested data not found in storage."""

    def _default_user_message(self) -> str:
        return "The requested item was not found."


class DataValidationError(StorageError):
    """Data validation failed before storage."""

    def _default_user_message(self) -> str:
        return "Invalid data format. Please check your input."


# File System Errors

class FileSystemError(SkynetteError):
    """Base class for file system errors."""

    def _default_user_message(self) -> str:
        return "File operation failed. Please check file permissions."


class FileNotFoundError(FileSystemError):
    """File not found at specified path."""

    def _default_user_message(self) -> str:
        return "File not found. Please check the file path."


class FilePermissionError(FileSystemError):
    """Insufficient permissions for file operation."""

    def _default_user_message(self) -> str:
        return "Permission denied. Please check file permissions."


class FileReadError(FileSystemError):
    """Failed to read file."""

    def _default_user_message(self) -> str:
        return "Unable to read file. The file may be corrupted."


class FileWriteError(FileSystemError):
    """Failed to write file."""

    def _default_user_message(self) -> str:
        return "Unable to save file. Please check available disk space."


# Network Errors

class NetworkError(SkynetteError):
    """Base class for network-related errors."""

    def _default_user_message(self) -> str:
        return "Network operation failed. Please check your internet connection."


class ConnectionTimeoutError(NetworkError):
    """Network connection timed out."""

    def _default_user_message(self) -> str:
        return "Connection timed out. Please check your internet connection and try again."


class APIError(NetworkError):
    """External API request failed."""

    def _default_user_message(self) -> str:
        return "External service request failed. Please try again later."


# Plugin Errors

class PluginError(SkynetteError):
    """Base class for plugin-related errors."""

    def _default_user_message(self) -> str:
        return "Plugin error occurred. Please check plugin configuration."


class PluginNotFoundError(PluginError):
    """Plugin not found."""

    def _default_user_message(self) -> str:
        return "Plugin not found. Please reinstall the plugin."


class PluginLoadError(PluginError):
    """Failed to load plugin."""

    def _default_user_message(self) -> str:
        return "Failed to load plugin. The plugin may be incompatible."


class PluginExecutionError(PluginError):
    """Plugin execution failed."""

    def _default_user_message(self) -> str:
        return "Plugin execution failed. Check the plugin logs for details."


# Configuration Errors

class ConfigurationError(SkynetteError):
    """Base class for configuration errors."""

    def _default_user_message(self) -> str:
        return "Configuration error. Please check your settings."


class InvalidConfigError(ConfigurationError):
    """Configuration file is invalid."""

    def _default_user_message(self) -> str:
        return "Invalid configuration. Please reset to defaults in settings."


class MissingConfigError(ConfigurationError):
    """Required configuration is missing."""

    def _default_user_message(self) -> str:
        return "Required configuration is missing. Please check your settings."


# Validation Errors

class ValidationError(SkynetteError):
    """Base class for validation errors."""

    def _default_user_message(self) -> str:
        return "Validation failed. Please check your input."


class InputValidationError(ValidationError):
    """User input validation failed."""

    def _default_user_message(self) -> str:
        return "Invalid input. Please check the form for errors."


class SchemaValidationError(ValidationError):
    """Data schema validation failed."""

    def _default_user_message(self) -> str:
        return "Data format is invalid. Please check your input structure."
