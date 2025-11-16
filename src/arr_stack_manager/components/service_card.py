"""Service card widget for displaying service status and information."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label

from arr_stack_manager.models.service import ServiceInfo, ServiceStatus


class ServiceCard(Container):
    """A card widget displaying service status and quick actions."""

    DEFAULT_CSS = """
    ServiceCard {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin: 1;
        background: $surface;
    }

    ServiceCard.running {
        border: solid $success;
    }

    ServiceCard.stopped {
        border: solid $error;
    }

    ServiceCard.error {
        border: solid $error;
        background: $error 10%;
    }

    ServiceCard .service-header {
        height: auto;
        width: 100%;
    }

    ServiceCard .service-name {
        text-style: bold;
        color: $text;
        width: 1fr;
    }

    ServiceCard .service-status {
        width: auto;
        padding: 0 1;
    }

    ServiceCard .status-running {
        color: $success;
        text-style: bold;
    }

    ServiceCard .status-stopped {
        color: $error;
    }

    ServiceCard .status-error {
        color: $error;
        text-style: bold;
    }

    ServiceCard .service-details {
        height: auto;
        margin-top: 1;
    }

    ServiceCard .detail-row {
        height: auto;
        width: 100%;
    }

    ServiceCard .detail-label {
        color: $text-muted;
        width: 12;
    }

    ServiceCard .detail-value {
        color: $text;
        width: 1fr;
    }

    ServiceCard .service-actions {
        height: auto;
        margin-top: 1;
        align: center middle;
    }

    ServiceCard Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        service_info: ServiceInfo,
        show_actions: bool = True,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the service card.

        Args:
            service_info: Service information to display
            show_actions: Whether to show action buttons
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service_info = service_info
        self.show_actions = show_actions
        self._update_classes()

    def _update_classes(self) -> None:
        """Update CSS classes based on service status."""
        self.remove_class("running", "stopped", "error")
        if self.service_info.status == ServiceStatus.RUNNING:
            self.add_class("running")
        elif self.service_info.status == ServiceStatus.STOPPED:
            self.add_class("stopped")
        elif self.service_info.status == ServiceStatus.ERROR:
            self.add_class("error")

    def compose(self) -> ComposeResult:
        """Compose the service card layout."""
        # Header with name and status
        with Horizontal(classes="service-header"):
            yield Label(self.service_info.name.title(), classes="service-name")
            yield Label(
                self._format_status(),
                classes=f"service-status status-{self.service_info.status.value}",
            )
            # Show update indicator if available
            if self.service_info.update_available:
                yield Label("🔄 Update", classes="service-status status-running")

        # Service details
        with Vertical(classes="service-details"):
            if self.service_info.is_running:
                # CPU and Memory
                if self.service_info.metrics:
                    yield from self._render_metrics()

                # Uptime
                with Horizontal(classes="detail-row"):
                    yield Label("Uptime:", classes="detail-label")
                    yield Label(self.service_info.format_uptime(), classes="detail-value")

                # Web UI URL
                if self.service_info.web_ui_url:
                    with Horizontal(classes="detail-row"):
                        yield Label("Web UI:", classes="detail-label")
                        yield Label(self.service_info.web_ui_url, classes="detail-value")
            else:
                with Horizontal(classes="detail-row"):
                    yield Label("Status:", classes="detail-label")
                    yield Label("Service is not running", classes="detail-value")

            # Show update availability
            if self.service_info.update_available:
                with Horizontal(classes="detail-row"):
                    yield Label("Update:", classes="detail-label")
                    yield Label("New version available", classes="detail-value")

        # Action buttons
        if self.show_actions:
            with Horizontal(classes="service-actions"):
                yield Button("Logs", id=f"logs-{self.service_info.name}", variant="primary")
                yield Button("⚙", id=f"settings-{self.service_info.name}", variant="default")

    def _render_metrics(self) -> ComposeResult:
        """Render resource metrics."""
        if not self.service_info.metrics:
            return

        metrics = self.service_info.metrics

        # CPU usage
        with Horizontal(classes="detail-row"):
            yield Label("CPU:", classes="detail-label")
            yield Label(f"{metrics.cpu_percent:.1f}%", classes="detail-value")

        # Memory usage
        with Horizontal(classes="detail-row"):
            yield Label("Memory:", classes="detail-label")
            yield Label(metrics.format_memory(), classes="detail-value")

    def _format_status(self) -> str:
        """Format status with indicator."""
        status_indicators = {
            ServiceStatus.RUNNING: "● Running",
            ServiceStatus.STOPPED: "○ Stopped",
            ServiceStatus.STARTING: "⟳ Starting",
            ServiceStatus.STOPPING: "⟳ Stopping",
            ServiceStatus.ERROR: "✗ Error",
            ServiceStatus.UNKNOWN: "? Unknown",
        }
        return status_indicators.get(self.service_info.status, "? Unknown")

    def update_service_info(self, service_info: ServiceInfo) -> None:
        """Update the service information and refresh display.

        Args:
            service_info: New service information
        """
        self.service_info = service_info
        self._update_classes()
        self.refresh(layout=True)
