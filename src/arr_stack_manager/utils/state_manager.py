"""State management and crash recovery system."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages application state persistence for crash recovery.
    
    This class handles:
    - Saving application state periodically
    - Recovering state after crashes
    - Cleaning up old state files
    """

    def __init__(self, state_dir: Path | None = None) -> None:
        """
        Initialize the state manager.

        Args:
            state_dir: Directory to store state files. Defaults to user config dir.
        """
        if state_dir is None:
            state_dir = Path.home() / ".config" / "arr-stack-manager" / "state"
        
        self.state_dir = state_dir
        self.state_file = state_dir / "app_state.json"
        self.backup_file = state_dir / "app_state.backup.json"
        
        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"StateManager initialized with state_dir: {state_dir}")

    def save_state(self, state: dict[str, Any]) -> bool:
        """
        Save current application state to disk.

        Args:
            state: Dictionary containing application state

        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Add metadata
            state_with_metadata = {
                "timestamp": datetime.now().isoformat(),
                "version": "0.1.0",
                "state": state,
            }
            
            # Backup existing state file if it exists
            if self.state_file.exists():
                try:
                    self.state_file.rename(self.backup_file)
                except Exception as e:
                    logger.warning(f"Failed to backup state file: {e}")
            
            # Write new state
            with open(self.state_file, "w") as f:
                json.dump(state_with_metadata, f, indent=2)
            
            logger.debug("Application state saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save application state: {e}")
            return False

    def load_state(self) -> dict[str, Any] | None:
        """
        Load saved application state from disk.

        Returns:
            Dictionary containing application state, or None if no state exists
        """
        try:
            # Try to load from primary state file
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    state_data: dict[str, Any] = json.load(f)
                
                # Validate state data
                if self._validate_state(state_data):
                    logger.info("Application state loaded successfully")
                    state_value = state_data.get("state", {})
                    return state_value if isinstance(state_value, dict) else {}
                else:
                    logger.warning("State file validation failed, trying backup")
            
            # Try backup file if primary failed
            if self.backup_file.exists():
                with open(self.backup_file, "r") as f:
                    state_data = json.load(f)
                
                if self._validate_state(state_data):
                    logger.info("Application state loaded from backup")
                    state_value = state_data.get("state", {})
                    return state_value if isinstance(state_value, dict) else {}
            
            logger.info("No valid state file found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load application state: {e}")
            return None

    def _validate_state(self, state_data: dict[str, Any]) -> bool:
        """
        Validate state data structure.

        Args:
            state_data: State data to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if "timestamp" not in state_data:
                logger.warning("State missing timestamp")
                return False
            
            if "state" not in state_data:
                logger.warning("State missing state data")
                return False
            
            # Check if state is too old (more than 7 days)
            timestamp = datetime.fromisoformat(state_data["timestamp"])
            age_days = (datetime.now() - timestamp).days
            
            if age_days > 7:
                logger.warning(f"State file is {age_days} days old, ignoring")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"State validation failed: {e}")
            return False

    def clear_state(self) -> bool:
        """
        Clear saved application state.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.state_file.exists():
                self.state_file.unlink()
                logger.info("Application state cleared")
            
            if self.backup_file.exists():
                self.backup_file.unlink()
                logger.debug("Backup state cleared")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear application state: {e}")
            return False

    def has_saved_state(self) -> bool:
        """
        Check if a saved state exists.

        Returns:
            True if saved state exists, False otherwise
        """
        return self.state_file.exists() or self.backup_file.exists()

    def get_state_age(self) -> int | None:
        """
        Get the age of the saved state in seconds.

        Returns:
            Age in seconds, or None if no state exists
        """
        try:
            if not self.state_file.exists():
                return None
            
            with open(self.state_file, "r") as f:
                state_data = json.load(f)
            
            timestamp = datetime.fromisoformat(state_data["timestamp"])
            age = (datetime.now() - timestamp).total_seconds()
            
            return int(age)
            
        except Exception as e:
            logger.warning(f"Failed to get state age: {e}")
            return None

    def create_crash_report(
        self,
        exception: Exception,
        context: dict[str, Any] | None = None
    ) -> Path | None:
        """
        Create a crash report file with exception details.

        Args:
            exception: The exception that caused the crash
            context: Additional context information

        Returns:
            Path to the crash report file, or None if failed
        """
        try:
            crash_dir = self.state_dir / "crashes"
            crash_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            crash_file = crash_dir / f"crash_{timestamp}.json"
            
            crash_data = {
                "timestamp": datetime.now().isoformat(),
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "context": context or {},
            }
            
            # Add traceback if available
            import traceback
            crash_data["traceback"] = traceback.format_exc()
            
            with open(crash_file, "w") as f:
                json.dump(crash_data, f, indent=2)
            
            logger.info(f"Crash report created: {crash_file}")
            return crash_file
            
        except Exception as e:
            logger.error(f"Failed to create crash report: {e}")
            return None

    def cleanup_old_crashes(self, max_age_days: int = 30) -> int:
        """
        Clean up old crash report files.

        Args:
            max_age_days: Maximum age of crash reports to keep

        Returns:
            Number of files deleted
        """
        try:
            crash_dir = self.state_dir / "crashes"
            if not crash_dir.exists():
                return 0
            
            deleted_count = 0
            cutoff_time = datetime.now().timestamp() - (max_age_days * 86400)
            
            for crash_file in crash_dir.glob("crash_*.json"):
                if crash_file.stat().st_mtime < cutoff_time:
                    crash_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old crash reports")
            
            return deleted_count
            
        except Exception as e:
            logger.warning(f"Failed to cleanup old crashes: {e}")
            return 0


# Global state manager instance
_state_manager: StateManager | None = None


def get_state_manager() -> StateManager:
    """
    Get the global state manager instance.

    Returns:
        Global StateManager instance
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def save_app_state(state: dict[str, Any]) -> bool:
    """
    Convenience function to save application state.

    Args:
        state: Dictionary containing application state

    Returns:
        True if save was successful, False otherwise
    """
    return get_state_manager().save_state(state)


def load_app_state() -> dict[str, Any] | None:
    """
    Convenience function to load application state.

    Returns:
        Dictionary containing application state, or None if no state exists
    """
    return get_state_manager().load_state()


def clear_app_state() -> bool:
    """
    Convenience function to clear application state.

    Returns:
        True if successful, False otherwise
    """
    return get_state_manager().clear_state()
