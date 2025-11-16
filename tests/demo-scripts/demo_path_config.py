#!/usr/bin/env python3
"""Demo script for testing the path configuration step in the wizard."""

import logging
from textual.app import App

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.configuration import Configuration, ServiceConfig
from arr_stack_manager.screens.config_wizard import ConfigWizardScreen

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class PathConfigDemoApp(App):
    """Demo application for testing path configuration."""

    CSS = """
    Screen {
        background: $background;
    }
    """

    def on_mount(self) -> None:
        """Handle app mount event."""
        # Create a mock controller
        controller = AppController()

        # Create a configuration with some selected services
        # Use a temporary path that will be updated in the wizard
        from arr_stack_manager.models.configuration import PathConfig
        
        config = Configuration(
            puid=1000,
            pgid=1000,
            timezone="America/New_York",
            paths=PathConfig(base_path="/tmp/arr-stack"),  # Temporary, will be updated in wizard
            services={
                "sonarr": ServiceConfig(name="sonarr", enabled=True, port=8989),
                "radarr": ServiceConfig(name="radarr", enabled=True, port=7878),
                "prowlarr": ServiceConfig(name="prowlarr", enabled=True, port=9696),
            },
        )

        # Push the wizard screen
        self.push_screen(ConfigWizardScreen(controller, config), self.handle_wizard_result)

    def handle_wizard_result(self, result: Configuration | None) -> None:
        """Handle wizard completion.

        Args:
            result: Configuration result from wizard, or None if cancelled
        """
        if result:
            self.notify(f"Wizard completed! Base path: {result.paths.base_path if result.paths else 'Not set'}")
            self.log(f"Configuration: {result}")
        else:
            self.notify("Wizard cancelled")

        # Exit after a short delay
        self.set_timer(2, self.exit)


if __name__ == "__main__":
    app = PathConfigDemoApp()
    app.run()
