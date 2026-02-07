"""Error handling utilities and decorators.

This module provides utilities for handling errors gracefully throughout
the application, including retry logic, error logging, and user notifications.
"""

import asyncio
import functools
import logging
from collections.abc import Callable
from typing import Any

from .exceptions import AIConnectionError, NetworkError, SkynetteError

logger = logging.getLogger(__name__)


def handle_errors(
    fallback_value: Any = None,
    log_error: bool = True,
    notify_user: bool = True,
    suppress_exceptions: tuple[type[Exception], ...] = (),
):
    """Decorator to handle errors in functions.

    Args:
        fallback_value: Value to return if error occurs
        log_error: Whether to log the error
        notify_user: Whether to notify user of the error
        suppress_exceptions: Exception types to suppress (return fallback)

    Usage:
        @handle_errors(fallback_value=[], log_error=True)
        def get_workflows():
            # Function that might raise errors
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except suppress_exceptions:
                if log_error:
                    logger.debug(f"Suppressed error in {func.__name__}", exc_info=True)
                return fallback_value
            except SkynetteError as e:
                if log_error:
                    logger.error(
                        f"Skynette error in {func.__name__}: {e.message}", extra=e.to_dict()
                    )
                if notify_user:
                    # In a real app, this would trigger a UI notification
                    pass
                if fallback_value is not None:
                    return fallback_value
                raise
            except Exception:
                if log_error:
                    logger.exception(f"Unexpected error in {func.__name__}")
                if notify_user:
                    # In a real app, this would trigger a UI notification
                    pass
                if fallback_value is not None:
                    return fallback_value
                raise

        return wrapper

    return decorator


def handle_errors_async(
    fallback_value: Any = None,
    log_error: bool = True,
    notify_user: bool = True,
    suppress_exceptions: tuple[type[Exception], ...] = (),
):
    """Async version of handle_errors decorator.

    Args:
        fallback_value: Value to return if error occurs
        log_error: Whether to log the error
        notify_user: Whether to notify user of the error
        suppress_exceptions: Exception types to suppress

    Usage:
        @handle_errors_async(fallback_value={})
        async def fetch_data():
            # Async function that might raise errors
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except suppress_exceptions:
                if log_error:
                    logger.debug(f"Suppressed error in {func.__name__}", exc_info=True)
                return fallback_value
            except SkynetteError as e:
                if log_error:
                    logger.error(
                        f"Skynette error in {func.__name__}: {e.message}", extra=e.to_dict()
                    )
                if notify_user:
                    pass  # Trigger UI notification
                if fallback_value is not None:
                    return fallback_value
                raise
            except Exception:
                if log_error:
                    logger.exception(f"Unexpected error in {func.__name__}")
                if notify_user:
                    pass  # Trigger UI notification
                if fallback_value is not None:
                    return fallback_value
                raise

        return wrapper

    return decorator


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (NetworkError, AIConnectionError),
):
    """Decorator to retry function on specific errors.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Exception types to retry on

    Usage:
        @retry_on_error(max_attempts=3, delay=1.0)
        def api_call():
            # Function that might fail temporarily
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}. "
                            f"Retrying in {current_delay}s..."
                        )
                        import time

                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")

            # All attempts exhausted
            raise last_exception

        return wrapper

    return decorator


def retry_on_error_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (NetworkError, AIConnectionError),
):
    """Async version of retry_on_error decorator.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Exception types to retry on

    Usage:
        @retry_on_error_async(max_attempts=3)
        async def api_call():
            # Async function that might fail temporarily
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")

            # All attempts exhausted
            raise last_exception

        return wrapper

    return decorator


class ErrorContext:
    """Context manager for error handling.

    Usage:
        with ErrorContext("Loading workflow", fallback_value=None):
            workflow = load_workflow(id)
    """

    def __init__(
        self,
        operation: str,
        fallback_value: Any = None,
        log_error: bool = True,
        notify_user: bool = True,
    ):
        """Initialize error context.

        Args:
            operation: Description of the operation being performed
            fallback_value: Value to use if error occurs
            log_error: Whether to log errors
            notify_user: Whether to notify user of errors
        """
        self.operation = operation
        self.fallback_value = fallback_value
        self.log_error = log_error
        self.notify_user = notify_user
        self.result = fallback_value

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and handle any errors."""
        if exc_type is None:
            return False

        if issubclass(exc_type, SkynetteError):
            if self.log_error:
                logger.error(f"Error during {self.operation}: {exc_val.message}")
            if self.notify_user:
                # Trigger user notification
                pass
        else:
            if self.log_error:
                logger.exception(f"Unexpected error during {self.operation}")
            if self.notify_user:
                # Trigger user notification
                pass

        # Suppress exception and use fallback value
        if self.fallback_value is not None:
            return True

        return False


def safe_call(func: Callable, *args, fallback_value: Any = None, **kwargs) -> Any:
    """Safely call a function, returning fallback on error.

    Args:
        func: Function to call
        *args: Positional arguments
        fallback_value: Value to return on error
        **kwargs: Keyword arguments

    Returns:
        Function result or fallback value

    Usage:
        result = safe_call(risky_function, arg1, arg2, fallback_value=[])
    """
    try:
        return func(*args, **kwargs)
    except Exception:
        logger.exception(f"Error in safe_call to {func.__name__}")
        return fallback_value


async def safe_call_async(func: Callable, *args, fallback_value: Any = None, **kwargs) -> Any:
    """Async version of safe_call.

    Args:
        func: Async function to call
        *args: Positional arguments
        fallback_value: Value to return on error
        **kwargs: Keyword arguments

    Returns:
        Function result or fallback value
    """
    try:
        return await func(*args, **kwargs)
    except Exception:
        logger.exception(f"Error in safe_call_async to {func.__name__}")
        return fallback_value
