"""Tests for UI components."""

import pytest

from arr_stack_manager.components.log_viewer import LogViewer
from arr_stack_manager.components.progress_bar import EnhancedProgressBar
from arr_stack_manager.components.service_card import ServiceCard
from arr_stack_manager.components.service_list import ServiceList, ServiceListItem
from arr_stack_manager.models.service import ResourceMetrics, ServiceInfo, ServiceStatus


@pytest.fixture
def sample_service_info():
    """Create a sample service info for testing."""
    return ServiceInfo(
        name="sonarr",
        status=ServiceStatus.RUNNING,
        container_id="abc123",
        image="lscr.io/linuxserver/sonarr:latest",
        uptime=3600,
        web_ui_url="http://localhost:8989",
        metrics=ResourceMetrics(
            cpu_percent=2.5,
            memory_usage=150 * 1024 * 1024,  # 150MB
            memory_limit=512 * 1024 * 1024,  # 512MB
        ),
    )


def test_service_card_initialization(sample_service_info):
    """Test that ServiceCard initializes correctly."""
    card = ServiceCard(sample_service_info)

    assert card.service_info == sample_service_info
    assert card.show_actions is True


def test_service_card_without_actions(sample_service_info):
    """Test ServiceCard without action buttons."""
    card = ServiceCard(sample_service_info, show_actions=False)

    assert card.show_actions is False


def test_service_card_format_status(sample_service_info):
    """Test status formatting."""
    card = ServiceCard(sample_service_info)

    assert card._format_status() == "● Running"

    sample_service_info.status = ServiceStatus.STOPPED
    card.service_info = sample_service_info
    assert card._format_status() == "○ Stopped"


def test_log_viewer_initialization():
    """Test that LogViewer initializes correctly."""
    viewer = LogViewer("sonarr", max_lines=500, auto_scroll=True)

    assert viewer.service_name == "sonarr"
    assert viewer.max_lines == 500
    assert viewer.auto_scroll is True
    assert viewer.is_streaming is False
    assert len(viewer._log_buffer) == 0


def test_log_viewer_add_log_line():
    """Test adding log lines."""
    viewer = LogViewer("sonarr")

    viewer.add_log_line("Test log line 1")
    viewer.add_log_line("Test log line 2")

    assert len(viewer._log_buffer) == 2
    assert viewer._line_count == 2


def test_log_viewer_add_multiple_lines():
    """Test adding multiple log lines at once."""
    viewer = LogViewer("sonarr")

    lines = ["Line 1", "Line 2", "Line 3"]
    viewer.add_log_lines(lines)

    assert len(viewer._log_buffer) == 3
    assert viewer._line_count == 3


def test_log_viewer_clear_logs():
    """Test clearing logs."""
    viewer = LogViewer("sonarr")

    viewer.add_log_lines(["Line 1", "Line 2"])
    assert len(viewer._log_buffer) == 2

    viewer.clear_logs()
    assert len(viewer._log_buffer) == 0
    assert viewer._line_count == 0


def test_log_viewer_max_lines():
    """Test that log buffer respects max_lines limit."""
    viewer = LogViewer("sonarr", max_lines=3)

    viewer.add_log_lines(["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"])

    # Should only keep last 3 lines
    assert len(viewer._log_buffer) == 3
    assert "Line 3" in viewer._log_buffer
    assert "Line 4" in viewer._log_buffer
    assert "Line 5" in viewer._log_buffer


def test_log_viewer_toggle_auto_scroll():
    """Test toggling auto-scroll."""
    viewer = LogViewer("sonarr", auto_scroll=True)

    assert viewer.auto_scroll is True

    viewer.toggle_auto_scroll()
    assert viewer.auto_scroll is False

    viewer.toggle_auto_scroll()
    assert viewer.auto_scroll is True


def test_log_viewer_set_streaming():
    """Test setting streaming state."""
    viewer = LogViewer("sonarr")

    assert viewer.is_streaming is False

    viewer.set_streaming(True)
    assert viewer.is_streaming is True

    viewer.set_streaming(False)
    assert viewer.is_streaming is False


def test_enhanced_progress_bar_initialization():
    """Test that EnhancedProgressBar initializes correctly."""
    progress = EnhancedProgressBar("Test Task", total=100.0)

    assert progress.title == "Test Task"
    assert progress.total == 100.0
    assert progress.show_percentage is True
    assert progress._progress == 0.0


def test_enhanced_progress_bar_update():
    """Test updating progress."""
    progress = EnhancedProgressBar("Test Task", total=100.0)

    progress.update_progress(50.0, status="Processing...")

    assert progress.progress == 50.0
    assert progress._status_message == "Processing..."
    assert progress.percentage == 50.0


def test_enhanced_progress_bar_complete():
    """Test marking progress as complete."""
    progress = EnhancedProgressBar("Test Task", total=100.0)

    progress.set_complete("Task finished")

    assert progress.is_complete is True
    assert progress.progress == 100.0
    assert "✓" in progress._status_message


def test_enhanced_progress_bar_error():
    """Test setting error state."""
    progress = EnhancedProgressBar("Test Task", total=100.0)

    progress.set_error("Something went wrong")

    assert "✗" in progress._status_message
    assert "Something went wrong" in progress._status_message


def test_enhanced_progress_bar_reset():
    """Test resetting progress."""
    progress = EnhancedProgressBar("Test Task", total=100.0)

    progress.update_progress(75.0, status="Almost done")
    progress.reset()

    assert progress.progress == 0.0
    assert progress._status_message == ""
    assert progress.percentage == 0.0


def test_service_list_item_initialization():
    """Test that ServiceListItem initializes correctly."""
    item = ServiceListItem(
        service_id="sonarr",
        name="Sonarr",
        description="TV show automation",
        category="Media Management",
        selected=False,
    )

    assert item.service_id == "sonarr"
    assert item.service_name == "Sonarr"
    assert item.description == "TV show automation"
    assert item.category == "Media Management"
    assert item._selected is False


def test_service_list_item_set_selected():
    """Test setting selection state."""
    item = ServiceListItem(
        service_id="sonarr",
        name="Sonarr",
        description="TV show automation",
        category="Media Management",
    )

    assert item._selected is False

    item.set_selected(True)
    assert item._selected is True

    item.set_selected(False)
    assert item._selected is False


def test_service_list_initialization():
    """Test that ServiceList initializes correctly."""
    services = {
        "Media Management": {
            "sonarr": {"name": "Sonarr", "description": "TV show automation"},
            "radarr": {"name": "Radarr", "description": "Movie automation"},
        }
    }

    service_list = ServiceList(title="Select Services", services=services)

    assert service_list.list_title == "Select Services"
    assert len(service_list.services) == 1
    assert "Media Management" in service_list.services


def test_service_list_get_selected_services():
    """Test getting selected services."""
    service_list = ServiceList()

    assert service_list.get_selected_services() == []

    service_list._selected_services = {"sonarr", "radarr"}
    selected = service_list.get_selected_services()

    assert len(selected) == 2
    assert "sonarr" in selected
    assert "radarr" in selected


def test_service_list_set_selected_services():
    """Test setting selected services."""
    service_list = ServiceList()

    service_list.set_selected_services(["sonarr", "radarr", "prowlarr"])

    assert len(service_list._selected_services) == 3
    assert "sonarr" in service_list._selected_services
    assert "radarr" in service_list._selected_services
    assert "prowlarr" in service_list._selected_services


def test_service_list_clear_selection():
    """Test clearing selection."""
    service_list = ServiceList()

    service_list._selected_services = {"sonarr", "radarr"}
    assert len(service_list._selected_services) == 2

    service_list.clear_selection()
    assert len(service_list._selected_services) == 0


def test_service_list_has_selection():
    """Test checking if any services are selected."""
    service_list = ServiceList()

    assert service_list.has_selection is False

    service_list._selected_services.add("sonarr")
    assert service_list.has_selection is True


def test_service_list_selection_count():
    """Test getting selection count."""
    service_list = ServiceList()

    assert service_list.selection_count == 0

    service_list._selected_services = {"sonarr", "radarr", "prowlarr"}
    assert service_list.selection_count == 3
