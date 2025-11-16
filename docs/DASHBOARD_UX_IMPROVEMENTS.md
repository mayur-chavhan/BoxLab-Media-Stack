# Dashboard UX Improvements

## Issues Fixed

### 1. No Way to Create Stack on First Run

**Problem:**
When the application starts with no existing stack configuration, the dashboard displays "No stack configured. Press 's' to select services." However:

- The message wasn't prominent enough
- Users might not notice the keyboard shortcut
- No visual button to click

**Solution:**
Added a prominent "Create New Stack" button in the services section when no stack is configured:

```python
def _show_no_stack_message(self) -> None:
    """Show message when no stack is configured."""
    services_list = self.query_one("#services-list", ScrollableContainer)
    services_list.remove_children()

    # Create a container with message and button
    services_list.mount(
        Label("No stack configured yet.", classes="no-services")
    )
    services_list.mount(
        Label("Get started by creating your first stack:", classes="no-services")
    )
    services_list.mount(
        Button("Create New Stack", id="create-stack-button", variant="primary")
    )
```

The button is styled to be centered and prominent:

```css
DashboardScreen #create-stack-button {
  margin: 2 auto;
  width: 30;
}
```

### 2. Keyboard Shortcuts Not Working

**Problem:**
The footer shows keyboard shortcuts (s, c, h, etc.) but they weren't functioning properly:

- `s` (Services) - Was a TODO, not implemented
- `c` (Config) - Was a TODO, not implemented
- `h` (Help) - Was a TODO, not implemented

**Solution:**
Implemented all keyboard shortcut actions in the dashboard:

```python
def action_services(self) -> None:
    """Navigate to services screen."""
    logger.info("Navigate to services requested")
    from arr_stack_manager.controller import ScreenType
    self.controller.navigate_to(ScreenType.SERVICE_SELECTOR)

def action_config(self) -> None:
    """Navigate to configuration screen."""
    logger.info("Navigate to config requested")
    from arr_stack_manager.controller import ScreenType
    # If we have a current stack, use its configuration
    if self.controller.current_stack:
        self.controller.navigate_to(
            ScreenType.CONFIG_WIZARD,
            configuration=self.controller.current_stack.configuration
        )
    else:
        # No stack, start with service selector
        self.controller.navigate_to(ScreenType.SERVICE_SELECTOR)

def action_help(self) -> None:
    """Show help screen."""
    logger.info("Help action triggered")
    from arr_stack_manager.app import HelpScreen
    self.app.push_screen(HelpScreen())
```

### 3. Improved "No Stack" Handling

**Problem:**
When pressing `c` (Config) with no stack configured, the app would try to navigate to the config wizard without any services selected, which doesn't make sense.

**Solution:**
Added smart navigation logic:

- If a stack exists → Go to config wizard with that configuration
- If no stack exists → Redirect to service selector first

This is implemented in both the dashboard and the main app:

```python
# In app.py
def action_goto_config(self) -> None:
    """Navigate to the configuration wizard."""
    if self.controller.current_stack:
        self.controller.navigate_to(
            ScreenType.CONFIG_WIZARD,
            configuration=self.controller.current_stack.configuration
        )
    else:
        # No stack configured, start with service selector
        logger.info("No stack configured, redirecting to service selector")
        self.controller.navigate_to(ScreenType.SERVICE_SELECTOR)
```

## User Experience Flow

### First-Time User (No Stack)

1. **Dashboard loads** → Shows "No stack configured yet" message
2. **User sees prominent "Create New Stack" button**
3. **User can either:**
   - Click the button
   - Press `s` to go to service selector
   - Press `c` which redirects to service selector
4. **Service selector** → User selects services
5. **Config wizard** → User configures the stack
6. **Dashboard** → Shows the configured stack

### Returning User (Stack Exists)

1. **Dashboard loads** → Shows stack status and services
2. **All keyboard shortcuts work:**
   - `s` → Service selector (to modify services)
   - `c` → Config wizard (to modify configuration)
   - `h` or `?` → Help screen
   - `r` → Refresh status
   - `q` → Quit
   - `d` → Dashboard (if on another screen)
   - `m` → Stack manager

## Files Modified

### `src/arr_stack_manager/screens/dashboard.py`

- Added "Create New Stack" button when no stack is configured
- Implemented `action_services()` to navigate to service selector
- Implemented `action_config()` with smart navigation
- Implemented `action_help()` to show help screen
- Added CSS styling for the create stack button
- Added button press handler for create stack button

### `src/arr_stack_manager/app.py`

- Updated `action_goto_config()` to handle no-stack case
- Added smart redirection to service selector when appropriate

## Testing

To test these improvements:

1. **Start with no configuration:**

   ```bash
   rm -rf ~/.config/arr-stack-manager
   python -m arr_stack_manager
   ```

2. **Verify:**

   - Dashboard shows "Create New Stack" button
   - Button is centered and prominent
   - Clicking button navigates to service selector
   - Pressing `s` navigates to service selector
   - Pressing `c` redirects to service selector (since no stack exists)
   - Pressing `h` or `?` shows help screen
   - All keyboard shortcuts are functional

3. **After creating a stack:**
   - Dashboard shows stack status
   - All keyboard shortcuts work as expected
   - `c` now goes to config wizard (not service selector)

## Benefits

1. **Clearer First-Run Experience** - New users immediately see how to get started
2. **Functional Keyboard Shortcuts** - All advertised shortcuts now work
3. **Smart Navigation** - App intelligently handles missing configuration
4. **Better Discoverability** - Visual button complements keyboard shortcuts
5. **Consistent UX** - Same flow whether using mouse or keyboard
