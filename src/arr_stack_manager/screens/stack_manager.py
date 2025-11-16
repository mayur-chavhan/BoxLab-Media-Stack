"""Stack management screen for detailed service control and monitoring."""

import logging
from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.service import ServiceInfo, ServiceStatus
from arr_stack_manager.models.validation import OperationResult

logger = logging.getLogger(__name__)


class ServiceDetails(Static):
    """Widget for displaying detailed service information."""

    DEFAULT_CSS = """
    ServiceDetails {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    ServiceDetails .section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    ServiceDetails .detail-row {
        height: auto;
        width: 100%;
        margin: 0;
    }

    ServiceDetails .detail-label {
        color: $text-muted;
        width: 15;
    }

    ServiceDetails .detail-value {
        color: $text;
        width: 1fr;
    }

    ServiceDetails .status-running {
        color: $success;
        text-style: bold;
    }

    ServiceDetails .status-stopped {
        color: $error;
    }

    ServiceDetails .status-error {
        color: $error;
        text-style: bold;
    }

    ServiceDetails .metric-bar {
        height: 1;
        width: 30;
        background: $panel;
        margin: 0 1;
    }

    ServiceDetails .metric-fill {
        height: 1;
        background: $success;
    }

    ServiceDetails .metric-fill-warning {
        background: $warning;
    }

    ServiceDetails .metric-fill-error {
        background: $error;
    }
    """

    service_info: reactive[ServiceInfo | None] = reactive(None)

    def __init__(
        self,
        service_info: ServiceInfo | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the service details widget.

        Args:
            service_info: Service information to display
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service_info = service_info

    def compose(self) -> ComposeResult:
        """Compose the service details layout."""
        if not self.service_info:
            yield Label("No service selected", classes="section-title")
            return

        yield Label(f"Service: {self.service_info.name.title()}", classes="section-title")

        # Basic information
        with Vertical():
            with Horizontal(classes="detail-row"):
                yield Label("Status:", classes="detail-label")
                yield Label(
                    self._format_status(),
                    classes=f"detail-value status-{self.service_info.status.value}",
                )

            if self.service_info.container_id:
                with Horizontal(classes="detail-row"):
                    yield Label("Container:", classes="detail-label")
                    yield Label(self.service_info.container_id, classes="detail-value")

            with Horizontal(classes="detail-row"):
                yield Label("Image:", classes="detail-label")
                yield Label(self.service_info.image, classes="detail-value")

            if self.service_info.is_running and self.service_info.uptime is not None:
                with Horizontal(classes="detail-row"):
                    yield Label("Uptime:", classes="detail-label")
                    yield Label(self.service_info.format_uptime(), classes="detail-value")

            if self.service_info.web_ui_url:
                with Horizontal(classes="detail-row"):
                    yield Label("Web UI:", classes="detail-label")
                    yield Label(self.service_info.web_ui_url, classes="detail-value")

        # Resource usage (if running)
        if self.service_info.is_running and self.service_info.metrics:
            yield Label("Resources:", classes="section-title")
            yield from self._render_metrics()

    def _render_metrics(self) -> ComposeResult:
        """Render resource usage metrics with visual indicators."""
        if not self.service_info or not self.service_info.metrics:
            return

        metrics = self.service_info.metrics

        # CPU usage with bar
        with Horizontal(classes="detail-row"):
            yield Label("CPU:", classes="detail-label")
            yield Label(f"{metrics.cpu_percent:.1f}%", classes="detail-value")
            # Simple text-based bar
            bar_width = int(metrics.cpu_percent / 100 * 20)
            bar = "█" * bar_width + "░" * (20 - bar_width)
            yield Label(bar, classes="detail-value")

        # Memory usage with bar
        with Horizontal(classes="detail-row"):
            yield Label("Memory:", classes="detail-label")
            yield Label(metrics.format_memory(), classes="detail-value")
            # Simple text-based bar
            bar_width = int(metrics.memory_percent / 100 * 20)
            bar = "█" * bar_width + "░" * (20 - bar_width)
            yield Label(f"{bar} {metrics.memory_percent:.0f}%", classes="detail-value")

    def _format_status(self) -> str:
        """Format status with indicator."""
        if not self.service_info:
            return "Unknown"

        status_indicators = {
            ServiceStatus.RUNNING: "● Running",
            ServiceStatus.STOPPED: "○ Stopped",
            ServiceStatus.STARTING: "⟳ Starting",
            ServiceStatus.STOPPING: "⟳ Stopping",
            ServiceStatus.ERROR: "✗ Error",
            ServiceStatus.UNKNOWN: "? Unknown",
        }
        return status_indicators.get(self.service_info.status, "? Unknown")

    def watch_service_info(self, new_info: ServiceInfo | None) -> None:
        """React to service info changes.

        Args:
            new_info: New service information
        """
        if self.is_mounted:
            self.refresh(layout=True)

    def update_service_info(self, service_info: ServiceInfo) -> None:
        """Update the displayed service information.

        Args:
            service_info: New service information
        """
        self.service_info = service_info


class VolumePortInfo(Static):
    """Widget for displaying volume mounts and port mappings."""

    DEFAULT_CSS = """
    VolumePortInfo {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    VolumePortInfo .section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    VolumePortInfo .info-item {
        color: $text;
        margin: 0;
        padding-left: 2;
    }

    VolumePortInfo .no-info {
        color: $text-muted;
        text-style: italic;
        padding-left: 2;
    }
    """

    def __init__(
        self,
        service_info: ServiceInfo | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the volume/port info widget.

        Args:
            service_info: Service information
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service_info = service_info

    def compose(self) -> ComposeResult:
        """Compose the volume/port info layout."""
        # Volumes section
        yield Label("Volumes:", classes="section-title")
        if self.service_info and self.service_info.container_id:
            # In a real implementation, we'd fetch this from Docker
            # For now, show placeholder based on service name
            yield Label(
                f"• /config/{self.service_info.name} → /config",
                classes="info-item",
            )
            yield Label("• /data → /data", classes="info-item")
        else:
            yield Label("No volume information available", classes="no-info")

        # Ports section
        yield Label("Ports:", classes="section-title")
        if self.service_info and self.service_info.web_ui_url:
            # Extract port from URL
            port = self.service_info.web_ui_url.split(":")[-1]
            yield Label(f"• {port}:{port}", classes="info-item")
        else:
            yield Label("No port mappings available", classes="no-info")


class ActionButtons(Static):
    """Widget for service action buttons."""

    DEFAULT_CSS = """
    ActionButtons {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    ActionButtons .section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    ActionButtons .button-row {
        height: auto;
        width: 100%;
        align: center middle;
    }

    ActionButtons Button {
        margin: 0 1;
        min-width: 12;
    }
    """

    def __init__(
        self,
        service_name: str,
        is_running: bool = False,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the action buttons widget.

        Args:
            service_name: Name of the service
            is_running: Whether the service is currently running
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service_name = service_name
        self._is_running = is_running

    @property
    def is_running(self) -> bool:
        """Get the running state."""
        return self._is_running

    @is_running.setter
    def is_running(self, value: bool) -> None:
        """Set the running state."""
        self._is_running = value

    def compose(self) -> ComposeResult:
        """Compose the action buttons layout."""
        yield Label("Actions:", classes="section-title")

        with Horizontal(classes="button-row"):
            if self.is_running:
                yield Button("Stop", id="action-stop", variant="error")
                yield Button("Restart", id="action-restart", variant="warning")
            else:
                yield Button("Start", id="action-start", variant="success")

            yield Button("Update", id="action-update", variant="primary")
            yield Button("View Logs", id="action-logs", variant="primary")
            yield Button("Remove", id="action-remove", variant="error")


class LogPreview(Static):
    """Widget for displaying recent container logs."""

    DEFAULT_CSS = """
    LogPreview {
        height: 15;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    LogPreview .section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    LogPreview .log-container {
        height: 1fr;
        width: 100%;
        background: $panel;
        padding: 1;
    }

    LogPreview .log-line {
        color: $text;
        margin: 0;
    }

    LogPreview .no-logs {
        color: $text-muted;
        text-style: italic;
    }

    LogPreview .log-footer {
        height: auto;
        margin-top: 1;
        align: right middle;
    }
    """

    def __init__(
        self,
        service_name: str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the log preview widget.

        Args:
            service_name: Name of the service
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service_name = service_name
        self._log_lines: list[str] = []

    def compose(self) -> ComposeResult:
        """Compose the log preview layout."""
        yield Label("Recent Logs:", classes="section-title")

        with ScrollableContainer(classes="log-container", id="log-container"):
            if self._log_lines:
                for line in self._log_lines[-10:]:  # Show last 10 lines
                    yield Label(line, classes="log-line")
            else:
                yield Label("No logs available", classes="no-logs")

        with Horizontal(classes="log-footer"):
            yield Button("Refresh Logs", id="refresh-logs", variant="default")
            yield Button("View Full Logs", id="view-full-logs", variant="primary")

    def update_logs(self, log_lines: list[str]) -> None:
        """Update the displayed log lines.

        Args:
            log_lines: New log lines to display
        """
        self._log_lines = log_lines

        if self.is_mounted:
            log_container = self.query_one("#log-container", ScrollableContainer)
            log_container.remove_children()

            if self._log_lines:
                for line in self._log_lines[-10:]:
                    log_container.mount(Label(line, classes="log-line"))
            else:
                log_container.mount(Label("No logs available", classes="no-logs"))


class StackManagerScreen(Screen):
    """Stack management screen for detailed service control and monitoring."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    CSS = """
    StackManagerScreen {
        background: $background;
    }

    StackManagerScreen .manager-container {
        height: 100%;
        width: 100%;
        padding: 1;
    }

    StackManagerScreen .service-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
        text-align: center;
    }
    """

    def __init__(
        self,
        controller: AppController,
        service_name: str | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the stack manager screen.

        Args:
            controller: Application controller instance
            service_name: Name of the service to manage (optional)
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.controller = controller
        self.service_name = service_name
        self._service_info: ServiceInfo | None = None

    def compose(self) -> ComposeResult:
        """Compose the stack manager screen layout."""
        yield Header()

        with ScrollableContainer(classes="manager-container"):
            # Service details
            yield ServiceDetails(id="service-details")

            # Volume and port information
            yield VolumePortInfo(id="volume-port-info")

            # Action buttons
            yield ActionButtons(
                service_name=self.service_name,
                is_running=False,
                id="action-buttons",
            )

            # Log preview
            yield LogPreview(service_name=self.service_name, id="log-preview")

        yield Footer()

    async def on_mount(self) -> None:
        """Handle screen mount event."""
        logger.info(f"Stack manager screen mounted for service: {self.service_name}")
        await self._load_service_data()

    async def _load_service_data(self) -> None:
        """Load service information and logs."""
        try:
            # Check if service name is provided
            if not self.service_name:
                logger.error("No service name provided to StackManagerScreen")
                self.notify("No service selected. Please select a service from the dashboard.", severity="error")
                return

            # Get service information
            self._service_info = self.controller.get_service_info(self.service_name)

            # Update service details
            details = self.query_one("#service-details", ServiceDetails)
            details.update_service_info(self._service_info)

            # Update volume/port info
            volume_port = self.query_one("#volume-port-info", VolumePortInfo)
            volume_port.service_info = self._service_info
            volume_port.refresh(layout=True)

            # Update action buttons
            action_buttons = self.query_one("#action-buttons", ActionButtons)
            action_buttons.is_running = self._service_info.is_running
            action_buttons.refresh(layout=True)

            # Load logs if service is running
            if self._service_info.is_running:
                await self._load_logs()

            logger.info(f"Service data loaded for: {self.service_name}")

        except Exception as e:
            logger.error(f"Failed to load service data: {e}", exc_info=True)
            # Escape the error message to prevent markup issues
            error_msg = str(e).replace("[", "\\[").replace("]", "\\]")
            self.notify(f"Error loading service data: {error_msg}", severity="error")

    async def _load_logs(self) -> None:
        """Load recent logs for the service."""
        try:
            log_lines = self.controller.docker_manager.get_service_logs(
                self.service_name, lines=50
            )

            log_preview = self.query_one("#log-preview", LogPreview)
            log_preview.update_logs(log_lines)

            logger.debug(f"Loaded {len(log_lines)} log lines")

        except Exception as e:
            logger.error(f"Failed to load logs: {e}")

    @on(Button.Pressed, "#action-start")
    async def handle_start(self) -> None:
        """Handle start button press."""
        logger.info(f"Starting service: {self.service_name}")
        self.notify(f"Starting {self.service_name}...", severity="information")

        result = self.controller.docker_manager.start_service(self.service_name)
        self._handle_operation_result(result, "start")

        await self._load_service_data()

    @on(Button.Pressed, "#action-stop")
    async def handle_stop(self) -> None:
        """Handle stop button press."""
        # Show confirmation dialog
        confirmed = await self._confirm_action(
            f"Stop {self.service_name}?",
            "This will stop the service container.",
        )

        if not confirmed:
            return

        logger.info(f"Stopping service: {self.service_name}")
        self.notify(f"Stopping {self.service_name}...", severity="warning")

        result = self.controller.docker_manager.stop_service(self.service_name)
        self._handle_operation_result(result, "stop")

        await self._load_service_data()

    @on(Button.Pressed, "#action-restart")
    async def handle_restart(self) -> None:
        """Handle restart button press."""
        logger.info(f"Restarting service: {self.service_name}")
        self.notify(f"Restarting {self.service_name}...", severity="information")

        result = self.controller.docker_manager.restart_service(self.service_name)
        self._handle_operation_result(result, "restart")

        await self._load_service_data()

    @on(Button.Pressed, "#action-update")
    async def handle_update(self) -> None:
        """Handle update button press."""
        # Show confirmation dialog
        confirmed = await self._confirm_action(
            f"Update {self.service_name}?",
            "This will pull the latest image and recreate the container.",
        )

        if not confirmed:
            return

        logger.info(f"Updating service: {self.service_name}")
        self.notify(f"Updating {self.service_name}...", severity="information")

        result = self.controller.docker_manager.update_service(self.service_name)
        self._handle_operation_result(result, "update")

        await self._load_service_data()

    @on(Button.Pressed, "#action-remove")
    async def handle_remove(self) -> None:
        """Handle remove button press."""
        # Show confirmation dialog
        confirmed = await self._confirm_action(
            f"Remove {self.service_name}?",
            "This will permanently remove the container. Configuration and data will be preserved.",
            destructive=True,
        )

        if not confirmed:
            return

        logger.info(f"Removing service: {self.service_name}")
        self.notify(f"Removing {self.service_name}...", severity="error")

        result = self.controller.docker_manager.remove_service(
            self.service_name, remove_volumes=False, force=True
        )
        self._handle_operation_result(result, "remove")

        # Go back to dashboard after removal
        if result.success:
            self.action_back()

    @on(Button.Pressed, "#action-logs")
    def handle_view_logs(self) -> None:
        """Handle view logs button press."""
        logger.info(f"Opening log viewer for: {self.service_name}")
        from arr_stack_manager.screens.log_viewer import LogViewerScreen

        self.app.push_screen(
            LogViewerScreen(
                controller=self.controller,
                service_name=self.service_name,
            )
        )

    @on(Button.Pressed, "#refresh-logs")
    async def handle_refresh_logs(self) -> None:
        """Handle refresh logs button press."""
        logger.info("Refreshing logs")
        await self._load_logs()
        self.notify("Logs refreshed", severity="information")

    @on(Button.Pressed, "#view-full-logs")
    def handle_view_full_logs(self) -> None:
        """Handle view full logs button press."""
        logger.info(f"Opening full log viewer for: {self.service_name}")
        from arr_stack_manager.screens.log_viewer import LogViewerScreen

        self.app.push_screen(
            LogViewerScreen(
                controller=self.controller,
                service_name=self.service_name,
            )
        )

    def _handle_operation_result(self, result: OperationResult, operation: str) -> None:
        """Handle the result of a Docker operation.

        Args:
            result: Operation result
            operation: Name of the operation
        """
        if result.success:
            self.notify(result.message, severity="information")
            logger.info(f"{operation} operation successful: {result.message}")
        else:
            self.notify(f"Failed to {operation}: {result.message}", severity="error")
            logger.error(f"{operation} operation failed: {result.message}")
            if result.details:
                logger.error(f"Details: {result.details}")

    async def _confirm_action(
        self, title: str, message: str, destructive: bool = False
    ) -> bool:
        """Show a confirmation dialog for destructive actions.

        Args:
            title: Dialog title
            message: Dialog message
            destructive: Whether this is a destructive action

        Returns:
            True if confirmed, False otherwise
        """
        # For now, return True (auto-confirm)
        # In a full implementation, this would show a modal dialog
        logger.info(f"Confirmation requested: {title}")
        return True

    def action_back(self) -> None:
        """Navigate back to the dashboard."""
        logger.info("Navigating back to dashboard")
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_refresh(self) -> None:
        """Refresh service data."""
        self.run_worker(self._load_service_data())
