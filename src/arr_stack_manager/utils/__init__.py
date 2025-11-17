"""Utility modules for arr-stack-manager."""

from .env_loader import EnvironmentLoader
from .error_boundary import ErrorBoundary, ErrorScreen, with_error_boundary
from .errors import (
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
from .services import (
    SUPPORTED_SERVICES,
    ServiceMetadata,
    get_service_metadata,
    get_services_by_category,
)
from .state_manager import (
    StateManager,
    clear_app_state,
    get_state_manager,
    load_app_state,
    save_app_state,
)

__all__ = [
    "ConfigurationError",
    "DockerError",
    "ERROR_MESSAGES",
    "EnvironmentLoader",
    "ErrorBoundary",
    "ErrorCategory",
    "ErrorDisplay",
    "ErrorHandler",
    "ErrorScreen",
    "FileSystemError",
    "NetworkError",
    "PermissionError",
    "SUPPORTED_SERVICES",
    "ServiceMetadata",
    "StackManagerError",
    "StateManager",
    "ValidationError",
    "clear_app_state",
    "get_error_handler",
    "get_service_metadata",
    "get_services_by_category",
    "get_state_manager",
    "handle_error",
    "handle_exception",
    "load_app_state",
    "save_app_state",
    "with_error_boundary",
]
