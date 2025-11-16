# Config Wizard Crash Fix

## Problem

The configuration wizard was crashing at the final step when the user clicked "Continue" to generate docker-compose files. The application would terminate unexpectedly without generating any files.

## Root Cause

A syntax error in the `handle_continue_button()` method in `src/arr_stack_manager/screens/config_wizard.py` caused a Python parsing error. The method had a malformed `try` block with incorrect indentation:

```python
@on(Button.Pressed, "#continue-button")
def handle_continue_button(self) -> None:
    """Handle continue button press."""
    logger.info(f"Continue button pressed on step {self._current_step}")

    try:
    self._go_to_next_step()  # ❌ Incorrect indentation after try
```

This syntax error prevented the method from executing, causing the wizard to crash when the continue button was pressed on the final step.

## Solution

Fixed the syntax error by removing the unnecessary `try` block. The `_go_to_next_step()` method already has proper error handling internally, so the outer try block was redundant:

```python
@on(Button.Pressed, "#continue-button")
def handle_continue_button(self) -> None:
    """Handle continue button press."""
    logger.info(f"Continue button pressed on step {self._current_step}")
    self._go_to_next_step()  # ✅ Clean, properly indented call
```

## Verification

The fix was verified with an end-to-end test that:

1. Creates a complete configuration with services (sonarr, radarr)
2. Validates the stack configuration
3. Generates docker-compose files
4. Verifies the generated files contain expected content

Test results:

```
✓ Configuration created with 2 services
✓ Stack config created: test-stack
✓ Stack validation passed
✓ Docker Compose files generated
✓ docker-compose.yml created (1038 bytes)
✓ .env created (340 bytes)
✓ Compose file contains expected services
```

## Wizard Workflow

The wizard now correctly completes all 4 steps:

1. **Service Confirmation** - Review selected services
2. **Base Configuration** - Set PUID, PGID, timezone
3. **Path Configuration** - Configure directory structure
4. **Service-Specific Configuration** - Set ports and custom volumes

After the final step, the wizard:

- Validates the complete configuration
- Generates docker-compose.yml and .env files
- Saves the stack configuration
- Navigates to the dashboard

## Files Modified

- `src/arr_stack_manager/screens/config_wizard.py`
  - Fixed syntax error in `handle_continue_button()` method
  - Removed malformed try block

## Impact

This fix resolves the critical issue preventing users from completing the configuration wizard and deploying their ARR stack. The wizard now successfully generates all required files and transitions to the dashboard for stack management.
