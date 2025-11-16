"""Service selector screen for choosing which services to include in the stack."""

import logging
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Header, Label, Static

from arr_stack_manager.controller import AppController, ScreenType
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.models.stack import StackConfig
from arr_stack_manager.utils.services import SUPPORTED_SERVICES, get_services_by_category

logger = logging.getLogger(__name__)


# Category display names
CATEGORY_NAMES = {
    "media_management": "Media Management",
    "media_server": "Media Servers",
    "request_management": "Request Management",
    "download_indexer": "Download Clients & Indexers",
    "media_processing": "Media Processing",
}


class ServiceItem(Static):
    """Widget for displaying a single service with checkbox."""

    DEFAULT_CSS = """
    ServiceItem {
        height: auto;
        width: 100%;
        padding: 0 1;
        margin: 0 0 1 0;
    }

    ServiceItem Horizontal {
        height: auto;
        width: 100%;
    }

    ServiceItem Checkbox {
        width: auto;
        margin-right: 2;
    }

    ServiceItem .service-info {
        width: 1fr;
        height: auto;
    }

    ServiceItem .service-name {
        text-style: bold;
        color: $text;
    }

    ServiceItem .service-description {
        color: $text-muted;
        margin-top: 0;
    }
    """

    def __init__(
        self,
        service_id: str,
        service_name: str,
        description: str,
        selected: bool = False,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the service item.

        Args:
            service_id: Service identifier (e.g., 'sonarr')
            service_name: Display name (e.g., 'Sonarr')
            description: Service description
            selected: Whether the service is initially selected
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.service_id = service_id
        self.service_name = service_name
        self.description = description
        self.selected = selected

    def compose(self) -> ComposeResult:
        """Compose the service item layout."""
        with Horizontal():
            yield Checkbox(
                "",
                value=self.selected,
                id=f"checkbox-{self.service_id}",
            )
            with Vertical(classes="service-info"):
                yield Label(self.service_name, classes="service-name")
                yield Label(self.description, classes="service-description")


class ServiceCategory(Static):
    """Widget for displaying a category of services."""

    DEFAULT_CSS = """
    ServiceCategory {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }

    ServiceCategory .category-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    ServiceCategory .services-container {
        height: auto;
        width: 100%;
    }
    """

    def __init__(
        self,
        category_id: str,
        category_name: str,
        service_ids: list[str],
        selected_services: set[str],
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the service category.

        Args:
            category_id: Category identifier
            category_name: Display name for the category
            service_ids: List of service IDs in this category
            selected_services: Set of currently selected service IDs
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.category_id = category_id
        self.category_name = category_name
        self.service_ids = service_ids
        self.selected_services = selected_services

    def compose(self) -> ComposeResult:
        """Compose the category layout."""
        yield Label(self.category_name, classes="category-title")
        with Vertical(classes="services-container"):
            for service_id in self.service_ids:
                metadata = SUPPORTED_SERVICES.get(service_id)
                if metadata:
                    yield ServiceItem(
                        service_id=service_id,
                        service_name=metadata["name"],
                        description=metadata["description"],
                        selected=service_id in self.selected_services,
                        id=f"service-{service_id}",
                    )


class ServiceSelectorScreen(Screen):
    """Screen for selecting which services to include in the stack."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    ServiceSelectorScreen {
        background: $background;
    }

    ServiceSelectorScreen .selector-container {
        height: 100%;
        width: 100%;
        padding: 1;
    }

    ServiceSelectorScreen .header-section {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }

    ServiceSelectorScreen .title {
        text-style: bold;
        color: $text;
        text-align: center;
        margin-bottom: 1;
    }

    ServiceSelectorScreen .instructions {
        color: $text-muted;
        text-align: center;
        margin-bottom: 1;
    }

    ServiceSelectorScreen .categories-section {
        height: 1fr;
        width: 100%;
    }

    ServiceSelectorScreen .footer-section {
        height: auto;
        width: 100%;
        margin-top: 1;
        padding: 1;
        background: $surface;
        border: solid $primary;
    }

    ServiceSelectorScreen .footer-content {
        height: auto;
        width: 100%;
        align: center middle;
    }

    ServiceSelectorScreen .selected-count {
        color: $text;
        text-style: bold;
        margin-right: 2;
    }

    ServiceSelectorScreen .validation-error {
        color: $error;
        text-style: italic;
        margin-right: 2;
    }

    ServiceSelectorScreen Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        controller: AppController,
        existing_config: Configuration | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the service selector screen.

        Args:
            controller: Application controller instance
            existing_config: Existing configuration to pre-populate selections
            name: Screen name
            id: Screen ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.controller = controller
        self.existing_config = existing_config
        self._selected_services: set[str] = set()
        self._validation_error: str | None = None

        # Pre-populate selections from existing config
        if existing_config:
            self._selected_services = set(existing_config.get_selected_services())

    def compose(self) -> ComposeResult:
        """Compose the service selector screen layout."""
        yield Header()

        with ScrollableContainer(classes="selector-container"):
            # Header section
            with Container(classes="header-section"):
                yield Label(
                    "Service Selection",
                    classes="title",
                )
                yield Label(
                    "Select the services you want to include in your stack:",
                    classes="instructions",
                )

            # Categories section
            with ScrollableContainer(classes="categories-section", id="categories-container"):
                yield from self._render_categories()

            # Footer section with actions
            with Container(classes="footer-section"):
                with Horizontal(classes="footer-content"):
                    yield Label(
                        self._format_selected_count(),
                        classes="selected-count",
                        id="selected-count",
                    )
                    if self._validation_error:
                        yield Label(
                            self._validation_error,
                            classes="validation-error",
                            id="validation-error",
                        )
                    yield Button("Back", id="back-button", variant="default")
                    yield Button("Continue →", id="continue-button", variant="primary")

        yield Footer()

    def _render_categories(self) -> ComposeResult:
        """Render service categories."""
        categories = get_services_by_category()

        # Render categories in a specific order
        category_order = [
            "media_management",
            "media_server",
            "request_management",
            "download_indexer",
            "media_processing",
        ]

        for category_id in category_order:
            if category_id in categories:
                category_name = CATEGORY_NAMES.get(category_id, category_id.replace("_", " ").title())
                service_ids = categories[category_id]
                yield ServiceCategory(
                    category_id=category_id,
                    category_name=category_name,
                    service_ids=service_ids,
                    selected_services=self._selected_services,
                    id=f"category-{category_id}",
                )

    def _format_selected_count(self) -> str:
        """Format the selected service count message."""
        count = len(self._selected_services)
        if count == 0:
            return "No services selected"
        elif count == 1:
            return "1 service selected"
        else:
            return f"{count} services selected"

    def _update_selected_count(self) -> None:
        """Update the selected count display."""
        try:
            count_label = self.query_one("#selected-count", Label)
            count_label.update(self._format_selected_count())
        except Exception as e:
            logger.warning(f"Failed to update selected count: {e}")

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
                footer_content = self.query_one(".footer-content", Horizontal)
                # Remove old error label if it exists
                for child in footer_content.children:
                    if hasattr(child, "id") and child.id == "validation-error":
                        child.remove()
                # Add new error label before buttons
                footer_content.mount(
                    Label(error, classes="validation-error", id="validation-error"),
                    before=footer_content.query_one("#back-button"),
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

    def _validate_selection(self) -> bool:
        """Validate that at least one service is selected.

        Returns:
            True if validation passes, False otherwise
        """
        if len(self._selected_services) == 0:
            self._show_validation_error("Please select at least one service")
            return False

        self._clear_validation_error()
        return True

    @on(Checkbox.Changed)
    def handle_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes.

        Args:
            event: Checkbox changed event
        """
        # Extract service ID from checkbox ID
        checkbox_id = event.checkbox.id
        if not checkbox_id or not checkbox_id.startswith("checkbox-"):
            return

        service_id = checkbox_id.replace("checkbox-", "")

        # Update selected services set
        if event.value:
            self._selected_services.add(service_id)
            logger.debug(f"Selected service: {service_id}")
        else:
            self._selected_services.discard(service_id)
            logger.debug(f"Deselected service: {service_id}")

        # Update the count display
        self._update_selected_count()

        # Clear validation error if services are now selected
        if len(self._selected_services) > 0:
            self._clear_validation_error()

    @on(Button.Pressed, "#back-button")
    def handle_back_button(self) -> None:
        """Handle back button press."""
        logger.info("Back button pressed")
        self.action_back()

    @on(Button.Pressed, "#continue-button")
    def handle_continue_button(self) -> None:
        """Handle continue button press."""
        logger.info(f"Continue button pressed with {len(self._selected_services)} services selected")

        # Validate selection
        if not self._validate_selection():
            logger.warning("Validation failed: no services selected")
            return

        # Create or update configuration with selected services
        if self.existing_config:
            config = self.existing_config
        else:
            # Create a new configuration with defaults
            config = Configuration(
                puid=1000,  # Will be configured in wizard
                pgid=1000,  # Will be configured in wizard
                timezone="UTC",  # Will be configured in wizard
                paths=PathConfig(base_path="/tmp"),  # Will be configured in wizard
                services={},
            )

        # Update services in configuration
        # First, disable all services not in selection
        for service_name in list(config.services.keys()):
            if service_name not in self._selected_services:
                config.services[service_name].enabled = False

        # Add or enable selected services
        for service_id in self._selected_services:
            metadata = SUPPORTED_SERVICES.get(service_id)
            if metadata:
                existing_service = config.get_service(service_id)
                if existing_service:
                    # Re-enable existing service
                    existing_service.enabled = True
                else:
                    # Add new service with defaults
                    service_config = ServiceConfig(
                        name=service_id,
                        enabled=True,
                        port=metadata["default_port"],
                    )
                    config.add_service(service_config)

        logger.info(f"Configuration updated with {len(self._selected_services)} selected services")

        # Navigate to configuration wizard
        # For now, we'll dismiss this screen and pass the config back
        self.dismiss(config)

    def action_back(self) -> None:
        """Navigate back to previous screen."""
        logger.info("Navigating back from service selector")
        self.dismiss(None)

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

