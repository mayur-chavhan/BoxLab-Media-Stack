#!/usr/bin/env python3
"""Demo script for the Deployment Monitor screen."""

import asyncio
import logging
from pathlib import Path

from textual.app import App

from arr_stack_manager.controller import AppController
from arr_stack_manager.screens.deployment_monitor import DeploymentMonitorScreen

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class DeploymentMonitorDemo(App):
    """Demo application for the Deployment Monitor screen."""

    CSS = """
    Screen {
        background: $background;
    }
    """

    def __init__(self):
        """Initialize the demo app."""
        super().__init__()
        self.controller = AppController()

    def on_mount(self) -> None:
        """Handle app mount."""
        # Create a dummy compose file path for demo
        compose_path = Path("docker-compose.yml")

        # Push the deployment monitor screen
        self.push_screen(
            DeploymentMonitorScreen(
                controller=self.controller,
                compose_path=compose_path,
                stack_name="media-automation",
            )
        )


if __name__ == "__main__":
    app = DeploymentMonitorDemo()
    app.run()
