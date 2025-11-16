#!/usr/bin/env python3
"""Test script to directly show the path configuration step."""

import logging
from textual.app import App
from textual.widgets import Header, Footer

from arr_stack_manager.screens.config_wizard import PathConfigurationStep

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class PathStepTestApp(App):
    """Test application for path configuration step."""

    CSS = """
    Screen {
        background: $background;
    }
    """

    def compose(self):
        """Compose the app layout."""
        yield Header()
        yield PathConfigurationStep(base_path="/mnt/storage")
        yield Footer()


if __name__ == "__main__":
    app = PathStepTestApp()
    app.run()
