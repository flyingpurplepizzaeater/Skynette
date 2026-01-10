  # Error Handling Guide

Comprehensive guide to error handling in Skynette, including custom exceptions, handlers, logging, and best practices.

## Table of Contents
- [Overview](#overview)
- [Custom Exceptions](#custom-exceptions)
- [Error Handlers](#error-handlers)
- [Logging](#logging)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Overview

Skynette provides a comprehensive error handling system designed to:
- **Catch errors gracefully** without crashing the application
- **Provide user-friendly messages** instead of technical stack traces
- **Log errors systematically** for debugging and monitoring
- **Retry transient failures** automatically
- **Maintain application stability** during unexpected conditions

## Custom Exceptions

All custom exceptions inherit from `SkynetteError` and include:
- Technical error message for logging
- User-friendly message for UI display
- Additional context details
- Structured serialization for logging systems

### Exception Hierarchy

```
SkynetteError (base)
├── AIProviderError
│   ├── AIConnectionError
│   ├── AIAuthenticationError
│   ├── AIRateLimitError
│   ├── AIModelNotFoundError
│   └── AIGenerationError
├── WorkflowError
│   ├── WorkflowNotFoundError
│   ├── WorkflowValidationError
│   ├── WorkflowExecutionError
│   └── NodeExecutionError
├── StorageError
│   ├── DatabaseConnectionError
│   ├── DataNotFoundError
│   └── DataValidationError
├── FileSystemError
│   ├── FileNotFoundError
│   ├── FilePermissionError
│   ├── FileReadError
│   └── FileWriteError
├── NetworkError
│   ├── ConnectionTimeoutError
│   └── APIError
├── PluginError
│   ├── PluginNotFoundError
│   ├── PluginLoadError
│   └── PluginExecutionError
├── ConfigurationError
│   ├── InvalidConfigError
│   └── MissingConfigError
└── ValidationError
    ├── InputValidationError
    └── SchemaValidationError
```

### Using Custom Exceptions

```python
from src.core.errors import WorkflowNotFoundError, AIAuthenticationError

# Raising exceptions with context
raise WorkflowNotFoundError(
    message=f"Workflow {workflow_id} not found in database",
    details={"workflow_id": workflow_id, "user_id": current_user.id},
    user_message="The workflow you're looking for doesn't exist. It may have been deleted."
)

# Catching specific exceptions
try:
    result = ai_provider.generate(prompt)
except AIAuthenticationError as e:
    logger.error(f"Authentication failed: {e.message}")
    show_user_message(e.user_message)  # Display user-friendly message
except AIRateLimitError as e:
    logger.warning(f"Rate limited: {e.message}")
    retry_after_delay()
```

## Error Handlers

### Decorator-Based Error Handling

#### `@handle_errors`

Automatically handle errors in functions:

```python
from src.core.errors import handle_errors

@handle_errors(fallback_value=[], log_error=True, notify_user=True)
def get_workflows():
    """Get all workflows. Returns empty list on error."""
    workflows = database.query(Workflow).all()
    return workflows

# Usage
workflows = get_workflows()  # Never raises, returns [] on error
```

#### `@handle_errors_async`

Async version for async functions:

```python
from src.core.errors import handle_errors_async

@handle_errors_async(fallback_value={})
async def fetch_ai_response(prompt: str):
    """Fetch AI response. Returns empty dict on error."""
    response = await ai_client.generate(prompt)
    return response

# Usage
response = await fetch_ai_response("Hello")
```

#### `@retry_on_error`

Automatically retry on transient failures:

```python
from src.core.errors import retry_on_error, NetworkError, AIConnectionError

@retry_on_error(
    max_attempts=3,
    delay=1.0,
    backoff=2.0,
    exceptions=(NetworkError, AIConnectionError)
)
def call_external_api():
    """Call API with automatic retry on network errors."""
    return requests.get("https://api.example.com/data")

# Retries: 1s, 2s, 4s delays
result = call_external_api()
```

#### `@retry_on_error_async`

Async version with exponential backoff:

```python
from src.core.errors import retry_on_error_async

@retry_on_error_async(max_attempts=5, delay=0.5)
async def fetch_model_data():
    """Fetch data with retry logic."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()
```

### Context Manager Error Handling

```python
from src.core.errors import ErrorContext

# With fallback value
with ErrorContext("Loading workflow", fallback_value=None) as ctx:
    workflow = load_workflow(workflow_id)
    # If error occurs, workflow will be None

# Check if error occurred
if ctx.result is None:
    logger.warning("Failed to load workflow")
```

### Safe Function Calls

```python
from src.core.errors import safe_call, safe_call_async

# Synchronous
result = safe_call(risky_function, arg1, arg2, fallback_value=[])

# Asynchronous
result = await safe_call_async(async_risky_function, fallback_value={})
```

## Logging

### Setup Logging

```python
from src.core.errors import setup_logging
from pathlib import Path

# Basic setup
setup_logging(level="INFO")

# With file logging
setup_logging(
    level="DEBUG",
    log_file=Path.home() / ".skynette" / "logs" / "app.log",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5
)

# Quick setup for development
from src.core.errors import quick_setup
quick_setup(debug=True)
```

### Using Loggers

```python
from src.core.errors import get_logger

logger = get_logger(__name__)

logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")
logger.exception("Error with traceback")  # Use in except blocks
```

### Structured Logging

```python
from src.core.errors import StructuredLogger

logger = StructuredLogger(__name__)

# Log with structured data
logger.info(
    "User action performed",
    user_id=123,
    action="create_workflow",
    workflow_id="wf-456",
    duration_ms=150
)

# Output: User action performed | user_id=123 | action=create_workflow | workflow_id=wf-456 | duration_ms=150
```

## Best Practices

### 1. Use Specific Exceptions

```python
# Good
raise WorkflowNotFoundError(f"Workflow {id} not found")

# Avoid
raise Exception("Workflow not found")
```

### 2. Provide Context

```python
# Good
raise AIAuthenticationError(
    message=f"Failed to authenticate with provider {provider_name}",
    details={"provider": provider_name, "api_key_prefix": api_key[:8]},
    user_message="Please check your API key in settings"
)

# Avoid
raise AIAuthenticationError("Auth failed")
```

### 3. Log Before Raising

```python
# Good
logger.error(f"Database connection failed: {error}")
raise DatabaseConnectionError(
    message=f"Cannot connect to database: {error}",
    details={"host": db_host, "port": db_port}
)

# Avoid just raising without context
raise DatabaseConnectionError()
```

### 4. Catch Specific Exceptions

```python
# Good
try:
    workflow = execute_workflow(id)
except WorkflowNotFoundError:
    return {"error": "Workflow not found"}
except WorkflowValidationError:
    return {"error": "Invalid workflow configuration"}
except WorkflowExecutionError as e:
    logger.error(f"Execution failed: {e.message}")
    return {"error": e.user_message}

# Avoid catching all exceptions
try:
    workflow = execute_workflow(id)
except Exception:
    return {"error": "Something went wrong"}
```

### 5. Use Decorators for Repetitive Patterns

```python
# Good
@handle_errors(fallback_value=None)
@retry_on_error(max_attempts=3)
def fetch_data():
    return api.get_data()

# Avoid repetitive try-except
def fetch_data():
    for attempt in range(3):
        try:
            return api.get_data()
        except:
            if attempt == 2:
                return None
            time.sleep(1)
```

### 6. Separate User Messages from Technical Messages

```python
# Good
raise FileReadError(
    message=f"Failed to read {file_path}: {error}",  # For logs
    user_message="Unable to open the file. It may be corrupted."  # For UI
)

# Avoid showing technical details to users
raise FileReadError(f"IOError: [Errno 2] No such file: {file_path}")
```

### 7. Use Contextual Logging

```python
# Good
logger.info(
    "Workflow execution started",
    workflow_id=workflow.id,
    user_id=user.id,
    node_count=len(workflow.nodes)
)

# Better than
logger.info(f"Starting workflow {workflow.id}")
```

## Examples

### Example 1: AI Provider with Error Handling

```python
from src.core.errors import (
    AIConnectionError,
    AIAuthenticationError,
    handle_errors_async,
    retry_on_error_async,
    get_logger
)

logger = get_logger(__name__)

class AIProvider:
    @handle_errors_async(fallback_value=None)
    @retry_on_error_async(max_attempts=3, delay=1.0)
    async def generate(self, prompt: str) -> Optional[str]:
        """Generate AI response with error handling and retry."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

        except AuthenticationError:
            logger.error("AI authentication failed", provider=self.provider_name)
            raise AIAuthenticationError(
                message=f"Authentication failed for {self.provider_name}",
                details={"provider": self.provider_name},
                user_message="API key is invalid. Please update it in settings."
            )

        except ConnectionError as e:
            logger.warning("AI connection failed", error=str(e))
            raise AIConnectionError(
                message=f"Cannot connect to {self.provider_name}: {e}",
                details={"provider": self.provider_name, "error": str(e)}
            )
```

### Example 2: Workflow Execution with Comprehensive Error Handling

```python
from src.core.errors import (
    WorkflowExecutionError,
    NodeExecutionError,
    ErrorContext,
    get_logger
)

logger = get_logger(__name__)

class WorkflowExecutor:
    async def execute(self, workflow_id: str) -> Dict[str, Any]:
        """Execute workflow with comprehensive error handling."""

        # Load workflow with error handling
        with ErrorContext("Loading workflow", fallback_value=None) as ctx:
            workflow = await self.storage.load(workflow_id)

        if ctx.result is None:
            raise WorkflowNotFoundError(
                message=f"Workflow {workflow_id} not found",
                details={"workflow_id": workflow_id},
                user_message="The workflow doesn't exist or has been deleted."
            )

        # Execute nodes
        results = {}
        for node in workflow.nodes:
            try:
                logger.info("Executing node", node_id=node.id, node_type=node.type)
                result = await self._execute_node(node)
                results[node.id] = result

            except Exception as e:
                logger.error(
                    "Node execution failed",
                    node_id=node.id,
                    error=str(e)
                )
                raise NodeExecutionError(
                    message=f"Node {node.id} failed: {e}",
                    details={
                        "node_id": node.id,
                        "node_type": node.type,
                        "error": str(e)
                    },
                    user_message=f"Step '{node.name}' failed. Check the error log."
                )

        return results
```

### Example 3: File Operations with Error Handling

```python
from pathlib import Path
from src.core.errors import (
    FileReadError,
    FileWriteError,
    FilePermissionError,
    handle_errors
)

@handle_errors(fallback_value=None)
def read_workflow_file(file_path: Path) -> Optional[Dict]:
    """Read workflow file with error handling."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)

    except FileNotFoundError:
        raise FileNotFoundError(
            message=f"File not found: {file_path}",
            details={"path": str(file_path)},
            user_message="The workflow file doesn't exist."
        )

    except PermissionError:
        raise FilePermissionError(
            message=f"Permission denied: {file_path}",
            details={"path": str(file_path)},
            user_message="You don't have permission to read this file."
        )

    except json.JSONDecodeError as e:
        raise FileReadError(
            message=f"Invalid JSON in {file_path}: {e}",
            details={"path": str(file_path), "error": str(e)},
            user_message="The workflow file is corrupted or invalid."
        )
```

## Testing Error Handling

```python
import pytest
from src.core.errors import WorkflowNotFoundError, AIAuthenticationError

def test_workflow_not_found():
    """Test that WorkflowNotFoundError is raised correctly."""
    with pytest.raises(WorkflowNotFoundError) as exc_info:
        load_workflow("nonexistent-id")

    assert "not found" in str(exc_info.value)
    assert exc_info.value.user_message is not None

def test_error_handler_fallback():
    """Test that error handler returns fallback value."""
    @handle_errors(fallback_value=[])
    def failing_function():
        raise ValueError("Test error")

    result = failing_function()
    assert result == []

@pytest.mark.asyncio
async def test_retry_logic():
    """Test that retry logic works correctly."""
    attempt_count = 0

    @retry_on_error_async(max_attempts=3, delay=0.1)
    async def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise NetworkError("Temporary failure")
        return "success"

    result = await flaky_function()
    assert result == "success"
    assert attempt_count == 3
```

## Migration Guide

### Before (Old Code)

```python
def get_workflow(id):
    try:
        workflow = database.query(Workflow).filter_by(id=id).first()
        if not workflow:
            return None
        return workflow
    except Exception as e:
        print(f"Error: {e}")
        return None
```

### After (With Error Handling)

```python
from src.core.errors import handle_errors, WorkflowNotFoundError, get_logger

logger = get_logger(__name__)

@handle_errors(fallback_value=None, log_error=True)
def get_workflow(id: str) -> Optional[Workflow]:
    """Get workflow by ID with proper error handling."""
    workflow = database.query(Workflow).filter_by(id=id).first()

    if not workflow:
        raise WorkflowNotFoundError(
            message=f"Workflow {id} not found in database",
            details={"workflow_id": id},
            user_message="The workflow you're looking for doesn't exist."
        )

    logger.info("Workflow retrieved", workflow_id=id)
    return workflow
```

## Resources

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Exception Handling Best Practices](https://docs.python.org/3/tutorial/errors.html)
- [Retry Patterns](https://docs.python.org/3/library/asyncio-task.html#timeouts)

---

**Last Updated**: 2026-01-10
**Maintainer**: Skynette Team
