"""Error handling and retry logic.

This package provides comprehensive error handling utilities including:
- Custom exception classes with user-friendly messages
- Error handling decorators and context managers
- Retry logic for transient failures
- Structured logging configuration
"""

# Exception classes
from .exceptions import (
    AIAuthenticationError,
    AIConnectionError,
    AIGenerationError,
    AIModelNotFoundError,
    # AI Providers
    AIProviderError,
    AIRateLimitError,
    APIError,
    # Configuration
    ConfigurationError,
    ConnectionTimeoutError,
    DatabaseConnectionError,
    DataNotFoundError,
    DataValidationError,
    FileNotFoundError,
    FilePermissionError,
    FileReadError,
    # File System
    FileSystemError,
    FileWriteError,
    InputValidationError,
    InvalidConfigError,
    MissingConfigError,
    # Network
    NetworkError,
    NodeExecutionError,
    # Plugins
    PluginError,
    PluginExecutionError,
    PluginLoadError,
    PluginNotFoundError,
    SchemaValidationError,
    # Base
    SkynetteError,
    # Storage
    StorageError,
    # Validation
    ValidationError,
    # Workflows
    WorkflowError,
    WorkflowExecutionError,
    WorkflowNotFoundError,
    WorkflowValidationError,
)

# Error handlers and decorators
from .handlers import (
    ErrorContext,
    handle_errors,
    handle_errors_async,
    retry_on_error,
    retry_on_error_async,
    safe_call,
    safe_call_async,
)

# Logging utilities
from .logging_config import (
    StructuredLogger,
    get_logger,
    quick_setup,
    setup_logging,
)

__all__ = [
    # Base exceptions
    "SkynetteError",
    # AI Provider exceptions
    "AIProviderError",
    "AIConnectionError",
    "AIAuthenticationError",
    "AIRateLimitError",
    "AIModelNotFoundError",
    "AIGenerationError",
    # Workflow exceptions
    "WorkflowError",
    "WorkflowNotFoundError",
    "WorkflowValidationError",
    "WorkflowExecutionError",
    "NodeExecutionError",
    # Storage exceptions
    "StorageError",
    "DatabaseConnectionError",
    "DataNotFoundError",
    "DataValidationError",
    # File System exceptions
    "FileSystemError",
    "FileNotFoundError",
    "FilePermissionError",
    "FileReadError",
    "FileWriteError",
    # Network exceptions
    "NetworkError",
    "ConnectionTimeoutError",
    "APIError",
    # Plugin exceptions
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "PluginExecutionError",
    # Configuration exceptions
    "ConfigurationError",
    "InvalidConfigError",
    "MissingConfigError",
    # Validation exceptions
    "ValidationError",
    "InputValidationError",
    "SchemaValidationError",
    # Error handlers
    "handle_errors",
    "handle_errors_async",
    "retry_on_error",
    "retry_on_error_async",
    "ErrorContext",
    "safe_call",
    "safe_call_async",
    # Logging
    "setup_logging",
    "get_logger",
    "StructuredLogger",
    "quick_setup",
]
