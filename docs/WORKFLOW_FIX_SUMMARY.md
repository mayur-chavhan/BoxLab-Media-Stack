# Workflow Navigation Fix

## Problem

When launching the application for the first time:

1. Dashboard shows for configuration
2. User presses continue → Service selection screen appears
3. User selects services and proceeds
4. **BUG**: Dashboard appears again instead of going to Config Wizard

## Root Cause

The `ServiceSelectorScreen` was dismissing with a `Configuration` object, but the `StackManagerApp` wasn't handling this result. When a screen is pushed without a callback, the dismissed result is ignored, and the app doesn't know what to do next.

## Solution

Added proper callback handling in `src/arr_stack_manager/app.py`:

### 1. Service Selector Navigation

**Before:**

```python
def _navigate_to_service_selector(self, **kwargs: Any) -> None:
    logger.info("Navigating to service selector")
    self.push_screen(ServiceSelectorScreen(self.controller))
```

**After:**

```python
def _navigate_to_service_selector(self, **kwargs: Any) -> None:
    logger.info("Navigating to service selector")
    self.push_screen(ServiceSelectorScreen(self.controller), self._handle_service_selection)
```

### 2. Added Service Selection Handler

```python
def _handle_service_selection(self, config: Any) -> None:
    """Handle the result from service selector screen.

    Args:
        config: Configuration object with selected services, or None if cancelled
    """
    if config is None:
        logger.info("Service selection cancelled, returning to dashboard")
        # User cancelled, go back to dashboard
        self.controller.navigate_to(ScreenType.DASHBOARD, stack_name=self.stack_name)
    else:
        logger.info(f"Services selected, navigating to config wizard")
        # User selected services, navigate to config wizard
        self.controller.navigate_to(ScreenType.CONFIG_WIZARD, configuration=config)
```

### 3. Config Wizard Navigation

**Before:**

```python
def _navigate_to_config_wizard(self, **kwargs: Any) -> None:
    logger.info("Navigating to configuration wizard")
    selected_services = kwargs.get("selected_services", [])
    self.push_screen(ConfigWizardScreen(self.controller, selected_services))
```

**After:**

```python
def _navigate_to_config_wizard(self, **kwargs: Any) -> None:
    logger.info("Navigating to configuration wizard")
    configuration = kwargs.get("configuration")
    self.push_screen(ConfigWizardScreen(self.controller, configuration), self._handle_config_wizard_result)
```

### 4. Added Config Wizard Result Handler

```python
def _handle_config_wizard_result(self, result: Any) -> None:
    """Handle the result from config wizard screen.

    Args:
        result: Result from config wizard (typically None as it handles its own navigation)
    """
    # Config wizard handles its own navigation to deployment monitor
    # If it returns here, user likely went back, so return to dashboard
    logger.info("Config wizard dismissed, returning to dashboard")
    if self.controller.current_stack:
        self.controller.navigate_to(ScreenType.DASHBOARD, stack_name=self.controller.current_stack.name)
    else:
        self.controller.navigate_to(ScreenType.DASHBOARD, stack_name=self.stack_name)
```

## Workflow Flow (Fixed)

```
First Run
    ↓
Setup Wizard
    ↓
[Continue Button]
    ↓
Service Selector
    ↓
[User selects services + Continue]
    ↓
_handle_service_selection(config)  ← NEW CALLBACK
    ↓
Config Wizard (receives Configuration)
    ↓
[User configures settings + Finish]
    ↓
Deployment Monitor
    ↓
Dashboard (with deployed stack)
```

## Key Changes

1. **Service Selector** now properly passes Configuration to callback
2. **App** handles the Configuration and navigates to Config Wizard
3. **Config Wizard** receives the Configuration object (not just service list)
4. **No more loop** back to Dashboard after service selection

## Testing

Run `python test_workflow_fix.py` to verify the navigation flow works correctly.

## Files Modified

- `src/arr_stack_manager/app.py` - Added callback handlers for screen navigation
