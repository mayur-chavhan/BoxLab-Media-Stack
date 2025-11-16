"""Tests for the log viewer screen."""

import pytest
from unittest.mock import Mock, MagicMock
from textual.widgets import Button, Input, Label, RichLog, Select

from arr_stack_manager.controller import AppController
from arr_stack_manager.screens.log_viewer import LogLevel, LogViewerScreen


@pytest.fixture
def mock_controller():
    """Create a mock controller for testing."""
    controller = Mock(spec=AppController)

    # Mock docker_manager
    controller.docker_manager = Mock()
    controller.docker_manager.get_service_logs.return_value = [
        "2024-01-15T10:00:00.123Z [INFO] Service started",
        "2024-01-15T10:00:01.456Z [DEBUG] Loading configuration",
        "2024-01-15T10:00:02.789Z [ERROR] Failed to connect to database",
        "2024-01-15T10:00:03.012Z [WARN] Retrying connection",
        "2024-01-15T10:00:04.345Z [INFO] Connection established",
    ]

    # Mock get_service_info
    service_info = Mock()
    service_info.is_running = True
    controller.get_service_info.return_value = service_info

    return controller


@pytest.mark.asyncio
async def test_log_viewer_initialization(mock_controller):
    """Test that LogViewerScreen initializes correctly."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    assert screen.service_name == "sonarr"
    assert screen.controller == mock_controller
    assert screen.is_streaming is False
    assert screen.auto_scroll is True
    assert screen.line_count == 0
    assert screen.filtered_count == 0


@pytest.mark.asyncio
async def test_log_viewer_load_initial_logs(mock_controller):
    """Test loading initial logs on mount."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    await screen._load_initial_logs()

    # Verify logs were loaded
    assert screen.line_count == 5
    assert len(screen._log_buffer) == 5

    # Verify docker_manager was called
    mock_controller.docker_manager.get_service_logs.assert_called_once_with(
        "sonarr",
        lines=500,
        timestamps=True,
    )


def test_log_viewer_add_log_line(mock_controller):
    """Test adding log lines to the viewer."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    screen._add_log_line("Test log line 1", refresh=False)
    screen._add_log_line("Test log line 2", refresh=False)

    assert len(screen._log_buffer) == 2
    assert screen.line_count == 2


def test_log_viewer_should_display_line_all_filter(mock_controller):
    """Test line filtering with ALL filter."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    screen._current_filter = LogLevel.ALL

    assert screen._should_display_line("[INFO] Test message") is True
    assert screen._should_display_line("[ERROR] Error message") is True
    assert screen._should_display_line("[DEBUG] Debug message") is True


def test_log_viewer_should_display_line_error_filter(mock_controller):
    """Test line filtering with ERROR filter."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    screen._current_filter = LogLevel.ERROR

    assert screen._should_display_line("[ERROR] Error message") is True
    assert screen._should_display_line("[FATAL] Fatal error") is True
    assert screen._should_display_line("[INFO] Info message") is False
    assert screen._should_display_line("[DEBUG] Debug message") is False


def test_log_viewer_should_display_line_warning_filter(mock_controller):
    """Test line filtering with WARNING filter."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    screen._current_filter = LogLevel.WARNING

    assert screen._should_display_line("[WARN] Warning message") is True
    assert screen._should_display_line("[WARNING] Another warning") is True
    assert screen._should_display_line("[INFO] Info message") is False
    assert screen._should_display_line("[ERROR] Error message") is False


def test_log_viewer_should_display_line_search_filter(mock_controller):
    """Test line filtering with search term."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    screen._search_term = "database"

    assert screen._should_display_line("Connected to database") is True
    assert screen._should_display_line("Database error occurred") is True
    assert screen._should_display_line("Service started") is False


def test_log_viewer_should_display_line_combined_filters(mock_controller):
    """Test line filtering with both level and search filters."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    screen._current_filter = LogLevel.ERROR
    screen._search_term = "database"

    assert screen._should_display_line("[ERROR] Database connection failed") is True
    assert screen._should_display_line("[ERROR] Network timeout") is False
    assert screen._should_display_line("[INFO] Database connected") is False


def test_log_viewer_matches_level_filter(mock_controller):
    """Test level matching logic."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    # Test ERROR level
    assert screen._matches_level_filter("[ERROR] Test", LogLevel.ERROR) is True
    assert screen._matches_level_filter("[FATAL] Test", LogLevel.ERROR) is True
    assert screen._matches_level_filter("[INFO] Test", LogLevel.ERROR) is False

    # Test WARNING level
    assert screen._matches_level_filter("[WARN] Test", LogLevel.WARNING) is True
    assert screen._matches_level_filter("[WARNING] Test", LogLevel.WARNING) is True
    assert screen._matches_level_filter("[INFO] Test", LogLevel.WARNING) is False

    # Test INFO level
    assert screen._matches_level_filter("[INFO] Test", LogLevel.INFO) is True
    assert screen._matches_level_filter("[INFORMATION] Test", LogLevel.INFO) is True
    assert screen._matches_level_filter("[ERROR] Test", LogLevel.INFO) is False

    # Test DEBUG level
    assert screen._matches_level_filter("[DEBUG] Test", LogLevel.DEBUG) is True
    assert screen._matches_level_filter("[TRACE] Test", LogLevel.DEBUG) is True
    assert screen._matches_level_filter("[INFO] Test", LogLevel.DEBUG) is False


def test_log_viewer_format_log_line(mock_controller):
    """Test log line formatting with syntax highlighting."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    # Test timestamp highlighting
    line = "2024-01-15T10:00:00.123Z [INFO] Test"
    formatted = screen._format_log_line(line)
    assert "[dim]2024-01-15T10:00:00.123Z[/dim]" in formatted

    # Test ERROR highlighting
    line = "[ERROR] Something went wrong"
    formatted = screen._format_log_line(line)
    assert "[bold red]ERROR[/bold red]" in formatted

    # Test WARNING highlighting
    line = "[WARN] Be careful"
    formatted = screen._format_log_line(line)
    assert "[bold yellow]WARN[/bold yellow]" in formatted

    # Test INFO highlighting
    line = "[INFO] Information"
    formatted = screen._format_log_line(line)
    assert "[bold cyan]INFO[/bold cyan]" in formatted

    # Test DEBUG highlighting
    line = "[DEBUG] Debug info"
    formatted = screen._format_log_line(line)
    assert "[dim]DEBUG[/dim]" in formatted

    # Test IP address highlighting
    line = "Connection from 192.168.1.100"
    formatted = screen._format_log_line(line)
    assert "[blue]192.168.1.100[/blue]" in formatted

    # Test URL highlighting
    line = "Fetching https://example.com/api"
    formatted = screen._format_log_line(line)
    assert "[link=https://example.com/api]" in formatted


def test_log_viewer_format_log_line_with_search(mock_controller):
    """Test log line formatting with search term highlighting."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    screen._search_term = "database"

    line = "Connected to database successfully"
    formatted = screen._format_log_line(line)

    assert "[black on yellow]database[/black on yellow]" in formatted


def test_log_viewer_get_stats_text(mock_controller):
    """Test statistics text generation."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    # Test with no filters
    screen.is_streaming = False
    screen.auto_scroll = True
    screen.line_count = 100
    stats = screen._get_stats_text()
    assert "Paused" in stats
    assert "Auto-scroll: ON" in stats
    assert "Lines: 100" in stats

    # Test with streaming
    screen.is_streaming = True
    stats = screen._get_stats_text()
    assert "Streaming" in stats

    # Test with filters
    screen._current_filter = LogLevel.ERROR
    screen.filtered_count = 10
    stats = screen._get_stats_text()
    assert "Showing: 10 / 100 lines" in stats

    # Test with search
    screen._current_filter = LogLevel.ALL
    screen._search_term = "test"
    screen.filtered_count = 25
    stats = screen._get_stats_text()
    assert "Showing: 25 / 100 lines" in stats


def test_log_viewer_handle_clear(mock_controller, monkeypatch):
    """Test clearing logs."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    # Mock notify to avoid NoActiveAppError
    screen.notify = Mock()

    # Add some logs
    screen._add_log_line("Line 1", refresh=False)
    screen._add_log_line("Line 2", refresh=False)
    assert screen.line_count == 2

    # Clear logs
    screen.handle_clear()

    assert len(screen._log_buffer) == 0
    assert screen.line_count == 0
    assert screen.filtered_count == 0
    screen.notify.assert_called_once()


def test_log_viewer_handle_toggle_streaming(mock_controller):
    """Test toggling streaming state."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    # Mock notify and run_worker to avoid NoActiveAppError
    screen.notify = Mock()
    screen.run_worker = Mock()

    assert screen.is_streaming is False

    # Start streaming
    screen.handle_toggle_streaming()
    assert screen.is_streaming is True

    # Stop streaming
    screen.handle_toggle_streaming()
    assert screen.is_streaming is False


def test_log_viewer_handle_toggle_autoscroll(mock_controller):
    """Test toggling auto-scroll."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    # Mock notify to avoid NoActiveAppError
    screen.notify = Mock()

    assert screen.auto_scroll is True

    # Disable auto-scroll
    screen.handle_toggle_autoscroll()
    assert screen.auto_scroll is False

    # Enable auto-scroll
    screen.handle_toggle_autoscroll()
    assert screen.auto_scroll is True


def test_log_viewer_buffer_max_size(mock_controller):
    """Test that log buffer respects max size."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    # Add more lines than max_lines (10000)
    for i in range(10500):
        screen._add_log_line(f"Line {i}", refresh=False)

    # Buffer should be capped at 10000
    assert len(screen._log_buffer) == 10000
    assert screen.line_count == 10500  # Count tracks all lines added


def test_log_viewer_export_logs(mock_controller, tmp_path, monkeypatch):
    """Test exporting logs to file."""
    screen = LogViewerScreen(
        controller=mock_controller,
        service_name="sonarr",
    )

    # Mock notify to avoid NoActiveAppError
    screen.notify = Mock()

    # Mock Path.home() to use tmp_path
    from pathlib import Path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    # Add some logs
    screen._add_log_line("[INFO] Test log 1", refresh=False)
    screen._add_log_line("[ERROR] Test log 2", refresh=False)

    # Export logs
    screen.handle_export()

    # Verify export directory was created
    export_dir = tmp_path / ".config" / "arr-stack-manager" / "exports"
    assert export_dir.exists()

    # Verify log file was created
    log_files = list(export_dir.glob("sonarr_logs_*.txt"))
    assert len(log_files) == 1

    # Verify content
    content = log_files[0].read_text()
    assert "Test log 1" in content
    assert "Test log 2" in content
    screen.notify.assert_called_once()
