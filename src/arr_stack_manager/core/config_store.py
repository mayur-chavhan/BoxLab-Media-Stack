"""Configuration storage and persistence."""

import json
from pathlib import Path
from typing import Any

from arr_stack_manager.models.configuration import Configuration
from arr_stack_manager.models.stack import StackConfig


class ConfigRepository:
    """Repository for managing configuration persistence."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """
        Initialize the configuration repository.

        Args:
            config_dir: Optional custom config directory. If None, uses default.
        """
        self._config_dir = config_dir or self.get_config_dir()
        self._ensure_directory_structure()

    @staticmethod
    def get_config_dir() -> Path:
        """
        Get the user configuration directory.

        Returns:
            Path to ~/.config/arr-stack-manager
        """
        config_dir = Path.home() / ".config" / "arr-stack-manager"
        return config_dir

    def _ensure_directory_structure(self) -> None:
        """Create the configuration directory structure if it doesn't exist."""
        # Create main config directory
        self._config_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for organization
        (self._config_dir / "stacks").mkdir(exist_ok=True)
        (self._config_dir / "backups").mkdir(exist_ok=True)

    def save(self, stack_config: StackConfig) -> None:
        """
        Persist a stack configuration to disk as JSON.

        Args:
            stack_config: The stack configuration to save

        Raises:
            IOError: If unable to write to disk
            ValueError: If stack_config is invalid
        """
        if not stack_config.name:
            raise ValueError("Stack name cannot be empty")

        # Update modification time
        stack_config.update_modified_time()

        # Determine file path
        file_path = self._get_stack_file_path(stack_config.name)

        # Convert to JSON-serializable dict
        config_dict = stack_config.model_dump(mode="json")

        # Write to disk with pretty formatting
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to save configuration to {file_path}: {e}") from e

    def load(self, stack_name: str) -> StackConfig:
        """
        Load a stack configuration from disk.

        Args:
            stack_name: Name of the stack to load

        Returns:
            The loaded stack configuration

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            ValueError: If the configuration file is invalid
            IOError: If unable to read from disk
        """
        file_path = self._get_stack_file_path(stack_name)

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
        except (IOError, OSError) as e:
            raise IOError(f"Failed to read configuration from {file_path}: {e}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file {file_path}: {e}") from e

        try:
            return StackConfig.model_validate(config_dict)
        except Exception as e:
            raise ValueError(f"Invalid configuration data in {file_path}: {e}") from e

    def list_stacks(self) -> list[str]:
        """
        List all available stack configurations.

        Returns:
            List of stack names
        """
        stacks_dir = self._config_dir / "stacks"
        if not stacks_dir.exists():
            return []

        stack_files = stacks_dir.glob("*.json")
        return [f.stem for f in stack_files]

    def delete(self, stack_name: str) -> None:
        """
        Delete a stack configuration.

        Args:
            stack_name: Name of the stack to delete

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            IOError: If unable to delete the file
        """
        file_path = self._get_stack_file_path(stack_name)

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        try:
            file_path.unlink()
        except (IOError, OSError) as e:
            raise IOError(f"Failed to delete configuration {file_path}: {e}") from e

    def exists(self, stack_name: str) -> bool:
        """
        Check if a stack configuration exists.

        Args:
            stack_name: Name of the stack to check

        Returns:
            True if the configuration exists, False otherwise
        """
        file_path = self._get_stack_file_path(stack_name)
        return file_path.exists()

    def backup(self, stack_name: str) -> Path:
        """
        Create a backup of a stack configuration.

        Args:
            stack_name: Name of the stack to backup

        Returns:
            Path to the backup file

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            IOError: If unable to create backup
        """
        source_path = self._get_stack_file_path(stack_name)

        if not source_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {source_path}")

        # Create backup filename with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{stack_name}_{timestamp}.json"
        backup_path = self._config_dir / "backups" / backup_filename

        try:
            import shutil

            shutil.copy2(source_path, backup_path)
            return backup_path
        except (IOError, OSError) as e:
            raise IOError(f"Failed to create backup: {e}") from e

    def restore_from_backup(self, backup_path: Path, stack_name: str | None = None) -> None:
        """
        Restore a stack configuration from a backup.

        Args:
            backup_path: Path to the backup file
            stack_name: Optional new name for the restored stack.
                       If None, uses the original name from the backup.

        Raises:
            FileNotFoundError: If the backup file doesn't exist
            ValueError: If the backup file is invalid
            IOError: If unable to restore from backup
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Load the backup to validate it
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
            stack_config = StackConfig.model_validate(config_dict)
        except Exception as e:
            raise ValueError(f"Invalid backup file: {e}") from e

        # Use provided name or original name
        if stack_name:
            stack_config.name = stack_name

        # Save the restored configuration
        self.save(stack_config)

    def get_stack_metadata(self, stack_name: str) -> dict[str, Any]:
        """
        Get metadata about a stack without loading the full configuration.

        Args:
            stack_name: Name of the stack

        Returns:
            Dictionary with metadata (name, created_at, last_modified, file_size)

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
        """
        file_path = self._get_stack_file_path(stack_name)

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)

            stat = file_path.stat()

            return {
                "name": config_dict.get("name", stack_name),
                "created_at": config_dict.get("created_at"),
                "last_modified": config_dict.get("last_modified"),
                "file_size": stat.st_size,
                "service_count": len(config_dict.get("configuration", {}).get("services", {})),
            }
        except Exception as e:
            raise IOError(f"Failed to read metadata from {file_path}: {e}") from e

    def _get_stack_file_path(self, stack_name: str) -> Path:
        """
        Get the file path for a stack configuration.

        Args:
            stack_name: Name of the stack

        Returns:
            Path to the stack configuration file
        """
        # Sanitize stack name to prevent directory traversal
        safe_name = "".join(c for c in stack_name if c.isalnum() or c in ("-", "_"))
        if not safe_name:
            raise ValueError("Invalid stack name")

        return self._config_dir / "stacks" / f"{safe_name}.json"
