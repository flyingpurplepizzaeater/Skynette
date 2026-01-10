"""Logging configuration for Skynette.

This module sets up structured logging for the application with
appropriate handlers, formatters, and log levels.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    format_string: Optional[str] = None
) -> None:
    """Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for console only)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        format_string: Custom log format string

    Usage:
        from src.core.errors.logging_config import setup_logging
        setup_logging(level="DEBUG", log_file=Path("skynette.log"))
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Default format with timestamp, level, logger name, and message
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )

    # Create formatter
    formatter = logging.Formatter(
        format_string,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (if log_file specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set levels for noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)

    logging.info(f"Logging configured at {level} level")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance

    Usage:
        logger = get_logger(__name__)
        logger.info("Starting workflow execution")
    """
    return logging.getLogger(name)


class StructuredLogger:
    """Logger that supports structured logging with additional context.

    Usage:
        logger = StructuredLogger(__name__)
        logger.info("User logged in", user_id=123, ip_address="192.168.1.1")
    """

    def __init__(self, name: str):
        """Initialize structured logger.

        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)

    def _log(self, level: int, message: str, **kwargs):
        """Log message with structured data.

        Args:
            level: Log level
            message: Log message
            **kwargs: Additional structured data
        """
        if kwargs:
            extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            full_message = f"{message} | {extra_info}"
        else:
            full_message = message

        self.logger.log(level, full_message)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        if kwargs:
            extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            full_message = f"{message} | {extra_info}"
        else:
            full_message = message

        self.logger.exception(full_message)


# Convenience function for quick logger setup
def quick_setup(debug: bool = False) -> None:
    """Quickly set up logging for development/testing.

    Args:
        debug: If True, set DEBUG level, otherwise INFO

    Usage:
        from src.core.errors.logging_config import quick_setup
        quick_setup(debug=True)
    """
    level = "DEBUG" if debug else "INFO"
    setup_logging(level=level)
