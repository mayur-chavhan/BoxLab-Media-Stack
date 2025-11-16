"""Configuration validation for stack deployments."""

import os
import pwd
import socket
from pathlib import Path

from arr_stack_manager.models.configuration import Configuration, PathConfig
from arr_stack_manager.models.stack import StackConfig
from arr_stack_manager.models.validation import ValidationResult
from arr_stack_manager.utils.services import SUPPORTED_SERVICES, get_service_metadata


class ConfigurationValidator:
    """Validates configuration before deployment."""

    def __init__(self) -> None:
        """Initialize the configuration validator."""
        pass

    def validate_paths(self, paths: PathConfig) -> ValidationResult:
        """
        Validate path existence and permissions.

        Args:
            paths: Path configuration to validate

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(valid=True)

        # Validate base path
        base_path = Path(paths.base_path)
        if not base_path.exists():
            result.add_error(
                f"Base path does not exist: {paths.base_path}\n"
                f"Remediation: Create the directory with: mkdir -p {paths.base_path}"
            )
        elif not base_path.is_dir():
            result.add_error(
                f"Base path is not a directory: {paths.base_path}\n"
                "Remediation: Specify a valid directory path"
            )
        else:
            # Check write permissions
            if not os.access(base_path, os.W_OK):
                result.add_error(
                    f"Base path is not writable: {paths.base_path}\n"
                    f"Remediation: Fix permissions with: sudo chmod u+w {paths.base_path}"
                )

            # Check read permissions
            if not os.access(base_path, os.R_OK):
                result.add_error(
                    f"Base path is not readable: {paths.base_path}\n"
                    f"Remediation: Fix permissions with: sudo chmod u+r {paths.base_path}"
                )

        # Validate config path
        if paths.config_path:
            config_path = Path(paths.config_path)
            if config_path.exists() and not config_path.is_dir():
                result.add_error(
                    f"Config path exists but is not a directory: {paths.config_path}\n"
                    "Remediation: Remove the file or choose a different path"
                )
            elif not config_path.exists():
                result.add_warning(
                    f"Config path does not exist and will be created: {paths.config_path}"
                )

        # Validate data path
        if paths.data_path:
            data_path = Path(paths.data_path)
            if data_path.exists() and not data_path.is_dir():
                result.add_error(
                    f"Data path exists but is not a directory: {paths.data_path}\n"
                    "Remediation: Remove the file or choose a different path"
                )
            elif not data_path.exists():
                result.add_warning(
                    f"Data path does not exist and will be created: {paths.data_path}"
                )

        return result

    def validate_ports(self, ports: list[int]) -> ValidationResult:
        """
        Validate port availability and detect conflicts.

        Args:
            ports: List of ports to validate

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(valid=True)

        # Check for duplicate ports in the list
        seen_ports: set[int] = set()
        for port in ports:
            if port in seen_ports:
                result.add_error(
                    f"Duplicate port detected: {port}\n"
                    "Remediation: Assign unique ports to each service"
                )
            seen_ports.add(port)

            # Validate port range
            if port < 1 or port > 65535:
                result.add_error(
                    f"Invalid port number: {port}\n"
                    "Remediation: Use a port between 1 and 65535"
                )
                continue

            # Check if port is in privileged range
            if port < 1024:
                result.add_warning(
                    f"Port {port} is in privileged range (< 1024)\n"
                    "This may require root privileges or special capabilities"
                )

            # Check if port is already in use
            if self._is_port_in_use(port):
                result.add_error(
                    f"Port {port} is already in use\n"
                    f"Remediation: Choose a different port or stop the conflicting service\n"
                    f"Check with: sudo lsof -i :{port}"
                )

        return result

    def _is_port_in_use(self, port: int) -> bool:
        """
        Check if a port is currently in use.

        Args:
            port: Port number to check

        Returns:
            True if port is in use, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(("127.0.0.1", port))
                return result == 0
        except (socket.error, OSError):
            return False

    def validate_permissions(self, puid: int, pgid: int) -> ValidationResult:
        """
        Validate PUID/PGID values.

        Args:
            puid: User ID to validate
            pgid: Group ID to validate

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(valid=True)

        # Validate PUID
        if puid < 0:
            result.add_error(
                f"Invalid PUID: {puid}\n"
                "Remediation: PUID must be a non-negative integer"
            )
        else:
            # Check if PUID exists in the system
            try:
                user_info = pwd.getpwuid(puid)
                result.add_warning(
                    f"PUID {puid} corresponds to user: {user_info.pw_name}"
                )
            except KeyError:
                result.add_warning(
                    f"PUID {puid} does not exist in the system\n"
                    "This may cause permission issues with mounted volumes"
                )

        # Validate PGID
        if pgid < 0:
            result.add_error(
                f"Invalid PGID: {pgid}\n"
                "Remediation: PGID must be a non-negative integer"
            )
        else:
            # Check if PGID exists in the system
            try:
                import grp

                group_info = grp.getgrgid(pgid)
                result.add_warning(
                    f"PGID {pgid} corresponds to group: {group_info.gr_name}"
                )
            except KeyError:
                result.add_warning(
                    f"PGID {pgid} does not exist in the system\n"
                    "This may cause permission issues with mounted volumes"
                )

        return result

    def validate_docker(self) -> ValidationResult:
        """
        Check Docker daemon availability.

        Returns:
            ValidationResult indicating if Docker is available
        """
        result = ValidationResult(valid=True)

        try:
            import docker

            try:
                client = docker.from_env()
                # Try to ping the Docker daemon
                client.ping()
                
                # Get Docker version info
                version_info = client.version()
                docker_version = version_info.get("Version", "unknown")
                result.add_warning(f"Docker daemon is available (version {docker_version})")
                
                client.close()
            except docker.errors.DockerException as e:
                result.add_error(
                    "Cannot connect to Docker daemon\n"
                    "Remediation:\n"
                    "  - Ensure Docker is installed and running\n"
                    "  - Check if your user has Docker permissions\n"
                    "  - Try: sudo systemctl start docker\n"
                    "  - Try: sudo usermod -aG docker $USER (then logout/login)\n"
                    f"Error details: {str(e)}"
                )
        except ImportError:
            result.add_error(
                "Docker Python SDK is not installed\n"
                "Remediation: Install with: pip install docker"
            )

        return result

    def validate_service_config(
        self, service_name: str, config: dict[str, object]
    ) -> ValidationResult:
        """
        Validate service-specific configuration.

        Args:
            service_name: Name of the service to validate
            config: Service configuration dictionary

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(valid=True)

        # Check if service is supported
        metadata = get_service_metadata(service_name)
        if metadata is None:
            result.add_error(
                f"Unsupported service: {service_name}\n"
                f"Remediation: Choose from supported services: {', '.join(SUPPORTED_SERVICES.keys())}"
            )
            return result

        # Validate port if specified
        if "port" in config:
            port = config["port"]
            if isinstance(port, int):
                port_result = self.validate_ports([port])
                result.merge(port_result)
            else:
                result.add_error(
                    f"Invalid port type for {service_name}: {type(port).__name__}\n"
                    "Remediation: Port must be an integer"
                )

        # Validate custom volumes if specified
        if "custom_volumes" in config:
            volumes = config["custom_volumes"]
            if isinstance(volumes, dict):
                for host_path, container_path in volumes.items():
                    if not isinstance(host_path, str) or not isinstance(container_path, str):
                        result.add_error(
                            f"Invalid volume mount for {service_name}: {host_path}:{container_path}\n"
                            "Remediation: Both host and container paths must be strings"
                        )
                    elif not container_path.startswith("/"):
                        result.add_error(
                            f"Invalid container path for {service_name}: {container_path}\n"
                            "Remediation: Container path must be absolute (start with /)"
                        )
            else:
                result.add_error(
                    f"Invalid custom_volumes type for {service_name}: {type(volumes).__name__}\n"
                    "Remediation: custom_volumes must be a dictionary"
                )

        # Service-specific validations
        if service_name in ["jellyfin", "emby", "plex"]:
            # Media servers should have access to media directory
            result.add_warning(
                f"{metadata['name']} requires access to media files\n"
                "Ensure the data path includes your media library"
            )

        if service_name == "recyclarr":
            # Recyclarr doesn't need a port
            if "port" in config and config["port"] != 0:
                result.add_warning(
                    "Recyclarr does not have a web UI and does not need a port"
                )

        if service_name == "unpackerr":
            # Unpackerr doesn't need a port
            if "port" in config and config["port"] != 0:
                result.add_warning(
                    "Unpackerr does not have a web UI and does not need a port"
                )

        return result

    def validate_complete_stack(self, stack: StackConfig) -> ValidationResult:
        """
        Perform full validation of a stack configuration.

        Args:
            stack: Complete stack configuration to validate

        Returns:
            ValidationResult with all validation errors and warnings
        """
        result = ValidationResult(valid=True)

        config = stack.configuration

        # Validate paths
        path_result = self.validate_paths(config.paths)
        result.merge(path_result)

        # Validate permissions
        perm_result = self.validate_permissions(config.puid, config.pgid)
        result.merge(perm_result)

        # Validate Docker availability
        docker_result = self.validate_docker()
        result.merge(docker_result)

        # Collect all ports from enabled services
        ports: list[int] = []
        for service_name, service_config in config.services.items():
            if service_config.enabled and service_config.port > 0:
                ports.append(service_config.port)

        # Validate ports
        if ports:
            port_result = self.validate_ports(ports)
            result.merge(port_result)

        # Validate each service configuration
        for service_name, service_config in config.services.items():
            if service_config.enabled:
                service_result = self.validate_service_config(
                    service_name,
                    {
                        "port": service_config.port,
                        "custom_volumes": service_config.custom_volumes,
                        "environment_vars": service_config.environment_vars,
                    },
                )
                result.merge(service_result)

        # Check if at least one service is enabled
        enabled_services = config.get_selected_services()
        if not enabled_services:
            result.add_error(
                "No services are enabled\n"
                "Remediation: Enable at least one service in the configuration"
            )
        else:
            result.add_warning(
                f"Stack will deploy {len(enabled_services)} service(s): {', '.join(enabled_services)}"
            )

        return result
