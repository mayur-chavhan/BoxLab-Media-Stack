"""Error boundary system for graceful error handling in screens."""

import logging
from typing import Any, Callable

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from arr_stack_manager.utils.errors import ErrorDisplay, handle_exception

logger = logging.getLogger(__name__)


class ErrorBoundary:
    """
    Error boundary that catches and handles exceptions in screen operations.
    
    This class provides a decorator pattern for wrapping screen methods
    with error handling logic, preventing crashes and providing user-friendly
    error messages.
    """

    def __init__(self, screen: Screen, fallback_action: str = "return_to_dashboard") -> None:
        """
        Initialize the error boundary.

        Args:
            screen: The screen to protect with error boundary
            fallback_action: Action to take on unrecoverable error
                           ("return_to_dashboard", "show_error_screen", "exit")
        """
        self.screen = screen
        self.fallback_action = fallback_action
        self._error_count = 0
        self._max_errors = 5  # Maximum errors before forcing fallback

    def wrap(self, func: Callable) -> Callable:
        """
        Wrap a function with error handling.

        Args:
            func: Function to wrap

        Returns:
            Wrapped function with error handling
        """
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return self._handle_error(e, func.__name__)

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return self._handle_error(e, func.__name__)

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    def _handle_error(self, exception: Exception, context: str) -> None:
        """
        Handle an error that occurred within the boundary.

        Args:
            exception: The exception that was raised
            context: Context where the error occurred (function name)
        """
        self._error_count += 1
        
        # Convert exception to user-friendly error display
        error_display = handle_exception(exception, context)
        
        # Log the error
        logger.error(
            f"Error in {context}: {error_display.message}",
            exc_info=True,
            extra={"screen": self.screen.__class__.__name__}
        )
        
        # Show error to user
        self._show_error_to_user(error_display)
        
        # Check if we've exceeded error threshold
        if self._error_count >= self._max_errors:
            logger.critical(
                f"Error threshold exceeded ({self._max_errors}) in {self.screen.__class__.__name__}"
            )
            self._execute_fallback(error_display)

    def _show_error_to_user(self, error_display: ErrorDisplay) -> None:
        """
        Display error to user in the screen.

        Args:
            error_display: Error information to display
        """
        try:
            # Try to show error using screen's notify method
            if hasattr(self.screen, "notify"):
                self.screen.notify(
                    error_display.message,
                    title=error_display.title,
                    severity="error",
                    timeout=10,
                )
            
            # Also try to show in a dedicated error area if available
            if hasattr(self.screen, "show_error"):
                self.screen.show_error(error_display)
                
        except Exception as e:
            # If we can't even show the error, log it
            logger.error(f"Failed to display error to user: {e}")

    def _execute_fallback(self, error_display: ErrorDisplay) -> None:
        """
        Execute fallback action for unrecoverable errors.

        Args:
            error_display: Error information
        """
        logger.info(f"Executing fallback action: {self.fallback_action}")
        
        try:
            if self.fallback_action == "return_to_dashboard":
                # Navigate back to dashboard
                if hasattr(self.screen.app, "controller"):
                    from arr_stack_manager.controller import ScreenType
                    self.screen.app.controller.navigate_to(ScreenType.DASHBOARD)
                else:
                    self.screen.app.pop_screen()
                    
            elif self.fallback_action == "show_error_screen":
                # Push error screen
                self.screen.app.push_screen(
                    ErrorScreen(error_display, self.screen.__class__.__name__)
                )
                
            elif self.fallback_action == "exit":
                # Exit application
                self.screen.app.exit(message=f"Fatal error: {error_display.message}")
                
        except Exception as e:
            logger.critical(f"Fallback action failed: {e}")
            # Last resort: exit
            self.screen.app.exit(message="Critical error occurred")


class ErrorScreen(Screen):
    """
    Dedicated error screen for displaying critical errors.
    
    This screen is shown when an error cannot be recovered from
    within the current screen context.
    """

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("enter", "dismiss", "Close"),
        ("q", "quit", "Quit App"),
    ]

    CSS = """
    ErrorScreen {
        align: center middle;
    }

    ErrorScreen .error-container {
        width: 80;
        height: auto;
        max-height: 90%;
        border: solid $error;
        background: $surface;
        padding: 2;
    }

    ErrorScreen .error-title {
        text-style: bold;
        color: $error;
        text-align: center;
        margin-bottom: 1;
    }

    ErrorScreen .error-message {
        color: $text;
        margin-bottom: 2;
    }

    ErrorScreen .error-details {
        color: $text-muted;
        margin-bottom: 2;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    ErrorScreen .remediation-section {
        margin-top: 2;
    }

    ErrorScreen .remediation-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    ErrorScreen .remediation-item {
        color: $text;
        margin-left: 2;
        margin-bottom: 1;
    }

    ErrorScreen .button-container {
        margin-top: 2;
        align: center middle;
    }

    ErrorScreen Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        error_display: ErrorDisplay,
        source_screen: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the error screen.

        Args:
            error_display: Error information to display
            source_screen: Name of the screen where error occurred
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.error_display = error_display
        self.source_screen = source_screen

    def compose(self) -> ComposeResult:
        """Compose the error screen layout."""
        with Container(classes="error-container"):
            yield Label(
                f"❌ {self.error_display.title}",
                classes="error-title"
            )
            
            yield Label(
                f"An error occurred in {self.source_screen}:",
                classes="error-message"
            )
            
            yield Label(
                self.error_display.message,
                classes="error-message"
            )
            
            if self.error_display.technical_details:
                with Static(classes="error-details"):
                    yield Label("Technical Details:")
                    yield Label(self.error_display.technical_details)
            
            if self.error_display.remediation:
                with Vertical(classes="remediation-section"):
                    yield Label(
                        "💡 How to fix:",
                        classes="remediation-title"
                    )
                    for step in self.error_display.remediation:
                        yield Label(f"• {step}", classes="remediation-item")
            
            with Container(classes="button-container"):
                yield Button("Close", variant="primary", id="close-button")
                yield Button("Quit App", variant="error", id="quit-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "close-button":
            self.action_dismiss()
        elif event.button.id == "quit-button":
            self.action_quit()

    async def action_dismiss(self) -> None:
        """Dismiss the error screen."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


def with_error_boundary(fallback_action: str = "return_to_dashboard") -> Callable:
    """
    Decorator to add error boundary to a screen method.

    Args:
        fallback_action: Action to take on unrecoverable error

    Returns:
        Decorator function

    Example:
        @with_error_boundary("show_error_screen")
        async def on_mount(self) -> None:
            # Method implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(self: Screen, *args: Any, **kwargs: Any) -> Any:
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                # Create error boundary for this screen
                boundary = ErrorBoundary(self, fallback_action)
                return boundary._handle_error(e, func.__name__)

        def sync_wrapper(self: Screen, *args: Any, **kwargs: Any) -> Any:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Create error boundary for this screen
                boundary = ErrorBoundary(self, fallback_action)
                return boundary._handle_error(e, func.__name__)

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
