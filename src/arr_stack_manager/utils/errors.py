"""Error handling system with user-friendly messages and custom exceptions."""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


# Configure logging
logger = logging.getLogger("arr_stack_manager")


class ErrorCategory(Enum):
    """Categories of errors that can occur."""

    VALIDATION = "validation"
    DOCKER = "docker"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    PERMISSION = "permission"
    UNKNOWN = "unknown"


@dataclass
class ErrorDisplay:
    """User-friendly error display information."""

    title: str
    message: str
    remediation: list[str]
    category: ErrorCategory = ErrorCategory.UNKNOWN
    technical_details: str | None = None

    def format_for_display(self) -> str:
        """Format error for terminal display."""
        lines = [
            f"❌ {self.title}",
            "",
            self.message,
            "",
        ]

        if self.remediation:
            lines.append("💡 How to fix:")
            for step in self.remediation:
                lines.append(f"  • {step}")
            lines.append("")

        if self.technical_details:
            lines.append("Technical details:")
            lines.append(f"  {self.technical_details}")

        return "\n".join(lines)

    def format_for_log(self) -> str:
        """Format error for logging."""
        parts = [
            f"[{self.category.value.upper()}] {self.title}",
            f"Message: {self.message}",
        ]

        if self.technical_details:
            parts.append(f"Details: {self.technical_details}")

        if self.remediation:
            parts.append(f"Remediation: {'; '.join(self.remediation)}")

        return " | ".join(parts)


# Custom Exception Classes


class StackManagerError(Exception):
    """Base exception for all Stack Manager errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        details: str | None = None,
    ) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.message = message
        self.category = category
        self.details = details
        self.timestamp = datetime.now()


class ValidationError(StackManagerError):
    """Raised when configuration validation fails."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize validation error."""
        super().__init__(message, ErrorCategory.VALIDATION, details)


class DockerError(StackManagerError):
    """Raised when Docker operations fail."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize Docker error."""
        super().__init__(message, ErrorCategory.DOCKER, details)


class FileSystemError(StackManagerError):
    """Raised when file system operations fail."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize file system error."""
        super().__init__(message, ErrorCategory.FILESYSTEM, details)


class NetworkError(StackManagerError):
    """Raised when network operations fail."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize network error."""
        super().__init__(message, ErrorCategory.NETWORK, details)


class ConfigurationError(StackManagerError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize configuration error."""
        super().__init__(message, ErrorCategory.CONFIGURATION, details)


class PermissionError(StackManagerError):
    """Raised when permission checks fail."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize permission error."""
        super().__init__(message, ErrorCategory.PERMISSION, details)


# Error message templates
ERROR_MESSAGES: dict[str, dict[str, Any]] = {
    "docker_unavailable": {
        "title": "Docker Not Available",
        "message": "Cannot connect to Docker daemon.",
        "category": ErrorCategory.DOCKER,
        "remediation": [
            "Ensure Docker is installed and running",
            "Check if your user has Docker permissions",
            "Try: sudo systemctl start docker",
            "Try: sudo usermod -aG docker $USER (then logout/login)",
        ],
    },
    "docker_connection_failed": {
        "title": "Docker Connection Failed",
        "message": "Failed to establish connection with Docker daemon.",
        "category": ErrorCategory.DOCKER,
        "remediation": [
            "Verify Docker service is running: systemctl status docker",
            "Check Docker socket permissions: ls -l /var/run/docker.sock",
            "Restart Docker service: sudo systemctl restart docker",
        ],
    },
    "docker_image_pull_failed": {
        "title": "Image Pull Failed",
        "message": "Failed to pull Docker image: {image}",
        "category": ErrorCategory.DOCKER,
        "remediation": [
            "Check your internet connection",
            "Verify the image name is correct",
            "Try pulling manually: docker pull {image}",
            "Check Docker Hub status if using public images",
        ],
    },
    "docker_container_start_failed": {
        "title": "Container Start Failed",
        "message": "Failed to start container: {container}",
        "category": ErrorCategory.DOCKER,
        "remediation": [
            "Check container logs: docker logs {container}",
            "Verify port is not already in use",
            "Check volume mount permissions",
            "Ensure sufficient system resources",
        ],
    },
    "path_not_found": {
        "title": "Path Not Found",
        "message": "The specified path does not exist: {path}",
        "category": ErrorCategory.FILESYSTEM,
        "remediation": [
            "Create the directory: mkdir -p {path}",
            "Verify the path is correct",
            "Check parent directory permissions",
        ],
    },
    "path_not_writable": {
        "title": "Permission Denied",
        "message": "Cannot write to path: {path}",
        "category": ErrorCategory.PERMISSION,
        "remediation": [
            "Check directory permissions: ls -ld {path}",
            "Ensure PUID/PGID match directory owner",
            "Fix permissions: sudo chown -R {puid}:{pgid} {path}",
            "Or grant write access: sudo chmod u+w {path}",
        ],
    },
    "path_not_readable": {
        "title": "Permission Denied",
        "message": "Cannot read from path: {path}",
        "category": ErrorCategory.PERMISSION,
        "remediation": [
            "Check directory permissions: ls -ld {path}",
            "Fix permissions: sudo chmod u+r {path}",
        ],
    },
    "port_in_use": {
        "title": "Port Conflict",
        "message": "Port {port} is already in use",
        "category": ErrorCategory.NETWORK,
        "remediation": [
            "Choose a different port in configuration",
            "Find what's using the port: sudo lsof -i :{port}",
            "Stop the conflicting service",
            "Or use: sudo netstat -tulpn | grep {port}",
        ],
    },
    "port_invalid": {
        "title": "Invalid Port",
        "message": "Port number {port} is invalid",
        "category": ErrorCategory.VALIDATION,
        "remediation": [
            "Use a port between 1 and 65535",
            "Avoid ports below 1024 unless running as root",
            "Check for typos in port configuration",
        ],
    },
    "invalid_puid_pgid": {
        "title": "Invalid User/Group ID",
        "message": "PUID {puid} or PGID {pgid} is invalid",
        "category": ErrorCategory.VALIDATION,
        "remediation": [
            "Use valid system user/group IDs",
            "Check current user: id -u (PUID) and id -g (PGID)",
            "List users: cat /etc/passwd",
            "List groups: cat /etc/group",
        ],
    },
    "service_not_supported": {
        "title": "Unsupported Service",
        "message": "Service '{service}' is not supported",
        "category": ErrorCategory.CONFIGURATION,
        "remediation": [
            "Check service name spelling",
            "View supported services in the service selector",
            "Refer to documentation for available services",
        ],
    },
    "no_services_selected": {
        "title": "No Services Selected",
        "message": "At least one service must be selected",
        "category": ErrorCategory.VALIDATION,
        "remediation": [
            "Select at least one service from the service selector",
            "Review your configuration file",
        ],
    },
    "config_file_not_found": {
        "title": "Configuration Not Found",
        "message": "Configuration file not found: {path}",
        "category": ErrorCategory.CONFIGURATION,
        "remediation": [
            "Run the configuration wizard to create a new configuration",
            "Check if the file path is correct",
            "Restore from backup if available",
        ],
    },
    "config_file_invalid": {
        "title": "Invalid Configuration",
        "message": "Configuration file is invalid or corrupted: {path}",
        "category": ErrorCategory.CONFIGURATION,
        "remediation": [
            "Run the configuration wizard to create a new configuration",
            "Check JSON syntax if editing manually",
            "Restore from backup if available",
            "Delete the file to start fresh",
        ],
    },
    "compose_generation_failed": {
        "title": "Compose Generation Failed",
        "message": "Failed to generate docker-compose.yml",
        "category": ErrorCategory.CONFIGURATION,
        "remediation": [
            "Check configuration for missing required fields",
            "Verify template files are present",
            "Review error details for specific issues",
        ],
    },
    "deployment_failed": {
        "title": "Deployment Failed",
        "message": "Stack deployment failed",
        "category": ErrorCategory.DOCKER,
        "remediation": [
            "Check Docker logs for specific errors",
            "Verify all configuration is valid",
            "Ensure sufficient disk space and memory",
            "Try deploying services individually",
        ],
    },
    "disk_space_low": {
        "title": "Low Disk Space",
        "message": "Insufficient disk space at {path}",
        "category": ErrorCategory.FILESYSTEM,
        "remediation": [
            "Free up disk space",
            "Check disk usage: df -h {path}",
            "Remove unused Docker images: docker image prune",
            "Choose a different path with more space",
        ],
    },
    "template_not_found": {
        "title": "Template Missing",
        "message": "Service template not found: {template}",
        "category": ErrorCategory.CONFIGURATION,
        "remediation": [
            "Reinstall the application",
            "Verify installation is complete",
            "Check if template files were accidentally deleted",
        ],
    },
}


class ErrorHandler:
    """Centralized error handling with user-friendly messages."""

    def __init__(self, enable_logging: bool = True) -> None:
        """
        Initialize the error handler.

        Args:
            enable_logging: Whether to enable error logging
        """
        self.enable_logging = enable_logging
        if enable_logging:
            self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        # Create logs directory if it doesn't exist
        log_dir = Path.home() / ".config" / "arr-stack-manager" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure file handler
        log_file = log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.ERROR)

        # Configure console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # Set format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Configure logger
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    def handle_error(
        self, error_type: str, **kwargs: Any
    ) -> ErrorDisplay:
        """
        Generate user-friendly error display from error type.

        Args:
            error_type: Type of error from ERROR_MESSAGES
            **kwargs: Variables to format into error message

        Returns:
            ErrorDisplay object with formatted error information
        """
        template = ERROR_MESSAGES.get(error_type)

        if template:
            # Format message with provided kwargs
            message = template["message"].format(**kwargs)

            # Format remediation steps with provided kwargs
            remediation = [
                step.format(**kwargs) for step in template["remediation"]
            ]

            error_display = ErrorDisplay(
                title=template["title"],
                message=message,
                remediation=remediation,
                category=template["category"],
                technical_details=kwargs.get("details"),
            )
        else:
            # Unknown error type, create generic error
            error_display = ErrorDisplay(
                title="Unexpected Error",
                message=kwargs.get("message", f"Unknown error type: {error_type}"),
                remediation=["Check logs for details", "Report this issue if it persists"],
                category=ErrorCategory.UNKNOWN,
                technical_details=kwargs.get("details"),
            )

        # Log the error
        if self.enable_logging:
            logger.error(error_display.format_for_log())

        return error_display

    def handle_exception(
        self, exception: Exception, context: str | None = None
    ) -> ErrorDisplay:
        """
        Handle an exception and convert to ErrorDisplay.

        Args:
            exception: The exception to handle
            context: Optional context about where the error occurred

        Returns:
            ErrorDisplay object with formatted error information
        """
        # Check if it's one of our custom exceptions
        if isinstance(exception, StackManagerError):
            # Map exception type to error message template
            error_type_map = {
                ValidationError: "validation_error",
                DockerError: "docker_connection_failed",
                FileSystemError: "path_not_found",
                NetworkError: "port_in_use",
                ConfigurationError: "config_file_invalid",
                PermissionError: "path_not_writable",
            }

            error_type = error_type_map.get(type(exception), "unknown_error")

            error_display = ErrorDisplay(
                title=exception.category.value.title() + " Error",
                message=exception.message,
                remediation=self._get_generic_remediation(exception.category),
                category=exception.category,
                technical_details=exception.details,
            )
        else:
            # Generic exception handling
            error_display = ErrorDisplay(
                title="Unexpected Error",
                message=str(exception),
                remediation=[
                    "Check logs for more details",
                    "Verify your configuration",
                    "Report this issue if it persists",
                ],
                category=ErrorCategory.UNKNOWN,
                technical_details=f"{type(exception).__name__}: {str(exception)}",
            )

        # Add context if provided
        if context:
            error_display.message = f"{context}: {error_display.message}"

        # Log the error
        if self.enable_logging:
            logger.error(error_display.format_for_log(), exc_info=True)

        return error_display

    def _get_generic_remediation(self, category: ErrorCategory) -> list[str]:
        """
        Get generic remediation steps for an error category.

        Args:
            category: Error category

        Returns:
            List of remediation steps
        """
        remediation_map = {
            ErrorCategory.VALIDATION: [
                "Review your configuration settings",
                "Check for typos or invalid values",
                "Refer to documentation for valid options",
            ],
            ErrorCategory.DOCKER: [
                "Ensure Docker is running",
                "Check Docker logs for details",
                "Verify Docker permissions",
            ],
            ErrorCategory.FILESYSTEM: [
                "Check file and directory permissions",
                "Verify paths exist and are accessible",
                "Ensure sufficient disk space",
            ],
            ErrorCategory.NETWORK: [
                "Check network connectivity",
                "Verify ports are available",
                "Review firewall settings",
            ],
            ErrorCategory.CONFIGURATION: [
                "Review configuration file",
                "Run configuration wizard",
                "Check for missing required fields",
            ],
            ErrorCategory.PERMISSION: [
                "Check file permissions",
                "Verify user/group ownership",
                "Ensure PUID/PGID are correct",
            ],
            ErrorCategory.UNKNOWN: [
                "Check logs for more information",
                "Verify system requirements",
                "Report issue if it persists",
            ],
        }

        return remediation_map.get(
            category, remediation_map[ErrorCategory.UNKNOWN]
        )

    def log_warning(self, message: str, **kwargs: Any) -> None:
        """
        Log a warning message.

        Args:
            message: Warning message
            **kwargs: Additional context
        """
        if self.enable_logging:
            logger.warning(message, extra=kwargs)

    def log_info(self, message: str, **kwargs: Any) -> None:
        """
        Log an info message.

        Args:
            message: Info message
            **kwargs: Additional context
        """
        if self.enable_logging:
            logger.info(message, extra=kwargs)

    def log_debug(self, message: str, **kwargs: Any) -> None:
        """
        Log a debug message.

        Args:
            message: Debug message
            **kwargs: Additional context
        """
        if self.enable_logging:
            logger.debug(message, extra=kwargs)


# Global error handler instance
_error_handler: ErrorHandler | None = None


def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance.

    Returns:
        Global ErrorHandler instance
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(error_type: str, **kwargs: Any) -> ErrorDisplay:
    """
    Convenience function to handle errors using global handler.

    Args:
        error_type: Type of error from ERROR_MESSAGES
        **kwargs: Variables to format into error message

    Returns:
        ErrorDisplay object with formatted error information
    """
    return get_error_handler().handle_error(error_type, **kwargs)


def handle_exception(
    exception: Exception, context: str | None = None
) -> ErrorDisplay:
    """
    Convenience function to handle exceptions using global handler.

    Args:
        exception: The exception to handle
        context: Optional context about where the error occurred

    Returns:
        ErrorDisplay object with formatted error information
    """
    return get_error_handler().handle_exception(exception, context)
