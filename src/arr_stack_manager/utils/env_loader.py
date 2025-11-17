"""Environment variable loader with .env file support."""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class EnvironmentLoader:
    """Load and manage environment variables from .env files and system environment.

    Searches for .env files in multiple locations:
    1. Current working directory
    2. Project root (where pyproject.toml is located)
    3. User config directory (~/.config/arr-stack-manager)

    Environment variables take precedence over .env file values.
    """

    # Supported environment variables with their types
    SUPPORTED_VARS = {
        "PUID": int,
        "PGID": int,
        "TZ": str,
        "TIMEZONE": str,  # Alternative to TZ
        "BASE_PATH": str,
        "CONFIG_PATH": str,
        "DATA_PATH": str,
        "COMPOSE_FILE_PATH": str,
        "STACK_NAME": str,
    }

    def __init__(self) -> None:
        """Initialize the environment loader and load .env files."""
        self._env_vars: dict[str, str] = {}
        self._load_env_files()

    def _load_env_files(self) -> None:
        """Load .env files from multiple locations in priority order."""
        search_paths = self._get_search_paths()

        # Load from all locations (later ones override earlier ones)
        for path in search_paths:
            env_file = path / ".env"
            if env_file.exists():
                load_dotenv(env_file, override=False)

    def _get_search_paths(self) -> list[Path]:
        """Get list of paths to search for .env files.

        Returns:
            List of paths in priority order (lowest to highest priority)
        """
        paths = []

        # 1. User config directory (lowest priority)
        config_dir = Path.home() / ".config" / "arr-stack-manager"
        if config_dir.exists():
            paths.append(config_dir)

        # 2. Project root (where pyproject.toml is)
        project_root = self._find_project_root()
        if project_root:
            paths.append(project_root)

        # 3. Current working directory (highest priority)
        paths.append(Path.cwd())

        return paths

    def _find_project_root(self) -> Path | None:
        """Find the project root by looking for pyproject.toml.

        Returns:
            Path to project root or None if not found
        """
        current = Path(__file__).resolve()

        # Walk up the directory tree
        for parent in [current, *current.parents]:
            if (parent / "pyproject.toml").exists():
                return parent

        return None

    def _convert_type(self, value: str, target_type: type) -> Any:
        """Convert string value to target type.

        Args:
            value: String value to convert
            target_type: Target type (int, bool, str)

        Returns:
            Converted value

        Raises:
            ValueError: If conversion fails
        """
        if target_type == bool:
            # Handle common boolean representations
            lower_value = value.lower()
            if lower_value in ("true", "1", "yes", "on"):
                return True
            elif lower_value in ("false", "0", "no", "off"):
                return False
            else:
                raise ValueError(f"Cannot convert '{value}' to boolean")
        elif target_type == int:
            return int(value)
        elif target_type == str:
            return value
        else:
            raise ValueError(f"Unsupported type: {target_type}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get an environment variable with type conversion.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value with appropriate type, or default if not found
        """
        # Check if this is a supported variable
        target_type = self.SUPPORTED_VARS.get(key, str)

        # Get value from environment (system env takes precedence)
        value = os.environ.get(key)

        if value is None:
            return default

        # Convert to appropriate type
        try:
            return self._convert_type(value, target_type)
        except (ValueError, TypeError):
            # If conversion fails, return default
            return default

    def get_all(self) -> dict[str, Any]:
        """Get all supported environment variables.

        Returns:
            Dictionary of environment variable names to values (with type conversion)
        """
        result = {}

        for key, target_type in self.SUPPORTED_VARS.items():
            value = os.environ.get(key)
            if value is not None:
                try:
                    result[key] = self._convert_type(value, target_type)
                except (ValueError, TypeError):
                    # Skip variables that can't be converted
                    continue

        return result

    def generate_example_file(self, output_path: Path | str | None = None) -> str:
        """Generate a .env.example file with all supported variables.

        Args:
            output_path: Path to write the file (optional)

        Returns:
            Content of the .env.example file
        """
        lines = [
            "# arr Stack Manager Environment Configuration",
            "#",
            "# This file contains all supported environment variables for configuring",
            "# the arr Stack Manager. Copy this file to .env and customize the values.",
            "#",
            "# Environment variables take precedence over saved configuration values.",
            "#",
            "",
            "# User and Group IDs",
            "# These should match the user that owns your media files",
            "# Default: Current user's UID and GID",
            "# PUID=1000",
            "# PGID=1000",
            "",
            "# Timezone",
            "# Use TZ database format (e.g., America/New_York, Europe/London)",
            "# Default: UTC",
            "# TZ=UTC",
            "# TIMEZONE=UTC  # Alternative to TZ",
            "",
            "# Base Path",
            "# Root directory for all stack data (config and media)",
            "# Default: None (must be set in wizard)",
            "# BASE_PATH=/mnt/storage",
            "",
            "# Config Path",
            "# Directory for service configurations",
            "# Default: {BASE_PATH}/config",
            "# CONFIG_PATH=/mnt/storage/config",
            "",
            "# Data Path",
            "# Directory for media and downloads",
            "# Default: {BASE_PATH}/data",
            "# DATA_PATH=/mnt/storage/data",
            "",
            "# Docker Compose File Path",
            "# Location to save generated docker-compose.yml",
            "# Default: ./stacks/{STACK_NAME}/docker-compose.yml",
            "# COMPOSE_FILE_PATH=/path/to/docker-compose.yml",
            "",
            "# Stack Name",
            "# Name for this stack configuration",
            "# Default: default",
            "# STACK_NAME=media-automation",
            "",
        ]

        content = "\n".join(lines)

        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content)

        return content
