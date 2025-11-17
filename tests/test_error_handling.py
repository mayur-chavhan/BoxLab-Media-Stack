"""Tests for error handling system."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from arr_stack_manager.utils.error_boundary import ErrorBoundary, ErrorScreen
from arr_stack_manager.utils.errors import (
    ConfigurationError,
    DockerError,
    ErrorCategory,
    ErrorDisplay,
    ErrorHandler,
    FileSystemError,
    NetworkError,
    PermissionError,
    StackManagerError,
    ValidationError,
    handle_error,
    handle_exception,
)
from arr_stack_manager.utils.state_manager import StateManager


class TestErrorDisplay:
    """Test ErrorDisplay class."""

    def test_error_display_creation(self):
        """Test creating an error display."""
        error = ErrorDisplay(
            title="Test Error",
            message="This is a test error",
            remediation=["Step 1", "Step 2"],
            category=ErrorCategory.VALIDATION,
        )

        assert error.title == "Test Error"
        assert error.message == "This is a test error"
        assert len(error.remediation) == 2
        assert error.category == ErrorCategory.VALIDATION

    def test_error_display_formatting(self):
        """Test error display formatting."""
        error = ErrorDisplay(
            title="Test Error",
            message="This is a test error",
            remediation=["Step 1", "Step 2"],
            technical_details="Technical info",
        )

        formatted = error.format_for_display()
        assert "Test Error" in formatted
        assert "This is a test error" in formatted
        assert "Step 1" in formatted
        assert "Technical info" in formatted

    def test_error_display_log_formatting(self):
        """Test error display log formatting."""
        error = ErrorDisplay(
            title="Test Error",
            message="This is a test error",
            remediation=["Step 1"],
            category=ErrorCategory.DOCKER,
        )

        log_msg = error.format_for_log()
        assert "DOCKER" in log_msg
        assert "Test Error" in log_msg
        assert "This is a test error" in log_msg


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_stack_manager_error(self):
        """Test base StackManagerError."""
        error = StackManagerError("Test error", ErrorCategory.VALIDATION, "Details")

        assert str(error) == "Test error"
        assert error.category == ErrorCategory.VALIDATION
        assert error.details == "Details"
        assert error.timestamp is not None

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input", "Field is required")

        assert error.category == ErrorCategory.VALIDATION
        assert error.message == "Invalid input"
        assert error.details == "Field is required"

    def test_docker_error(self):
        """Test DockerError."""
        error = DockerError("Docker unavailable")

        assert error.category == ErrorCategory.DOCKER
        assert error.message == "Docker unavailable"

    def test_filesystem_error(self):
        """Test FileSystemError."""
        error = FileSystemError("Path not found")

        assert error.category == ErrorCategory.FILESYSTEM

    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Port in use")

        assert error.category == ErrorCategory.NETWORK

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid config")

        assert error.category == ErrorCategory.CONFIGURATION

    def test_permission_error(self):
        """Test PermissionError."""
        error = PermissionError("Access denied")

        assert error.category == ErrorCategory.PERMISSION


class TestErrorHandler:
    """Test ErrorHandler class."""

    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        handler = ErrorHandler(enable_logging=False)
        assert handler is not None

    def test_handle_known_error(self):
        """Test handling a known error type."""
        handler = ErrorHandler(enable_logging=False)
        error_display = handler.handle_error(
            "docker_unavailable"
        )

        assert error_display.title == "Docker Not Available"
        assert "Docker daemon" in error_display.message
        assert len(error_display.remediation) > 0
        assert error_display.category == ErrorCategory.DOCKER

    def test_handle_error_with_formatting(self):
        """Test handling error with variable formatting."""
        handler = ErrorHandler(enable_logging=False)
        error_display = handler.handle_error(
            "port_in_use",
            port=8080
        )

        assert "8080" in error_display.message
        assert any("8080" in step for step in error_display.remediation)

    def test_handle_unknown_error(self):
        """Test handling an unknown error type."""
        handler = ErrorHandler(enable_logging=False)
        error_display = handler.handle_error(
            "unknown_error_type",
            message="Custom error message"
        )

        assert error_display.title == "Unexpected Error"
        assert "Custom error message" in error_display.message

    def test_handle_custom_exception(self):
        """Test handling a custom exception."""
        handler = ErrorHandler(enable_logging=False)
        exception = ValidationError("Invalid input", "Field required")

        error_display = handler.handle_exception(exception, "test_context")

        assert "Validation Error" in error_display.title
        assert "Invalid input" in error_display.message
        assert error_display.category == ErrorCategory.VALIDATION

    def test_handle_generic_exception(self):
        """Test handling a generic exception."""
        handler = ErrorHandler(enable_logging=False)
        exception = ValueError("Something went wrong")

        error_display = handler.handle_exception(exception)

        assert error_display.title == "Unexpected Error"
        assert "Something went wrong" in error_display.message

    def test_handle_exception_with_context(self):
        """Test handling exception with context."""
        handler = ErrorHandler(enable_logging=False)
        exception = RuntimeError("Test error")

        error_display = handler.handle_exception(exception, "Loading configuration")

        assert "Loading configuration" in error_display.message


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_handle_error_function(self):
        """Test handle_error convenience function."""
        error_display = handle_error("docker_unavailable")

        assert error_display.title == "Docker Not Available"
        assert error_display.category == ErrorCategory.DOCKER

    def test_handle_exception_function(self):
        """Test handle_exception convenience function."""
        exception = DockerError("Test error")
        error_display = handle_exception(exception)

        assert "Docker Error" in error_display.title
        assert error_display.category == ErrorCategory.DOCKER


class TestStateManager:
    """Test StateManager class."""

    def test_state_manager_initialization(self, tmp_path):
        """Test state manager initialization."""
        state_dir = tmp_path / "state"
        manager = StateManager(state_dir)

        assert manager.state_dir == state_dir
        assert state_dir.exists()

    def test_save_and_load_state(self, tmp_path):
        """Test saving and loading state."""
        state_dir = tmp_path / "state"
        manager = StateManager(state_dir)

        test_state = {
            "key1": "value1",
            "key2": 123,
            "key3": ["a", "b", "c"],
        }

        # Save state
        result = manager.save_state(test_state)
        assert result is True
        assert manager.state_file.exists()

        # Load state
        loaded_state = manager.load_state()
        assert loaded_state == test_state

    def test_load_nonexistent_state(self, tmp_path):
        """Test loading state when no state file exists."""
        state_dir = tmp_path / "state"
        manager = StateManager(state_dir)

        loaded_state = manager.load_state()
        assert loaded_state is None

    def test_state_backup(self, tmp_path):
        """Test state backup functionality."""
        state_dir = tmp_path / "state"
        manager = StateManager(state_dir)

        # Save initial state
        manager.save_state({"version": 1})

        # Save new state (should backup old one)
        manager.save_state({"version": 2})

        # Backup file should exist
        assert manager.backup_file.exists()

        # Load from backup
        with open(manager.backup_file, "r") as f:
            backup_data = json.load(f)
        assert backup_data["state"]["version"] == 1

    def test_clear_state(self, tmp_path):
        """Test clearing state."""
        state_dir = tmp_path / "state"
        manager = StateManager(state_dir)

        # Save state
        manager.save_state({"test": "data"})
        assert manager.state_file.exists()

        # Clear state
        result = manager.clear_state()
        assert result is True
        assert not manager.state_file.exists()

    def test_has_saved_state(self, tmp_path):
        """Test checking for saved state."""
        state_dir = tmp_path / "state"
        manager = StateManager(state_dir)

        assert not manager.has_saved_state()

        manager.save_state({"test": "data"})
        assert manager.has_saved_state()

    def test_get_state_age(self, tmp_path):
        """Test getting state age."""
        state_dir = tmp_path / "state"
        manager = StateManager(state_dir)

        # No state
        assert manager.get_state_age() is None

        # Save state
        manager.save_state({"test": "data"})

        # State should be very recent
        age = manager.get_state_age()
        assert age is not None
        assert age < 5  # Less than 5 seconds old

    def test_create_crash_report(self, tmp_path):
        """Test creating crash report."""
        state_dir = tmp_path / "state"
        manager = StateManager(state_dir)

        exception = RuntimeError("Test crash")
        context = {"screen": "TestScreen", "action": "test_action"}

        crash_file = manager.create_crash_report(exception, context)

        assert crash_file is not None
        assert crash_file.exists()

        # Verify crash report content
        with open(crash_file, "r") as f:
            crash_data = json.load(f)

        assert crash_data["exception_type"] == "RuntimeError"
        assert crash_data["exception_message"] == "Test crash"
        assert crash_data["context"]["screen"] == "TestScreen"
        assert "traceback" in crash_data

    def test_cleanup_old_crashes(self, tmp_path):
        """Test cleaning up old crash reports."""
        state_dir = tmp_path / "state"
        manager = StateManager(state_dir)

        crash_dir = state_dir / "crashes"
        crash_dir.mkdir(parents=True, exist_ok=True)

        # Create some crash files
        for i in range(3):
            crash_file = crash_dir / f"crash_test_{i}.json"
            crash_file.write_text(json.dumps({"test": i}))

        # Cleanup (with max_age_days=0 to delete all)
        deleted = manager.cleanup_old_crashes(max_age_days=0)

        assert deleted == 3
        assert len(list(crash_dir.glob("crash_*.json"))) == 0


class TestErrorBoundary:
    """Test ErrorBoundary class."""

    def test_error_boundary_creation(self):
        """Test creating an error boundary."""
        mock_screen = MagicMock()
        boundary = ErrorBoundary(mock_screen, "return_to_dashboard")

        assert boundary.screen == mock_screen
        assert boundary.fallback_action == "return_to_dashboard"

    def test_error_boundary_wrap_sync(self):
        """Test wrapping a synchronous function."""
        mock_screen = MagicMock()
        boundary = ErrorBoundary(mock_screen)

        def test_func():
            raise ValueError("Test error")

        wrapped = boundary.wrap(test_func)

        # Should not raise, error should be handled
        result = wrapped()
        assert result is None

    @pytest.mark.asyncio
    async def test_error_boundary_wrap_async(self):
        """Test wrapping an asynchronous function."""
        mock_screen = MagicMock()
        boundary = ErrorBoundary(mock_screen)

        async def test_func():
            raise ValueError("Test error")

        wrapped = boundary.wrap(test_func)

        # Should not raise, error should be handled
        result = await wrapped()
        assert result is None


class TestErrorScreen:
    """Test ErrorScreen class."""

    def test_error_screen_creation(self):
        """Test creating an error screen."""
        error_display = ErrorDisplay(
            title="Test Error",
            message="Test message",
            remediation=["Step 1"],
        )

        screen = ErrorScreen(error_display, "TestScreen")

        assert screen.error_display == error_display
        assert screen.source_screen == "TestScreen"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
