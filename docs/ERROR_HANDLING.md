# Error Handling System

This document describes the comprehensive error handling system implemented in the arr Stack Manager.

## Overview

The error handling system provides:

1. **Error Boundaries** - Catch and handle exceptions in screens without crashing
2. **User-Friendly Error Messages** - Convert technical errors into actionable guidance
3. **Crash Recovery** - Save and restore application state after crashes
4. **Logging** - Comprehensive error logging for debugging
5. **Custom Exceptions** - Typed exceptions for different error categories

## Components

### 1. Error Display (`ErrorDisplay`)

A data class that represents user-friendly error information:

```python
from arr_stack_manager.utils import ErrorDisplay, ErrorCategory

error = ErrorDisplay(
    title="Docker Not Available",
    message="Cannot connect to Docker daemon.",
    remediation=[
        "Ensure Docker is installed and running",
        "Check if your user has Docker permissions",
    ],
    category=ErrorCategory.DOCKER,
    technical_details="Connection refused on /var/run/docker.sock"
)
```

### 2. Custom Exceptions

Typed exceptions for different error categories:

```python
from arr_stack_manager.utils import (
    ValidationError,
    DockerError,
    FileSystemError,
    NetworkError,
    ConfigurationError,
    PermissionError,
)

# Raise specific exceptions
raise ValidationError("Invalid port number", "Port must be between 1-65535")
raise DockerError("Docker daemon not available")
raise FileSystemError("Path not found: /data")
```

### 3. Error Handler (`ErrorHandler`)

Centralized error handling with predefined error messages:

```python
from arr_stack_manager.utils import ErrorHandler, handle_error

# Using the global handler
error_display = handle_error("docker_unavailable")

# With variable substitution
error_display = handle_error("port_in_use", port=8080)

# Handle exceptions
try:
    # Some operation
    pass
except Exception as e:
    error_display = handle_exception(e, "Loading configuration")
```

### 4. Error Boundary (`ErrorBoundary`)

Protects screens from crashes by catching exceptions:

```python
from arr_stack_manager.utils import ErrorBoundary, with_error_boundary
from textual.screen import Screen

class MyScreen(Screen):
    def __init__(self):
        super().__init__()
        self._error_boundary = ErrorBoundary(self, "return_to_dashboard")

    # Using decorator
    @with_error_boundary("show_error_screen")
    async def on_mount(self):
        # This method is protected by error boundary
        await self.load_data()
```

### 5. Base Screen (`BaseScreen`)

All screens should inherit from `BaseScreen` for built-in error handling:

```python
from arr_stack_manager.screens import BaseScreen, ErrorContainer

class MyScreen(BaseScreen):
    # Enable state persistence for crash recovery
    ENABLE_STATE_PERSISTENCE = True

    # Customize error fallback behavior
    ERROR_FALLBACK_ACTION = "return_to_dashboard"

    def compose(self):
        # Add error container for displaying errors
        yield ErrorContainer()
        # ... other widgets

    def _on_mount_impl(self):
        # Override this instead of on_mount
        # Automatically protected by error boundary
        pass

    def _get_state(self):
        # Return state to save for crash recovery
        return {"my_data": self.my_data}

    def _set_state(self, state):
        # Restore state after crash
        self.my_data = state.get("my_data")
```

### 6. State Manager (`StateManager`)

Manages application state for crash recovery:

```python
from arr_stack_manager.utils import StateManager, save_app_state, load_app_state

# Save application state
save_app_state({
    "stack_name": "my-stack",
    "current_screen": "Dashboard",
})

# Load saved state
state = load_app_state()
if state:
    stack_name = state.get("stack_name")

# Create crash report
state_manager = StateManager()
crash_file = state_manager.create_crash_report(
    exception,
    context={"screen": "Dashboard", "action": "refresh"}
)
```

## Error Categories

The system defines the following error categories:

- **VALIDATION** - Invalid user input or configuration
- **DOCKER** - Docker daemon or container errors
- **FILESYSTEM** - File system access errors
- **NETWORK** - Network connectivity or port errors
- **CONFIGURATION** - Configuration file errors
- **PERMISSION** - Permission or access control errors
- **UNKNOWN** - Unclassified errors

## Predefined Error Messages

The system includes predefined error messages for common scenarios:

- `docker_unavailable` - Docker daemon not accessible
- `docker_connection_failed` - Failed to connect to Docker
- `docker_image_pull_failed` - Failed to pull Docker image
- `docker_container_start_failed` - Failed to start container
- `path_not_found` - Directory or file not found
- `path_not_writable` - No write permission
- `path_not_readable` - No read permission
- `port_in_use` - Port already in use
- `port_invalid` - Invalid port number
- `invalid_puid_pgid` - Invalid user/group ID
- `service_not_supported` - Unsupported service
- `no_services_selected` - No services selected
- `config_file_not_found` - Configuration file missing
- `config_file_invalid` - Invalid configuration file
- `compose_generation_failed` - Failed to generate compose file
- `deployment_failed` - Stack deployment failed
- `disk_space_low` - Insufficient disk space
- `template_not_found` - Service template missing

## Usage Examples

### Handling Errors in Screens

```python
from arr_stack_manager.screens import BaseScreen, ErrorContainer
from arr_stack_manager.utils import handle_exception

class DashboardScreen(BaseScreen):
    def compose(self):
        yield ErrorContainer()
        # ... other widgets

    async def load_data(self):
        try:
            # Load data
            data = await self.controller.get_stack_status()
        except Exception as e:
            # Handle exception and show to user
            error_display = handle_exception(e, "Loading dashboard data")
            self.show_error(error_display)
```

### Using Error Boundaries

```python
from arr_stack_manager.utils import with_error_boundary

class MyScreen(Screen):
    @with_error_boundary("return_to_dashboard")
    async def on_button_pressed(self, event):
        # This method is protected
        # Errors will be caught and handled gracefully
        await self.perform_action()
```

### Creating Custom Error Messages

```python
from arr_stack_manager.utils import ErrorDisplay, ErrorCategory

def validate_config(config):
    if not config.services:
        error = ErrorDisplay(
            title="No Services Configured",
            message="At least one service must be configured",
            remediation=[
                "Go to Service Selector",
                "Select at least one service",
                "Complete the configuration wizard",
            ],
            category=ErrorCategory.VALIDATION,
        )
        return error
    return None
```

### Crash Recovery

```python
from arr_stack_manager.utils import save_app_state, load_app_state

# In your application
def on_mount(self):
    # Check for saved state
    saved_state = load_app_state()
    if saved_state:
        self.notify("Recovered from previous session")
        self.restore_state(saved_state)

    # Periodically save state
    self.set_interval(60, self.save_current_state)

def save_current_state(self):
    state = {
        "stack_name": self.stack_name,
        "current_screen": self.screen.__class__.__name__,
    }
    save_app_state(state)
```

## Best Practices

### 1. Always Use Error Boundaries

Wrap critical operations with error boundaries to prevent crashes:

```python
@with_error_boundary("return_to_dashboard")
async def critical_operation(self):
    # Protected operation
    pass
```

### 2. Provide Actionable Remediation

Always include specific steps users can take to fix errors:

```python
error = ErrorDisplay(
    title="Port Conflict",
    message="Port 8080 is already in use",
    remediation=[
        "Choose a different port in configuration",
        "Find what's using the port: sudo lsof -i :8080",
        "Stop the conflicting service",
    ],
)
```

### 3. Log Errors for Debugging

Always log errors with context:

```python
try:
    result = perform_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    error_display = handle_exception(e, "Performing operation")
    self.show_error(error_display)
```

### 4. Use Specific Exception Types

Use specific exception types for better error handling:

```python
from arr_stack_manager.utils import DockerError, ValidationError

if not docker_available:
    raise DockerError("Docker daemon not available")

if port < 1 or port > 65535:
    raise ValidationError("Invalid port", f"Port {port} out of range")
```

### 5. Enable State Persistence for Complex Screens

Enable state persistence for screens with important user data:

```python
class ConfigWizardScreen(BaseScreen):
    ENABLE_STATE_PERSISTENCE = True

    def _get_state(self):
        return {
            "current_step": self.current_step,
            "form_data": self.form_data,
        }

    def _set_state(self, state):
        self.current_step = state.get("current_step", 1)
        self.form_data = state.get("form_data", {})
```

## Testing Error Handling

The error handling system includes comprehensive tests:

```bash
# Run error handling tests
python -m pytest tests/test_error_handling.py -v

# Test specific components
python -m pytest tests/test_error_handling.py::TestErrorHandler -v
python -m pytest tests/test_error_handling.py::TestStateManager -v
```

## Logging

Error logs are stored in:

- `~/.config/arr-stack-manager/logs/errors_YYYYMMDD.log`

Crash reports are stored in:

- `~/.config/arr-stack-manager/state/crashes/crash_YYYYMMDD_HHMMSS.json`

Old crash reports are automatically cleaned up after 30 days.

## Troubleshooting

### Error Boundary Not Working

Make sure your screen inherits from `BaseScreen` or manually creates an `ErrorBoundary`:

```python
from arr_stack_manager.screens import BaseScreen

class MyScreen(BaseScreen):  # Inherit from BaseScreen
    pass
```

### State Not Persisting

Enable state persistence and implement state methods:

```python
class MyScreen(BaseScreen):
    ENABLE_STATE_PERSISTENCE = True  # Enable persistence

    def _get_state(self):
        return {"data": self.data}  # Return state to save

    def _set_state(self, state):
        self.data = state.get("data")  # Restore state
```

### Errors Not Displaying

Add an `ErrorContainer` to your screen's compose method:

```python
from arr_stack_manager.screens import ErrorContainer

def compose(self):
    yield ErrorContainer()  # Add error container
    # ... other widgets
```

## Future Enhancements

Potential improvements to the error handling system:

1. **Error Analytics** - Track error frequency and patterns
2. **Automatic Error Reporting** - Optional error reporting to developers
3. **Error Recovery Suggestions** - AI-powered error resolution suggestions
4. **Error History** - View past errors and their resolutions
5. **Custom Error Handlers** - Allow users to define custom error handlers

## References

- [Textual Error Handling](https://textual.textualize.io/guide/screens/#error-handling)
- [Python Exception Handling](https://docs.python.org/3/tutorial/errors.html)
- [Logging Best Practices](https://docs.python.org/3/howto/logging.html)
