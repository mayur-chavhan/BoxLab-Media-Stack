"""Main Textual application for arr Stack Manager."""

import logging
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Static

from arr_stack_manager.controller import AppController, ScreenType
from arr_stack_manager.screens import (
    ConfigWizardScreen,
    DashboardScreen,
    DeploymentMonitorScreen,
    ServiceSelectorScreen,
    SetupWizardScreen,
    StackManagerScreen,
)

logger = logging.getLogger(__name__)


class HelpScreen(Screen):
    """Help screen showing keyboard shortcuts and usage guide."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]

    CSS = """
    HelpScreen {
        align: center middle;
    }

    HelpScreen .help-container {
        width: 80;
        height: auto;
        max-height: 90%;
        border: solid $primary;
        background: $surface;
        padding: 2;
    }

    HelpScreen .help-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }

    HelpScreen .help-section {
        margin-top: 1;
        margin-bottom: 1;
    }

    HelpScreen .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    HelpScreen .help-item {
        color: $text;
        margin-left: 2;
    }

    HelpScreen .key {
        text-style: bold;
        color: $accent;
    }

    HelpScreen .description {
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the help screen layout."""
        with Static(classes="help-container"):
            yield Label("*arr Stack Manager - Help", classes="help-title")

            with Static(classes="help-section"):
                yield Label("Global Keyboard Shortcuts", classes="section-title")
                yield Label("[key]q[/key] - Quit application", classes="help-item", markup=True)
                yield Label("[key]h[/key] or [key]?[/key] - Show this help screen", classes="help-item", markup=True)
                yield Label("[key]d[/key] - Go to Dashboard", classes="help-item", markup=True)
                yield Label("[key]s[/key] - Go to Service Selector", classes="help-item", markup=True)
                yield Label("[key]c[/key] - Go to Configuration Wizard", classes="help-item", markup=True)
                yield Label("[key]m[/key] - Go to Stack Manager", classes="help-item", markup=True)
                yield Label("[key]r[/key] - Refresh current screen", classes="help-item", markup=True)

            with Static(classes="help-section"):
                yield Label("Dashboard", classes="section-title")
                yield Label("View overall stack status and service health", classes="description")
                yield Label("• Quick actions: Start All, Stop All, Restart All, Update All", classes="help-item")
                yield Label("• Real-time status updates every 5 seconds", classes="help-item")
                yield Label("• Recent activity log", classes="help-item")

            with Static(classes="help-section"):
                yield Label("Service Selector", classes="section-title")
                yield Label("Choose which services to include in your stack", classes="description")
                yield Label("• Use [key]space[/key] or [key]enter[/key] to toggle service selection", classes="help-item", markup=True)
                yield Label("• Services are organized by category", classes="help-item")
                yield Label("• At least one service must be selected", classes="help-item")

            with Static(classes="help-section"):
                yield Label("Configuration Wizard", classes="section-title")
                yield Label("Step-by-step configuration of your stack", classes="description")
                yield Label("• Configure PUID/PGID for file permissions", classes="help-item")
                yield Label("• Set timezone for containers", classes="help-item")
                yield Label("• Configure directory paths", classes="help-item")
                yield Label("• Set service-specific options", classes="help-item")

            with Static(classes="help-section"):
                yield Label("Stack Manager", classes="section-title")
                yield Label("Manage individual services", classes="description")
                yield Label("• View detailed service information", classes="help-item")
                yield Label("• Start, stop, restart, or update services", classes="help-item")
                yield Label("• View container logs", classes="help-item")
                yield Label("• Monitor resource usage", classes="help-item")

            with Static(classes="help-section"):
                yield Label("About", classes="section-title")
                yield Label("arr Stack Manager v0.1.0", classes="help-item")
                yield Label("A TUI for deploying and managing *arr media automation stacks", classes="description")
                yield Label("Following Trash-Guides best practices", classes="description")

            yield Label("\nPress [key]ESC[/key] or [key]q[/key] to close", classes="help-item", markup=True)

    def action_dismiss(self) -> None:
        """Dismiss the help screen."""
        self.app.pop_screen()


class WelcomeScreen(Screen):
    """Welcome screen shown on first run."""

    BINDINGS = [
        ("enter", "continue", "Continue"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    WelcomeScreen {
        align: center middle;
    }

    WelcomeScreen .welcome-container {
        width: 70;
        height: auto;
        border: solid $accent;
        background: $surface;
        padding: 3;
    }

    WelcomeScreen .welcome-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 2;
    }

    WelcomeScreen .welcome-text {
        color: $text;
        text-align: center;
        margin-bottom: 1;
    }

    WelcomeScreen .feature-list {
        margin-top: 2;
        margin-bottom: 2;
    }

    WelcomeScreen .feature-item {
        color: $text;
        margin-left: 4;
        margin-bottom: 1;
    }

    WelcomeScreen .continue-text {
        text-align: center;
        color: $text-muted;
        margin-top: 2;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the welcome screen layout."""
        with Static(classes="welcome-container"):
            yield Label("Welcome to *arr Stack Manager!", classes="welcome-title")
            yield Label(
                "A Terminal User Interface for deploying and managing",
                classes="welcome-text",
            )
            yield Label(
                "Docker-based media automation stacks",
                classes="welcome-text",
            )

            with Static(classes="feature-list"):
                yield Label("Features:", classes="welcome-text")
                yield Label("✓ Easy service selection and configuration", classes="feature-item")
                yield Label("✓ Automatic Trash-Guides best practices", classes="feature-item")
                yield Label("✓ Real-time monitoring and management", classes="feature-item")
                yield Label("✓ Docker Compose generation", classes="feature-item")
                yield Label("✓ Container lifecycle management", classes="feature-item")

            yield Label(
                "\nPress [key]ENTER[/key] to get started or [key]q[/key] to quit",
                classes="continue-text",
                markup=True,
            )

    def action_continue(self) -> None:
        """Continue to the main application."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class StackManagerApp(App):
    """Main Textual application for arr Stack Manager.

    This is the main application class that manages screens, navigation,
    and global application state.
    """

    TITLE = "*arr Stack Manager"
    SUB_TITLE = "Media Automation Stack Management"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("h", "help", "Help", key_display="h/?"),
        Binding("question_mark", "help", "Help", show=False),
        Binding("d", "goto_dashboard", "Dashboard"),
        Binding("s", "goto_services", "Services"),
        Binding("c", "goto_config", "Config"),
        Binding("m", "goto_manager", "Manager"),
        Binding("r", "refresh", "Refresh"),
    ]

    CSS = """
    /* Global theme colors */
    * {
        scrollbar-background: $panel;
        scrollbar-color: $primary;
        scrollbar-color-hover: $accent;
        scrollbar-color-active: $accent;
    }

    /* Color scheme */
    App {
        background: $background;
    }

    /* Header styling */
    Header {
        background: $primary;
        color: $text;
    }

    Header .header--title {
        color: $text;
        text-style: bold;
    }

    Header .header--subtitle {
        color: $text-muted;
    }

    /* Footer styling */
    Footer {
        background: $panel;
    }

    Footer .footer--key {
        background: $primary;
        color: $text;
    }

    Footer .footer--description {
        color: $text-muted;
    }

    /* Button styling */
    Button {
        min-width: 12;
        height: 3;
        border: solid $primary;
    }

    Button:hover {
        background: $primary;
        color: $text;
    }

    Button:focus {
        border: solid $accent;
    }

    Button.-primary {
        background: $primary;
        color: $text;
    }

    Button.-success {
        background: $success;
        color: $text;
    }

    Button.-warning {
        background: $warning;
        color: $text;
    }

    Button.-error {
        background: $error;
        color: $text;
    }

    /* Input styling */
    Input {
        border: solid $primary;
        background: $surface;
    }

    Input:focus {
        border: solid $accent;
    }

    /* Container styling */
    Container {
        background: $background;
    }

    /* Scrollbar styling */
    ScrollableContainer {
        scrollbar-background: $panel;
        scrollbar-color: $primary;
    }

    /* Label styling */
    Label {
        color: $text;
    }

    /* Static widget styling */
    Static {
        background: $background;
    }
    """

    def __init__(
        self,
        config_dir: Path | None = None,
        template_dir: Path | None = None,
        stack_name: str | None = None,
        show_welcome: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the Stack Manager application.

        Args:
            config_dir: Optional custom configuration directory
            template_dir: Optional custom template directory
            stack_name: Optional stack name to load on startup
            show_welcome: Whether to show the welcome screen on startup
            *args: Additional positional arguments for App
            **kwargs: Additional keyword arguments for App
        """
        super().__init__(*args, **kwargs)

        # Initialize controller
        self.controller = AppController(config_dir=config_dir, template_dir=template_dir)
        self.stack_name = stack_name
        self.show_welcome = show_welcome

        # Register navigation callbacks
        self._register_navigation_callbacks()

        logger.info("StackManagerApp initialized")

    def _register_navigation_callbacks(self) -> None:
        """Register navigation callbacks with the controller."""
        self.controller.register_navigation_callback(
            ScreenType.DASHBOARD, self._navigate_to_dashboard
        )
        self.controller.register_navigation_callback(
            ScreenType.SERVICE_SELECTOR, self._navigate_to_service_selector
        )
        self.controller.register_navigation_callback(
            ScreenType.CONFIG_WIZARD, self._navigate_to_config_wizard
        )
        self.controller.register_navigation_callback(
            ScreenType.STACK_MANAGER, self._navigate_to_stack_manager
        )
        self.controller.register_navigation_callback(
            ScreenType.DEPLOYMENT_MONITOR, self._navigate_to_deployment_monitor
        )
        self.controller.register_navigation_callback(
            ScreenType.SETUP_WIZARD, self._navigate_to_setup_wizard
        )

    def on_mount(self) -> None:
        """Handle application mount event."""
        logger.info("Application mounted")

        # Initialize controller
        self.controller.initialize()

        # Check if this is first run
        is_first_run = self.controller.is_first_run()

        # Show welcome screen if requested or if first run
        if self.show_welcome or is_first_run:
            if is_first_run:
                logger.info("First run detected, showing setup wizard")
                self.push_screen(SetupWizardScreen(self.controller))
            else:
                self.push_screen(WelcomeScreen())
        else:
            # Load stack if specified
            if self.stack_name:
                try:
                    self.controller.load_configuration(self.stack_name)
                    logger.info(f"Loaded stack: {self.stack_name}")
                except Exception as e:
                    logger.error(f"Failed to load stack {self.stack_name}: {e}")

            # Navigate to dashboard
            self.push_screen(DashboardScreen(self.controller, self.stack_name))

    def _navigate_to_dashboard(self, **kwargs: Any) -> None:
        """Navigate to the dashboard screen."""
        logger.info("Navigating to dashboard")
        stack_name = kwargs.get("stack_name", self.stack_name)
        self.switch_screen(DashboardScreen(self.controller, stack_name))

    def _navigate_to_service_selector(self, **kwargs: Any) -> None:
        """Navigate to the service selector screen."""
        logger.info("Navigating to service selector")
        self.push_screen(ServiceSelectorScreen(self.controller), self._handle_service_selection)

    def _navigate_to_config_wizard(self, **kwargs: Any) -> None:
        """Navigate to the configuration wizard screen."""
        logger.info("Navigating to configuration wizard")
        configuration = kwargs.get("configuration")
        self.push_screen(ConfigWizardScreen(self.controller, configuration), self._handle_config_wizard_result)

    def _navigate_to_stack_manager(self, **kwargs: Any) -> None:
        """Navigate to the stack manager screen."""
        logger.info("Navigating to stack manager")
        service_name = kwargs.get("service_name")
        self.push_screen(StackManagerScreen(self.controller, service_name))

    def _navigate_to_deployment_monitor(self, **kwargs: Any) -> None:
        """Navigate to the deployment monitor screen."""
        logger.info("Navigating to deployment monitor")
        stack_config = kwargs.get("stack_config")
        output_dir = kwargs.get("output_dir")
        self.push_screen(DeploymentMonitorScreen(self.controller, stack_config, output_dir))

    def _navigate_to_setup_wizard(self, **kwargs: Any) -> None:
        """Navigate to the setup wizard screen."""
        logger.info("Navigating to setup wizard")
        self.push_screen(SetupWizardScreen(self.controller))

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

    def action_quit(self) -> None:
        """Quit the application."""
        logger.info("Application quit requested")
        self.exit()

    def action_help(self) -> None:
        """Show the help screen."""
        logger.info("Help screen requested")
        self.push_screen(HelpScreen())

    def action_goto_dashboard(self) -> None:
        """Navigate to the dashboard."""
        self.controller.navigate_to(ScreenType.DASHBOARD, stack_name=self.stack_name)

    def action_goto_services(self) -> None:
        """Navigate to the service selector."""
        self.controller.navigate_to(ScreenType.SERVICE_SELECTOR)

    def action_goto_config(self) -> None:
        """Navigate to the configuration wizard."""
        # Get currently selected services if available
        selected_services = []
        if self.controller.current_stack:
            selected_services = self.controller.current_stack.configuration.get_selected_services()
        self.controller.navigate_to(ScreenType.CONFIG_WIZARD, selected_services=selected_services)

    def action_goto_manager(self) -> None:
        """Navigate to the stack manager."""
        self.controller.navigate_to(ScreenType.STACK_MANAGER)

    def action_refresh(self) -> None:
        """Refresh the current screen."""
        logger.info("Refresh action triggered")
        # The current screen should handle its own refresh logic
        # This is a placeholder for screens that support refresh
        if hasattr(self.screen, "action_refresh"):
            self.screen.action_refresh()
