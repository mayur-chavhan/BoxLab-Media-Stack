"""Tests for the Dashboard screen."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.configuration import Configuration, PathConfig, ServiceConfig
from arr_stack_manager.models.stack import StackConfig, StackStatus
from arr_stack_manager.screens.dashboard import (
    ActivityLog,
    DashboardScreen,
    StackStatusOverview,
)


@pytest.fixture
def mock_controller(tmp_path):
    """Create a mock controller with test configuration."""
    with patch("arr_stack_manager.controller.DockerManager"):
        controller = AppController(config_dir=tmp_path / "config")

        # Create a test stack configuration
        config = Configuration(
            puid=1000,
            pgid=1000,
            timezone="America/New_York",
            paths=PathConfig(
                base_path=str(tmp_path / "stack"),
                config_path=str(tmp_path / "stack" / "config"),
                data_path=str(tmp_path / "stack" / "data"),
            ),
            services={
                "sonarr": ServiceConfig(name="sonarr", enabled=True, port=8989),
                "radarr": ServiceConfig(name="radarr", enabled=True, port=7878),
                "prowlarr": ServiceConfig(name="prowlarr", enabled=True, port=9696),
            },
        )

        stack_config = StackConfig(
            name="test-stack",
            configuration=config,
            compose_path=str(tmp_path / "docker-compose.yml"),
            created_at=datetime.now(),
            last_modified=datetime.now(),
        )

        controller.current_stack = stack_config
        return controller


@pytest.fixture
def sample_stack_status():
    """Create a sample stack status for testing."""
    return StackStatus(
        name="test-stack",
        total_services=3,
        running_services=2,
        stopped_services=1,
        error_services=0,
    )


def test_activity_log_initialization():
    """Test that ActivityLog initializes correctly."""
    log = ActivityLog(max_entries=10)

    assert log.max_entries == 10
    assert len(log._entries) == 0


def test_activity_log_add_entry():
    """Test adding entries to activity log."""
    log = ActivityLog(max_entries=5)

    log.add_entry("Service started")
    log.add_entry("Configuration updated")

    assert len(log._entries) == 2
    assert log._entries[0][1] == "Service started"
    assert log._entries[1][1] == "Configuration updated"


def test_activity_log_max_entries():
    """Test that activity log respects max entries limit."""
    log = ActivityLog(max_entries=3)

    # Add more entries than the limit
    for i in range(10):
        log.add_entry(f"Entry {i}")

    # Should keep only recent entries (up to 2x max for buffer)
    assert len(log._entries) <= 6  # max_entries * 2


def test_stack_status_overview_initialization(sample_stack_status):
    """Test that StackStatusOverview initializes correctly."""
    overview = StackStatusOverview(stack_status=sample_stack_status)

    assert overview.stack_status == sample_stack_status


def test_stack_status_overview_format_status_running():
    """Test status formatting for running stack."""
    status = StackStatus(
        name="test",
        total_services=3,
        running_services=3,
        stopped_services=0,
        error_services=0,
    )
    overview = StackStatusOverview(stack_status=status)

    formatted = overview._format_status_indicator()
    assert "Running" in formatted
    assert "3/3" in formatted


def test_stack_status_overview_format_status_error():
    """Test status formatting for stack with errors."""
    status = StackStatus(
        name="test",
        total_services=3,
        running_services=1,
        stopped_services=1,
        error_services=1,
    )
    overview = StackStatusOverview(stack_status=status)

    formatted = overview._format_status_indicator()
    assert "Error" in formatted


def test_stack_status_overview_format_status_stopped():
    """Test status formatting for stopped stack."""
    status = StackStatus(
        name="test",
        total_services=3,
        running_services=0,
        stopped_services=3,
        error_services=0,
    )
    overview = StackStatusOverview(stack_status=status)

    formatted = overview._format_status_indicator()
    assert "Stopped" in formatted


def test_stack_status_overview_get_status_class():
    """Test getting CSS class for status."""
    # Healthy status
    status = StackStatus(
        name="test",
        total_services=3,
        running_services=3,
        stopped_services=0,
        error_services=0,
    )
    overview = StackStatusOverview(stack_status=status)
    assert overview._get_status_class() == "status-running"

    # Error status
    status.error_services = 1
    status.running_services = 2
    overview.stack_status = status
    assert overview._get_status_class() == "status-error"

    # Stopped status
    status.error_services = 0
    status.running_services = 0
    status.stopped_services = 3
    overview.stack_status = status
    assert overview._get_status_class() == "status-stopped"


def test_stack_status_overview_update_status(sample_stack_status):
    """Test updating stack status."""
    overview = StackStatusOverview()

    assert overview.stack_status is None

    overview.update_status(sample_stack_status)
    assert overview.stack_status == sample_stack_status


def test_dashboard_screen_initialization(mock_controller):
    """Test that DashboardScreen initializes correctly."""
    screen = DashboardScreen(mock_controller, "test-stack")

    assert screen.controller == mock_controller
    assert screen.stack_name == "test-stack"
    assert len(screen._service_cards) == 0
    assert screen._auto_refresh_enabled is True
    assert screen._refresh_interval == 5


def test_dashboard_screen_initialization_without_stack_name(mock_controller):
    """Test dashboard initialization without explicit stack name."""
    screen = DashboardScreen(mock_controller)

    assert screen.controller == mock_controller
    assert screen.stack_name is None


def test_dashboard_screen_bindings():
    """Test that dashboard has correct key bindings."""
    # Create a minimal controller for testing
    with patch("arr_stack_manager.controller.DockerManager"):
        controller = AppController()
        screen = DashboardScreen(controller)

        # Check that bindings are defined
        assert len(screen.BINDINGS) > 0

        # Check for specific bindings
        binding_keys = [binding[0] for binding in screen.BINDINGS]
        assert "q" in binding_keys  # Quit
        assert "s" in binding_keys  # Services
        assert "c" in binding_keys  # Config
        assert "h" in binding_keys  # Help
        assert "r" in binding_keys  # Refresh


def test_dashboard_screen_service_cards_dict(mock_controller):
    """Test that service cards dictionary is properly initialized."""
    screen = DashboardScreen(mock_controller, "test-stack")

    assert isinstance(screen._service_cards, dict)
    assert len(screen._service_cards) == 0


def test_dashboard_screen_auto_refresh_settings(mock_controller):
    """Test auto-refresh settings."""
    screen = DashboardScreen(mock_controller)

    assert screen._auto_refresh_enabled is True
    assert screen._refresh_interval == 5

    # Test disabling auto-refresh
    screen._auto_refresh_enabled = False
    assert screen._auto_refresh_enabled is False

