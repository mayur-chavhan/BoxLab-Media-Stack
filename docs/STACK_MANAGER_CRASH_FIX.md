# Stack Manager Crash Fix

## Problem

When the wizard completes and navigates to the Stack Manager screen, the entire app crashes with a `MarkupError`:

```
MarkupError: Expected markup value (found '=None, input_type=NoneType]\n').
```

The error trace shows:

```
Error loading service data: 1 validation error for ServiceInfo
name
  Input should be a valid string [type=string_type, input_type=NoneType]
```

## Root Cause Analysis

### Issue 1: Missing Service Name

The `StackManagerScreen` was being instantiated without a service name:

```python
# In app.py
def _navigate_to_stack_manager(self, **kwargs: Any) -> None:
    service_name = kwargs.get("service_name")  # Can be None!
    self.push_screen(StackManagerScreen(self.controller, service_name))
```

When `service_name` is `None`, the screen tries to load service info with `None`, which causes a Pydantic validation error.

### Issue 2: Markup Error in Notification

The error message from Pydantic contains square brackets `[]` which are special characters in Textual's markup system:

```
Input should be a valid string [type=string_type, input_type=NoneType]
                                ^                                     ^
                                These brackets break the markup parser
```

When this error is displayed in a Toast notification, it causes a `MarkupError` that crashes the rendering system.

## Solution

### Fix 1: Handle Missing Service Name

Modified `StackManagerScreen.__init__` to accept optional service_name:

```python
def __init__(
    self,
    controller: AppController,
    service_name: str | None = None,  # Now optional
    ...
) -> None:
```

### Fix 2: Check for None Before Loading

Added validation in `_load_service_data`:

```python
async def _load_service_data(self) -> None:
    try:
        # Check if service name is provided
        if not self.service_name:
            logger.error("No service name provided to StackManagerScreen")
            self.notify("No service selected. Please select a service from the dashboard.", severity="error")
            return

        # Continue with loading...
```

### Fix 3: Escape Error Messages

Escape special markup characters in error messages:

```python
except Exception as e:
    logger.error(f"Failed to load service data: {e}", exc_info=True)
    # Escape the error message to prevent markup issues
    error_msg = str(e).replace("[", "\\[").replace("]", "\\]")
    self.notify(f"Error loading service data: {error_msg}", severity="error")
```

## Why This Happened

The Stack Manager screen is designed to show details for a specific service. However, when navigating from the wizard, no specific service was selected, so `service_name` was `None`. The screen should either:

1. **Show a service selection UI** when no service is specified
2. **Navigate to dashboard** instead of stack manager after wizard completion
3. **Select the first service automatically** from the deployed stack

## Current Behavior After Fix

✅ If `service_name` is `None`:

- Shows a friendly error message: "No service selected. Please select a service from the dashboard."
- Doesn't crash the app
- User can navigate back to dashboard

✅ If there's any error loading service data:

- Error message is properly escaped
- Toast notification displays correctly
- App continues to function

## Recommendation

The wizard should probably navigate to the **Dashboard** after completion, not the Stack Manager. The Stack Manager is for managing individual services, while the Dashboard shows the overall stack status.

To fix the navigation flow, update the wizard's finish handler to navigate to dashboard instead:

```python
# In config_wizard.py, after deployment
self.controller.navigate_to(ScreenType.DASHBOARD, stack_name=stack_name)
```

## Files Modified

- `src/arr_stack_manager/screens/stack_manager.py`
  - Made `service_name` parameter optional
  - Added None check before loading service data
  - Added error message escaping to prevent markup errors

## Testing

1. Complete the wizard
2. Verify no crash occurs
3. See friendly error message if no service selected
4. Navigate back to dashboard
5. Select a specific service from dashboard → Stack Manager should work correctly
