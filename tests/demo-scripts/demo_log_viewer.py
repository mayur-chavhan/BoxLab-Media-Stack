#!/usr/bin/env python3
"""Demo script for testing the log viewer screen."""

import asyncio
import logging
from pathlib import Path

from textual.app import App

from arr_stack_manager.controller import AppController
from arr_stack_manager.screens.log_viewer import LogViewerScreen

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class LogViewerDemoApp(App):
    """Demo app for testing log viewer."""

    CSS = """
    Screen {
        background: $background;
    }
    """

    def __init__(self, service_name: str = "sonarr"):
        """Initialize the demo app.

        Args:
            service_name: Name of the service to view logs for
        """
        super().__init__()
        self.service_name = service_name

    def on_mount(self) -> None:
        """Handle app mount."""
        # Initialize controller
        controller = AppController()

        # Push log viewer screen
        self.push_screen(
            LogViewerScreen(
                controller=controller,
                service_name=self.service_name,
            )
        )


def main():
    """Run the demo app."""
    import sys

    service_name = sys.argv[1] if len(sys.argv) > 1 else "sonarr"

    print(f"Starting log viewer demo for service: {service_name}")
    print("Features to test:")
    print("  - Real-time log streaming")
    print("  - Auto-scroll toggle (keyboard: 'a')")
    print("  - Log filtering by level")
    print("  - Search functionality (keyboard: 'f')")
    print("  - Clear logs (keyboard: 'c')")
    print("  - Toggle streaming (keyboard: 's')")
    print("  - Export logs to file")
    print("  - Syntax highlighting for log levels, timestamps, IPs, URLs")
    print("\nPress 'q' to quit, 'escape' to go back")
    print()

    app = LogViewerDemoApp(service_name=service_name)
    app.run()


if __name__ == "__main__":
    main()
