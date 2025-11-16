"""Tests for the Stack Manager screen."""

from unittest.mock import MagicMock, patch

import pytest

from arr_stack_manager.controller import AppController
from arr_stack_manager.models.service import ResourceMetrics, ServiceInfo, ServiceStatus
from arr_stack_manager.models.validation import OperationResult
from arr_stack_manager.screens.stack_manager import (
    ActionButtons,
    LogPreview,
    ServiceDetails,
    StackManagerScreen,
    VolumePortInfo,
)


@pytest.fixture
def mock_controller(tmp_path):
    """Create a mock controller for testing."""
    with patch("arr_stack_manager.controller.DockerManager"):
        controller = AppController(config_dir=tmp_path / "config")
        return controller


@pytest.fixture
def sample_service_info_running():
    """Create a sample running service info."""
    return ServiceInfo(
        name="sonarr",
        status=ServiceStatus.RUNNING,
        container_id="abc123",
        image="lscr.io/linuxserver/sonarr:latest",
        uptime=3600,  # 1 hour
        web_ui_url="http://localhost:8989",
        metrics=ResourceMetrics(
            cpu_percent=2.5,
            memory_usage=150 * 1024 * 1024,  # 150MB
            memory_limit=512 * 1024 * 1024,  # 512MB
            network_rx=1024 * 1024,  # 1MB
            network_tx=512 * 1024,  # 512KB
        ),
    )


@pytest.fixture
def sample_service_info_stopped():
    """Create a sample stopped service info."""
    return ServiceInfo(
        name="radarr",
        status=ServiceStatus.STOPPED,
        container_id="def456",
        image="lscr.io/linuxserver/radarr:latest",
        uptime=None,
        web_ui_url=None,
        metrics=None,
    )


def test_service_details_initialization():
    """Test that ServiceDetails initializes correctly."""
    details = ServiceDetails()
    assert details.service_info is None


def test_service_details_with_service_info(sample_service_info_running):
    """Test ServiceDetails with service information."""
    details = ServiceDetails(service_info=sample_service_info_running)
    assert details.service_info == sample_service_info_running


def test_service_details_format_status_running(sample_service_info_running):
    """Test status formatting for running service."""
    details = ServiceDetails(service_info=sample_service_info_running)
    formatted = details._format_status()
    assert "Running" in formatted
    assert "●" in formatted


def test_service_details_format_status_stopped(sample_service_info_stopped):
    """Test status formatting for stopped service."""
    details = ServiceDetails(service_info=sample_service_info_stopped)
    formatted = details._format_status()
    assert "Stopped" in formatted
    assert "○" in formatted


def test_service_details_update_service_info(sample_service_info_running):
    """Test updating service information."""
    details = ServiceDetails()
    assert details.service_info is None

    details.update_service_info(sample_service_info_running)
    assert details.service_info == sample_service_info_running


def test_volume_port_info_initialization():
    """Test that VolumePortInfo initializes correctly."""
    info = VolumePortInfo()
    assert info.service_info is None


def test_volume_port_info_with_service(sample_service_info_running):
    """Test VolumePortInfo with service information."""
    info = VolumePortInfo(service_info=sample_service_info_running)
    assert info.service_info == sample_service_info_running


def test_action_buttons_initialization():
    """Test that ActionButtons initializes correctly."""
    buttons = ActionButtons(service_name="sonarr", is_running=False)
    assert buttons.service_name == "sonarr"
    assert buttons.is_running is False


def test_action_buttons_running_state():
    """Test ActionButtons in running state."""
    buttons = ActionButtons(service_name="sonarr", is_running=True)
    assert buttons.is_running is True


def test_log_preview_initialization():
    """Test that LogPreview initializes correctly."""
    preview = LogPreview(service_name="sonarr")
    assert preview.service_name == "sonarr"
    assert len(preview._log_lines) == 0


def test_log_preview_update_logs():
    """Test updating log lines."""
    preview = LogPreview(service_name="sonarr")

    log_lines = [
        "[INFO] Service started",
        "[INFO] Configuration loaded",
        "[INFO] Ready to accept connections",
    ]

    preview.update_logs(log_lines)
    assert preview._log_lines == log_lines


def test_stack_manager_screen_initialization(mock_controller):
    """Test that StackManagerScreen initializes correctly."""
    screen = StackManagerScreen(mock_controller, "sonarr")

    assert screen.controller == mock_controller
    assert screen.service_name == "sonarr"
    assert screen._service_info is None


def test_stack_manager_screen_bindings(mock_controller):
    """Test that stack manager has correct key bindings."""
    screen = StackManagerScreen(mock_controller, "sonarr")

    # Check that bindings are defined
    assert len(screen.BINDINGS) > 0

    # Check for specific bindings
    binding_keys = [binding[0] for binding in screen.BINDINGS]
    assert "escape" in binding_keys  # Back
    assert "q" in binding_keys  # Quit
    assert "r" in binding_keys  # Refresh


def test_stack_manager_handle_operation_result_success(mock_controller):
    """Test handling successful operation result."""
    screen = StackManagerScreen(mock_controller, "sonarr")

    result = OperationResult.success_result(
        message="Service started successfully",
        details="Container ID: abc123",
    )

    # Mock notify to avoid app context issues
    with patch.object(screen, "notify"):
        screen._handle_operation_result(result, "start")
        screen.notify.assert_called_once()


def test_stack_manager_handle_operation_result_failure(mock_controller):
    """Test handling failed operation result."""
    screen = StackManagerScreen(mock_controller, "sonarr")

    result = OperationResult.failure_result(
        message="Failed to start service",
        details="Docker daemon not available",
    )

    # Mock notify to avoid app context issues
    with patch.object(screen, "notify"):
        screen._handle_operation_result(result, "start")
        screen.notify.assert_called_once()


def test_stack_manager_action_back(mock_controller):
    """Test back action."""
    screen = StackManagerScreen(mock_controller, "sonarr")

    # Mock the app property using patch
    mock_app = MagicMock()
    with patch.object(type(screen), "app", new_callable=lambda: property(lambda self: mock_app)):
        screen.action_back()
        mock_app.pop_screen.assert_called_once()


def test_stack_manager_action_quit(mock_controller):
    """Test quit action."""
    screen = StackManagerScreen(mock_controller, "sonarr")

    # Mock the app property using patch
    mock_app = MagicMock()
    with patch.object(type(screen), "app", new_callable=lambda: property(lambda self: mock_app)):
        screen.action_quit()
        mock_app.exit.assert_called_once()


def test_service_details_no_service():
    """Test ServiceDetails with no service information."""
    details = ServiceDetails(service_info=None)
    assert details.service_info is None


def test_action_buttons_different_services():
    """Test ActionButtons with different service names."""
    buttons1 = ActionButtons(service_name="sonarr", is_running=True)
    buttons2 = ActionButtons(service_name="radarr", is_running=False)

    assert buttons1.service_name == "sonarr"
    assert buttons2.service_name == "radarr"
    assert buttons1.is_running is True
    assert buttons2.is_running is False


def test_log_preview_empty_logs():
    """Test LogPreview with empty logs."""
    preview = LogPreview(service_name="sonarr")
    preview.update_logs([])

    assert len(preview._log_lines) == 0


def test_log_preview_many_logs():
    """Test LogPreview with many log lines."""
    preview = LogPreview(service_name="sonarr")

    # Create 100 log lines
    log_lines = [f"[INFO] Log line {i}" for i in range(100)]
    preview.update_logs(log_lines)

    assert len(preview._log_lines) == 100


def test_service_details_with_metrics(sample_service_info_running):
    """Test ServiceDetails displays metrics correctly."""
    details = ServiceDetails(service_info=sample_service_info_running)

    assert details.service_info.metrics is not None
    assert details.service_info.metrics.cpu_percent == 2.5
    assert details.service_info.metrics.memory_usage == 150 * 1024 * 1024


def test_service_details_without_metrics(sample_service_info_stopped):
    """Test ServiceDetails with no metrics."""
    details = ServiceDetails(service_info=sample_service_info_stopped)

    assert details.service_info.metrics is None


def test_stack_manager_screen_service_name_storage(mock_controller):
    """Test that service name is properly stored."""
    screen = StackManagerScreen(mock_controller, "prowlarr")

    assert screen.service_name == "prowlarr"
