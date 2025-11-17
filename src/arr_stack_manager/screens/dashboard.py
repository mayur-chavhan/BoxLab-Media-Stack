"""Dashboard screen for displaying stack status and service overview."""

import asyncio
import logging
from datetime import datetime

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from arr_stack_manager.components.service_card import ServiceCard
from arr_stack_manager.controller import AppController
from arr_stack_manager.models.service import ServiceInfo, ServiceStatus
from arr_stack_manager.models.stack import StackStatus

logger = logging.getLogger(__name__)


class ActivityLog(Static):
    """Widget for displaying recent activity."""

    DEFAULT_CSS = """
    ActivityLog {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    ActivityLog .log-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    ActivityLog .log-entry {
        color: $text-muted;
        margin: 0;
    }

    ActivityLog .log-empty {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(
        self,
        max_entries: int = 10,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the activity log.

        Args:
            max_entries: Maximum number of log entries to display
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.max_entries = max_entries
        self._entries: list[tuple[datetime, str]] = []

    def compose(self) -> ComposeResult:
        """Compose the activity log layout."""
        yield Label("Recent Activity:", classes="log-title")
        if self._entries:
            for timestamp, message in self._entries[-self.max_entries :]:
                time_str = timestamp.strftime("%H:%M")
                yield Label(f"• {time_str} - {message}", classes="log-entry")
        else:
            yield Label("No recent activity", classes="log-empty")

    def add_entry(self, message: str) -> None:
        """Add a new activity log entry.

        Args:
            message: Activity message to log
        """
        self._entries.append((datetime.now(), message))
        # Keep only the most recent entries
        if len(self._entries) > self.max_entries * 2:
            self._entries = self._entries[-self.max_entries :]
        self.refresh(layout=True)


class StackStatusOverview(Static):
    """Widget for displaying overall stack status."""

    DEFAULT_CSS = """
    StackStatusOverview {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    StackStatusOverview .status-header {
        height: auto;
        width: 100%;
    }

    StackStatusOverview .status-title {
        text-style: bold;
        color: $text;
        width: 1fr;
    }

    StackStatusOverview .status-indicator {
        width: auto;
        text-style: bold;
        padding: 0 2;
    }

    StackStatusOverview .status-running {
        color: $success;
    }

    StackStatusOverview .status-error {
        color: $error;
    }

    StackStatusOverview .status-stopped {
        color: $warning;
    }

    StackStatusOverview .status-details {
        height: auto;
        margin-top: 1;
    }

    StackStatusOverview .detail-item {
        color: $text-muted;
        margin: 0;
    }

    StackStatusOverview .actions {
        height: auto;
        margin-top: 1;
    }

    StackStatusOverview Button {
        margin: 0 1 0 0;
    }
    """

    stack_status: reactive[StackStatus | None] = reactive(None)

    def __init__(
        self,
        stack_status: StackStatus | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the stack status overview.

        Args:
            stack_status: Initial stack status
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.stack_status = stack_status

    def compose(self) -> ComposeResult:
        """Compose the stack status overview layout."""
        with Horizontal(classes="status-header"):
            yield Label("Stack Status:", classes="status-title")
            yield Label(
                self._format_status_indicator(),
                classes=f"status-indicator {self._get_status_class()}",
                id="status-indicator",
            )
            yield Button("Refresh", id="refresh-status", variant="primary")
            yield Button("?", id="help", variant="default")

        with Vertical(classes="status-details", id="status-details"):
            yield from self._render_details()

        with Horizontal(classes="actions"):
            yield Button("Start All", id="start-all", variant="success")
            yield Button("Stop All", id="stop-all", variant="error")
            yield Button("Restart All", id="restart-all", variant="warning")
            yield Button("Update All", id="update-all", variant="primary")

    def _render_details(self) -> ComposeResult:
        """Render status details."""
        if self.stack_status:
            yield Label(
                f"Total Services: {self.stack_status.total_services}",
                classes="detail-item",
            )
            yield Label(
                f"Running: {self.stack_status.running_services}",
                classes="detail-item",
            )
            yield Label(
                f"Stopped: {self.stack_status.stopped_services}",
                classes="detail-item",
            )
            if self.stack_status.error_services > 0:
                yield Label(
                    f"Errors: {self.stack_status.error_services}",
                    classes="detail-item",
                )
        else:
            yield Label("No stack loaded", classes="detail-item")

    def _format_status_indicator(self) -> str:
        """Format the status indicator text."""
        if not self.stack_status:
            return "○ No Stack"

        if self.stack_status.is_healthy:
            return f"● Running ({self.stack_status.running_services}/{self.stack_status.total_services})"
        elif self.stack_status.has_errors:
            return f"✗ Error ({self.stack_status.error_services} errors)"
        elif self.stack_status.stopped_services == self.stack_status.total_services:
            return "○ Stopped"
        else:
            return f"◐ Partial ({self.stack_status.running_services}/{self.stack_status.total_services})"

    def _get_status_class(self) -> str:
        """Get the CSS class for the current status."""
        if not self.stack_status:
            return "status-stopped"

        if self.stack_status.is_healthy:
            return "status-running"
        elif self.stack_status.has_errors:
            return "status-error"
        else:
            return "status-stopped"

    def watch_stack_status(self, new_status: StackStatus | None) -> None:
        """React to stack status changes.

        Args:
            new_status: New stack status
        """
        if self.is_mounted:
            # Update status indicator
            indicator = self.query_one("#status-indicator", Label)
            indicator.update(self._format_status_indicator())
            indicator.remove_class("status-running", "status-error", "status-stopped")
            indicator.add_class(self._get_status_class())

            # Update details
            details_container = self.query_one("#status-details", Vertical)
            details_container.remove_children()
            details_container.mount(*self._render_details())

    def update_status(self, stack_status: StackStatus) -> None:
        """Update the displayed stack status.

        Args:
            stack_status: New stack status
        """
        self.stack_status = stack_status


class DashboardScreen(Screen):
    """Main dashboard screen showing stack overview and service status."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "services", "Services"),
        ("c", "config", "Config"),
        ("h", "help", "Help"),
        ("r", "refresh", "Refresh"),
    ]

    CSS = """
    DashboardScreen {
        background: $background;
    }

    DashboardScreen .dashboard-container {
        height: 100%;
        width: 100%;
        padding: 1;
    }

    DashboardScreen .services-section {
        height: 1fr;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    DashboardScreen .services-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    DashboardScreen .services-list {
        height: 1fr;
        width: 100%;
    }

    DashboardScreen .no-stack-container {
        height: 100%;
        width: 100%;
        align: center middle;
    }

    DashboardScreen .no-services {
        color: $text-muted;
        text-style: italic;
        text-align: center;
        height: auto;
        margin: 1;
    }

    DashboardScreen #create-stack-button {
        margin-top: 2;
        width: 30;
    }

    DashboardScreen .activity-section {
        height: auto;
        width: 100%;
        max-height: 15;
    }
    """

    def __init__(
        self,
        controller: AppController,
        stack_name: str | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the dashboard screen.

        Args:
            controller: Application controller instance
            stack_name: Name of the stack to display (optional)
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.controller = controller
        self.stack_name = stack_name
        self._service_cards: dict[str, ServiceCard] = {}
        self._auto_refresh_enabled = True
        self._refresh_interval = 5  # seconds

    def compose(self) -> ComposeResult:
        """Compose the dashboard screen layout."""
        yield Header()

        with ScrollableContainer(classes="dashboard-container"):
            # Stack status overview
            yield StackStatusOverview(id="stack-overview")

            # Services section
            with Container(classes="services-section"):
                yield Label("Services", classes="services-title")
                with ScrollableContainer(classes="services-list", id="services-list"):
                    yield Label("Loading services...", classes="no-services", id="loading-message")

            # Activity log section
            with Container(classes="activity-section"):
                yield ActivityLog(id="activity-log")

        yield Footer()

    async def on_mount(self) -> None:
        """Handle screen mount event."""
        logger.info("Dashboard screen mounted")

        # Load initial data
        await self._load_dashboard_data()

        # Start auto-refresh
        if self._auto_refresh_enabled:
            self._start_auto_refresh()

    async def _load_dashboard_data(self) -> None:
        """Load dashboard data from controller."""
        try:
            # Get stack status
            if self.stack_name or self.controller.current_stack:
                stack_status = self.controller.get_stack_status(self.stack_name)
                overview = self.query_one("#stack-overview", StackStatusOverview)
                overview.update_status(stack_status)

                # Load service cards
                await self._load_services(stack_status)

                # Log activity
                activity_log = self.query_one("#activity-log", ActivityLog)
                activity_log.add_entry("Dashboard loaded")
            else:
                logger.warning("No stack configured")
                self._show_no_stack_message()

        except Exception as e:
            logger.error(f"Failed to load dashboard data: {e}")
            self._show_error_message(str(e))

    async def _load_services(self, stack_status: StackStatus) -> None:
        """Load and display service cards.

        Args:
            stack_status: Current stack status
        """
        services_list = self.query_one("#services-list", ScrollableContainer)

        # Remove loading message
        try:
            loading_msg = self.query_one("#loading-message")
            loading_msg.remove()
        except Exception:
            pass

        # Get service information
        if self.controller.current_stack:
            enabled_services = self.controller.current_stack.configuration.get_selected_services()

            if not enabled_services:
                services_list.mount(
                    Label("No services configured", classes="no-services", id="no-services")
                )
                return

            # Clear existing cards
            self._service_cards.clear()
            services_list.remove_children()

            # Create service cards
            for service_name in enabled_services:
                service_info = self.controller.get_service_info(service_name)
                card = ServiceCard(service_info, show_actions=True, id=f"card-{service_name}")
                self._service_cards[service_name] = card
                services_list.mount(card)

    def _show_no_stack_message(self) -> None:
        """Show message when no stack is configured."""
        services_list = self.query_one("#services-list", ScrollableContainer)
        services_list.remove_children()
        
        # Create a centered container with message and button
        from textual.containers import Center
        
        container = Vertical(classes="no-stack-container")
        container.mount(
            Label(
                "No stack configured yet.",
                classes="no-services",
                id="no-stack-message",
            )
        )
        container.mount(
            Label(
                "Get started by creating your first stack:",
                classes="no-services",
            )
        )
        container.mount(
            Center(
                Button(
                    "Create New Stack",
                    id="create-stack-button",
                    variant="primary",
                )
            )
        )
        
        services_list.mount(container)

    def _show_error_message(self, error: str) -> None:
        """Show error message.

        Args:
            error: Error message to display
        """
        services_list = self.query_one("#services-list", ScrollableContainer)
        services_list.remove_children()
        services_list.mount(
            Label(f"Error: {error}", classes="no-services", id="error-message")
        )

    @work(exclusive=True)
    async def _start_auto_refresh(self) -> None:
        """Start automatic status refresh."""
        logger.info("Starting auto-refresh")
        while self._auto_refresh_enabled:
            await asyncio.sleep(self._refresh_interval)
            if self._auto_refresh_enabled and self.is_mounted:
                await self._refresh_status()

    async def _refresh_status(self, check_updates: bool = False) -> None:
        """Refresh service status.

        Args:
            check_updates: Whether to check for available updates (slower)
        """
        try:
            if not self.controller.current_stack:
                return

            # Get updated stack status
            stack_status = self.controller.get_stack_status(self.stack_name)

            # Update overview
            overview = self.query_one("#stack-overview", StackStatusOverview)
            overview.update_status(stack_status)

            # Update service cards
            enabled_services = self.controller.current_stack.configuration.get_selected_services()
            for service_name in enabled_services:
                if service_name in self._service_cards:
                    # Get service info with optional update check
                    service_info = self.controller.docker_manager.get_service_status(
                        service_name, check_updates=check_updates
                    )
                    self._service_cards[service_name].update_service_info(service_info)

            logger.debug("Status refreshed successfully")

        except Exception as e:
            logger.error(f"Failed to refresh status: {e}")

    @on(Button.Pressed, "#refresh-status")
    async def handle_refresh_button(self) -> None:
        """Handle refresh button press."""
        activity_log = self.query_one("#activity-log", ActivityLog)
        activity_log.add_entry("Checking for updates...")
        # Check for updates on manual refresh
        await self._refresh_status(check_updates=True)
        activity_log.add_entry("Refresh complete")

    @on(Button.Pressed, "#start-all")
    async def handle_start_all(self) -> None:
        """Handle start all button press."""
        activity_log = self.query_one("#activity-log", ActivityLog)
        activity_log.add_entry("Starting all services...")
        logger.info("Start all services requested")

        if not self.controller.current_stack:
            activity_log.add_entry("Error: No stack configured")
            return

        enabled_services = self.controller.current_stack.configuration.get_selected_services()
        success_count = 0

        for service_name in enabled_services:
            result = self.controller.start_service(service_name)
            if result.success:
                success_count += 1

        activity_log.add_entry(f"Started {success_count}/{len(enabled_services)} services")
        await self._refresh_status()

    @on(Button.Pressed, "#stop-all")
    async def handle_stop_all(self) -> None:
        """Handle stop all button press."""
        activity_log = self.query_one("#activity-log", ActivityLog)
        activity_log.add_entry("Stopping all services...")
        logger.info("Stop all services requested")

        if not self.controller.current_stack:
            activity_log.add_entry("Error: No stack configured")
            return

        enabled_services = self.controller.current_stack.configuration.get_selected_services()
        success_count = 0

        for service_name in enabled_services:
            result = self.controller.stop_service(service_name)
            if result.success:
                success_count += 1

        activity_log.add_entry(f"Stopped {success_count}/{len(enabled_services)} services")
        await self._refresh_status()

    @on(Button.Pressed, "#restart-all")
    async def handle_restart_all(self) -> None:
        """Handle restart all button press."""
        activity_log = self.query_one("#activity-log", ActivityLog)
        activity_log.add_entry("Restarting all services...")
        logger.info("Restart all services requested")

        if not self.controller.current_stack:
            activity_log.add_entry("Error: No stack configured")
            return

        enabled_services = self.controller.current_stack.configuration.get_selected_services()
        success_count = 0

        for service_name in enabled_services:
            result = self.controller.restart_service(service_name)
            if result.success:
                success_count += 1

        activity_log.add_entry(f"Restarted {success_count}/{len(enabled_services)} services")
        await self._refresh_status()

    @on(Button.Pressed, "#update-all")
    async def handle_update_all(self) -> None:
        """Handle update all button press."""
        activity_log = self.query_one("#activity-log", ActivityLog)
        activity_log.add_entry("Updating all services...")
        logger.info("Update all services requested")

        # Perform updates
        results = self.controller.update_all_services()

        # Log results
        success_count = sum(1 for r in results.values() if r.success)
        total_count = len(results)

        if success_count == total_count:
            activity_log.add_entry(f"Successfully updated all {total_count} services")
        else:
            activity_log.add_entry(
                f"Updated {success_count}/{total_count} services (some failed)"
            )

        # Refresh status to show updated services
        await self._refresh_status()

    @on(Button.Pressed, "#help")
    def handle_help(self) -> None:
        """Handle help button press."""
        # TODO: Show help screen
        logger.info("Help requested")

    @on(Button.Pressed, "#create-stack-button")
    def handle_create_stack(self) -> None:
        """Handle create stack button press."""
        logger.info("Create stack button pressed")
        from arr_stack_manager.controller import ScreenType
        self.controller.navigate_to(ScreenType.SERVICE_SELECTOR)

    def action_quit(self) -> None:
        """Quit the application."""
        self._auto_refresh_enabled = False
        self.app.exit()

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
        # Push help screen from the app
        from arr_stack_manager.app import HelpScreen
        self.app.push_screen(HelpScreen())

    def action_refresh(self) -> None:
        """Manually refresh the dashboard."""
        self.run_worker(self._refresh_status())

    async def on_unmount(self) -> None:
        """Handle screen unmount event."""
        logger.info("Dashboard screen unmounting")
        self._auto_refresh_enabled = False

