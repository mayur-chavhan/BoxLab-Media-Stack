"""Tests for error handling system."""

import logging
import tempfile
from pathlib import Path

import pytest

from arr_stack_manager.utils.errors import (
    ERROR_MESSAGES,
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
    get_error_handler,
    handle_error,
    handle_exception,
)


class TestErrorDisplay:
    """Test suite for ErrorDisplay."""

    def test_error_display_creation(self):
        """Test creating an ErrorDisplay object."""
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

    def test_format_for_display(self):
        """Test formatting error for display."""
        error = ErrorDisplay(
            title="Test Error",
            message="This is a test error",
            remediation=["Step 1", "Step 2"],
        )

        formatted = error.format_for_display()

        assert "Test Error" in formatted
        assert "This is a test error" in formatted
        assert "Step 1" in formatted
        assert "Step 2" in formatted

    def test_format_for_display_with_details(self):
        """Test formatting error with technical details."""
        error = ErrorDisplay(
            title="Test Error",
            message="This is a test error",
            remediation=["Step 1"],
            technical_details="Exception: Something went wrong",
        )

        formatted = error.format_for_display()

        assert "Technical details:" in formatted
        assert "Exception: Something went wrong" in formatted

    def test_format_for_log(self):
        """Test formatting error for logging."""
        error = ErrorDisplay(
            title="Test Error",
            message="This is a test error",
            remediation=["Step 1", "Step 2"],
            category=ErrorCategory.DOCKER,
            technical_details="Details here",
        )

        formatted = error.format_for_log()

        assert "DOCKER" in formatted
        assert "Test Error" in formatted
        assert "This is a test error" in formatted


class TestCustomExceptions:
    """Test suite for custom exception classes."""

    def test_stack_manager_error(self):
        """Test base StackManagerError."""
        error = StackManagerError("Test error", ErrorCategory.UNKNOWN, "Details")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.details == "Details"
        assert error.timestamp is not None

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid configuration")

        assert error.category == ErrorCategory.VALIDATION
        assert error.message == "Invalid configuration"

    def test_docker_error(self):
        """Test DockerError."""
        error = DockerError("Docker daemon not available")

        assert error.category == ErrorCategory.DOCKER
        assert error.message == "Docker daemon not available"

    def test_filesystem_error(self):
        """Test FileSystemError."""
        error = FileSystemError("Path not found")

        assert error.category == ErrorCategory.FILESYSTEM
        assert error.message == "Path not found"

    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Port in use")

        assert error.category == ErrorCategory.NETWORK
        assert error.message == "Port in use"

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid config file")

        assert error.category == ErrorCategory.CONFIGURATION
        assert error.message == "Invalid config file"

    def test_permission_error(self):
        """Test PermissionError."""
        error = PermissionError("Access denied")

        assert error.category == ErrorCategory.PERMISSION
        assert error.message == "Access denied"


class TestErrorHandler:
    """Test suite for ErrorHandler."""

    def test_error_handler_creation(self):
        """Test creating an ErrorHandler."""
        handler = ErrorHandler(enable_logging=False)

        assert handler is not None
        assert handler.enable_logging is False

    def test_handle_error_docker_unavailable(self):
        """Test handling docker_unavailable error."""
        handler = ErrorHandler(enable_logging=False)

        error_display = handler.handle_error("docker_unavailable")

        assert error_display.title == "Docker Not Available"
        assert "Docker daemon" in error_display.message
        assert len(error_display.remediation) > 0
        assert error_display.category == ErrorCategory.DOCKER

    def test_handle_error_with_formatting(self):
        """Test handling error with message formatting."""
        handler = ErrorHandler(enable_logging=False)

        error_display = handler.handle_error("port_in_use", port=8080)

        assert "8080" in error_display.message
        assert any("8080" in step for step in error_display.remediation)

    def test_handle_error_path_not_writable(self):
        """Test handling path_not_writable error."""
        handler = ErrorHandler(enable_logging=False)

        error_display = handler.handle_error(
            "path_not_writable", path="/test/path", puid=1000, pgid=1000
        )

        assert "/test/path" in error_display.message
        assert error_display.category == ErrorCategory.PERMISSION
        assert any("chown" in step for step in error_display.remediation)

    def test_handle_error_unknown_type(self):
        """Test handling unknown error type."""
        handler = ErrorHandler(enable_logging=False)

        error_display = handler.handle_error("unknown_error_type", message="Custom message")

        assert error_display.title == "Unexpected Error"
        assert "Custom message" in error_display.message
        assert error_display.category == ErrorCategory.UNKNOWN

    def test_handle_exception_custom(self):
        """Test handling custom exception."""
        handler = ErrorHandler(enable_logging=False)

        exception = ValidationError("Invalid input", "Field X is required")
        error_display = handler.handle_exception(exception)

        assert "Invalid input" in error_display.message
        assert error_display.category == ErrorCategory.VALIDATION
        assert error_display.technical_details == "Field X is required"

    def test_handle_exception_generic(self):
        """Test handling generic exception."""
        handler = ErrorHandler(enable_logging=False)

        exception = ValueError("Something went wrong")
        error_display = handler.handle_exception(exception)

        assert "Something went wrong" in error_display.message
        assert error_display.category == ErrorCategory.UNKNOWN
        assert "ValueError" in error_display.technical_details

    def test_handle_exception_with_context(self):
        """Test handling exception with context."""
        handler = ErrorHandler(enable_logging=False)

        exception = DockerError("Connection failed")
        error_display = handler.handle_exception(exception, context="Starting container")

        assert "Starting container" in error_display.message
        assert "Connection failed" in error_display.message

    def test_get_generic_remediation(self):
        """Test getting generic remediation steps."""
        handler = ErrorHandler(enable_logging=False)

        remediation = handler._get_generic_remediation(ErrorCategory.DOCKER)

        assert len(remediation) > 0
        assert any("Docker" in step for step in remediation)

    def test_logging_methods(self):
        """Test logging methods don't raise errors."""
        handler = ErrorHandler(enable_logging=False)

        # These should not raise errors even with logging disabled
        handler.log_warning("Test warning")
        handler.log_info("Test info")
        handler.log_debug("Test debug")


class TestGlobalFunctions:
    """Test suite for global convenience functions."""

    def test_get_error_handler(self):
        """Test getting global error handler."""
        handler = get_error_handler()

        assert handler is not None
        assert isinstance(handler, ErrorHandler)

        # Should return same instance
        handler2 = get_error_handler()
        assert handler is handler2

    def test_handle_error_global(self):
        """Test global handle_error function."""
        error_display = handle_error("docker_unavailable")

        assert error_display is not None
        assert error_display.title == "Docker Not Available"

    def test_handle_exception_global(self):
        """Test global handle_exception function."""
        exception = ValidationError("Test error")
        error_display = handle_exception(exception)

        assert error_display is not None
        assert "Test error" in error_display.message


class TestErrorMessages:
    """Test suite for ERROR_MESSAGES dictionary."""

    def test_error_messages_structure(self):
        """Test that ERROR_MESSAGES has correct structure."""
        assert len(ERROR_MESSAGES) > 0

        for error_type, template in ERROR_MESSAGES.items():
            assert "title" in template
            assert "message" in template
            assert "category" in template
            assert "remediation" in template
            assert isinstance(template["remediation"], list)
            assert len(template["remediation"]) > 0

    def test_all_error_categories_valid(self):
        """Test that all error categories are valid."""
        for error_type, template in ERROR_MESSAGES.items():
            assert isinstance(template["category"], ErrorCategory)

    def test_docker_errors_present(self):
        """Test that Docker-related errors are present."""
        docker_errors = [
            "docker_unavailable",
            "docker_connection_failed",
            "docker_image_pull_failed",
            "docker_container_start_failed",
        ]

        for error_type in docker_errors:
            assert error_type in ERROR_MESSAGES
            assert ERROR_MESSAGES[error_type]["category"] == ErrorCategory.DOCKER

    def test_filesystem_errors_present(self):
        """Test that filesystem-related errors are present."""
        fs_errors = ["path_not_found", "disk_space_low"]

        for error_type in fs_errors:
            assert error_type in ERROR_MESSAGES

    def test_network_errors_present(self):
        """Test that network-related errors are present."""
        assert "port_in_use" in ERROR_MESSAGES
        assert ERROR_MESSAGES["port_in_use"]["category"] == ErrorCategory.NETWORK

    def test_validation_errors_present(self):
        """Test that validation-related errors are present."""
        validation_errors = ["port_invalid", "invalid_puid_pgid", "no_services_selected"]

        for error_type in validation_errors:
            assert error_type in ERROR_MESSAGES
            assert ERROR_MESSAGES[error_type]["category"] == ErrorCategory.VALIDATION


class TestErrorHandlerLogging:
    """Test suite for ErrorHandler logging functionality."""

    def test_logging_setup(self):
        """Test that logging is set up correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change config dir for testing
            import arr_stack_manager.utils.errors as errors_module

            original_home = Path.home

            def mock_home():
                return Path(tmpdir)

            Path.home = mock_home

            try:
                handler = ErrorHandler(enable_logging=True)

                # Check that log directory was created
                log_dir = Path(tmpdir) / ".config" / "arr-stack-manager" / "logs"
                assert log_dir.exists()
            finally:
                Path.home = original_home

    def test_error_logging(self):
        """Test that errors are logged."""
        handler = ErrorHandler(enable_logging=True)

        # This should log the error
        error_display = handler.handle_error("docker_unavailable")

        assert error_display is not None
