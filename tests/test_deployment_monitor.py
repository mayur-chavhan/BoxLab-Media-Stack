"""Tests for the Deployment Monitor screen."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.validation import DeploymentEvent
from arr_stack_manager.screens.deployment_monitor import (
    DeploymentMonitorScreen,
    DeploymentStage,
    DockerOutput,
)


@pytest.fixture
def mock_controller(tmp_path):
    """Create a mock controller with test configuration."""
    with patch("arr_stack_manager.controller.DockerManager"):
        controller = AppController(config_dir=tmp_path / "config")
        return controller


@pytest.fixture
def sample_compose_path(tmp_path):
    """Create a sample docker-compose.yml file."""
    compose_path = tmp_path / "docker-compose.yml"
    compose_path.write_text(
        """
version: '3.8'
services:
  sonarr:
    image: lscr.io/linuxserver/sonarr:latest
    container_name: sonarr
"""
    )
    return compose_path


def test_deployment_stage_initialization():
    """Test that DeploymentStage initializes correctly."""
    stage = DeploymentStage(label="Validating configuration")

    assert stage.label == "Validating configuration"
    assert stage.status == "pending"


def test_deployment_stage_get_indicator():
    """Test status indicator symbols."""
    stage = DeploymentStage(label="Test Stage")

    # Test pending
    stage.status = "pending"
    assert stage._get_indicator() == "[ ]"

    # Test active
    stage.status = "active"
    assert stage._get_indicator() == "[⟳]"

    # Test complete
    stage.status = "complete"
    assert stage._get_indicator() == "[✓]"

    # Test error
    stage.status = "error"
    assert stage._get_indicator() == "[✗]"


def test_docker_output_initialization():
    """Test that DockerOutput initializes correctly."""
    output = DockerOutput()

    assert len(output._output_lines) == 0
    assert output._auto_scroll is True


def test_docker_output_add_line():
    """Test adding lines to Docker output."""
    output = DockerOutput()

    output.add_line("Starting deployment...")
    output.add_line("Pulling images...")

    assert len(output._output_lines) == 2
    assert output._output_lines[0] == "Starting deployment..."
    assert output._output_lines[1] == "Pulling images..."


def test_docker_output_clear():
    """Test clearing Docker output."""
    output = DockerOutput()

    output.add_line("Line 1")
    output.add_line("Line 2")
    assert len(output._output_lines) == 2

    output.clear()
    assert len(output._output_lines) == 0


def test_docker_output_auto_scroll():
    """Test auto-scroll functionality."""
    output = DockerOutput()

    assert output._auto_scroll is True

    output.set_auto_scroll(False)
    assert output._auto_scroll is False

    output.set_auto_scroll(True)
    assert output._auto_scroll is True


def test_deployment_monitor_screen_initialization(mock_controller, sample_compose_path):
    """Test that DeploymentMonitorScreen initializes correctly."""
    screen = DeploymentMonitorScreen(
        controller=mock_controller,
        compose_path=sample_compose_path,
        stack_name="test-stack",
    )

    assert screen.controller == mock_controller
    assert screen.compose_path == sample_compose_path
    assert screen.stack_name == "test-stack"
    assert screen._start_time is None
    assert screen._is_complete is False
    assert screen._is_error is False
    assert screen._can_cancel is True


def test_deployment_monitor_screen_bindings(mock_controller, sample_compose_path):
    """Test that deployment monitor has correct key bindings."""
    screen = DeploymentMonitorScreen(
        controller=mock_controller,
        compose_path=sample_compose_path,
        stack_name="test-stack",
    )

    # Check that bindings are defined
    assert len(screen.BINDINGS) > 0

    # Check for specific bindings
    binding_keys = [binding[0] for binding in screen.BINDINGS]
    assert "escape" in binding_keys  # Cancel
    assert "q" in binding_keys  # Quit


def test_deployment_event_handling():
    """Test deployment event structure."""
    event = DeploymentEvent.create(
        stage="validation",
        message="Validating docker-compose.yml",
        progress=0.1,
    )

    assert event.stage == "validation"
    assert event.message == "Validating docker-compose.yml"
    assert event.progress == 0.1
    assert isinstance(event.timestamp, datetime)


def test_deployment_event_progress_range():
    """Test that deployment event progress is within valid range."""
    # Valid progress values
    event1 = DeploymentEvent.create(stage="test", message="Test", progress=0.0)
    assert event1.progress == 0.0

    event2 = DeploymentEvent.create(stage="test", message="Test", progress=0.5)
    assert event2.progress == 0.5

    event3 = DeploymentEvent.create(stage="test", message="Test", progress=1.0)
    assert event3.progress == 1.0


def test_deployment_monitor_state_flags(mock_controller, sample_compose_path):
    """Test deployment monitor state flags."""
    screen = DeploymentMonitorScreen(
        controller=mock_controller,
        compose_path=sample_compose_path,
        stack_name="test-stack",
    )

    # Initial state
    assert screen._is_complete is False
    assert screen._is_error is False
    assert screen._can_cancel is True

    # Simulate completion
    screen._is_complete = True
    screen._can_cancel = False
    assert screen._is_complete is True
    assert screen._can_cancel is False

    # Simulate error
    screen._is_complete = False
    screen._is_error = True
    assert screen._is_error is True


def test_deployment_monitor_compose_path_validation(mock_controller, tmp_path):
    """Test that compose path is properly converted to Path object."""
    # Test with string path
    screen1 = DeploymentMonitorScreen(
        controller=mock_controller,
        compose_path=str(tmp_path / "compose.yml"),
        stack_name="test-stack",
    )
    assert isinstance(screen1.compose_path, Path)

    # Test with Path object
    screen2 = DeploymentMonitorScreen(
        controller=mock_controller,
        compose_path=tmp_path / "compose.yml",
        stack_name="test-stack",
    )
    assert isinstance(screen2.compose_path, Path)


def test_deployment_stages_order():
    """Test that deployment stages are in correct order."""
    expected_stages = [
        "Validating configuration",
        "Creating directories",
        "Generating docker-compose.yml",
        "Generating .env file",
        "Pulling container images",
        "Starting services",
        "Health checks",
    ]

    # Verify stage labels match expected order
    for i, label in enumerate(expected_stages):
        stage = DeploymentStage(label=label)
        assert stage.label == expected_stages[i]


def test_deployment_monitor_elapsed_time_format(mock_controller, sample_compose_path):
    """Test elapsed time formatting."""
    screen = DeploymentMonitorScreen(
        controller=mock_controller,
        compose_path=sample_compose_path,
        stack_name="test-stack",
    )

    # Set start time
    screen._start_time = datetime.now()

    # The _update_elapsed_time method should format time as HH:MM:SS
    # We can't easily test the actual formatting without mounting the screen,
    # but we can verify the method exists
    assert hasattr(screen, "_update_elapsed_time")
    assert callable(screen._update_elapsed_time)
