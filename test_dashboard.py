"""Test script for the Dashboard screen."""

import asyncio
from datetime import datetime
from pathlib import Path

from textual.app import App

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.models.stack import StackConfig
from arr_stack_manager.screens.dashboard import DashboardScreen


class TestDashboardApp(App):
    """Test application for the dashboard screen."""

    def __init__(self) -> None:
        """Initialize the test app."""
        super().__init__()
        self.controller = AppController()

        # Create a mock stack configuration
        config = Configuration(
            puid=1000,
            pgid=1000,
            timezone="America/New_York",
            paths=PathConfig(
                base_path="/tmp/test",
                config_path="/tmp/test/config",
                data_path="/tmp/test/data",
            ),
            services={
                "sonarr": ServiceConfig(
                    name="sonarr",
                    enabled=True,
                    port=8989,
                ),
                "radarr": ServiceConfig(
                    name="radarr",
                    enabled=True,
                    port=7878,
                ),
                "prowlarr": ServiceConfig(
                    name="prowlarr",
                    enabled=True,
                    port=9696,
                ),
            },
        )

        stack_config = StackConfig(
            name="test-stack",
            configuration=config,
            compose_path="/tmp/test/docker-compose.yml",
            created_at=datetime.now(),
            last_modified=datetime.now(),
        )

        self.controller.current_stack = stack_config

    def on_mount(self) -> None:
        """Handle app mount."""
        self.push_screen(DashboardScreen(self.controller, "test-stack"))


if __name__ == "__main__":
    app = TestDashboardApp()
    app.run()

