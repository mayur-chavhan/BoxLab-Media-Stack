#!/usr/bin/env python3
"""Demo script for testing the Stack Manager screen."""

import logging
from pathlib import Path

from textual.app import App

from arr_stack_manager.controller import AppController
from arr_stack_manager.screens.stack_manager import StackManagerScreen

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class StackManagerDemo(App):
    """Demo application for Stack Manager screen."""

    CSS = """
    Screen {
        background: $background;
    }
    """

    def __init__(self, service_name: str = "sonarr"):
        """Initialize the demo app.

        Args:
            service_name: Name of the service to display
        """
        super().__init__()
        self.service_name = service_name

    def on_mount(self) -> None:
        """Handle app mount event."""
        # Initialize controller
        controller = AppController()
        controller.initialize()

        # Push the stack manager screen
        self.push_screen(StackManagerScreen(controller, self.service_name))


if __name__ == "__main__":
    import sys

    service_name = sys.argv[1] if len(sys.argv) > 1 else "sonarr"
    app = StackManagerDemo(service_name)
    app.run()
