#!/usr/bin/env python3
"""Demo script for testing service-specific configuration step."""

import asyncio
import logging

from textual.app import App

from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.screens.config_wizard import ConfigWizardScreen
from arr_stack_manager.controller import AppController

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class DemoApp(App):
    """Demo application for testing service-specific configuration."""

    CSS = """
    Screen {
        background: $background;
    }
    """

    def on_mount(self) -> None:
        """Handle app mount."""
        # Create a mock controller
        controller = AppController()

        # Create a configuration with some selected services
        config = Configuration(
            puid=1000,
            pgid=1000,
            timezone="America/New_York",
            paths=PathConfig(base_path="/mnt/storage"),
        )

        # Add some selected services
        config.add_service(
            ServiceConfig(
                name="sonarr",
                enabled=True,
                port=8989,
            )
        )
        config.add_service(
            ServiceConfig(
                name="radarr",
                enabled=True,
                port=7878,
            )
        )
        config.add_service(
            ServiceConfig(
                name="jellyfin",
                enabled=True,
                port=8096,
            )
        )

        # Push the wizard screen
        self.push_screen(ConfigWizardScreen(controller, config), self.handle_wizard_result)

    def handle_wizard_result(self, result: Configuration | None) -> None:
        """Handle wizard completion.

        Args:
            result: Configuration result from wizard, or None if cancelled
        """
        if result:
            self.console.print("\n[bold green]Configuration completed![/bold green]")
            self.console.print(f"\nPUID: {result.puid}")
            self.console.print(f"PGID: {result.pgid}")
            self.console.print(f"Timezone: {result.timezone}")
            self.console.print(f"Base Path: {result.paths.base_path}")
            self.console.print(f"\nConfigured Services:")
            for service_name, service_config in result.services.items():
                self.console.print(f"  • {service_name}: Port {service_config.port}")
                if service_config.custom_volumes:
                    self.console.print(f"    Custom volumes: {service_config.custom_volumes}")
        else:
            self.console.print("\n[yellow]Configuration cancelled[/yellow]")

        self.exit()


if __name__ == "__main__":
    app = DemoApp()
    app.run()
