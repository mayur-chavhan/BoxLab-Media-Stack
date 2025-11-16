"""Full-featured log viewer screen for container logs."""

import logging
import re
from collections import deque
from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Select, Static
from textual.worker import Worker, WorkerState

from arr_stack_manager.controller import AppController

logger = logging.getLogger(__name__)


class LogLevel:
    """Log severity levels for filtering."""

    ALL = "all"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class LogViewerScreen(Screen):
    """Full-featured log viewer screen with streaming, filtering, and search."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("q", "quit", "Quit"),
        ("f", "focus_search", "Search"),
        ("c", "clear_logs", "Clear"),
        ("s", "toggle_streaming", "Toggle Stream"),
        ("a", "toggle_autoscroll", "Toggle Auto-scroll"),
    ]

    CSS = """
    LogViewerScreen {
        background: $background;
    }

    LogViewerScreen .viewer-container {
        height: 100%;
        width: 100%;
    }

    LogViewerScreen .controls-bar {
        height: 3;
        width: 100%;
        background: $surface;
        border-bottom: solid $primary;
        padding: 0 1;
    }

    LogViewerScreen .controls-left {
        width: auto;
        height: 100%;
        align: left middle;
    }

    LogViewerScreen .controls-right {
        width: auto;
        height: 100%;
        align: right middle;
    }

    LogViewerScreen .service-label {
        text-style: bold;
        color: $text;
        margin-right: 2;
    }

    LogViewerScreen .status-label {
        margin-left: 2;
        margin-right: 2;
    }

    LogViewerScreen .streaming {
        color: $success;
        text-style: bold;
    }

    LogViewerScreen .paused {
        color: $warning;
    }

    LogViewerScreen .filter-bar {
        height: 3;
        width: 100%;
        background: $surface;
        border-bottom: solid $primary;
        padding: 0 1;
    }

    LogViewerScreen .filter-left {
        width: 1fr;
        height: 100%;
        align: left middle;
    }

    LogViewerScreen .filter-right {
        width: auto;
        height: 100%;
        align: right middle;
    }

    LogViewerScreen Select {
        width: 20;
        margin-right: 2;
    }

    LogViewerScreen Input {
        width: 40;
        margin-right: 2;
    }

    LogViewerScreen Button {
        margin: 0 1;
    }

    LogViewerScreen .log-content {
        height: 1fr;
        width: 100%;
        padding: 1;
    }

    LogViewerScreen RichLog {
        height: 100%;
        width: 100%;
        background: $panel;
        border: solid $primary;
    }

    LogViewerScreen .stats-bar {
        height: 3;
        width: 100%;
        background: $surface;
        border-top: solid $primary;
        padding: 0 1;
    }

    LogViewerScreen .stats-content {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    LogViewerScreen .stats-text {
        color: $text-muted;
    }
    """

    is_streaming: reactive[bool] = reactive(False)
    auto_scroll: reactive[bool] = reactive(True)
    line_count: reactive[int] = reactive(0)
    filtered_count: reactive[int] = reactive(0)

    def __init__(
        self,
        controller: AppController,
        service_name: str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the log viewer screen.

        Args:
            controller: Application controller instance
            service_name: Name of the service to view logs for
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.controller = controller
        self.service_name = service_name
        self._log_buffer: deque[str] = deque(maxlen=10000)
        self._stream_worker: Worker | None = None
        self._current_filter = LogLevel.ALL
        self._search_term = ""

    def compose(self) -> ComposeResult:
        """Compose the log viewer screen layout."""
        yield Header()

        with Vertical(classes="viewer-container"):
            # Top controls bar
            with Horizontal(classes="controls-bar"):
                with Horizontal(classes="controls-left"):
                    yield Label(
                        f"Logs: {self.service_name.title()}",
                        classes="service-label",
                    )
                    yield Label(
                        "● Streaming" if self.is_streaming else "○ Paused",
                        classes=f"status-label {'streaming' if self.is_streaming else 'paused'}",
                        id="status-label",
                    )

                with Horizontal(classes="controls-right"):
                    yield Button("Clear", id="clear-btn", variant="default")
                    yield Button(
                        "⏸ Pause" if self.is_streaming else "▶ Stream",
                        id="stream-btn",
                        variant="primary",
                    )
                    yield Button(
                        "✓ Auto-scroll" if self.auto_scroll else "✗ Auto-scroll",
                        id="autoscroll-btn",
                        variant="success" if self.auto_scroll else "default",
                    )

            # Filter and search bar
            with Horizontal(classes="filter-bar"):
                with Horizontal(classes="filter-left"):
                    yield Label("Filter:", classes="filter-label")
                    yield Select(
                        options=[
                            ("All Levels", LogLevel.ALL),
                            ("Errors Only", LogLevel.ERROR),
                            ("Warnings", LogLevel.WARNING),
                            ("Info", LogLevel.INFO),
                            ("Debug", LogLevel.DEBUG),
                        ],
                        value=LogLevel.ALL,
                        id="level-filter",
                    )
                    yield Label("Search:", classes="filter-label")
                    yield Input(
                        placeholder="Search logs...",
                        id="search-input",
                    )

                with Horizontal(classes="filter-right"):
                    yield Button("Export", id="export-btn", variant="default")

            # Log content area
            with Container(classes="log-content"):
                yield RichLog(
                    highlight=True,
                    markup=True,
                    wrap=True,
                    id="log-display",
                )

            # Stats bar
            with Horizontal(classes="stats-bar"):
                with Horizontal(classes="stats-content"):
                    yield Label(
                        self._get_stats_text(),
                        classes="stats-text",
                        id="stats-label",
                    )

        yield Footer()

    async def on_mount(self) -> None:
        """Handle screen mount event."""
        logger.info(f"Log viewer mounted for service: {self.service_name}")

        # Load initial logs
        await self._load_initial_logs()

        # Start streaming if service is running
        service_info = self.controller.get_service_info(self.service_name)
        if service_info.is_running:
            self.start_streaming()

    def on_unmount(self) -> None:
        """Handle screen unmount event."""
        logger.info("Log viewer unmounting")
        self.stop_streaming()

    async def _load_initial_logs(self) -> None:
        """Load initial log history."""
        try:
            log_lines = self.controller.docker_manager.get_service_logs(
                self.service_name,
                lines=500,
                timestamps=True,
            )

            for line in log_lines:
                self._add_log_line(line, refresh=False)

            # Refresh display once after loading all lines
            self._refresh_display()

            logger.info(f"Loaded {len(log_lines)} initial log lines")

        except Exception as e:
            logger.error(f"Failed to load initial logs: {e}")
            self.notify(f"Error loading logs: {e}", severity="error")

    def _add_log_line(self, line: str, refresh: bool = True) -> None:
        """Add a log line to the buffer and display.

        Args:
            line: Log line to add
            refresh: Whether to refresh the display immediately
        """
        self._log_buffer.append(line)
        self.line_count += 1

        # Apply filtering and search
        if self._should_display_line(line):
            self.filtered_count += 1

            if self.is_mounted and refresh:
                log_display = self.query_one("#log-display", RichLog)

                # Format the line with syntax highlighting
                formatted_line = self._format_log_line(line)
                log_display.write(formatted_line)

                # Auto-scroll if enabled
                if self.auto_scroll:
                    log_display.scroll_end(animate=False)

                # Update stats
                self._update_stats()

    def _should_display_line(self, line: str) -> bool:
        """Check if a log line should be displayed based on filters.

        Args:
            line: Log line to check

        Returns:
            True if line should be displayed, False otherwise
        """
        # Apply level filter
        if self._current_filter != LogLevel.ALL:
            if not self._matches_level_filter(line, self._current_filter):
                return False

        # Apply search filter
        if self._search_term:
            if self._search_term.lower() not in line.lower():
                return False

        return True

    def _matches_level_filter(self, line: str, level: str) -> bool:
        """Check if a log line matches the level filter.

        Args:
            line: Log line to check
            level: Level to filter for

        Returns:
            True if line matches the level, False otherwise
        """
        line_lower = line.lower()

        if level == LogLevel.ERROR:
            return any(
                keyword in line_lower
                for keyword in ["error", "err", "fatal", "critical", "exception"]
            )
        elif level == LogLevel.WARNING:
            return any(keyword in line_lower for keyword in ["warn", "warning"])
        elif level == LogLevel.INFO:
            return any(keyword in line_lower for keyword in ["info", "information"])
        elif level == LogLevel.DEBUG:
            return any(keyword in line_lower for keyword in ["debug", "trace"])

        return True

    def _format_log_line(self, line: str) -> str:
        """Format a log line with syntax highlighting.

        Args:
            line: Raw log line

        Returns:
            Formatted log line with Rich markup
        """
        # Highlight timestamps (ISO 8601 format)
        line = re.sub(
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z?)",
            r"[dim]\1[/dim]",
            line,
        )

        # Highlight log levels
        line = re.sub(
            r"\b(ERROR|ERR|FATAL|CRITICAL)\b",
            r"[bold red]\1[/bold red]",
            line,
            flags=re.IGNORECASE,
        )
        line = re.sub(
            r"\b(WARN|WARNING)\b",
            r"[bold yellow]\1[/bold yellow]",
            line,
            flags=re.IGNORECASE,
        )
        line = re.sub(
            r"\b(INFO|INFORMATION)\b",
            r"[bold cyan]\1[/bold cyan]",
            line,
            flags=re.IGNORECASE,
        )
        line = re.sub(
            r"\b(DEBUG|TRACE)\b",
            r"[dim]\1[/dim]",
            line,
            flags=re.IGNORECASE,
        )

        # Highlight IP addresses
        line = re.sub(
            r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b",
            r"[blue]\1[/blue]",
            line,
        )

        # Highlight URLs
        line = re.sub(
            r"(https?://[^\s]+)",
            r"[link=\1]\1[/link]",
            line,
        )

        # Highlight search term if present
        if self._search_term:
            pattern = re.compile(re.escape(self._search_term), re.IGNORECASE)
            line = pattern.sub(
                lambda m: f"[black on yellow]{m.group()}[/black on yellow]",
                line,
            )

        return line

    def _refresh_display(self) -> None:
        """Refresh the entire log display with current filters."""
        if not self.is_mounted:
            return

        log_display = self.query_one("#log-display", RichLog)
        log_display.clear()

        self.filtered_count = 0

        for line in self._log_buffer:
            if self._should_display_line(line):
                self.filtered_count += 1
                formatted_line = self._format_log_line(line)
                log_display.write(formatted_line)

        # Scroll to end if auto-scroll is enabled
        if self.auto_scroll:
            log_display.scroll_end(animate=False)

        self._update_stats()

    def start_streaming(self) -> None:
        """Start streaming logs in real-time."""
        if self.is_streaming:
            return

        logger.info(f"Starting log stream for {self.service_name}")
        self.is_streaming = True
        self._stream_worker = self.run_worker(
            self._stream_logs(),
            exclusive=True,
            name="log_stream",
        )

    def stop_streaming(self) -> None:
        """Stop streaming logs."""
        if not self.is_streaming:
            return

        logger.info(f"Stopping log stream for {self.service_name}")
        self.is_streaming = False

        if self._stream_worker:
            self._stream_worker.cancel()
            self._stream_worker = None

    @work(exclusive=True)
    async def _stream_logs(self) -> None:
        """Worker to stream logs from Docker."""
        try:
            log_stream = self.controller.docker_manager.stream_logs(
                self.service_name,
                timestamps=True,
                follow=True,
            )

            for line in log_stream:
                if not self.is_streaming:
                    break

                self._add_log_line(line)

        except Exception as e:
            logger.error(f"Error streaming logs: {e}")
            self.is_streaming = False
            self.notify(f"Log streaming stopped: {e}", severity="error")

    def _update_stats(self) -> None:
        """Update the statistics bar."""
        if self.is_mounted:
            stats_label = self.query_one("#stats-label", Label)
            stats_label.update(self._get_stats_text())

    def _get_stats_text(self) -> str:
        """Get the current statistics text."""
        status = "Streaming" if self.is_streaming else "Paused"
        scroll = "Auto-scroll: ON" if self.auto_scroll else "Auto-scroll: OFF"

        if self._current_filter != LogLevel.ALL or self._search_term:
            return (
                f"{status} | {scroll} | "
                f"Showing: {self.filtered_count} / {self.line_count} lines"
            )
        else:
            return f"{status} | {scroll} | Lines: {self.line_count}"

    def watch_is_streaming(self, new_value: bool) -> None:
        """React to streaming state changes.

        Args:
            new_value: New streaming state
        """
        if self.is_mounted:
            status_label = self.query_one("#status-label", Label)
            status_label.update("● Streaming" if new_value else "○ Paused")
            status_label.remove_class("streaming", "paused")
            status_label.add_class("streaming" if new_value else "paused")

            stream_btn = self.query_one("#stream-btn", Button)
            stream_btn.label = "⏸ Pause" if new_value else "▶ Stream"

            self._update_stats()

    def watch_auto_scroll(self, new_value: bool) -> None:
        """React to auto-scroll state changes.

        Args:
            new_value: New auto-scroll state
        """
        if self.is_mounted:
            autoscroll_btn = self.query_one("#autoscroll-btn", Button)
            autoscroll_btn.label = "✓ Auto-scroll" if new_value else "✗ Auto-scroll"
            autoscroll_btn.variant = "success" if new_value else "default"

            self._update_stats()

    @on(Button.Pressed, "#clear-btn")
    def handle_clear(self) -> None:
        """Handle clear button press."""
        logger.info("Clearing logs")
        self._log_buffer.clear()
        self.line_count = 0
        self.filtered_count = 0

        if self.is_mounted:
            log_display = self.query_one("#log-display", RichLog)
            log_display.clear()
            self._update_stats()

        self.notify("Logs cleared", severity="information")

    @on(Button.Pressed, "#stream-btn")
    def handle_toggle_streaming(self) -> None:
        """Handle stream toggle button press."""
        if self.is_streaming:
            self.stop_streaming()
            self.notify("Log streaming paused", severity="information")
        else:
            self.start_streaming()
            self.notify("Log streaming started", severity="information")

    @on(Button.Pressed, "#autoscroll-btn")
    def handle_toggle_autoscroll(self) -> None:
        """Handle auto-scroll toggle button press."""
        self.auto_scroll = not self.auto_scroll
        status = "enabled" if self.auto_scroll else "disabled"
        self.notify(f"Auto-scroll {status}", severity="information")

    @on(Select.Changed, "#level-filter")
    def handle_level_filter_changed(self, event: Select.Changed) -> None:
        """Handle level filter selection change.

        Args:
            event: Select changed event
        """
        if event.value != Select.BLANK:
            self._current_filter = str(event.value)
            logger.info(f"Log level filter changed to: {self._current_filter}")
            self._refresh_display()
            self.notify(f"Filter: {self._current_filter}", severity="information")

    @on(Input.Submitted, "#search-input")
    def handle_search_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission.

        Args:
            event: Input submitted event
        """
        self._search_term = event.value.strip()
        logger.info(f"Search term: {self._search_term}")
        self._refresh_display()

        if self._search_term:
            self.notify(
                f"Searching for: {self._search_term}",
                severity="information",
            )
        else:
            self.notify("Search cleared", severity="information")

    @on(Input.Changed, "#search-input")
    def handle_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes (live search).

        Args:
            event: Input changed event
        """
        # Only trigger live search if input is empty (clearing search)
        if not event.value:
            self._search_term = ""
            self._refresh_display()

    @on(Button.Pressed, "#export-btn")
    def handle_export(self) -> None:
        """Handle export button press."""
        try:
            from pathlib import Path
            from datetime import datetime

            # Create exports directory
            export_dir = Path.home() / ".config" / "arr-stack-manager" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.service_name}_logs_{timestamp}.txt"
            export_path = export_dir / filename

            # Write logs to file
            with open(export_path, "w") as f:
                for line in self._log_buffer:
                    if self._should_display_line(line):
                        # Remove Rich markup for plain text export
                        plain_line = re.sub(r"\[.*?\]", "", line)
                        f.write(plain_line + "\n")

            logger.info(f"Exported logs to: {export_path}")
            self.notify(
                f"Logs exported to: {export_path}",
                severity="information",
            )

        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            self.notify(f"Export failed: {e}", severity="error")

    def action_back(self) -> None:
        """Navigate back to the previous screen."""
        logger.info("Navigating back from log viewer")
        self.stop_streaming()
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.stop_streaming()
        self.app.exit()

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def action_clear_logs(self) -> None:
        """Clear logs via keyboard shortcut."""
        self.handle_clear()

    def action_toggle_streaming(self) -> None:
        """Toggle streaming via keyboard shortcut."""
        self.handle_toggle_streaming()

    def action_toggle_autoscroll(self) -> None:
        """Toggle auto-scroll via keyboard shortcut."""
        self.handle_toggle_autoscroll()
