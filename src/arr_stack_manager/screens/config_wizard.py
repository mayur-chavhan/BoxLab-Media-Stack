"""Configuration wizard screen for guided stack setup."""

import logging
import os
import subprocess
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.validation import Integer, ValidationResult, Validator
from textual.widgets import Button, Footer, Header, Input, Label, Static

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.models.validation import ValidationResult
from arr_stack_manager.utils.services import SUPPORTED_SERVICES, get_service_metadata

logger = logging.getLogger(__name__)


class WizardStep(IntEnum):
    """Wizard step enumeration."""

    SERVICE_CONFIRMATION = 1
    BASE_CONFIGURATION = 2
    PATH_CONFIGURATION = 3
    SERVICE_SPECIFIC_CONFIGURATION = 4


class PositiveIntegerValidator(Validator):
    """Validator for positive integers."""

    def validate(self, value: str) -> ValidationResult:
        """Validate that the value is a positive integer.

        Args:
            value: The value to validate

        Returns:
            ValidationResult indicating if the value is valid
        """
        if not value:
            return self.failure("Value is required")

        try:
            int_value = int(value)
            if int_value < 0:
                return self.failure("Value must be positive")
            return self.success()
        except ValueError:
            return self.failure("Value must be a valid integer")


class TimezoneValidator(Validator):
    """Validator for timezone strings."""

    def validate(self, value: str) -> ValidationResult:
        """Validate that the value is a non-empty timezone string.

        Args:
            value: The value to validate

        Returns:
            ValidationResult indicating if the value is valid
        """
        if not value or not value.strip():
            return self.failure("Timezone is required")

        # Basic validation - just check it's not empty
        # More sophisticated validation could check against zoneinfo
        return self.success()


class StepIndicator(Static):
    """Widget for displaying wizard step progress."""

    DEFAULT_CSS = """
    StepIndicator {
        height: auto;
        width: 100%;
        padding: 1;
        background: $surface;
        border: solid $primary;
        margin-bottom: 1;
    }

    StepIndicator .step-title {
        text-style: bold;
        color: $text;
        text-align: center;
    }

    StepIndicator .step-progress {
        color: $text-muted;
        text-align: center;
        margin-top: 0;
    }
    """

    def __init__(
        self,
        current_step: int,
        total_steps: int,
        step_title: str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the step indicator.

        Args:
            current_step: Current step number (1-indexed)
            total_steps: Total number of steps
            step_title: Title of the current step
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.current_step = current_step
        self.total_steps = total_steps
        self.step_title = step_title

    def compose(self) -> ComposeResult:
        """Compose the step indicator layout."""
        yield Label(f"Step {self.current_step} of {self.total_steps}: {self.step_title}", classes="step-title")
        
        # Create progress bar
        progress_chars = []
        for i in range(1, self.total_steps + 1):
            if i < self.current_step:
                progress_chars.append("━")
            elif i == self.current_step:
                progress_chars.append("━")
            else:
                progress_chars.append("━")
        
        progress_bar = "".join(progress_chars)
        yield Label(progress_bar, classes="step-progress")

    def update_step(self, current_step: int, step_title: str) -> None:
        """Update the step indicator.

        Args:
            current_step: New current step number
            step_title: New step title
        """
        self.current_step = current_step
        self.step_title = step_title
        
        # Update the label text
        try:
            title_label = self.query_one(".step-title", Label)
            title_label.update(f"Step {self.current_step} of {self.total_steps}: {self.step_title}")
        except Exception:
            # If query fails, do a full refresh
            self.refresh(layout=True)


class ServiceConfirmationStep(Static):
    """Widget for step 1: Service selection confirmation."""

    DEFAULT_CSS = """
    ServiceConfirmationStep {
        height: auto;
        width: 100%;
        padding: 1;
    }

    ServiceConfirmationStep .section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    ServiceConfirmationStep .service-list {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    ServiceConfirmationStep .service-item {
        color: $text;
        margin: 0;
    }

    ServiceConfirmationStep .info-text {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(
        self,
        selected_services: list[str],
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the service confirmation step.

        Args:
            selected_services: List of selected service names
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.selected_services = selected_services

    def compose(self) -> ComposeResult:
        """Compose the service confirmation step layout."""
        yield Label("Selected Services", classes="section-title")
        
        with Vertical(classes="service-list"):
            if self.selected_services:
                for service in self.selected_services:
                    yield Label(f"• {service.title()}", classes="service-item")
            else:
                yield Label("No services selected", classes="info-text")
        
        yield Label(
            "The following steps will configure these services for deployment.",
            classes="info-text",
        )


class BaseConfigurationStep(Static):
    """Widget for step 2: Base configuration (PUID, PGID, timezone)."""

    DEFAULT_CSS = """
    BaseConfigurationStep {
        height: auto;
        width: 100%;
        padding: 1;
    }

    BaseConfigurationStep .section {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    BaseConfigurationStep .section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    BaseConfigurationStep .form-row {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }

    BaseConfigurationStep .form-label {
        width: 20;
        color: $text;
        padding: 1 0;
    }

    BaseConfigurationStep .form-input {
        width: 1fr;
    }

    BaseConfigurationStep .info-text {
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
    }

    BaseConfigurationStep .detect-button {
        margin-left: 1;
    }

    BaseConfigurationStep .validation-error {
        color: $error;
        text-style: italic;
        margin-top: 0;
    }

    BaseConfigurationStep .env-indicator {
        color: $success;
        text-style: bold;
    }
    """

    def __init__(
        self,
        puid: int = 1000,
        pgid: int = 1000,
        timezone: str = "UTC",
        from_env: dict[str, bool] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the base configuration step.

        Args:
            puid: Initial PUID value
            pgid: Initial PGID value
            timezone: Initial timezone value
            from_env: Dictionary indicating which values come from environment
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.puid = puid
        self.pgid = pgid
        self.timezone = timezone
        self.from_env = from_env or {}

    def compose(self) -> ComposeResult:
        """Compose the base configuration step layout."""
        # User & Permissions section
        with Vertical(classes="section"):
            yield Label("User & Permissions", classes="section-title")
            
            # PUID input
            with Horizontal(classes="form-row"):
                puid_label = "PUID (User ID):"
                if self.from_env.get("puid"):
                    puid_label += " 🌍"  # Environment indicator
                yield Label(puid_label, classes="form-label")
                yield Input(
                    value=str(self.puid),
                    placeholder="1000",
                    validators=[PositiveIntegerValidator()],
                    classes="form-input",
                    id="puid-input",
                )
            
            # PGID input
            with Horizontal(classes="form-row"):
                pgid_label = "PGID (Group ID):"
                if self.from_env.get("pgid"):
                    pgid_label += " 🌍"  # Environment indicator
                yield Label(pgid_label, classes="form-label")
                yield Input(
                    value=str(self.pgid),
                    placeholder="1000",
                    validators=[PositiveIntegerValidator()],
                    classes="form-input",
                    id="pgid-input",
                )
            
            # Info text showing detected user and environment status
            detected_user = self._detect_current_user()
            info_parts = [f"ℹ Current user: {detected_user}"]
            if self.from_env.get("puid") or self.from_env.get("pgid"):
                info_parts.append("🌍 Values from environment file")
            yield Label(
                " | ".join(info_parts),
                classes="info-text",
                id="user-info",
            )

        # Timezone section
        with Vertical(classes="section"):
            yield Label("Timezone", classes="section-title")
            
            with Horizontal(classes="form-row"):
                tz_label = "Timezone:"
                if self.from_env.get("timezone"):
                    tz_label += " 🌍"  # Environment indicator
                yield Label(tz_label, classes="form-label")
                yield Input(
                    value=self.timezone,
                    placeholder="America/New_York",
                    validators=[TimezoneValidator()],
                    classes="form-input",
                    id="timezone-input",
                )
                yield Button("Detect", id="detect-timezone", variant="primary", classes="detect-button")
            
            # Info text showing detected timezone and environment status
            detected_tz = self._detect_timezone()
            info_parts = [f"ℹ Detected: {detected_tz}"]
            if self.from_env.get("timezone"):
                info_parts.append("🌍 Value from environment file")
            yield Label(
                " | ".join(info_parts),
                classes="info-text",
                id="timezone-info",
            )

    def _detect_current_user(self) -> str:
        """Detect current user and their PUID/PGID.

        Returns:
            String describing the current user
        """
        try:
            uid = os.getuid()
            gid = os.getgid()
            username = os.getenv("USER", "unknown")
            return f"{username} ({uid}:{gid})"
        except Exception as e:
            logger.warning(f"Failed to detect current user: {e}")
            return "unknown"

    def _detect_timezone(self) -> str:
        """Detect system timezone.

        Returns:
            Detected timezone string
        """
        try:
            # Try to read from /etc/timezone (Debian/Ubuntu)
            try:
                with open("/etc/timezone", "r") as f:
                    tz = f.read().strip()
                    if tz:
                        return tz
            except FileNotFoundError:
                pass

            # Try to use timedatectl (systemd)
            try:
                result = subprocess.run(
                    ["timedatectl", "show", "-p", "Timezone", "--value"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0:
                    tz = result.stdout.strip()
                    if tz:
                        return tz
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            # Fallback: try to get from environment
            tz = os.getenv("TZ")
            if tz:
                return tz

            # Last resort: use UTC
            return "UTC"

        except Exception as e:
            logger.warning(f"Failed to detect timezone: {e}")
            return "UTC"

    def get_values(self) -> dict[str, Any]:
        """Get the current form values.

        Returns:
            Dictionary with puid, pgid, and timezone values
        """
        try:
            puid_input = self.query_one("#puid-input", Input)
            pgid_input = self.query_one("#pgid-input", Input)
            timezone_input = self.query_one("#timezone-input", Input)

            return {
                "puid": int(puid_input.value) if puid_input.value else 1000,
                "pgid": int(pgid_input.value) if pgid_input.value else 1000,
                "timezone": timezone_input.value or "UTC",
            }
        except Exception as e:
            logger.error(f"Failed to get form values: {e}")
            return {
                "puid": self.puid,
                "pgid": self.pgid,
                "timezone": self.timezone,
            }


class PathConfigurationStep(Static):
    """Widget for step 3: Directory structure configuration."""

    DEFAULT_CSS = """
    PathConfigurationStep {
        height: auto;
        width: 100%;
        padding: 1;
    }

    PathConfigurationStep .section {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    PathConfigurationStep .section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    PathConfigurationStep .form-row {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }

    PathConfigurationStep .form-label {
        width: 20;
        color: $text;
        padding: 1 0;
    }

    PathConfigurationStep .form-input {
        width: 1fr;
    }

    PathConfigurationStep .browse-button {
        margin-left: 1;
    }

    PathConfigurationStep .info-text {
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
    }

    PathConfigurationStep .tree-view {
        height: auto;
        width: 100%;
        padding: 1;
        background: $surface-darken-1;
        border: solid $primary-darken-1;
        margin-top: 1;
    }

    PathConfigurationStep .tree-item {
        color: $text;
        margin: 0;
    }

    PathConfigurationStep .tree-indent {
        color: $text-muted;
    }

    PathConfigurationStep .validation-status {
        height: auto;
        width: 100%;
        padding: 1;
        margin-top: 1;
    }

    PathConfigurationStep .status-item {
        color: $text;
        margin: 0 0 0 1;
    }

    PathConfigurationStep .status-success {
        color: $success;
    }

    PathConfigurationStep .status-error {
        color: $error;
    }

    PathConfigurationStep .status-warning {
        color: $warning;
    }
    """

    def __init__(
        self,
        base_path: str = "",
        from_env: bool = False,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the path configuration step.

        Args:
            base_path: Initial base path value
            from_env: Whether the base path comes from environment
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.base_path = base_path or self._detect_default_path()
        self.from_env = from_env
        self._validation_result: ValidationResult | None = None

    def compose(self) -> ComposeResult:
        """Compose the path configuration step layout."""
        # Base path section
        with Vertical(classes="section"):
            yield Label("Directory Structure", classes="section-title")
            
            # Base path input
            with Horizontal(classes="form-row"):
                base_path_label = "Base Path:"
                if self.from_env:
                    base_path_label += " 🌍"  # Environment indicator
                yield Label(base_path_label, classes="form-label")
                yield Input(
                    value=self.base_path,
                    placeholder="/mnt/storage",
                    classes="form-input",
                    id="base-path-input",
                )
                yield Button("Browse", id="browse-button", variant="default", classes="browse-button")
            
            info_parts = ["All configuration and data will be stored under this directory."]
            if self.from_env:
                info_parts.append("🌍 Value from environment file")
            yield Label(
                " ".join(info_parts),
                classes="info-text",
            )

            # Directory structure preview
            yield Label("Generated Structure:", classes="section-title")
            with Vertical(classes="tree-view", id="tree-view"):
                yield from self._render_directory_tree()

        # Validation status section
        with Vertical(classes="section", id="validation-section"):
            yield Label("Validation Status", classes="section-title")
            with Vertical(classes="validation-status", id="validation-status"):
                yield Label("Enter a base path to validate", classes="info-text")

    def _detect_default_path(self) -> str:
        """Detect a sensible default base path.

        Returns:
            Default base path string
        """
        # Try common locations
        common_paths = [
            "/mnt/storage",
            "/data",
            "/media",
            os.path.expanduser("~/arr-stack"),
        ]

        for path in common_paths:
            if os.path.exists(path) and os.path.isdir(path):
                return path

        # Fallback to user's home directory
        return os.path.expanduser("~/arr-stack")

    def _render_directory_tree(self) -> ComposeResult:
        """Render the directory structure tree.

        Yields:
            Labels representing the directory tree
        """
        base = self.base_path or "/path/to/base"
        
        yield Label(f"{base}/", classes="tree-item")
        yield Label("├── config/          (Application configurations)", classes="tree-item")
        yield Label("│   ├── sonarr/", classes="tree-item")
        yield Label("│   ├── radarr/", classes="tree-item")
        yield Label("│   ├── prowlarr/", classes="tree-item")
        yield Label("│   └── ...", classes="tree-item")
        yield Label("└── data/            (Media and downloads)", classes="tree-item")
        yield Label("    ├── media/       (Final media location)", classes="tree-item")
        yield Label("    │   ├── tv/", classes="tree-item")
        yield Label("    │   └── movies/", classes="tree-item")
        yield Label("    └── downloads/   (Download client output)", classes="tree-item")

    def update_directory_tree(self, base_path: str) -> None:
        """Update the directory tree preview with a new base path.

        Args:
            base_path: New base path to display
        """
        self.base_path = base_path
        
        try:
            tree_view = self.query_one("#tree-view", Vertical)
            tree_view.remove_children()
            tree_view.mount(*self._render_directory_tree())
        except Exception as e:
            logger.error(f"Failed to update directory tree: {e}")

    def validate_path(self) -> ValidationResult:
        """Validate the current base path.

        Returns:
            ValidationResult with validation status
        """
        from arr_stack_manager.core.validator import ConfigurationValidator
        
        validator = ConfigurationValidator()
        
        # Create a PathConfig for validation
        path_config = PathConfig(base_path=self.base_path)
        
        # Validate the paths
        result = validator.validate_paths(path_config)
        self._validation_result = result
        
        return result

    def update_validation_status(self, result: ValidationResult) -> None:
        """Update the validation status display.

        Args:
            result: ValidationResult to display
        """
        self._validation_result = result
        
        try:
            validation_status = self.query_one("#validation-status", Vertical)
            validation_status.remove_children()
            
            if result.valid and not result.errors:
                # Show success status
                validation_status.mount(
                    Label("✓ Path exists and is writable", classes="status-item status-success")
                )
                validation_status.mount(
                    Label("✓ Path is readable", classes="status-item status-success")
                )
            else:
                # Show errors
                for error in result.errors:
                    # Split error message to show only the first line
                    error_lines = error.split("\n")
                    validation_status.mount(
                        Label(f"✗ {error_lines[0]}", classes="status-item status-error")
                    )
            
            # Show warnings
            for warning in result.warnings:
                # Split warning message to show only the first line
                warning_lines = warning.split("\n")
                validation_status.mount(
                    Label(f"⚠ {warning_lines[0]}", classes="status-item status-warning")
                )
            
            # If no errors but path doesn't exist, show info about creation
            if not result.errors and result.warnings:
                validation_status.mount(
                    Label(
                        "ℹ Directories will be created during deployment",
                        classes="info-text"
                    )
                )
                
        except Exception as e:
            logger.error(f"Failed to update validation status: {e}")

    def get_values(self) -> dict[str, Any]:
        """Get the current form values.

        Returns:
            Dictionary with base_path value
        """
        try:
            base_path_input = self.query_one("#base-path-input", Input)
            return {
                "base_path": base_path_input.value or self.base_path,
            }
        except Exception as e:
            logger.error(f"Failed to get form values: {e}")
            return {
                "base_path": self.base_path,
            }


class ServiceSpecificConfigurationStep(Static):
    """Widget for step 4: Service-specific configuration."""

    DEFAULT_CSS = """
    ServiceSpecificConfigurationStep {
        height: auto;
        width: 100%;
        padding: 1;
    }

    ServiceSpecificConfigurationStep .section {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    ServiceSpecificConfigurationStep .section-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    ServiceSpecificConfigurationStep .service-section {
        height: auto;
        width: 100%;
        border: solid $primary-darken-1;
        padding: 1;
        background: $surface-darken-1;
        margin-bottom: 1;
    }

    ServiceSpecificConfigurationStep .service-name {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    ServiceSpecificConfigurationStep .form-row {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }

    ServiceSpecificConfigurationStep .form-label {
        width: 25;
        color: $text;
        padding: 1 0;
    }

    ServiceSpecificConfigurationStep .form-input {
        width: 1fr;
    }

    ServiceSpecificConfigurationStep .info-text {
        color: $text-muted;
        text-style: italic;
        margin-top: 0;
        margin-bottom: 1;
    }

    ServiceSpecificConfigurationStep .summary-section {
        height: auto;
        width: 100%;
        border: solid $success;
        padding: 1;
        background: $surface;
        margin-top: 1;
    }

    ServiceSpecificConfigurationStep .summary-title {
        text-style: bold;
        color: $success;
        margin-bottom: 1;
    }

    ServiceSpecificConfigurationStep .summary-item {
        color: $text;
        margin: 0 0 0 2;
    }

    ServiceSpecificConfigurationStep .add-volume-button {
        margin-top: 1;
    }

    ServiceSpecificConfigurationStep .volume-row {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }

    ServiceSpecificConfigurationStep .volume-input {
        width: 1fr;
        margin-right: 1;
    }

    ServiceSpecificConfigurationStep .remove-button {
        width: auto;
    }
    """

    def __init__(
        self,
        selected_services: list[str],
        configuration: Configuration,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the service-specific configuration step.

        Args:
            selected_services: List of selected service names
            configuration: Configuration object with base settings
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.selected_services = selected_services
        self.configuration = configuration
        self._custom_volumes: dict[str, list[tuple[str, str]]] = {
            service: [] for service in selected_services
        }

    def compose(self) -> ComposeResult:
        """Compose the service-specific configuration step layout."""
        yield Label("Service-Specific Configuration", classes="section-title")
        yield Label(
            "Configure ports and custom volumes for each service. Default values are provided.",
            classes="info-text",
        )

        # Create a section for each selected service
        for service_id in self.selected_services:
            metadata = get_service_metadata(service_id)
            if not metadata:
                continue

            with Vertical(classes="service-section", id=f"service-{service_id}"):
                yield Label(f"{metadata['name']}", classes="service-name")
                yield Label(metadata["description"], classes="info-text")

                # Port configuration
                with Horizontal(classes="form-row"):
                    yield Label("Port:", classes="form-label")
                    yield Input(
                        value=str(metadata["default_port"]),
                        placeholder=str(metadata["default_port"]),
                        validators=[PositiveIntegerValidator()],
                        classes="form-input",
                        id=f"port-{service_id}",
                    )
                
                yield Label(
                    f"Default: {metadata['default_port']} (Web UI will be accessible at http://localhost:{metadata['default_port']})",
                    classes="info-text",
                )

                # Custom volumes section
                yield Label("Custom Volume Mounts (optional):", classes="form-label")
                yield Label(
                    "Add additional volume mounts beyond the default configuration.",
                    classes="info-text",
                )
                
                # Container for custom volumes
                with Vertical(id=f"volumes-{service_id}"):
                    pass  # Will be populated dynamically

                yield Button(
                    "+ Add Volume Mount",
                    id=f"add-volume-{service_id}",
                    variant="default",
                    classes="add-volume-button",
                )

        # Configuration summary section
        with Vertical(classes="summary-section", id="config-summary"):
            yield Label("Configuration Summary", classes="summary-title")
            yield from self._render_summary()

    def _render_summary(self) -> ComposeResult:
        """Render the configuration summary.

        Yields:
            Labels with configuration summary
        """
        # Base configuration
        yield Label("Base Configuration:", classes="section-title")
        yield Label(f"  • PUID: {self.configuration.puid}", classes="summary-item")
        yield Label(f"  • PGID: {self.configuration.pgid}", classes="summary-item")
        yield Label(f"  • Timezone: {self.configuration.timezone}", classes="summary-item")
        
        # Path configuration
        yield Label("Paths:", classes="section-title")
        if hasattr(self.configuration, 'paths') and self.configuration.paths:
            yield Label(f"  • Base Path: {self.configuration.paths.base_path}", classes="summary-item")
            yield Label(f"  • Config Path: {self.configuration.paths.config_path}", classes="summary-item")
            yield Label(f"  • Data Path: {self.configuration.paths.data_path}", classes="summary-item")
        
        # Services
        yield Label("Services:", classes="section-title")
        for service_id in self.selected_services:
            metadata = get_service_metadata(service_id)
            if metadata:
                yield Label(f"  • {metadata['name']} (Port: {metadata['default_port']})", classes="summary-item")

    def update_summary(self) -> None:
        """Update the configuration summary with current values."""
        try:
            summary_section = self.query_one("#config-summary", Vertical)
            # Remove existing summary items
            for child in list(summary_section.children):
                if not isinstance(child, Label) or "summary-title" not in child.classes:
                    child.remove()
            
            # Re-render summary
            summary_section.mount(*self._render_summary())
        except Exception as e:
            logger.error(f"Failed to update summary: {e}")

    def add_volume_mount(self, service_id: str) -> None:
        """Add a custom volume mount input for a service.

        Args:
            service_id: Service identifier
        """
        try:
            volumes_container = self.query_one(f"#volumes-{service_id}", Vertical)
            volume_index = len(self._custom_volumes[service_id])
            
            # Create the volume row container
            volume_row = Horizontal(classes="volume-row", id=f"volume-row-{service_id}-{volume_index}")
            
            # Add inputs to the row
            volume_row.mount(
                Input(
                    placeholder="Host path (e.g., /mnt/extra)",
                    classes="volume-input",
                    id=f"volume-host-{service_id}-{volume_index}",
                )
            )
            volume_row.mount(
                Input(
                    placeholder="Container path (e.g., /extra)",
                    classes="volume-input",
                    id=f"volume-container-{service_id}-{volume_index}",
                )
            )
            volume_row.mount(
                Button(
                    "Remove",
                    id=f"remove-volume-{service_id}-{volume_index}",
                    variant="error",
                    classes="remove-button",
                )
            )
            
            # Mount the row to the container
            volumes_container.mount(volume_row)
            
            self._custom_volumes[service_id].append(("", ""))
            
        except Exception as e:
            logger.error(f"Failed to add volume mount: {e}")

    def remove_volume_mount(self, service_id: str, volume_index: int) -> None:
        """Remove a custom volume mount input.

        Args:
            service_id: Service identifier
            volume_index: Index of the volume to remove
        """
        try:
            volume_row = self.query_one(f"#volume-row-{service_id}-{volume_index}", Horizontal)
            volume_row.remove()
            
            # Remove from tracking
            if volume_index < len(self._custom_volumes[service_id]):
                self._custom_volumes[service_id].pop(volume_index)
                
        except Exception as e:
            logger.error(f"Failed to remove volume mount: {e}")

    def get_values(self) -> dict[str, Any]:
        """Get the current form values for all services.

        Returns:
            Dictionary with service configurations
        """
        service_configs = {}
        
        for service_id in self.selected_services:
            metadata = get_service_metadata(service_id)
            if not metadata:
                continue
            
            try:
                # Get port value
                port_input = self.query_one(f"#port-{service_id}", Input)
                port = int(port_input.value) if port_input.value else metadata["default_port"]
                
                # Get custom volumes
                custom_volumes = {}
                for i, _ in enumerate(self._custom_volumes[service_id]):
                    try:
                        host_input = self.query_one(f"#volume-host-{service_id}-{i}", Input)
                        container_input = self.query_one(f"#volume-container-{service_id}-{i}", Input)
                        
                        if host_input.value and container_input.value:
                            custom_volumes[host_input.value] = container_input.value
                    except Exception:
                        pass  # Volume input might have been removed
                
                service_configs[service_id] = {
                    "name": service_id,
                    "enabled": True,
                    "port": port,
                    "custom_volumes": custom_volumes,
                    "environment_vars": {},
                }
                
            except Exception as e:
                logger.error(f"Failed to get values for service {service_id}: {e}")
                # Use defaults
                service_configs[service_id] = {
                    "name": service_id,
                    "enabled": True,
                    "port": metadata["default_port"],
                    "custom_volumes": {},
                    "environment_vars": {},
                }
        
        return service_configs

    def validate_services(self) -> ValidationResult:
        """Validate service-specific configurations.

        Returns:
            ValidationResult with validation status
        """
        from arr_stack_manager.core.validator import ConfigurationValidator
        
        errors = []
        warnings = []
        
        # Get current values
        service_configs = self.get_values()
        
        # Check for port conflicts
        ports_used = {}
        for service_id, config in service_configs.items():
            port = config["port"]
            
            # Validate port range
            if port < 1 or port > 65535:
                errors.append(f"{service_id}: Port {port} is out of valid range (1-65535)")
                continue
            
            # Check for conflicts
            if port in ports_used:
                errors.append(
                    f"Port conflict: {service_id} and {ports_used[port]} both use port {port}"
                )
            else:
                ports_used[port] = service_id
        
        # Validate custom volumes
        for service_id, config in service_configs.items():
            for host_path, container_path in config["custom_volumes"].items():
                if not host_path or not host_path.strip():
                    warnings.append(f"{service_id}: Empty host path in custom volume")
                if not container_path or not container_path.strip():
                    warnings.append(f"{service_id}: Empty container path in custom volume")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )


class ConfigWizardScreen(Screen):
    """Configuration wizard screen for guided stack setup."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    ConfigWizardScreen {
        background: $background;
    }

    ConfigWizardScreen .wizard-container {
        height: 100%;
        width: 100%;
        padding: 1;
    }

    ConfigWizardScreen .step-content {
        height: 1fr;
        width: 100%;
    }

    ConfigWizardScreen .navigation-section {
        height: auto;
        width: 100%;
        margin-top: 1;
        padding: 1;
        background: $surface;
        border: solid $primary;
    }

    ConfigWizardScreen .navigation-buttons {
        height: auto;
        width: 100%;
        align: center middle;
    }

    ConfigWizardScreen Button {
        margin: 0 1;
    }

    ConfigWizardScreen .validation-error {
        color: $error;
        text-style: italic;
        text-align: center;
        margin-bottom: 1;
    }

    ConfigWizardScreen #env-info {
        color: $success;
        text-style: italic;
        text-align: center;
        padding: 1;
        background: $surface;
        border: solid $success;
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        controller: AppController,
        configuration: Configuration,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the configuration wizard screen.

        Args:
            controller: Application controller instance
            configuration: Configuration object with selected services
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.controller = controller
        self.configuration = configuration
        self._current_step = WizardStep.SERVICE_CONFIRMATION
        self._total_steps = 4
        self._validation_error: str | None = None

        # Get environment defaults from controller
        self._env_defaults = self.controller.get_env_defaults()
        
        # Auto-detect PUID/PGID and timezone, preferring environment values
        self._detected_puid = self._env_defaults.get("puid", self._detect_puid())
        self._detected_pgid = self._env_defaults.get("pgid", self._detect_pgid())
        self._detected_timezone = self._env_defaults.get("timezone", self._detect_timezone())
        self._detected_base_path = self._env_defaults.get("base_path", "")

        logger.info(
            f"Wizard initialized with {len(configuration.get_selected_services())} services, "
            f"PUID={self._detected_puid} (from_env={('puid' in self._env_defaults)}), "
            f"PGID={self._detected_pgid} (from_env={('pgid' in self._env_defaults)}), "
            f"TZ={self._detected_timezone} (from_env={('timezone' in self._env_defaults)})"
        )

    def compose(self) -> ComposeResult:
        """Compose the configuration wizard screen layout."""
        yield Header()

        with ScrollableContainer(classes="wizard-container"):
            # Show environment info if any defaults are loaded
            if self._env_defaults:
                yield Label(
                    "🌍 Some values are pre-filled from your .env file. You can override them below.",
                    classes="info-text",
                    id="env-info",
                )
            
            # Step indicator
            yield StepIndicator(
                current_step=self._current_step,
                total_steps=self._total_steps,
                step_title=self._get_step_title(),
                id="step-indicator",
            )

            # Step content
            with ScrollableContainer(classes="step-content", id="step-content"):
                yield from self._render_current_step()

            # Navigation section
            with Container(classes="navigation-section"):
                if self._validation_error:
                    yield Label(
                        self._validation_error,
                        classes="validation-error",
                        id="validation-error",
                    )
                
                with Horizontal(classes="navigation-buttons"):
                    yield Button("← Back", id="back-button", variant="default")
                    yield Button("Continue →", id="continue-button", variant="primary")

        yield Footer()

    def _get_step_title(self) -> str:
        """Get the title for the current step.

        Returns:
            Step title string
        """
        if self._current_step == WizardStep.SERVICE_CONFIRMATION:
            return "Service Selection Confirmation"
        elif self._current_step == WizardStep.BASE_CONFIGURATION:
            return "Base Configuration"
        elif self._current_step == WizardStep.PATH_CONFIGURATION:
            return "Directory Structure Configuration"
        elif self._current_step == WizardStep.SERVICE_SPECIFIC_CONFIGURATION:
            return "Service-Specific Configuration"
        else:
            return "Unknown Step"

    def _render_current_step(self) -> ComposeResult:
        """Render the current wizard step.

        Yields:
            Widgets for the current step
        """
        if self._current_step == WizardStep.SERVICE_CONFIRMATION:
            yield ServiceConfirmationStep(
                selected_services=self.configuration.get_selected_services(),
                id="service-confirmation-step",
            )
        elif self._current_step == WizardStep.BASE_CONFIGURATION:
            # Determine which values come from environment
            from_env = {
                "puid": "puid" in self._env_defaults,
                "pgid": "pgid" in self._env_defaults,
                "timezone": "timezone" in self._env_defaults,
            }
            
            yield BaseConfigurationStep(
                puid=self._detected_puid,
                pgid=self._detected_pgid,
                timezone=self._detected_timezone,
                from_env=from_env,
                id="base-config-step",
            )
        elif self._current_step == WizardStep.PATH_CONFIGURATION:
            # Get base path from configuration if available, otherwise use detected
            base_path = self._detected_base_path
            if hasattr(self.configuration, 'paths') and self.configuration.paths:
                base_path = self.configuration.paths.base_path
            
            yield PathConfigurationStep(
                base_path=base_path,
                from_env="base_path" in self._env_defaults,
                id="path-config-step",
            )
        elif self._current_step == WizardStep.SERVICE_SPECIFIC_CONFIGURATION:
            yield ServiceSpecificConfigurationStep(
                selected_services=self.configuration.get_selected_services(),
                configuration=self.configuration,
                id="service-specific-step",
            )

    def _detect_puid(self) -> int:
        """Detect current user's PUID.

        Returns:
            Detected PUID or 1000 as default
        """
        try:
            return os.getuid()
        except Exception as e:
            logger.warning(f"Failed to detect PUID: {e}")
            return 1000

    def _detect_pgid(self) -> int:
        """Detect current user's PGID.

        Returns:
            Detected PGID or 1000 as default
        """
        try:
            return os.getgid()
        except Exception as e:
            logger.warning(f"Failed to detect PGID: {e}")
            return 1000

    def _detect_timezone(self) -> str:
        """Detect system timezone.

        Returns:
            Detected timezone string or UTC as default
        """
        try:
            # Try to read from /etc/timezone (Debian/Ubuntu)
            try:
                with open("/etc/timezone", "r") as f:
                    tz = f.read().strip()
                    if tz:
                        return tz
            except FileNotFoundError:
                pass

            # Try to use timedatectl (systemd)
            try:
                result = subprocess.run(
                    ["timedatectl", "show", "-p", "Timezone", "--value"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0:
                    tz = result.stdout.strip()
                    if tz:
                        return tz
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            # Fallback: try to get from environment
            tz = os.getenv("TZ")
            if tz:
                return tz

            # Last resort: use UTC
            return "UTC"

        except Exception as e:
            logger.warning(f"Failed to detect timezone: {e}")
            return "UTC"

    def _show_validation_error(self, error: str) -> None:
        """Show a validation error message.

        Args:
            error: Error message to display
        """
        self._validation_error = error

        # Try to update existing error label
        try:
            error_label = self.query_one("#validation-error", Label)
            error_label.update(error)
        except Exception:
            # Error label doesn't exist, need to add it
            try:
                nav_section = self.query_one(".navigation-section", Container)
                # Add error label before buttons
                nav_section.mount(
                    Label(error, classes="validation-error", id="validation-error"),
                    before=nav_section.query_one(".navigation-buttons"),
                )
            except Exception as e:
                logger.error(f"Failed to show validation error: {e}")

    def _clear_validation_error(self) -> None:
        """Clear any validation error message."""
        self._validation_error = None
        try:
            error_label = self.query_one("#validation-error", Label)
            error_label.remove()
        except Exception:
            pass

    def _validate_current_step(self) -> bool:
        """Validate the current step before proceeding.

        Returns:
            True if validation passes, False otherwise
        """
        if self._current_step == WizardStep.SERVICE_CONFIRMATION:
            # No validation needed for confirmation step
            return True

        elif self._current_step == WizardStep.BASE_CONFIGURATION:
            # Validate base configuration inputs
            try:
                base_config_step = self.query_one("#base-config-step", BaseConfigurationStep)
                values = base_config_step.get_values()

                # Validate PUID
                if values["puid"] < 0:
                    self._show_validation_error("PUID must be a positive integer")
                    return False

                # Validate PGID
                if values["pgid"] < 0:
                    self._show_validation_error("PGID must be a positive integer")
                    return False

                # Validate timezone
                if not values["timezone"] or not values["timezone"].strip():
                    self._show_validation_error("Timezone is required")
                    return False

                self._clear_validation_error()
                return True

            except Exception as e:
                logger.error(f"Validation error: {e}")
                self._show_validation_error(f"Validation failed: {str(e)}")
                return False

        elif self._current_step == WizardStep.PATH_CONFIGURATION:
            # Validate path configuration
            try:
                path_config_step = self.query_one("#path-config-step", PathConfigurationStep)
                values = path_config_step.get_values()

                # Validate base path is not empty
                if not values["base_path"] or not values["base_path"].strip():
                    self._show_validation_error("Base path is required")
                    return False

                # Check if path exists, if not offer to create it
                base_path = Path(values["base_path"])
                if not base_path.exists():
                    # Offer to create the directory
                    try:
                        base_path.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created directory: {base_path}")
                        # Update validation status to show success
                        path_config_step.update_directory_tree()
                    except Exception as create_error:
                        self._show_validation_error(
                            f"Cannot create directory: {str(create_error)}. "
                            f"Please create it manually or choose a different path."
                        )
                        return False

                # Perform full path validation
                result = path_config_step.validate_path()
                
                # Check for errors (excluding the "does not exist" error since we just created it)
                if result.errors:
                    # Filter out "does not exist" errors since we handle that above
                    real_errors = [e for e in result.errors if "does not exist" not in e]
                    if real_errors:
                        # Show first error
                        error_lines = real_errors[0].split("\n")
                        self._show_validation_error(error_lines[0])
                        return False

                self._clear_validation_error()
                return True

            except Exception as e:
                logger.error(f"Validation error: {e}")
                self._show_validation_error(f"Validation failed: {str(e)}")
                return False

        elif self._current_step == WizardStep.SERVICE_SPECIFIC_CONFIGURATION:
            # Validate service-specific configuration
            try:
                service_specific_step = self.query_one("#service-specific-step", ServiceSpecificConfigurationStep)
                
                # Perform service-specific validation
                result = service_specific_step.validate_services()
                
                # Check for errors
                if result.errors:
                    # Show first error
                    self._show_validation_error(result.errors[0])
                    return False

                self._clear_validation_error()
                return True

            except Exception as e:
                logger.error(f"Validation error: {e}")
                self._show_validation_error(f"Validation failed: {str(e)}")
                return False

        return True

    def _save_current_step_data(self) -> None:
        """Save data from the current step to the configuration."""
        if self._current_step == WizardStep.BASE_CONFIGURATION:
            try:
                base_config_step = self.query_one("#base-config-step", BaseConfigurationStep)
                values = base_config_step.get_values()

                # Update configuration
                self.configuration.puid = values["puid"]
                self.configuration.pgid = values["pgid"]
                self.configuration.timezone = values["timezone"]

                logger.info(
                    f"Saved base configuration: PUID={values['puid']}, "
                    f"PGID={values['pgid']}, TZ={values['timezone']}"
                )

            except Exception as e:
                logger.error(f"Failed to save step data: {e}")

        elif self._current_step == WizardStep.PATH_CONFIGURATION:
            try:
                path_config_step = self.query_one("#path-config-step", PathConfigurationStep)
                values = path_config_step.get_values()

                # Create PathConfig and update configuration
                path_config = PathConfig(base_path=values["base_path"])
                self.configuration.paths = path_config

                logger.info(
                    f"Saved path configuration: base_path={values['base_path']}, "
                    f"config_path={path_config.config_path}, data_path={path_config.data_path}"
                )

            except Exception as e:
                logger.error(f"Failed to save path configuration: {e}")

        elif self._current_step == WizardStep.SERVICE_SPECIFIC_CONFIGURATION:
            try:
                service_specific_step = self.query_one("#service-specific-step", ServiceSpecificConfigurationStep)
                service_configs = service_specific_step.get_values()

                # Create ServiceConfig objects and add to configuration
                for service_id, config_data in service_configs.items():
                    service_config = ServiceConfig(**config_data)
                    self.configuration.add_service(service_config)

                logger.info(
                    f"Saved service-specific configuration for {len(service_configs)} services"
                )

            except Exception as e:
                logger.error(f"Failed to save service-specific configuration: {e}")

    def _go_to_next_step(self) -> None:
        """Navigate to the next wizard step."""
        # Validate current step
        if not self._validate_current_step():
            logger.warning("Validation failed, cannot proceed to next step")
            return

        # Save current step data
        self._save_current_step_data()

        # Check if we're on the last step
        if self._current_step == WizardStep.SERVICE_SPECIFIC_CONFIGURATION:
            # This is the last step, trigger deployment workflow
            logger.info("Wizard completed, starting deployment workflow")
            self._start_deployment_workflow()
            return

        # Move to next step
        self._current_step = WizardStep(self._current_step + 1)
        logger.info(f"Moving to step {self._current_step}")

        # Update UI
        self._update_step_display()

    def _go_to_previous_step(self) -> None:
        """Navigate to the previous wizard step."""
        if self._current_step == WizardStep.SERVICE_CONFIRMATION:
            # First step, go back to service selector
            logger.info("Going back from first step, dismissing wizard")
            self.dismiss(None)
            return

        # Move to previous step
        self._current_step = WizardStep(self._current_step - 1)
        logger.info(f"Moving back to step {self._current_step}")

        # Update UI
        self._update_step_display()

    def _update_step_display(self) -> None:
        """Update the display for the current step."""
        # Update step indicator
        try:
            step_indicator = self.query_one("#step-indicator", StepIndicator)
            step_indicator.update_step(self._current_step, self._get_step_title())
        except Exception as e:
            logger.error(f"Failed to update step indicator: {e}")

        # Update step content
        try:
            step_content = self.query_one("#step-content", ScrollableContainer)
            step_content.remove_children()
            step_content.mount(*self._render_current_step())
        except Exception as e:
            logger.error(f"Failed to update step content: {e}")

        # Clear any validation errors
        self._clear_validation_error()

    @on(Button.Pressed, "#back-button")
    def handle_back_button(self) -> None:
        """Handle back button press."""
        logger.info("Back button pressed")
        self._go_to_previous_step()

    @on(Button.Pressed, "#continue-button")
    def handle_continue_button(self) -> None:
        """Handle continue button press."""
        logger.info(f"Continue button pressed on step {self._current_step}")
        self._go_to_next_step()

    @on(Button.Pressed, "#detect-timezone")
    def handle_detect_timezone(self) -> None:
        """Handle detect timezone button press."""
        logger.info("Detect timezone button pressed")
        
        try:
            # Detect timezone
            detected_tz = self._detect_timezone()
            
            # Update the input field
            timezone_input = self.query_one("#timezone-input", Input)
            timezone_input.value = detected_tz
            
            # Update the info text
            timezone_info = self.query_one("#timezone-info", Label)
            timezone_info.update(f"ℹ Detected: {detected_tz}")
            
            logger.info(f"Timezone detected and set to: {detected_tz}")
            
        except Exception as e:
            logger.error(f"Failed to detect timezone: {e}")

    @on(Input.Changed)
    def handle_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes for real-time validation.

        Args:
            event: Input changed event
        """
        # Clear validation error when user starts typing
        if self._validation_error:
            self._clear_validation_error()

        # Handle base path input changes
        if event.input.id == "base-path-input" and self._current_step == WizardStep.PATH_CONFIGURATION:
            try:
                path_config_step = self.query_one("#path-config-step", PathConfigurationStep)
                
                # Update the directory tree preview
                path_config_step.update_directory_tree(event.value)
                
                # Validate the path if it's not empty
                if event.value and event.value.strip():
                    path_config_step.base_path = event.value
                    result = path_config_step.validate_path()
                    path_config_step.update_validation_status(result)
                    
            except Exception as e:
                logger.error(f"Failed to handle base path input change: {e}")

    @on(Button.Pressed, "#browse-button")
    def handle_browse_button(self) -> None:
        """Handle browse button press for path selection."""
        logger.info("Browse button pressed")
        
        try:
            # Get current base path
            base_path_input = self.query_one("#base-path-input", Input)
            current_path = base_path_input.value or os.path.expanduser("~")
            
            # For now, just show a message that file browser is not implemented
            # In a full implementation, this would open a file browser dialog
            logger.info(f"File browser not yet implemented. Current path: {current_path}")
            
            # You could implement a simple directory selector here using Textual's DirectoryTree
            # or just let users type the path manually
            
        except Exception as e:
            logger.error(f"Failed to handle browse button: {e}")

    @on(Button.Pressed)
    def handle_volume_buttons(self, event: Button.Pressed) -> None:
        """Handle add/remove volume mount buttons.

        Args:
            event: Button pressed event
        """
        button_id = event.button.id
        if not button_id:
            return

        # Handle add volume buttons
        if button_id.startswith("add-volume-"):
            service_id = button_id.replace("add-volume-", "")
            logger.info(f"Adding volume mount for service: {service_id}")
            
            try:
                service_specific_step = self.query_one("#service-specific-step", ServiceSpecificConfigurationStep)
                service_specific_step.add_volume_mount(service_id)
            except Exception as e:
                logger.error(f"Failed to add volume mount: {e}")

        # Handle remove volume buttons
        elif button_id.startswith("remove-volume-"):
            parts = button_id.replace("remove-volume-", "").rsplit("-", 1)
            if len(parts) == 2:
                service_id, volume_index_str = parts
                try:
                    volume_index = int(volume_index_str)
                    logger.info(f"Removing volume mount {volume_index} for service: {service_id}")
                    
                    service_specific_step = self.query_one("#service-specific-step", ServiceSpecificConfigurationStep)
                    service_specific_step.remove_volume_mount(service_id, volume_index)
                except Exception as e:
                    logger.error(f"Failed to remove volume mount: {e}")

    def _start_deployment_workflow(self) -> None:
        """Start the deployment workflow after wizard completion."""
        try:
            logger.info("Starting deployment workflow")
            
            # Create a stack name (use timestamp for uniqueness)
            stack_name = f"arr-stack-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            logger.info(f"Creating stack: {stack_name}")
            
            # Determine output directory (use stack-specific directory)
            output_dir = self.controller.config_repository.get_config_dir() / "stacks" / stack_name
            logger.info(f"Output directory: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
            compose_path = str(output_dir / "docker-compose.yml")
            
            # Create StackConfig with compose_path
            from arr_stack_manager.models.stack import StackConfig
            logger.info("Creating StackConfig")
            stack_config = StackConfig(
                name=stack_name,
                configuration=self.configuration,
                compose_path=compose_path,
            )
            
            # Step 1: Validate the complete stack configuration
            logger.info("Validating stack configuration before deployment")
            validation_result = self.controller.validate_stack(stack_config)
            
            if not validation_result.valid:
                # Show validation errors
                error_msg = "Configuration validation failed:\n" + "\n".join(validation_result.errors[:3])
                self._show_validation_error(error_msg)
                logger.error(f"Stack validation failed: {validation_result.errors}")
                return
            
            # Log warnings if any
            if validation_result.warnings:
                logger.info(f"Validation warnings: {validation_result.warnings}")
            
            # Step 2: Generate Docker Compose files
            logger.info("Generating Docker Compose files")
            
            try:
                compose_content, env_content = self.controller.generate_compose_files(
                    stack_config, output_dir
                )
                logger.info(f"Generated compose files in {output_dir}")
            except Exception as e:
                error_msg = f"Failed to generate compose files: {str(e)}"
                self._show_validation_error(error_msg)
                logger.error(error_msg, exc_info=True)
                return
            
            # Step 3: Persist stack configuration before deployment
            logger.info("Persisting stack configuration")
            try:
                self.controller.save_configuration(stack_config)
                logger.info(f"Stack configuration saved: {stack_name}")
            except Exception as e:
                logger.error(f"Failed to save stack configuration: {e}", exc_info=True)
                # Continue anyway - we can still deploy
            
            # Step 4: Navigate to Dashboard instead of deployment monitor
            logger.info(f"Wizard complete! Navigating to dashboard for stack: {stack_name}")
            
            # Set the current stack in the controller
            self.controller.current_stack = stack_config
            
            # Dismiss the wizard
            self.dismiss(None)
            
            # Navigate to dashboard
            from arr_stack_manager.controller import ScreenType
            self.controller.navigate_to(ScreenType.DASHBOARD, stack_name=stack_name)
            
            logger.info("Successfully navigated to dashboard")
            
        except Exception as e:
            error_msg = f"Failed to start deployment workflow: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._show_validation_error(error_msg)
            # Show notification to user
            try:
                self.app.notify(f"Error: {error_msg}", severity="error", timeout=10)
            except Exception:
                pass
            logger.error(error_msg, exc_info=True)

    def action_back(self) -> None:
        """Navigate back to previous screen."""
        logger.info("Navigating back from wizard")
        self.dismiss(None)

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
