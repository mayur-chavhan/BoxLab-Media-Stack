"""Selectable service list widget for service selection."""


from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.widgets import Checkbox, Label


class ServiceListItem(Container):
    """A single service item in the list."""

    DEFAULT_CSS = """
    ServiceListItem {
        height: auto;
        width: 100%;
        padding: 1;
        background: $surface;
        border-bottom: solid $primary-background;
    }

    ServiceListItem:hover {
        background: $primary 20%;
    }

    ServiceListItem.selected {
        background: $primary 30%;
    }

    ServiceListItem .item-content {
        height: auto;
        width: 100%;
    }

    ServiceListItem Checkbox {
        width: auto;
        margin-right: 2;
    }

    ServiceListItem .item-details {
        height: auto;
        width: 1fr;
    }

    ServiceListItem .item-name {
        text-style: bold;
        color: $text;
        width: 100%;
    }

    ServiceListItem .item-description {
        color: $text-muted;
        width: 100%;
        margin-top: 0;
    }

    ServiceListItem .item-category {
        color: $accent;
        width: auto;
        text-style: italic;
    }
    """

    def __init__(
        self,
        service_id: str,
        name: str,
        description: str,
        category: str,
        selected: bool = False,
        *,
        widget_name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize a service list item.

        Args:
            service_id: Unique service identifier
            name: Display name of the service
            description: Service description
            category: Service category
            selected: Whether the service is initially selected
            widget_name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=widget_name, id=id, classes=classes)
        self.service_id = service_id
        self.service_name = name
        self.description = description
        self.category = category
        self._selected = selected

    def compose(self) -> ComposeResult:
        """Compose the service list item layout."""
        with Horizontal(classes="item-content"):
            yield Checkbox(value=self._selected, id=f"checkbox-{self.service_id}")
            with Vertical(classes="item-details"):
                yield Label(self.service_name, classes="item-name")
                yield Label(self.description, classes="item-description")

    @property
    def selected(self) -> bool:
        """Check if the service is selected."""
        if self.is_mounted:
            checkbox = self.query_one(f"#checkbox-{self.service_id}", Checkbox)
            return checkbox.value
        return self._selected

    def set_selected(self, selected: bool) -> None:
        """Set the selection state.

        Args:
            selected: Whether the service should be selected
        """
        self._selected = selected
        if self.is_mounted:
            checkbox = self.query_one(f"#checkbox-{self.service_id}", Checkbox)
            checkbox.value = selected

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes.

        Args:
            event: Checkbox changed event
        """
        self._selected = event.value
        if self._selected:
            self.add_class("selected")
        else:
            self.remove_class("selected")

        # Post a custom message that parent can handle
        self.post_message(self.ServiceSelected(self.service_id, self._selected))

    class ServiceSelected(Message):
        """Message posted when a service selection changes."""

        def __init__(self, service_id: str, selected: bool) -> None:
            """Initialize the message.

            Args:
                service_id: ID of the service
                selected: Whether the service is now selected
            """
            super().__init__()
            self.service_id = service_id
            self.selected = selected


class ServiceList(Container):
    """A list widget for selecting multiple services."""

    DEFAULT_CSS = """
    ServiceList {
        height: 100%;
        width: 100%;
        border: solid $primary;
        background: $surface;
    }

    ServiceList .list-header {
        height: 3;
        width: 100%;
        background: $primary;
        padding: 0 1;
    }

    ServiceList .list-title {
        text-style: bold;
        color: $text;
        width: 1fr;
        content-align: center middle;
    }

    ServiceList .list-count {
        color: $accent;
        text-style: bold;
        width: auto;
        content-align: center middle;
    }

    ServiceList .list-content {
        height: 1fr;
        width: 100%;
    }

    ServiceList .category-header {
        height: auto;
        width: 100%;
        background: $primary-background;
        padding: 1;
        margin-top: 1;
    }

    ServiceList .category-title {
        text-style: bold;
        color: $accent;
    }

    ServiceList .list-footer {
        height: 3;
        width: 100%;
        background: $surface;
        padding: 0 1;
        border-top: solid $primary;
    }

    ServiceList .footer-info {
        color: $text-muted;
        width: 100%;
        content-align: center middle;
    }
    """

    def __init__(
        self,
        title: str = "Select Services",
        services: dict[str, dict[str, dict[str, str]]] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the service list.

        Args:
            title: Title to display in the header
            services: Dictionary of services grouped by category
                     Format: {category: {service_id: {name, description}}}
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)
        self.list_title = title
        self.services = services or {}
        self._selected_services: set[str] = set()

    def compose(self) -> ComposeResult:
        """Compose the service list layout."""
        # Header with title and count
        with Horizontal(classes="list-header"):
            yield Label(self.list_title, classes="list-title")
            yield Label(
                f"Selected: {len(self._selected_services)}", classes="list-count", id="list-count"
            )

        # Scrollable content area
        with ScrollableContainer(classes="list-content", id="list-content"):
            yield from self._render_services()

        # Footer with info
        with Horizontal(classes="list-footer"):
            yield Label(
                "Use checkboxes to select services", classes="footer-info", id="footer-info"
            )

    def _render_services(self) -> ComposeResult:
        """Render all services grouped by category."""
        for category, services in self.services.items():
            # Category header
            yield Label(category, classes="category-header category-title")

            # Services in this category
            for service_id, service_info in services.items():
                yield ServiceListItem(
                    service_id=service_id,
                    name=str(service_info.get("name", "")),
                    description=str(service_info.get("description", "")),
                    category=category,
                    selected=service_id in self._selected_services,
                    id=f"item-{service_id}",
                )

    def on_service_list_item_service_selected(
        self, event: ServiceListItem.ServiceSelected
    ) -> None:
        """Handle service selection changes.

        Args:
            event: Service selected event
        """
        if event.selected:
            self._selected_services.add(event.service_id)
        else:
            self._selected_services.discard(event.service_id)

        # Update count in header
        if self.is_mounted:
            count_label = self.query_one("#list-count", Label)
            count_label.update(f"Selected: {len(self._selected_services)}")

            # Update footer message
            footer_label = self.query_one("#footer-info", Label)
            if len(self._selected_services) == 0:
                footer_label.update("Select at least one service to continue")
            else:
                footer_label.update(
                    f"{len(self._selected_services)} service(s) selected - Ready to continue"
                )

    def get_selected_services(self) -> list[str]:
        """Get the list of selected service IDs.

        Returns:
            List of selected service IDs
        """
        return list(self._selected_services)

    def set_selected_services(self, service_ids: list[str]) -> None:
        """Set the selected services.

        Args:
            service_ids: List of service IDs to select
        """
        self._selected_services = set(service_ids)

        if self.is_mounted:
            # Update all checkboxes
            for service_id in service_ids:
                try:
                    item = self.query_one(f"#item-{service_id}", ServiceListItem)
                    item.set_selected(True)
                except Exception:
                    pass

            # Update count
            count_label = self.query_one("#list-count", Label)
            count_label.update(f"Selected: {len(self._selected_services)}")

    def clear_selection(self) -> None:
        """Clear all selections."""
        self._selected_services.clear()

        if self.is_mounted:
            # Uncheck all checkboxes
            for item in self.query(ServiceListItem):
                item.set_selected(False)

            # Update count
            count_label = self.query_one("#list-count", Label)
            count_label.update("Selected: 0")

    @property
    def has_selection(self) -> bool:
        """Check if any services are selected."""
        return len(self._selected_services) > 0

    @property
    def selection_count(self) -> int:
        """Get the number of selected services."""
        return len(self._selected_services)
