"""Error handling and retry logic.

This package provides comprehensive error handling utilities including:
- Custom exception classes with user-friendly messages
- Error handling decorators and context managers
- Retry logic for transient failures
- Structured logging configuration
"""

# Exception classes
from .exceptions import (
    # Base
    SkynetteError,
    # AI Providers
    AIProviderError,
    AIConnectionError,
    AIAuthenticationError,
    AIRateLimitError,
    AIModelNotFoundError,
    AIGenerationError,
    # Workflows
    WorkflowError,
    WorkflowNotFoundError,
    WorkflowValidationError,
    WorkflowExecutionError,
    NodeExecutionError,
    # Storage
    StorageError,
    DatabaseConnectionError,
    DataNotFoundError,
    DataValidationError,
    # File System
    FileSystemError,
    FileNotFoundError,
    FilePermissionError,
    FileReadError,
    FileWriteError,
    # Network
    NetworkError,
    ConnectionTimeoutError,
    APIError,
    # Plugins
    PluginError,
    PluginNotFoundError,
    PluginLoadError,
    PluginExecutionError,
    # Configuration
    ConfigurationError,
    InvalidConfigError,
    MissingConfigError,
    # Validation
    ValidationError,
    InputValidationError,
    SchemaValidationError,
)

# Error handlers and decorators
from .handlers import (
    handle_errors,
    handle_errors_async,
    retry_on_error,
    retry_on_error_async,
    ErrorContext,
    safe_call,
    safe_call_async,
)

# Logging utilities
from .logging_config import (
    setup_logging,
    get_logger,
    StructuredLogger,
    quick_setup,
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
