"""Log viewer widget for displaying and streaming container logs."""

from collections import deque

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Label, RichLog


class LogViewer(Container):
    """A widget for viewing and streaming service logs."""

    DEFAULT_CSS = """
    LogViewer {
        height: 100%;
        width: 100%;
        border: solid $primary;
        background: $surface;
    }

    LogViewer .log-header {
        height: 3;
        width: 100%;
        background: $primary;
        padding: 0 1;
    }

    LogViewer .log-title {
        text-style: bold;
        color: $text;
        width: 1fr;
        content-align: center middle;
    }

    LogViewer .log-controls {
        height: auto;
        width: auto;
        align: right middle;
    }

    LogViewer .log-content {
        height: 1fr;
        width: 100%;
        padding: 1;
    }

    LogViewer RichLog {
        height: 100%;
        width: 100%;
        background: $panel;
        border: none;
    }

    LogViewer .log-footer {
        height: 3;
        width: 100%;
        background: $surface;
        padding: 0 1;
        border-top: solid $primary;
    }

    LogViewer .log-status {
        color: $text-muted;
        width: 1fr;
        content-align: center middle;
    }

    LogViewer Button {
        margin: 0 1;
    }

    LogViewer .streaming {
        color: $success;
        text-style: bold;
    }

    LogViewer .paused {
        color: $warning;
    }
    """

    def __init__(
        self,
        service_name: str,
        max_lines: int = 1000,
        auto_scroll: bool = True,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the log viewer.

        Args:
            service_name: Name of the service to view logs for
            max_lines: Maximum number of log lines to keep in memory
            auto_scroll: Whether to auto-scroll to new log entries
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service_name = service_name
        self.max_lines = max_lines
        self.auto_scroll = auto_scroll
        self.is_streaming = False
        self._log_buffer: deque[str] = deque(maxlen=max_lines)
        self._line_count = 0

    def compose(self) -> ComposeResult:
        """Compose the log viewer layout."""
        # Header with title and controls
        with Horizontal(classes="log-header"):
            yield Label(f"Logs: {self.service_name.title()}", classes="log-title")
            with Horizontal(classes="log-controls"):
                yield Button("Clear", id="clear-logs", variant="default")
                yield Button(
                    "⏸ Pause" if self.auto_scroll else "▶ Resume",
                    id="toggle-scroll",
                    variant="primary",
                )
                yield Button("✕", id="close-logs", variant="error")

        # Log content area
        with Vertical(classes="log-content"):
            yield RichLog(highlight=True, markup=True, wrap=True, id="log-display")

        # Footer with status
        with Horizontal(classes="log-footer"):
            yield Label(
                self._get_status_text(),
                classes=f"log-status {'streaming' if self.is_streaming else 'paused'}",
                id="log-status",
            )

    def on_mount(self) -> None:
        """Handle mount event."""
        # Load any buffered logs
        log_display = self.query_one("#log-display", RichLog)
        for line in self._log_buffer:
            log_display.write(line)

    def add_log_line(self, line: str) -> None:
        """Add a new log line to the viewer.

        Args:
            line: Log line to add
        """
        self._log_buffer.append(line)
        self._line_count += 1

        # Update display if mounted
        if self.is_mounted:
            log_display = self.query_one("#log-display", RichLog)
            log_display.write(line)

            # Auto-scroll to bottom if enabled
            if self.auto_scroll:
                log_display.scroll_end(animate=False)

            # Update status
            self._update_status()

    def add_log_lines(self, lines: list[str]) -> None:
        """Add multiple log lines at once.

        Args:
            lines: List of log lines to add
        """
        for line in lines:
            self.add_log_line(line)

    def clear_logs(self) -> None:
        """Clear all logs from the viewer."""
        self._log_buffer.clear()
        self._line_count = 0

        if self.is_mounted:
            log_display = self.query_one("#log-display", RichLog)
            log_display.clear()
            self._update_status()

    def toggle_auto_scroll(self) -> None:
        """Toggle auto-scroll functionality."""
        self.auto_scroll = not self.auto_scroll

        if self.is_mounted:
            button = self.query_one("#toggle-scroll", Button)
            button.label = "⏸ Pause" if self.auto_scroll else "▶ Resume"
            self._update_status()

    def set_streaming(self, streaming: bool) -> None:
        """Set the streaming state.

        Args:
            streaming: Whether logs are being streamed
        """
        self.is_streaming = streaming
        if self.is_mounted:
            self._update_status()

    def _update_status(self) -> None:
        """Update the status footer."""
        if self.is_mounted:
            status_label = self.query_one("#log-status", Label)
            status_label.update(self._get_status_text())
            status_label.remove_class("streaming", "paused")
            status_label.add_class("streaming" if self.is_streaming else "paused")

    def _get_status_text(self) -> str:
        """Get the current status text."""
        status = "Streaming" if self.is_streaming else "Paused"
        scroll = "Auto-scroll: ON" if self.auto_scroll else "Auto-scroll: OFF"
        return f"{status} | {scroll} | Lines: {self._line_count}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events.

        Args:
            event: Button pressed event
        """
        if event.button.id == "clear-logs":
            self.clear_logs()
        elif event.button.id == "toggle-scroll":
            self.toggle_auto_scroll()
        elif event.button.id == "close-logs":
            # Post a custom message that parent can handle
            self.post_message(self.LogViewerClosed(self.service_name))

    class LogViewerClosed(Message):
        """Message posted when log viewer is closed."""

        def __init__(self, service_name: str) -> None:
            """Initialize the message.

            Args:
                service_name: Name of the service whose logs were being viewed
            """
            super().__init__()
            self.service_name = service_name
