#!/usr/bin/env python3
"""Demo script for the Service Selector screen."""

import asyncio
import logging
from pathlib import Path

from textual.app import App

from arr_stack_manager.controller import AppController
from arr_stack_manager.screens.service_selector import ServiceSelectorScreen

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class ServiceSelectorDemo(App):
    """Demo application for the Service Selector screen."""

    CSS = """
    Screen {
        background: $background;
    }
    """

    def __init__(self):
        """Initialize the demo app."""
        super().__init__()
        # Create a temporary controller
        self.controller = AppController(config_dir=Path("/tmp/arr-stack-demo"))

    def on_mount(self) -> None:
        """Handle app mount event."""
        # Push the service selector screen
        self.push_screen(ServiceSelectorScreen(self.controller), self.handle_selection)

    def handle_selection(self, config) -> None:
        """Handle service selection result.

        Args:
            config: The configuration with selected services, or None if cancelled
        """
        if config:
            selected = config.get_selected_services()
            self.notify(
                f"Selected {len(selected)} services: {', '.join(selected)}",
                title="Selection Complete",
                severity="information",
            )
            logging.info(f"User selected services: {selected}")

            # Show the configuration details
            for service_name in selected:
                service = config.get_service(service_name)
                if service:
                    logging.info(
                        f"  - {service_name}: port={service.port}, enabled={service.enabled}"
                    )
        else:
            self.notify("Selection cancelled", title="Cancelled", severity="warning")
            logging.info("User cancelled service selection")

        # Exit after showing the result
        self.call_later(self.exit)


def main():
    """Run the demo application."""
    print("Service Selector Screen Demo")
    print("=" * 50)
    print()
    print("Instructions:")
    print("  - Use arrow keys or mouse to navigate")
    print("  - Space or click to toggle service selection")
    print("  - Press 'Continue' when done selecting services")
    print("  - Press 'Back' or ESC to cancel")
    print("  - Press 'q' to quit")
    print()
    print("=" * 50)
    print()

    app = ServiceSelectorDemo()
    app.run()


if __name__ == "__main__":
    main()

