"""Docker prerequisite checker and permission helper."""

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class DockerCheckResult:
    """Result of Docker prerequisite check."""

    def __init__(
        self,
        docker_installed: bool,
        docker_running: bool,
        has_permission: bool,
        is_root: bool,
        in_docker_group: bool,
        error_message: str | None = None,
        remediation_steps: list[str] | None = None,
    ):
        self.docker_installed = docker_installed
        self.docker_running = docker_running
        self.has_permission = has_permission
        self.is_root = is_root
        self.in_docker_group = in_docker_group
        self.error_message = error_message
        self.remediation_steps = remediation_steps or []

    @property
    def is_ready(self) -> bool:
        """Check if Docker is ready to use."""
        return self.docker_installed and self.docker_running and self.has_permission


def check_docker_prerequisites() -> DockerCheckResult:
    """
    Check if Docker is installed, running, and accessible.

    Returns:
        DockerCheckResult with detailed status and remediation steps
    """
    # Check if running as root
    is_root = os.geteuid() == 0

    # Check if Docker is installed
    docker_installed = _check_docker_installed()
    if not docker_installed:
        return DockerCheckResult(
            docker_installed=False,
            docker_running=False,
            has_permission=False,
            is_root=is_root,
            in_docker_group=False,
            error_message="Docker is not installed",
            remediation_steps=[
                "Install Docker using your system's package manager:",
                "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install docker.io",
                "  Fedora: sudo dnf install docker",
                "  Arch: sudo pacman -S docker",
                "Or visit: https://docs.docker.com/engine/install/",
            ],
        )

    # Check if Docker daemon is running
    docker_running = _check_docker_running()
    if not docker_running:
        return DockerCheckResult(
            docker_installed=True,
            docker_running=False,
            has_permission=False,
            is_root=is_root,
            in_docker_group=False,
            error_message="Docker daemon is not running",
            remediation_steps=[
                "Start the Docker service:",
                "  sudo systemctl start docker",
                "Enable Docker to start on boot:",
                "  sudo systemctl enable docker",
            ],
        )

    # Check if user has permission to access Docker
    has_permission, in_docker_group = _check_docker_permission()

    if not has_permission:
        if is_root:
            # Root user should have permission but doesn't - unusual case
            return DockerCheckResult(
                docker_installed=True,
                docker_running=True,
                has_permission=False,
                is_root=True,
                in_docker_group=False,
                error_message="Cannot access Docker socket even as root",
                remediation_steps=[
                    "Check Docker socket permissions:",
                    "  ls -l /var/run/docker.sock",
                    "Try restarting Docker:",
                    "  sudo systemctl restart docker",
                ],
            )
        else:
            # Regular user without permission
            username = os.getenv("USER", "your-username")
            return DockerCheckResult(
                docker_installed=True,
                docker_running=True,
                has_permission=False,
                is_root=False,
                in_docker_group=in_docker_group,
                error_message="Permission denied accessing Docker socket",
                remediation_steps=[
                    f"Add your user to the docker group:",
                    f"  sudo usermod -aG docker {username}",
                    "Then log out and log back in for changes to take effect",
                    "",
                    "OR run this application with sudo:",
                    "  sudo python -m arr_stack_manager",
                    "",
                    "OR fix socket permissions (temporary):",
                    "  sudo chmod 666 /var/run/docker.sock",
                ],
            )

    # All checks passed
    return DockerCheckResult(
        docker_installed=True,
        docker_running=True,
        has_permission=True,
        is_root=is_root,
        in_docker_group=in_docker_group,
    )


def _check_docker_installed() -> bool:
    """Check if Docker is installed."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_docker_running() -> bool:
    """Check if Docker daemon is running."""
    try:
        # Try to ping the Docker daemon
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_docker_permission() -> tuple[bool, bool]:
    """
    Check if current user has permission to access Docker.

    Returns:
        Tuple of (has_permission, in_docker_group)
    """
    # Check if user is in docker group
    in_docker_group = _is_in_docker_group()

    # Try to access Docker socket
    docker_socket = Path("/var/run/docker.sock")
    if not docker_socket.exists():
        return False, in_docker_group

    # Check if we can read/write the socket
    try:
        has_permission = os.access(docker_socket, os.R_OK | os.W_OK)
        return has_permission, in_docker_group
    except Exception:
        return False, in_docker_group


def _is_in_docker_group() -> bool:
    """Check if current user is in the docker group."""
    try:
        import grp

        docker_group = grp.getgrnam("docker")
        return os.getegid() == docker_group.gr_gid or docker_group.gr_gid in os.getgroups()
    except (KeyError, ImportError):
        return False


def print_docker_check_result(result: DockerCheckResult) -> None:
    """Print Docker check result in a user-friendly format."""
    print("\n" + "=" * 70)
    print("Docker Prerequisites Check")
    print("=" * 70)

    print(f"\n✓ Docker Installed: {'Yes' if result.docker_installed else 'No'}")
    print(f"✓ Docker Running: {'Yes' if result.docker_running else 'No'}")
    print(f"✓ Has Permission: {'Yes' if result.has_permission else 'No'}")
    print(f"  - Running as root: {'Yes' if result.is_root else 'No'}")
    print(f"  - In docker group: {'Yes' if result.in_docker_group else 'No'}")

    if not result.is_ready:
        print(f"\n❌ Error: {result.error_message}")
        print("\nHow to fix:")
        for step in result.remediation_steps:
            print(f"  {step}")

    print("\n" + "=" * 70 + "\n")


def can_fix_permissions_automatically() -> bool:
    """Check if we can automatically fix Docker permissions."""
    # We can fix if:
    # 1. User has sudo access
    # 2. Docker socket exists
    docker_socket = Path("/var/run/docker.sock")
    if not docker_socket.exists():
        return False

    # Check if user can use sudo
    try:
        result = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            timeout=2,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def fix_docker_permissions() -> bool:
    """
    Attempt to fix Docker permissions automatically.

    Returns:
        True if permissions were fixed successfully
    """
    username = os.getenv("USER")
    if not username:
        logger.error("Cannot determine current username")
        return False

    try:
        # Add user to docker group
        logger.info(f"Adding user {username} to docker group...")
        result = subprocess.run(
            ["sudo", "usermod", "-aG", "docker", username],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            logger.error(f"Failed to add user to docker group: {result.stderr}")
            return False

        logger.info("Successfully added user to docker group")
        logger.info("Note: You need to log out and log back in for changes to take effect")
        return True

    except Exception as e:
        logger.error(f"Failed to fix Docker permissions: {e}")
        return False
