# Header NoMatches Error Fix

## Issue

When exiting the application, a `NoMatches` exception was being raised from Textual's Header widget:

```
NoMatches: No nodes match 'HeaderTitle' on Header()
```

This occurred during the unmount phase when the Header widget tried to update its title, but the widget tree was already being torn down.

## Root Cause

This is a known issue in some versions of Textual where the Header widget attempts to query for its child `HeaderTitle` widget during the unmount process, but the child widgets have already been removed from the widget tree.

## Solution

Implemented two fixes:

### 1. Override `_handle_exception` Method

Added a custom exception handler in the `StackManagerApp` class that specifically catches and suppresses `NoMatches` errors related to `HeaderTitle`:

```python
def _handle_exception(self, error: Exception) -> None:
    """Handle exceptions from Textual framework."""
    # Suppress NoMatches errors from Header during unmount
    if isinstance(error, NoMatches) and "HeaderTitle" in str(error):
        logger.debug("Suppressed Header NoMatches error during unmount")
        return

    # For other exceptions, use the default handler
    super()._handle_exception(error)
```

### 2. Improved Exception Handler Safety

Enhanced the global exception handler to safely handle cases where the screen stack is empty:

```python
# Safely get screen name
screen_name = "Unknown"
try:
    if self.screen:
        screen_name = self.screen.__class__.__name__
except Exception:
    pass
```

## Changes Made

- **File**: `src/arr_stack_manager/app.py`
  - Added import for `NoMatches` from `textual.css.query`
  - Added `_handle_exception` method to suppress Header-related NoMatches errors
  - Added `compose` method to explicitly yield Header and Footer widgets
  - Improved exception handler to safely access screen information

## Testing

The fix ensures that:

1. The application exits cleanly without showing NoMatches errors to users
2. The error is logged at DEBUG level for troubleshooting
3. Other exceptions are still properly handled
4. The unmount process completes successfully

## Impact

- Users will no longer see the confusing NoMatches traceback when exiting the application
- The application logs "Application unmounted cleanly" as expected
- No functional changes to the application behavior
