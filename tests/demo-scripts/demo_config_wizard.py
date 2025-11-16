"""Demo script for testing the Configuration Wizard screen."""

import logging
from pathlib import Path

from textual.app import App

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.screens.config_wizard import ConfigWizardScreen

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class ConfigWizardDemoApp(App):
    """Demo application for testing the Configuration Wizard screen."""

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
        """Handle app mount event."""
        # Create a sample configuration with selected services
        config = Configuration(
            puid=1000,
            pgid=1000,
            timezone="UTC",
            paths=PathConfig(base_path="/tmp/arr-stack"),
            services={
                "sonarr": ServiceConfig(name="sonarr", enabled=True, port=8989),
                "radarr": ServiceConfig(name="radarr", enabled=True, port=7878),
                "prowlarr": ServiceConfig(name="prowlarr", enabled=True, port=9696),
            },
        )

        # Push the wizard screen
        self.push_screen(ConfigWizardScreen(self.controller, config), self.handle_wizard_result)

    def handle_wizard_result(self, result: Configuration | None) -> None:
        """Handle the wizard result.

        Args:
            result: The configuration from the wizard, or None if cancelled
        """
        if result:
            self.console.print("\n[bold green]Wizard completed successfully![/bold green]")
            self.console.print(f"\nConfiguration:")
            self.console.print(f"  PUID: {result.puid}")
            self.console.print(f"  PGID: {result.pgid}")
            self.console.print(f"  Timezone: {result.timezone}")
            self.console.print(f"  Base Path: {result.paths.base_path}")
            self.console.print(f"  Selected Services: {', '.join(result.get_selected_services())}")
        else:
            self.console.print("\n[bold yellow]Wizard cancelled[/bold yellow]")

        # Exit the app
        self.exit()


if __name__ == "__main__":
    app = ConfigWizardDemoApp()
    app.run()
