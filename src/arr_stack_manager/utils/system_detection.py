"""System detection utilities for first-run setup."""

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SystemDetector:
    """Detect system information for automatic configuration."""

    @staticmethod
    def get_current_user_info() -> tuple[int, int]:
        """
        Get the current user's PUID and PGID.

        Returns:
            Tuple of (puid, pgid)
        """
        try:
            puid = os.getuid()
            pgid = os.getgid()
            logger.info(f"Detected user: PUID={puid}, PGID={pgid}")
            return puid, pgid
        except AttributeError:
            # Windows doesn't have getuid/getgid
            logger.warning("Unable to detect PUID/PGID on this platform")
            return 1000, 1000

    @staticmethod
    def get_current_username() -> str:
        """
        Get the current username.

        Returns:
            Username string
        """
        try:
            import pwd

            username = pwd.getpwuid(os.getuid()).pw_name
            logger.info(f"Detected username: {username}")
            return username
        except (ImportError, KeyError):
            # Fallback for Windows or if pwd module is unavailable
            username = os.getenv("USER") or os.getenv("USERNAME") or "user"
            logger.info(f"Detected username (fallback): {username}")
            return username

    @staticmethod
    def detect_timezone() -> str:
        """
        Detect the system timezone.

        Returns:
            Timezone string (e.g., "America/New_York")
        """
        try:
            # Try to read from /etc/timezone (Debian/Ubuntu)
            timezone_file = Path("/etc/timezone")
            if timezone_file.exists():
                timezone = timezone_file.read_text().strip()
                logger.info(f"Detected timezone from /etc/timezone: {timezone}")
                return timezone
        except Exception as e:
            logger.debug(f"Could not read /etc/timezone: {e}")

        try:
            # Try to get timezone from timedatectl (systemd)
            result = subprocess.run(
                ["timedatectl", "show", "-p", "Timezone", "--value"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                timezone = result.stdout.strip()
                if timezone:
                    logger.info(f"Detected timezone from timedatectl: {timezone}")
                    return timezone
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug(f"Could not get timezone from timedatectl: {e}")

        try:
            # Try to read symlink from /etc/localtime
            localtime = Path("/etc/localtime")
            if localtime.is_symlink():
                target = localtime.resolve()
                # Extract timezone from path like /usr/share/zoneinfo/America/New_York
                parts = target.parts
                if "zoneinfo" in parts:
                    idx = parts.index("zoneinfo")
                    timezone = "/".join(parts[idx + 1 :])
                    logger.info(f"Detected timezone from /etc/localtime: {timezone}")
                    return timezone
        except Exception as e:
            logger.debug(f"Could not read /etc/localtime: {e}")

        # Fallback to UTC
        logger.warning("Could not detect timezone, defaulting to UTC")
        return "UTC"

    @staticmethod
    def check_docker_available() -> tuple[bool, Optional[str]]:
        """
        Check if Docker is available and get version.

        Returns:
            Tuple of (is_available, version_string)
        """
        try:
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"Docker is available, version: {version}")
                return True, version
            else:
                logger.warning("Docker command failed")
                return False, None
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning(f"Docker not available: {e}")
            return False, None

    @staticmethod
    def get_system_info() -> dict[str, str]:
        """
        Get general system information.

        Returns:
            Dictionary with system information
        """
        info = {
            "os": platform.system(),
            "os_version": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
        }
        logger.info(f"System info: {info}")
        return info

    @staticmethod
    def suggest_base_path() -> Path:
        """
        Suggest a default base path for stack configuration.

        Returns:
            Suggested base path
        """
        # Check common locations
        candidates = [
            Path("/opt/arr-stacks"),
            Path.home() / "arr-stacks",
            Path("/mnt/storage/arr-stacks"),
            Path("/data/arr-stacks"),
        ]

        for path in candidates:
            # Check if parent directory exists and is writable
            if path.parent.exists() and os.access(path.parent, os.W_OK):
                logger.info(f"Suggested base path: {path}")
                return path

        # Fallback to home directory
        fallback = Path.home() / "arr-stacks"
        logger.info(f"Using fallback base path: {fallback}")
        return fallback

    @staticmethod
    def check_disk_space(path: Path, required_gb: float = 10.0) -> tuple[bool, float]:
        """
        Check if there's enough disk space at the given path.

        Args:
            path: Path to check
            required_gb: Required space in GB

        Returns:
            Tuple of (has_enough_space, available_gb)
        """
        try:
            import shutil

            stat = shutil.disk_usage(path if path.exists() else path.parent)
            available_gb = stat.free / (1024**3)
            has_enough = available_gb >= required_gb
            logger.info(
                f"Disk space at {path}: {available_gb:.2f} GB available "
                f"(required: {required_gb} GB)"
            )
            return has_enough, available_gb
        except Exception as e:
            logger.error(f"Could not check disk space: {e}")
            return False, 0.0
