"""Setup wizard screen for first-run experience."""

import logging
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from arr_stack_manager.controller import AppController, ScreenType
from arr_stack_manager.utils.system_detection import SystemDetector

logger = logging.getLogger(__name__)


class SetupWizardScreen(Screen):
    """
    Setup wizard screen for first-run experience.

    This screen:
    - Welcomes the user
    - Detects system information
    - Checks Docker availability
    - Creates default configuration directory structure
    - Guides user to service selection
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Cancel"),
    ]

    CSS = """
    SetupWizardScreen {
        align: center middle;
    }

    SetupWizardScreen .setup-container {
        width: 80;
        height: auto;
        max-height: 90%;
        border: solid $accent;
        background: $surface;
        padding: 3;
    }

    SetupWizardScreen .setup-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 2;
        width: 100%;
    }

    SetupWizardScreen .setup-subtitle {
        color: $text-muted;
        text-align: center;
        margin-bottom: 2;
        width: 100%;
    }

    SetupWizardScreen .section {
        margin-top: 1;
        margin-bottom: 2;
        width: 100%;
    }

    SetupWizardScreen .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    SetupWizardScreen .info-item {
        color: $text;
        margin-left: 2;
        margin-bottom: 0;
    }

    SetupWizardScreen .status-ok {
        color: $success;
        text-style: bold;
    }

    SetupWizardScreen .status-warning {
        color: $warning;
        text-style: bold;
    }

    SetupWizardScreen .status-error {
        color: $error;
        text-style: bold;
    }

    SetupWizardScreen .button-container {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    SetupWizardScreen Button {
        margin: 0 1;
    }
    """

    def __init__(self, controller: AppController) -> None:
        """
        Initialize the setup wizard screen.

        Args:
            controller: Application controller instance
        """
        super().__init__()
        self.controller = controller
        self.detector = SystemDetector()

        # Detect system information
        self.puid, self.pgid = self.detector.get_current_user_info()
        self.username = self.detector.get_current_username()
        self.timezone = self.detector.detect_timezone()
        self.docker_available, self.docker_version = self.detector.check_docker_available()
        self.system_info = self.detector.get_system_info()
        self.suggested_path = self.detector.suggest_base_path()

        logger.info("Setup wizard initialized with detected system information")

    def compose(self) -> ComposeResult:
        """Compose the setup wizard layout."""
        yield Header()

        with Container(classes="setup-container"):
            yield Label("Welcome to *arr Stack Manager!", classes="setup-title")
            yield Label(
                "Let's get your system ready for managing media automation stacks",
                classes="setup-subtitle",
            )

            # System Detection Section
            with Vertical(classes="section"):
                yield Label("System Detection", classes="section-title")
                yield Label(
                    f"Operating System: {self.system_info['os']} {self.system_info['os_version']}",
                    classes="info-item",
                )
                yield Label(
                    f"Architecture: {self.system_info['architecture']}",
                    classes="info-item",
                )
                yield Label(
                    f"Python Version: {self.system_info['python_version']}",
                    classes="info-item",
                )

            # User Information Section
            with Vertical(classes="section"):
                yield Label("User Information", classes="section-title")
                yield Label(
                    f"Username: {self.username}",
                    classes="info-item",
                )
                yield Label(
                    f"PUID: {self.puid}",
                    classes="info-item",
                )
                yield Label(
                    f"PGID: {self.pgid}",
                    classes="info-item",
                )
                yield Label(
                    f"Timezone: {self.timezone}",
                    classes="info-item",
                )

            # Docker Status Section
            with Vertical(classes="section"):
                yield Label("Docker Status", classes="section-title")
                if self.docker_available:
                    yield Label(
                        f"✓ Docker is available (version {self.docker_version})",
                        classes="info-item status-ok",
                        markup=False,
                    )
                else:
                    yield Label(
                        "✗ Docker is not available or not running",
                        classes="info-item status-error",
                        markup=False,
                    )
                    yield Label(
                        "  Please install Docker and ensure it's running",
                        classes="info-item status-error",
                        markup=False,
                    )

            # Configuration Directory Section
            with Vertical(classes="section"):
                yield Label("Configuration", classes="section-title")
                config_dir = self.controller.config_repository.get_config_dir()
                yield Label(
                    f"Config Directory: {config_dir}",
                    classes="info-item",
                )
                yield Label(
                    f"Suggested Base Path: {self.suggested_path}",
                    classes="info-item",
                )

            # Next Steps Section
            with Vertical(classes="section"):
                yield Label("Next Steps", classes="section-title")
                yield Label(
                    "1. Select the services you want to deploy",
                    classes="info-item",
                )
                yield Label(
                    "2. Configure paths and settings",
                    classes="info-item",
                )
                yield Label(
                    "3. Generate and deploy your stack",
                    classes="info-item",
                )

            # Buttons
            with Horizontal(classes="button-container"):
                if self.docker_available:
                    yield Button("Get Started", variant="primary", id="continue")
                else:
                    yield Button("Continue Anyway", variant="warning", id="continue")
                yield Button("Exit", variant="default", id="cancel")

        yield Footer()

    @on(Button.Pressed, "#continue")
    def on_continue(self) -> None:
        """Handle continue button press."""
        logger.info("User continuing from setup wizard")

        # Navigate to service selector to begin configuration
        self.controller.navigate_to(ScreenType.SERVICE_SELECTOR)

    @on(Button.Pressed, "#cancel")
    def action_cancel(self) -> None:
        """Handle cancel action."""
        logger.info("User cancelled setup wizard")
        self.app.exit()
