"""Base screen class with built-in error handling and state management."""

import logging
from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Label, Static

from arr_stack_manager.utils.error_boundary import ErrorBoundary
from arr_stack_manager.utils.errors import ErrorDisplay
from arr_stack_manager.utils.state_manager import get_state_manager

logger = logging.getLogger(__name__)


class BaseScreen(Screen):
    """
    Base screen class with built-in error handling and state management.
    
    All screens should inherit from this class to get:
    - Automatic error boundary protection
    - State persistence for crash recovery
    - Standardized error display
    - Logging integration
    """

    # Override in subclasses to customize error handling
    ERROR_FALLBACK_ACTION = "return_to_dashboard"
    
    # Override to enable state persistence for this screen
    ENABLE_STATE_PERSISTENCE = False

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the base screen."""
        super().__init__(*args, **kwargs)
        
        # Initialize error boundary
        self._error_boundary = ErrorBoundary(self, self.ERROR_FALLBACK_ACTION)
        
        # State manager
        self._state_manager = get_state_manager()
        
        # Error display state
        self._current_error: ErrorDisplay | None = None
        
        logger.debug(f"{self.__class__.__name__} initialized")

    def on_mount(self) -> None:
        """Handle screen mount event with error protection."""
        try:
            # Restore state if enabled
            if self.ENABLE_STATE_PERSISTENCE:
                self._restore_state()
            
            # Call subclass mount handler
            self._on_mount_impl()
            
        except Exception as e:
            self._error_boundary._handle_error(e, "on_mount")

    def _on_mount_impl(self) -> None:
        """
        Override this method in subclasses instead of on_mount.
        
        This method is called by on_mount with error protection.
        """
        pass

    def on_unmount(self) -> None:
        """Handle screen unmount event with error protection."""
        try:
            # Save state if enabled
            if self.ENABLE_STATE_PERSISTENCE:
                self._save_state()
            
            # Call subclass unmount handler
            self._on_unmount_impl()
            
        except Exception as e:
            logger.error(f"Error during unmount: {e}")

    def _on_unmount_impl(self) -> None:
        """
        Override this method in subclasses instead of on_unmount.
        
        This method is called by on_unmount with error protection.
        """
        pass

    def show_error(self, error_display: ErrorDisplay) -> None:
        """
        Display an error message in the screen.

        Args:
            error_display: Error information to display
        """
        self._current_error = error_display
        
        # Try to find and update error container
        try:
            error_container = self.query_one("#error-container", Container)
            error_container.remove_children()
            
            with error_container:
                error_container.mount(
                    Label(f"❌ {error_display.title}", classes="error-title")
                )
                error_container.mount(
                    Label(error_display.message, classes="error-message")
                )
                
                if error_display.remediation:
                    error_container.mount(
                        Label("💡 How to fix:", classes="remediation-title")
                    )
                    for step in error_display.remediation:
                        error_container.mount(
                            Label(f"• {step}", classes="remediation-item")
                        )
            
            error_container.display = True
            
        except Exception as e:
            # Error container doesn't exist, use notification
            logger.warning(f"Error container not found, using notification: {e}")
            self.notify(
                error_display.message,
                title=error_display.title,
                severity="error",
                timeout=10,
            )

    def clear_error(self) -> None:
        """Clear any displayed error message."""
        self._current_error = None
        
        try:
            error_container = self.query_one("#error-container", Container)
            error_container.display = False
            error_container.remove_children()
        except Exception:
            pass

    def _save_state(self) -> None:
        """
        Save screen state for crash recovery.
        
        Override this method in subclasses to save screen-specific state.
        """
        try:
            state = self._get_state()
            if state:
                screen_state = {
                    "screen_name": self.__class__.__name__,
                    "state": state,
                }
                self._state_manager.save_state(screen_state)
                logger.debug(f"State saved for {self.__class__.__name__}")
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")

    def _restore_state(self) -> None:
        """
        Restore screen state after crash.
        
        Override this method in subclasses to restore screen-specific state.
        """
        try:
            saved_state = self._state_manager.load_state()
            if saved_state and saved_state.get("screen_name") == self.__class__.__name__:
                self._set_state(saved_state.get("state", {}))
                logger.info(f"State restored for {self.__class__.__name__}")
        except Exception as e:
            logger.warning(f"Failed to restore state: {e}")

    def _get_state(self) -> dict[str, Any]:
        """
        Get current screen state for persistence.
        
        Override this method in subclasses to return screen-specific state.

        Returns:
            Dictionary containing screen state
        """
        return {}

    def _set_state(self, state: dict[str, Any]) -> None:
        """
        Set screen state from persisted data.
        
        Override this method in subclasses to restore screen-specific state.

        Args:
            state: Dictionary containing screen state
        """
        pass

    def handle_exception(self, exception: Exception, context: str = "") -> None:
        """
        Handle an exception that occurred in the screen.

        Args:
            exception: The exception to handle
            context: Optional context about where the error occurred
        """
        self._error_boundary._handle_error(exception, context or "screen_operation")

    def safe_query_one(self, selector: str, expect_type: type | None = None) -> Any:
        """
        Safely query for a widget, returning None if not found.

        Args:
            selector: CSS selector or widget ID
            expect_type: Expected widget type

        Returns:
            Widget if found, None otherwise
        """
        try:
            if expect_type:
                return self.query_one(selector, expect_type)
            else:
                return self.query_one(selector)
        except Exception as e:
            logger.debug(f"Widget not found: {selector} - {e}")
            return None

    def safe_update_widget(
        self,
        selector: str,
        content: str,
        expect_type: type | None = None
    ) -> bool:
        """
        Safely update a widget's content.

        Args:
            selector: CSS selector or widget ID
            content: New content for the widget
            expect_type: Expected widget type

        Returns:
            True if update was successful, False otherwise
        """
        try:
            widget = self.safe_query_one(selector, expect_type)
            if widget and hasattr(widget, "update"):
                widget.update(content)
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to update widget {selector}: {e}")
            return False


class ErrorContainer(Static):
    """
    Reusable error display container for screens.
    
    Add this to your screen's compose method to enable error display:
    
    ```python
    def compose(self) -> ComposeResult:
        yield ErrorContainer()
        # ... other widgets
    ```
    """

    DEFAULT_CSS = """
    ErrorContainer {
        display: none;
        width: 100%;
        height: auto;
        background: $error 20%;
        border: solid $error;
        padding: 1 2;
        margin: 1 0;
    }

    ErrorContainer .error-title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }

    ErrorContainer .error-message {
        color: $text;
        margin-bottom: 1;
    }

    ErrorContainer .remediation-title {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 1;
    }

    ErrorContainer .remediation-item {
        color: $text;
        margin-left: 2;
    }
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the error container."""
        super().__init__(*args, **kwargs, id="error-container")

    def compose(self) -> ComposeResult:
        """Compose the error container (initially empty)."""
        yield Vertical()
