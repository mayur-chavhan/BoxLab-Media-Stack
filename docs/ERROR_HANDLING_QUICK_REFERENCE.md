# Error Handling Quick Reference

Quick reference guide for using the error handling system in arr Stack Manager.

## Quick Start

### 1. Create a Screen with Error Handling

```python
from arr_stack_manager.screens import BaseScreen, ErrorContainer

class MyScreen(BaseScreen):
    # Enable state persistence (optional)
    ENABLE_STATE_PERSISTENCE = True

    # Set fallback action on critical errors
    ERROR_FALLBACK_ACTION = "return_to_dashboard"

    def compose(self):
        # Add error container for inline error display
        yield ErrorContainer()
        # ... your widgets

    def _on_mount_impl(self):
        # Override this instead of on_mount
        # Automatically protected by error boundary
        pass
```

### 2. Handle Errors in Methods

```python
from arr_stack_manager.utils import handle_exception

async def load_data(self):
    try:
        data = await self.controller.get_data()
    except Exception as e:
        error_display = handle_exception(e, "Loading data")
        self.show_error(error_display)
```

### 3. Use Error Boundaries

```python
from arr_stack_manager.utils import with_error_boundary

@with_error_boundary("return_to_dashboard")
async def on_button_pressed(self, event):
    # This method is protected from crashes
    await self.perform_action()
```

### 4. Raise Custom Exceptions

```python
from arr_stack_manager.utils import ValidationError, DockerError

if not valid:
    raise ValidationError("Invalid input", "Port must be 1-65535")

if not docker_available:
    raise DockerError("Docker daemon not available")
```

### 5. Use Predefined Error Messages

```python
from arr_stack_manager.utils import handle_error

# Simple error
error_display = handle_error("docker_unavailable")

# Error with variables
error_display = handle_error("port_in_use", port=8080)

# Show to user
self.show_error(error_display)
```

## Common Patterns

### Pattern 1: Safe Widget Updates

```python
# Instead of this (can crash):
widget = self.query_one("#my-widget")
widget.update("new value")

# Use this (safe):
self.safe_update_widget("#my-widget", "new value")
```

### Pattern 2: State Persistence

```python
class MyScreen(BaseScreen):
    ENABLE_STATE_PERSISTENCE = True

    def _get_state(self):
        # Return state to save
        return {
            "current_step": self.current_step,
            "form_data": self.form_data,
        }

    def _set_state(self, state):
        # Restore state
        self.current_step = state.get("current_step", 1)
        self.form_data = state.get("form_data", {})
```

### Pattern 3: Error Display with Remediation

```python
from arr_stack_manager.utils import ErrorDisplay, ErrorCategory

error = ErrorDisplay(
    title="Configuration Error",
    message="Invalid port configuration",
    remediation=[
        "Check port number is between 1-65535",
        "Ensure port is not already in use",
        "Try a different port number",
    ],
    category=ErrorCategory.VALIDATION,
)
self.show_error(error)
```

### Pattern 4: Logging Errors

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = perform_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    error_display = handle_exception(e, "Performing operation")
    self.show_error(error_display)
```

## Available Error Types

```python
from arr_stack_manager.utils import (
    ValidationError,      # Invalid input/config
    DockerError,          # Docker issues
    FileSystemError,      # File/directory issues
    NetworkError,         # Network/port issues
    ConfigurationError,   # Config file issues
    PermissionError,      # Permission issues
)
```

## Predefined Error Messages

```python
# Docker errors
handle_error("docker_unavailable")
handle_error("docker_connection_failed")
handle_error("docker_image_pull_failed", image="sonarr:latest")
handle_error("docker_container_start_failed", container="sonarr")

# File system errors
handle_error("path_not_found", path="/data")
handle_error("path_not_writable", path="/data", puid=1000, pgid=1000)
handle_error("path_not_readable", path="/data")

# Network errors
handle_error("port_in_use", port=8080)
handle_error("port_invalid", port=99999)

# Validation errors
handle_error("invalid_puid_pgid", puid=1000, pgid=1000)
handle_error("no_services_selected")

# Configuration errors
handle_error("config_file_not_found", path="config.json")
handle_error("config_file_invalid", path="config.json")
handle_error("compose_generation_failed")

# Deployment errors
handle_error("deployment_failed")
handle_error("disk_space_low", path="/data")

# Template errors
handle_error("template_not_found", template="sonarr.yml.j2")
```

## Error Categories

```python
from arr_stack_manager.utils import ErrorCategory

ErrorCategory.VALIDATION      # Invalid input
ErrorCategory.DOCKER          # Docker issues
ErrorCategory.FILESYSTEM      # File system issues
ErrorCategory.NETWORK         # Network issues
ErrorCategory.CONFIGURATION   # Config issues
ErrorCategory.PERMISSION      # Permission issues
ErrorCategory.UNKNOWN         # Unknown issues
```

## State Management

```python
from arr_stack_manager.utils import (
    save_app_state,
    load_app_state,
    clear_app_state,
)

# Save state
save_app_state({
    "stack_name": "my-stack",
    "current_screen": "Dashboard",
})

# Load state
state = load_app_state()
if state:
    stack_name = state.get("stack_name")

# Clear state
clear_app_state()
```

## Testing Error Handling

```python
import pytest
from arr_stack_manager.utils import ValidationError, handle_error

def test_validation_error():
    """Test validation error handling."""
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError("Invalid input")

    assert exc_info.value.category == ErrorCategory.VALIDATION

def test_error_display():
    """Test error display creation."""
    error = handle_error("port_in_use", port=8080)

    assert "8080" in error.message
    assert len(error.remediation) > 0
```

## Debugging

### View Error Logs

```bash
# Error logs
tail -f ~/.config/arr-stack-manager/logs/errors_$(date +%Y%m%d).log

# Crash reports
ls -la ~/.config/arr-stack-manager/state/crashes/
cat ~/.config/arr-stack-manager/state/crashes/crash_*.json
```

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("arr_stack_manager")
logger.setLevel(logging.DEBUG)
```

## Best Practices

1. ✅ **Always inherit from BaseScreen** for automatic error protection
2. ✅ **Add ErrorContainer** to screens for inline error display
3. ✅ **Use specific exception types** instead of generic Exception
4. ✅ **Provide actionable remediation** in error messages
5. ✅ **Log errors with context** for debugging
6. ✅ **Enable state persistence** for important screens
7. ✅ **Use error boundaries** for critical operations
8. ✅ **Test error scenarios** in your tests

## Common Mistakes

❌ **Don't do this:**

```python
# Catching exceptions without handling
try:
    do_something()
except:
    pass  # Silent failure!

# Using generic error messages
raise Exception("Something went wrong")

# Not providing remediation
error = ErrorDisplay(title="Error", message="Failed")
```

✅ **Do this instead:**

```python
# Proper error handling
try:
    do_something()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    error_display = handle_exception(e, "Operation")
    self.show_error(error_display)

# Using specific exceptions
raise ValidationError("Invalid port", "Port must be 1-65535")

# Providing remediation
error = ErrorDisplay(
    title="Validation Error",
    message="Invalid port number",
    remediation=[
        "Use a port between 1-65535",
        "Check for typos",
    ],
)
```

## Resources

- Full Documentation: `docs/ERROR_HANDLING.md`
- Implementation Summary: `docs/TASK_27_IMPLEMENTATION.md`
- Test Examples: `tests/test_error_handling.py`
- Error Handler Code: `src/arr_stack_manager/utils/errors.py`
- Error Boundary Code: `src/arr_stack_manager/utils/error_boundary.py`
- State Manager Code: `src/arr_stack_manager/utils/state_manager.py`
