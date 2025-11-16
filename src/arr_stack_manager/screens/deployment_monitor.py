"""Deployment monitor screen for real-time stack deployment tracking."""

import logging
from datetime import datetime
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from arr_stack_manager.components.progress_bar import EnhancedProgressBar
from arr_stack_manager.controller import AppController
from arr_stack_manager.models.validation import DeploymentEvent

logger = logging.getLogger(__name__)


class DeploymentStage(Static):
    """Widget for displaying a deployment stage with status indicator."""

    DEFAULT_CSS = """
    DeploymentStage {
        height: auto;
        width: 100%;
        margin: 0 0 0 2;
    }

    DeploymentStage .stage-row {
        height: auto;
        width: 100%;
    }

    DeploymentStage .stage-indicator {
        width: 3;
        color: $text-muted;
    }

    DeploymentStage .stage-indicator-pending {
        color: $text-muted;
    }

    DeploymentStage .stage-indicator-active {
        color: $accent;
        text-style: bold;
    }

    DeploymentStage .stage-indicator-complete {
        color: $success;
        text-style: bold;
    }

    DeploymentStage .stage-indicator-error {
        color: $error;
        text-style: bold;
    }

    DeploymentStage .stage-label {
        width: 1fr;
        color: $text;
    }

    DeploymentStage .stage-label-active {
        text-style: bold;
        color: $accent;
    }

    DeploymentStage .stage-label-complete {
        color: $text-muted;
    }

    DeploymentStage .stage-label-error {
        color: $error;
        text-style: bold;
    }
    """

    status: reactive[str] = reactive("pending")

    def __init__(
        self,
        label: str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the deployment stage widget.

        Args:
            label: Stage label text
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.label = label

    def compose(self) -> ComposeResult:
        """Compose the stage layout."""
        with Horizontal(classes="stage-row"):
            yield Label(
                self._get_indicator(),
                classes=f"stage-indicator stage-indicator-{self.status}",
                id="stage-indicator",
            )
            yield Label(
                self.label,
                classes=f"stage-label stage-label-{self.status}",
                id="stage-label",
            )

    def _get_indicator(self) -> str:
        """Get the status indicator symbol."""
        indicators = {
            "pending": "[ ]",
            "active": "[⟳]",
            "complete": "[✓]",
            "error": "[✗]",
        }
        return indicators.get(self.status, "[ ]")

    def watch_status(self, new_status: str) -> None:
        """React to status changes.

        Args:
            new_status: New status value
        """
        if self.is_mounted:
            # Update indicator
            indicator = self.query_one("#stage-indicator", Label)
            indicator.update(self._get_indicator())
            indicator.remove_class(
                "stage-indicator-pending",
                "stage-indicator-active",
                "stage-indicator-complete",
                "stage-indicator-error",
            )
            indicator.add_class(f"stage-indicator-{new_status}")

            # Update label styling
            label = self.query_one("#stage-label", Label)
            label.remove_class(
                "stage-label-active",
                "stage-label-complete",
                "stage-label-error",
            )
            if new_status != "pending":
                label.add_class(f"stage-label-{new_status}")


class DockerOutput(Static):
    """Widget for displaying Docker Compose output in real-time."""

    DEFAULT_CSS = """
    DockerOutput {
        height: 100%;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $panel;
    }

    DockerOutput .output-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    DockerOutput .output-container {
        height: 1fr;
        width: 100%;
        background: $surface;
        padding: 1;
    }

    DockerOutput .output-line {
        color: $text;
        margin: 0;
    }

    DockerOutput .output-line-error {
        color: $error;
    }

    DockerOutput .output-line-warning {
        color: $warning;
    }

    DockerOutput .output-line-success {
        color: $success;
    }

    DockerOutput .no-output {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the Docker output widget.

        Args:
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self._output_lines: list[str] = []
        self._auto_scroll = True

    def compose(self) -> ComposeResult:
        """Compose the output layout."""
        yield Label("Docker Output:", classes="output-title")

        with ScrollableContainer(classes="output-container", id="output-container"):
            yield Label("Waiting for deployment to start...", classes="no-output")

    def add_line(self, line: str) -> None:
        """Add a line to the output.

        Args:
            line: Output line to add
        """
        self._output_lines.append(line)

        if self.is_mounted:
            container = self.query_one("#output-container", ScrollableContainer)

            # Remove "no output" message if present
            if len(self._output_lines) == 1:
                container.remove_children()

            # Determine line styling based on content
            line_class = "output-line"
            lower_line = line.lower()
            if "error" in lower_line or "failed" in lower_line:
                line_class = "output-line-error"
            elif "warning" in lower_line or "warn" in lower_line:
                line_class = "output-line-warning"
            elif "complete" in lower_line or "success" in lower_line or "✓" in line:
                line_class = "output-line-success"

            # Add the new line
            container.mount(Label(line, classes=line_class))

            # Auto-scroll to bottom
            if self._auto_scroll:
                container.scroll_end(animate=False)

    def clear(self) -> None:
        """Clear all output lines."""
        self._output_lines.clear()

        if self.is_mounted:
            container = self.query_one("#output-container", ScrollableContainer)
            container.remove_children()
            container.mount(Label("Waiting for deployment to start...", classes="no-output"))

    def set_auto_scroll(self, enabled: bool) -> None:
        """Enable or disable auto-scrolling.

        Args:
            enabled: Whether to enable auto-scrolling
        """
        self._auto_scroll = enabled


class DeploymentMonitorScreen(Screen):
    """Deployment monitor screen for real-time stack deployment tracking."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    DeploymentMonitorScreen {
        background: $background;
    }

    DeploymentMonitorScreen .monitor-container {
        height: 100%;
        width: 100%;
        padding: 1;
    }

    DeploymentMonitorScreen .monitor-title {
        text-style: bold;
        color: $text;
        text-align: center;
        margin-bottom: 1;
    }

    DeploymentMonitorScreen .progress-section {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    DeploymentMonitorScreen .section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    DeploymentMonitorScreen .stages-container {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }

    DeploymentMonitorScreen .output-section {
        height: 1fr;
        width: 100%;
        margin-bottom: 1;
    }

    DeploymentMonitorScreen .footer-info {
        height: auto;
        width: 100%;
        align: center middle;
    }

    DeploymentMonitorScreen .elapsed-time {
        color: $text-muted;
        margin-right: 2;
    }

    DeploymentMonitorScreen .button-container {
        height: auto;
        width: 100%;
        align: center middle;
        margin-top: 1;
    }

    DeploymentMonitorScreen Button {
        margin: 0 1;
    }

    DeploymentMonitorScreen .success-message {
        color: $success;
        text-style: bold;
        text-align: center;
        margin: 1;
    }

    DeploymentMonitorScreen .error-message {
        color: $error;
        text-style: bold;
        text-align: center;
        margin: 1;
    }
    """

    def __init__(
        self,
        controller: AppController,
        compose_path: str | Path,
        stack_name: str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the deployment monitor screen.

        Args:
            controller: Application controller instance
            compose_path: Path to docker-compose.yml file
            stack_name: Name of the stack being deployed
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.controller = controller
        self.compose_path = Path(compose_path)
        self.stack_name = stack_name
        self._start_time: datetime | None = None
        self._is_complete = False
        self._is_error = False
        self._can_cancel = True

    def compose(self) -> ComposeResult:
        """Compose the deployment monitor screen layout."""
        yield Header()

        with ScrollableContainer(classes="monitor-container"):
            yield Label(
                f"Deploying Stack: {self.stack_name}",
                classes="monitor-title",
            )

            # Progress section
            with Vertical(classes="progress-section"):
                yield Label("Progress:", classes="section-title")

                # Deployment stages
                with Vertical(classes="stages-container", id="stages-container"):
                    yield DeploymentStage("Validating configuration", id="stage-validation")
                    yield DeploymentStage("Creating directories", id="stage-directories")
                    yield DeploymentStage("Generating docker-compose.yml", id="stage-compose")
                    yield DeploymentStage("Generating .env file", id="stage-env")
                    yield DeploymentStage("Pulling container images", id="stage-pull")
                    yield DeploymentStage("Starting services", id="stage-start")
                    yield DeploymentStage("Health checks", id="stage-health")

                # Overall progress bar
                yield EnhancedProgressBar(
                    title="Overall Progress",
                    total=100.0,
                    show_percentage=True,
                    id="overall-progress",
                )

            # Docker output section
            with Vertical(classes="output-section"):
                yield DockerOutput(id="docker-output")

            # Footer with elapsed time and buttons
            with Horizontal(classes="footer-info"):
                yield Label("Elapsed: 00:00:00", classes="elapsed-time", id="elapsed-time")

            with Horizontal(classes="button-container", id="button-container"):
                yield Button("Cancel", id="cancel-button", variant="error")

        yield Footer()

    async def on_mount(self) -> None:
        """Handle screen mount event."""
        logger.info(f"Deployment monitor screen mounted for stack: {self.stack_name}")
        self._start_time = datetime.now()

        # Start the deployment worker
        self.run_worker(self._deploy_stack(), exclusive=True, name="deployment")

        # Start the elapsed time updater
        self.set_interval(1.0, self._update_elapsed_time)

    async def _deploy_stack(self) -> None:
        """Deploy the stack and track progress."""
        try:
            logger.info(f"Starting deployment of {self.compose_path}")

            # Stream deployment events
            for event in self.controller.docker_manager.deploy_stack(self.compose_path):
                await self._handle_deployment_event(event)

            # Deployment completed successfully
            self._is_complete = True
            self._can_cancel = False
            await self._show_success()

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            self._is_error = True
            self._can_cancel = False
            await self._show_error(str(e))

    async def _handle_deployment_event(self, event: DeploymentEvent) -> None:
        """Handle a deployment event.

        Args:
            event: Deployment event to process
        """
        logger.debug(f"Deployment event: {event.stage} - {event.message}")

        # Update stage status
        stage_map = {
            "validation": "stage-validation",
            "directories": "stage-directories",
            "compose": "stage-compose",
            "env": "stage-env",
            "pull": "stage-pull",
            "start": "stage-start",
            "health_check": "stage-health",
            "complete": None,
            "error": None,
        }

        # Mark previous stages as complete
        if event.stage in stage_map and stage_map[event.stage]:
            await self._update_stage_status(event.stage, "active")

            # Mark earlier stages as complete
            stages = [
                "validation",
                "directories",
                "compose",
                "env",
                "pull",
                "start",
                "health_check",
            ]
            current_index = stages.index(event.stage) if event.stage in stages else -1
            for i, stage in enumerate(stages):
                if i < current_index and stage_map[stage]:
                    stage_widget = self.query_one(f"#{stage_map[stage]}", DeploymentStage)
                    if stage_widget.status != "complete":
                        stage_widget.status = "complete"

        # Update overall progress
        progress_bar = self.query_one("#overall-progress", EnhancedProgressBar)
        progress_bar.update_progress(
            progress=event.progress * 100,
            status=event.message,
        )

        # Add output line
        docker_output = self.query_one("#docker-output", DockerOutput)
        timestamp = event.timestamp.strftime("%H:%M:%S")
        docker_output.add_line(f"[{timestamp}] {event.message}")

        # Mark stage as complete if moving to next stage
        if event.progress >= 1.0 or event.stage == "complete":
            for stage_id in stage_map.values():
                if stage_id:
                    stage_widget = self.query_one(f"#{stage_id}", DeploymentStage)
                    if stage_widget.status == "active":
                        stage_widget.status = "complete"

    async def _update_stage_status(self, stage: str, status: str) -> None:
        """Update the status of a deployment stage.

        Args:
            stage: Stage identifier
            status: New status (pending, active, complete, error)
        """
        stage_map = {
            "validation": "stage-validation",
            "directories": "stage-directories",
            "compose": "stage-compose",
            "env": "stage-env",
            "pull": "stage-pull",
            "start": "stage-start",
            "health_check": "stage-health",
        }

        if stage in stage_map:
            stage_widget = self.query_one(f"#{stage_map[stage]}", DeploymentStage)
            stage_widget.status = status

    async def _show_success(self) -> None:
        """Show deployment success message."""
        logger.info("Deployment completed successfully")

        # Mark all stages as complete
        for stage_id in [
            "stage-validation",
            "stage-directories",
            "stage-compose",
            "stage-env",
            "stage-pull",
            "stage-start",
            "stage-health",
        ]:
            stage_widget = self.query_one(f"#{stage_id}", DeploymentStage)
            stage_widget.status = "complete"

        # Update progress bar
        progress_bar = self.query_one("#overall-progress", EnhancedProgressBar)
        progress_bar.set_complete("Deployment completed successfully")

        # Add success message
        docker_output = self.query_one("#docker-output", DockerOutput)
        docker_output.add_line("")
        docker_output.add_line("✓ Stack deployment completed successfully!")
        docker_output.add_line(f"✓ All services for '{self.stack_name}' are now running")

        # Update buttons
        button_container = self.query_one("#button-container", Horizontal)
        button_container.remove_children()
        button_container.mount(Button("View Dashboard", id="view-dashboard", variant="success"))
        button_container.mount(Button("Close", id="close-button", variant="default"))

        self.notify("Deployment completed successfully!", severity="information")

    async def _show_error(self, error_message: str) -> None:
        """Show deployment error message.

        Args:
            error_message: Error message to display
        """
        logger.error(f"Deployment error: {error_message}")

        # Mark current stage as error
        for stage_id in [
            "stage-validation",
            "stage-directories",
            "stage-compose",
            "stage-env",
            "stage-pull",
            "stage-start",
            "stage-health",
        ]:
            stage_widget = self.query_one(f"#{stage_id}", DeploymentStage)
            if stage_widget.status == "active":
                stage_widget.status = "error"
                break

        # Update progress bar
        progress_bar = self.query_one("#overall-progress", EnhancedProgressBar)
        progress_bar.set_error("Deployment failed")

        # Add error message
        docker_output = self.query_one("#docker-output", DockerOutput)
        docker_output.add_line("")
        docker_output.add_line(f"✗ Deployment failed: {error_message}")
        docker_output.add_line("")
        docker_output.add_line("Please check the output above for details.")

        # Update buttons
        button_container = self.query_one("#button-container", Horizontal)
        button_container.remove_children()
        button_container.mount(Button("Retry", id="retry-button", variant="warning"))
        button_container.mount(Button("Close", id="close-button", variant="default"))

        self.notify(f"Deployment failed: {error_message}", severity="error")

    def _update_elapsed_time(self) -> None:
        """Update the elapsed time display."""
        if not self._start_time:
            return

        elapsed = datetime.now() - self._start_time
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        seconds = int(elapsed.total_seconds() % 60)

        time_label = self.query_one("#elapsed-time", Label)
        time_label.update(f"Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}")

    @on(Button.Pressed, "#cancel-button")
    async def handle_cancel(self) -> None:
        """Handle cancel button press."""
        if not self._can_cancel:
            return

        logger.info("User requested deployment cancellation")

        # Show confirmation
        confirmed = await self._confirm_cancel()
        if not confirmed:
            return

        # Cancel all workers
        self.workers.cancel_all()
        logger.info("Deployment workers cancelled")

        # Add cancellation message
        docker_output = self.query_one("#docker-output", DockerOutput)
        docker_output.add_line("")
        docker_output.add_line("⚠ Deployment cancelled by user")

        self.notify("Deployment cancelled", severity="warning")
        self.action_back()

    @on(Button.Pressed, "#view-dashboard")
    def handle_view_dashboard(self) -> None:
        """Handle view dashboard button press."""
        logger.info("Navigating to dashboard after successful deployment")
        
        # Import here to avoid circular dependency
        from arr_stack_manager.controller import ScreenType
        
        # Pop this screen and navigate to dashboard
        self.app.pop_screen()
        
        # Navigate to dashboard through controller
        self.controller.navigate_to(ScreenType.DASHBOARD, stack_name=self.stack_name)

    @on(Button.Pressed, "#retry-button")
    async def handle_retry(self) -> None:
        """Handle retry button press."""
        logger.info("Retrying deployment")

        # Reset state
        self._is_complete = False
        self._is_error = False
        self._can_cancel = True
        self._start_time = datetime.now()

        # Clear output
        docker_output = self.query_one("#docker-output", DockerOutput)
        docker_output.clear()

        # Reset progress
        progress_bar = self.query_one("#overall-progress", EnhancedProgressBar)
        progress_bar.reset()

        # Reset stages
        for stage_id in [
            "stage-validation",
            "stage-directories",
            "stage-compose",
            "stage-env",
            "stage-pull",
            "stage-start",
            "stage-health",
        ]:
            stage_widget = self.query_one(f"#{stage_id}", DeploymentStage)
            stage_widget.status = "pending"

        # Update buttons
        button_container = self.query_one("#button-container", Horizontal)
        button_container.remove_children()
        button_container.mount(Button("Cancel", id="cancel-button", variant="error"))

        # Start new deployment
        self.run_worker(self._deploy_stack(), exclusive=True, name="deployment")

    @on(Button.Pressed, "#close-button")
    def handle_close(self) -> None:
        """Handle close button press."""
        logger.info("Closing deployment monitor")
        self.action_back()

    async def _confirm_cancel(self) -> bool:
        """Show confirmation dialog for cancellation.

        Returns:
            True if confirmed, False otherwise
        """
        # For now, return True (auto-confirm)
        # In a full implementation, this would show a modal dialog
        logger.info("Cancellation confirmed")
        return True

    def action_cancel(self) -> None:
        """Handle cancel action."""
        if self._can_cancel:
            self.run_worker(self.handle_cancel())

    def action_back(self) -> None:
        """Navigate back to previous screen."""
        logger.info("Navigating back from deployment monitor")
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
